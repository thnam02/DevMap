"""Add RQ2's ablation (Proviso with each selection part off, as B1_ABLATE=all) to B1 rows recorded without it, from
each pair's saved map: selection only, no test run. Per pair (status ok): the map and base outcomes saved at P
($PROVISO_WORK/PROJECT/b1/<id>/covmap.json, base_outcomes.json), scenarios S and F rebuilt on a separate tree, every
ablation variant selected with b1._proviso and scored with b1.score against the row's confirmed failures. As a check,
Proviso itself is selected again and compared with the row's own selection (count and misses).

  python research/v2/b1_ablate_rows.py PROJECT [--dry-run] [--only ID ...]

Rows get proviso-<part> entries in S/F tools (as b1.selections writes them) and "ablation_offline" (date, parts, the
check). --dry-run prints and writes nothing. Run it only when no b1.py run on PROJECT is writing rows."""
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


def ablate(tree, cov, universe, plain, truth, ref, edited, row_tools):
    sets, extra = {}, {}
    s, why, _, warm = b1._proviso(tree, cov, universe)
    sets["proviso"] = set(universe) if s is None else s
    for part in b1.SELECTION_PARTS:
        s, _, _, warm = b1._proviso(tree, cov, universe, part)
        sets[f"proviso-{part}"] = set(universe) if s is None else s
        extra[f"proviso-{part}"] = {"full": s is None, "selection_s": warm}
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
    b1.use(name)
    files = sorted(glob.glob(os.path.join(b1.res(), "rows.w*.jsonl")))
    tree = None
    for path in files:
        rows = [json.loads(l) for l in open(path) if l.strip()]
        changed_any = False
        for r in rows:
            if r.get("status") != "ok" or (only and r["id"][:12] not in only and r["id"] not in only):
                continue
            if any(k.startswith("proviso-") for k in (r.get("S") or {}).get("tools", {})):
                continue   # already has the ablation
            p, c = r["parent"], r["id"]
            d = os.path.join(PL.WORK, "b1", c[:12])
            cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
            if not cov or not base or (cov.get("__base__") or {}).get("commit") != p:
                print(f"{c[:10]}: no usable saved map/base outcomes at P; left without ablation", flush=True)
                continue
            plain = {k: tt for k, (ok_, tt) in base.items()}
            base_fail = PL.failing(base)
            universe = PL.universe_of(cov, base_fail)
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
                scored, checks[sc] = ablate(tree, cov, universe, plain, set(r[sc]["failing"]), ref, edited,
                                            r[sc]["tools"])
                r[sc]["tools"].update(scored)
            b1.to_parent(tree, p)
            r["ablation_offline"] = {"date": time.strftime("%Y-%m-%d"), "parts": b1.SELECTION_PARTS,
                                     "from": "saved map at P, selection only", "check_proviso": checks}
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
