"""(v2.3.1 freeze check, follow-up) Is a test that record_speed_check.py lists "beyond noise" really changed by the new
recorder, or is it noise the two old recordings did not show? For each listed test, record only its test file RUNS times
with the old code and RUNS times with the new code (same tree and commit as record_speed_check.py), then compare that
test's record (own record united with its fixture records) within the old runs, within the new runs, and old vs new.

  python research/v2/record_pertest_check.py REPO --old-src OLD/src --new-src NEW/src [--runs 5] [--tests T ...]

Default tests: "beyond_noise" of results/record_speed/REPO.json. Verdict per test:
  noise  the record varies within the old runs (not caused by the new code)
  real   identical in all old runs and in all new runs, but old != new (diff shown)
  same   identical in all runs, old == new (the difference does not reproduce when the file is recorded alone)
  new-varies  identical in all old runs, varies within the new runs
Results: results/record_speed/pertest/REPO.json; maps in $PROVISO_WORK/record_speed_maps/pertest/."""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from record_speed_check import _full  # noqa: E402


def record_file(src: str, repo: str, target: str, out: str) -> float:
    code = f"""
import os, sys, time
sys.path.insert(0, {src!r})
from dc_engine import record as REC
sys.path.insert(1, {HERE!r})
import pipeline as PL
assert REC.__file__.startswith({src!r}), REC.__file__
PL.use({repo!r}); CFG = PL.CFG
tree = os.path.join(PL.WORK, "trees", "incr")
if not os.path.isdir(os.path.join(tree, ".git")):
    tree = PL.make_tree("incr", CFG["commit"])
t = time.time()
REC.record(tree, CFG["pkg"], {out!r}, PL.PY, [{target!r}], 1, CFG["before_test"],
           ["-p", "no:randomly", *CFG["pytest_args"]], PL.env(tree, [PL.PLUG]))
print(time.time() - t)
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"recording {target} with {src} failed: {(r.stdout + r.stderr)[-1500:]}")
    return round(float(r.stdout.strip().splitlines()[-1]), 1)


def canon(rec: dict | None) -> str:
    if rec is None:
        return "<missing>"
    return json.dumps({k: sorted(map(list, v)) if k == "funcs" else (sorted(v) if isinstance(v, set) else v)
                       for k, v in rec.items()}, sort_keys=True)


def diff(a: dict, b: dict) -> dict:
    out = {}
    for k in ("funcs", "classes", "files", "dirs"):
        only_a, only_b = sorted(map(str, a[k] - b[k])), sorted(map(str, b[k] - a[k]))
        if only_a or only_b:
            out[k] = {"only_old": only_a, "only_new": only_b}
    if a["always"] != b["always"]:
        out["always"] = {"old": a["always"], "new": b["always"]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--old-src", required=True)
    ap.add_argument("--new-src", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--tests", nargs="*")
    a = ap.parse_args()
    tests = a.tests or json.load(open(os.path.join(HERE, "results", "record_speed", f"{a.repo}.json")))["beyond_noise"]
    by_file = collections.OrderedDict()
    for t in tests:
        by_file.setdefault(t.split("::", 1)[0], []).append(t)
    maps = os.path.join(os.environ.get("PROVISO_WORK") or tempfile.gettempdir(), "record_speed_maps", "pertest")
    os.makedirs(maps, exist_ok=True)
    res = {"repo": a.repo, "runs": a.runs, "files": {}, "tests": {}}
    for f, ts in by_file.items():
        recs = {"old": [], "new": []}
        secs = {"old": [], "new": []}
        for k in range(a.runs):          # interleaved old/new, so drift over time hits both sides alike
            for side, src in (("old", a.old_src), ("new", a.new_src)):
                p = os.path.join(maps, f"{a.repo}-{f.replace('/', '_')}-{side}{k}.json")
                secs[side].append(record_file(src, a.repo, f, p))
                m = json.load(open(p))
                recs[side].append({t: (_full(m, t) if t in m else None) for t in ts})
        res["files"][f] = {"seconds": secs}
        for t in ts:
            old = [r[t] for r in recs["old"]]
            new = [r[t] for r in recs["new"]]
            co, cn = {canon(x) for x in old}, {canon(x) for x in new}
            if len(co) > 1:
                verdict = "noise"
            elif len(cn) > 1:
                verdict = "new-varies"
            elif co != cn:
                verdict = "real"
            else:
                verdict = "same"
            row = {"verdict": verdict, "distinct_old": len(co), "distinct_new": len(cn),
                   "missing_old": sum(x is None for x in old), "missing_new": sum(x is None for x in new)}
            if verdict == "real" and old[0] is not None and new[0] is not None:
                row["diff"] = diff(old[0], new[0])
            res["tests"][t] = row
            print(f"{verdict:10s} old {len(co)} distinct / new {len(cn)} distinct  {t}", flush=True)
    res["summary"] = dict(collections.Counter(r["verdict"] for r in res["tests"].values()))
    d = os.path.join(HERE, "results", "record_speed", "pertest")
    os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{a.repo}.json"), "w"), indent=1)
    print(json.dumps(res["summary"]))


if __name__ == "__main__":
    main()
