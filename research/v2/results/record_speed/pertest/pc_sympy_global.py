"""Is sympy/core/power.py:656 in __global__ of the per-file maps (old vs new)? Also: do __global__ records differ?"""
import collections
import glob
import json
import os
import re

d = os.path.expanduser("~/proviso-work/v2/record_speed_maps/pertest")
hit = collections.Counter()
tot = collections.Counter()
glob_sets = collections.defaultdict(set)
for p in sorted(glob.glob(os.path.join(d, "sympy-*.json"))):
    m = re.match(r"sympy-(.+)-(old|new)\d\.json", os.path.basename(p))
    f, side = m.group(1), m.group(2)
    g = json.load(open(p)).get("__global__") or {}
    funcs = {tuple(x) for x in g.get("funcs", [])}
    tot[side] += 1
    hit[side] += ("sympy/core/power.py", 656) in funcs
    glob_sets[(f, side)].add(json.dumps(g, sort_keys=True))
print("maps with power.py:656 in __global__:", {s: f"{hit[s]}/{tot[s]}" for s in tot})
files = sorted({f for f, _ in glob_sets})
var_old = sum(len(glob_sets[(f, "old")]) > 1 for f in files)
var_new = sum(len(glob_sets[(f, "new")]) > 1 for f in files)
diff = sum(glob_sets[(f, "old")] != glob_sets[(f, "new")] for f in files)
print(f"files {len(files)}: __global__ varies within old in {var_old}, within new in {var_new}, old-set != new-set in {diff}")
