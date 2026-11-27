"""RQ2's ablation for B1 rows, from each pair's saved map: selection only, no test run, each variant selected ONCE.
Variants (the rows of the paper's RQ2 table), recorded as tools "proviso-<variant>" in scenarios S and F:
  snapshot    PROVISO_OFF=snapshot
  files       PROVISO_OFF=files
  nameindex   PROVISO_OFF=callers,bindings
  fallbacks   PROVISO_OFF=config,data,syntax,newfiles
  nofixattr   the map without fixture attribution (emulated, see no_fixture_attribution and results/b1/ABLATION.md)
Per pair (status ok): the map and base outcomes saved at P ($PROVISO_WORK/PROJECT/b1/<id>/), scenarios S and F rebuilt
on a separate tree, each variant selected once and scored with b1.score against the row's confirmed failures. As a
check, Proviso itself is selected once more and compared with the row's own selection (count and misses).

  python research/v2/b1_ablate_rows.py PROJECT [--dry-run] [--only ID ...] [--pause-file F]

Rows get the variants in S/F tools and "ablation_offline" (date, variants, the check). --dry-run writes nothing.
--pause-file F: before each pair, wait while F does not exist or the 1-minute load is above GATE_MAX_LOAD (default 8):
run only while another job has yielded the CPU and the CPU is free.
Run it only when no b1.py run on PROJECT is writing rows."""
from __future__ import annotations

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
from dc_engine import impact as I  # noqa: E402

VARIANTS = [("snapshot", ["snapshot"]), ("files", ["files"]), ("nameindex", ["callers", "bindings"]),
            ("fallbacks", ["config", "data", "syntax", "newfiles"]), ("nofixattr", None)]


def no_fixture_attribution(cov: dict) -> dict:
    """The map a recorder without fixture attribution would give, emulated: a fixture instance shared by several tests
    (class, module or session scope; and the "<session>" record) stays only on the FIRST test in its file that lists it
    (each test file is recorded in its own process, in execution order, which the map keeps). Function-scoped
    instances (their scope node is the test itself), package-import records ("<import>@...") and setup/teardown
    records ("<setup/teardown>@...") stay as they are."""
    out, first = dict(cov), set()
    for n, v in cov.items():
        if n.startswith("__") or not isinstance(v, dict) or "fx" not in v:
            continue
        f = n.split("::", 1)[0]
        keep = []
        for k in v["fx"]:
            if k.startswith("<import>@") or k.startswith("<setup/teardown>@") or f"@{n}[" in k:
                keep.append(k)
            elif (f, k) not in first:
                first.add((f, k))
                keep.append(k)
        out[n] = {**v, "fx": keep}
    return out


def select_once(tree, cov, universe, off=None):
    old = os.environ.get("PROVISO_OFF")
    if off:
        os.environ["PROVISO_OFF"] = ",".join(off)
    try:
        t = time.time()
        sel, why = I.selection(tree, cov, PL.PY)
        secs = round(time.time() - t, 2)
    finally:
        if off:
            if old is None:
                os.environ.pop("PROVISO_OFF", None)
            else:
                os.environ["PROVISO_OFF"] = old
    return (set(universe) if sel is None else set(sel) & universe), sel is None, secs


def ablate(tree, cov, cov_nofix, universe, plain, truth, ref, edited, row_tools):
    sets, extra = {}, {}
    sets["proviso"], _, _ = select_once(tree, cov, universe)
    for name, off in VARIANTS:
        s, full, secs = select_once(tree, cov_nofix if name == "nofixattr" else cov, universe, off)
        sets[f"proviso-{name}"] = s
        extra[f"proviso-{name}"] = {"full": full, "selection_s": secs}
    scored = b1.score(sets, extra, universe, plain, truth, ref, edited)
    mine, old = scored.pop("proviso"), row_tools.get("proviso", {})
    check = {"selected": mine["selected"], "row_selected": old.get("selected"),
             "missed": len(mine["missed"]), "row_missed": len(old.get("missed", [])),
             "same": mine["selected"] == old.get("selected") and mine["missed"] == old.get("missed")}
    return scored, check


def main():
    a = sys.argv[1:]
    name, dry = a[0], "--dry-run" in a
    only = set(a[a.index("--only") + 1:]) if "--only" in a else None
    gate = a[a.index("--pause-file") + 1] if "--pause-file" in a else None
    b1.use(name)
    tree = None
    for path in sorted(glob.glob(os.path.join(b1.res(), "rows.w*.jsonl"))):
        rows = [json.loads(l) for l in open(path) if l.strip()]
        changed_any = False
        for r in rows:
            if r.get("status") != "ok" or (only and r["id"][:10] not in {x[:10] for x in only}):
                continue
            if all(f"proviso-{v}" in (r.get("S") or {}).get("tools", {}) for v, _ in VARIANTS):
                continue
            while gate and (not os.path.exists(gate) or os.getloadavg()[0] > float(os.environ.get("GATE_MAX_LOAD", "8"))):
                time.sleep(60)
            p, c = r["parent"], r["id"]
            d = os.path.join(PL.WORK, "b1", c[:12])
            cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
            if not cov or not base or (cov.get("__base__") or {}).get("commit") != p:
                print(f"{c[:10]}: no usable saved map/base outcomes at P; left without ablation", flush=True)
                continue
            cov_nofix = no_fixture_attribution(cov)
            plain = {k: tt for k, (ok_, tt) in base.items()}
            universe = PL.universe_of(cov, PL.failing(base))
            tree = PL.make_tree("b1-ablate", p)
            b1.use_targets(tree)
            if PL.CFG.get("sync"):
                PL.CFG["sync"](tree, PL.PY)
            t = time.time()
            checks = {}
            for sc in ("S", "F"):
                if sc not in r or r[sc].get("timeout"):
                    continue
                b1.to_parent(tree, p)
                if sc == "S":
                    b1.apply_source(tree, p, c)
                    edited = []
                else:
                    b1.apply_full(tree, p, c)
                    edited = [f for _, f in b1._changed(tree, p, c) if I._is_test_path(f) and f.endswith(".py")]
                ref, _ = b1.affected(tree, cov, universe)
                scored, checks[sc] = ablate(tree, cov, cov_nofix, universe, plain, set(r[sc]["failing"]), ref,
                                            edited, r[sc]["tools"])
                r[sc]["tools"].update(scored)
                if dry:
                    print(f"  {c[:10]} {sc}: " + "; ".join(
                        f"{k[8:]} {v['selected']}/{len(universe)} missed {len(v['missed'])} {v['selection_s']} s"
                        for k, v in scored.items()), flush=True)
            b1.to_parent(tree, p)
            r["ablation_offline"] = {"date": time.strftime("%Y-%m-%d"), "variants": dict(VARIANTS),
                                     "from": "saved map at P, selection only, each variant once",
                                     "check_proviso": checks}
            changed_any = True
            print(f"{c[:10]}: universe {len(universe)} (row {r['universe']}); proviso reproduced: "
                  f"{ {k: v['same'] for k, v in checks.items()} }; {round(time.time() - t, 1)} s", flush=True)
        if changed_any and not dry:
            tmp = path + ".tmp"
            with open(tmp, "w") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            os.replace(tmp, path)
            print(f"rewrote {path}", flush=True)
    if tree:
        PL.reset(tree)


if __name__ == "__main__":
    main()
