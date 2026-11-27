"""sqlalchemy freeze-check diagnostic, variants A-D (2 runs each), compared with the old recordings (8e8f0bb) of the
freeze check (same incr tree, same commit). Nothing under the repository's src/ is changed: C/D use a scratch copy of
src outside the repository with the covplugin fast path switched off.
  A  new src as-is, record_times.json present (longest-first order active)
  B  new src, record_times.json removed before each run (collection order, as the old code)
  C  scratch src, fast path off (covplugin._start: m = None), times present
  D  scratch src, fast path off, times removed
  python diag_abcd.py [RUNS]"""
import collections
import json
import os
import shutil
import subprocess
import sys
import time

REPO_DIR = os.path.expanduser("~/proviso-dev")
sys.path.insert(0, os.path.join(REPO_DIR, "research/v2"))
import record_speed_check as RSC  # noqa: E402

repo = "sqlalchemy"
runs = int(sys.argv[1]) if len(sys.argv) > 1 else 2
work = os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2"))
maps = os.path.join(work, "record_speed_maps")
tree = os.path.join(work, repo, "trees", "incr")
times = os.path.join(tree, ".dc-engine", "record_times.json")
new_src = os.path.join(REPO_DIR, "src")

# scratch src with the fast path off (outside the repository)
scratch = os.path.expanduser("~/proviso-scratch/src-nofastpath")
shutil.rmtree(scratch, ignore_errors=True)
shutil.copytree(new_src, scratch, ignore=shutil.ignore_patterns("__pycache__"))
cp = os.path.join(scratch, "dc_engine", "covplugin.py")
code = open(cp).read()
old_line = "    m = _meth.get(id(code))\n"
assert code.count(old_line) == 1, "fast-path line not found exactly once"
open(cp, "w").write(code.replace(old_line, "    m = None   # DIAGNOSTIC: v2.3.1 fast path off\n"))
patch = subprocess.run(["diff", "-u", os.path.join(new_src, "dc_engine/covplugin.py"), cp], capture_output=True,
                       text=True).stdout

old1, old2 = (json.load(open(os.path.join(maps, f"{repo}-{k}.json"))) for k in ("old1", "old2"))
noise = RSC.differing(old1, old2)


def fixture_diff(a, b):
    fa, fb = a.get("__fixtures__") or {}, b.get("__fixtures__") or {}
    out = {}
    for k in sorted(set(fa) | set(fb)):
        if fa.get(k) != fb.get(k):
            ra, rb = fa.get(k) or {}, fb.get(k) or {}
            d = {}
            for part in ("funcs", "classes", "files"):
                sa = {json.dumps(x) for x in ra.get(part, [])}
                sb = {json.dumps(x) for x in rb.get(part, [])}
                if sa != sb:
                    d[part] = {"only_old": sorted(sa - sb)[:8], "only_new": sorted(sb - sa)[:8]}
            out[k] = d or {"other": "differs outside funcs/classes/files"}
    return out


variants = [("A", new_src, False), ("B", new_src, True), ("C", scratch, False), ("D", scratch, True)]
res = {"repo": repo, "runs": runs, "noise_old1_old2": len(noise), "patch": patch, "variants": {}}
for name, src, drop_times in variants:
    rows = []
    for k in range(runs):
        if drop_times and os.path.exists(times):
            os.remove(times)
        had_times = os.path.exists(times)
        p = os.path.join(maps, f"{repo}-diag{name}{k}.json")
        secs = RSC.record(src, repo, p, int(os.environ.get("DIAG_WORKERS", "8")))
        m = json.load(open(p))
        ch = RSC.differing(old1, m)
        fx = fixture_diff(old1, m)
        row = {"run": k, "times_file_before": had_times, "seconds": secs, "vs_old1": len(ch),
               "beyond_noise": len(ch - noise), "same_global": m.get("__global__") == old1.get("__global__"),
               "fixture_records_differing": len(fx), "fixture_examples": dict(list(fx.items())[:6])}
        rows.append(row)
        print(name, k, json.dumps({x: row[x] for x in row if x != "fixture_examples"}), flush=True)
    res["variants"][name] = rows
json.dump(res, open(os.path.expanduser("~/proviso-logs/diag_abcd_sqlalchemy.json"), "w"), indent=1)
print("== DIAG ABCD DONE")
