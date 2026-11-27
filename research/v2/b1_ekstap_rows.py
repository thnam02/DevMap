"""Add EkstaP (NameRTS's file-level baseline, see ekstap_driver.py) to B1 rows recorded before it was integrated:
per pair (status ok), EkstaP's init on a tree at P (its own dependency run, timed as ekstap_init_s) and its selection for
scenarios S and F, scored with b1.score against the row's confirmed failures (affected-tests references from the pair's
saved map). No other test run.

  python research/v2/b1_ekstap_rows.py PROJECT [--dry-run] [--only ID ...] [--pause-file F]

--pause-file F: before each pair, wait while F does not exist or the 1-minute load is above GATE_MAX_LOAD (default 8).

--dry-run prints (selected files vs the failing tests' files) and writes nothing. Run it only when no b1.py run on
PROJECT is writing rows."""
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


def main():
    a = sys.argv[1:]
    name, dry = a[0], "--dry-run" in a
    only = set(a[a.index("--only") + 1:]) if "--only" in a else None
    gate = a[a.index("--pause-file") + 1] if "--pause-file" in a else None
    b1.use(name)
    for path in sorted(glob.glob(os.path.join(b1.res(), "rows.w*.jsonl"))):
        rows = [json.loads(l) for l in open(path) if l.strip()]
        changed_any = False
        for r in rows:
            if r.get("status") != "ok" or (only and r["id"][:10] not in {x[:10] for x in only}):
                continue
            if "ekstap" in (r.get("S") or {}).get("tools", {}):
                continue
            while gate and (not os.path.exists(gate) or os.getloadavg()[0] > float(os.environ.get("GATE_MAX_LOAD", "8"))):
                time.sleep(60)
            p, c = r["parent"], r["id"]
            d = os.path.join(PL.WORK, "b1", c[:12])
            cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
            if not cov or not base or (cov.get("__base__") or {}).get("commit") != p:
                print(f"{c[:10]}: no usable saved map/base outcomes at P; left without EkstaP", flush=True)
                continue
            plain = {k: tt for k, (ok_, tt) in base.items()}
            universe = PL.universe_of(cov, PL.failing(base))
            tree = PL.make_tree("b1-ekbf", p)
            b1.use_targets(tree)
            if PL.CFG.get("sync"):
                PL.CFG["sync"](tree, PL.PY)
            cache = os.path.join(d, "ek-cache")
            t = time.time()
            try:
                b1.ekstap("init", tree, cache)
                init_s = round(time.time() - t, 1)
            except Exception as e:  # noqa: BLE001
                init_s, err = None, repr(e)[:300]
            out = {}
            for sc in ("S", "F"):
                if sc not in r or r[sc].get("timeout"):
                    continue
                b1.to_parent(tree, p)
                if init_s is None:
                    out[sc] = {"error": err}
                    continue
                if sc == "S":
                    b1.apply_source(tree, p, c)
                    edited = []
                else:
                    b1.apply_full(tree, p, c)
                    edited = [f for _, f in b1._changed(tree, p, c) if I._is_test_path(f) and f.endswith(".py")]
                ref, _ = b1.affected(tree, cov, universe)
                try:
                    got, secs = b1._timed(b1.ekstap, "select", tree, cache)
                except Exception as e:  # noqa: BLE001
                    out[sc] = {"error": repr(e)[:300]}
                    continue
                sel = {n for n in universe if n.split("::", 1)[0] in set(got)}
                truth = set(r[sc]["failing"])
                out[sc] = b1.score({"ekstap": sel}, {"ekstap": {"selection_s": secs, "files": len(set(got))}},
                                   universe, plain, truth, ref, edited)["ekstap"]
                fail_files = sorted(b1._files(truth))
                print(f"{c[:10]} {sc}: EkstaP {len(set(got))} files, {out[sc]['selected']}/{len(universe)} tests, "
                      f"missed {len(out[sc]['missed'])}; failing tests' files {fail_files} "
                      f"all selected: {set(fail_files) <= set(got) | set(edited)}; select {secs} s", flush=True)
            b1.to_parent(tree, p)
            print(f"{c[:10]}: EkstaP init {init_s} s", flush=True)
            for sc, v in out.items():
                r[sc]["tools"]["ekstap"] = v
            r["ekstap_init_s"] = init_s
            r["ekstap_offline"] = {"date": time.strftime("%Y-%m-%d"), "from": "init at P + selection, no other test run"}
            changed_any = True
        if changed_any and not dry:
            tmp = path + ".tmp"
            with open(tmp, "w") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            os.replace(tmp, path)
            print(f"rewrote {path}", flush=True)


if __name__ == "__main__":
    main()
