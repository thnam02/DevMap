"""Control for diag_abcd: re-record sqlalchemy NOW with the OLD src (8e8f0bb) on the same incr tree (O0, O1), and once
with every v2.3.1 change off (E: scratch src without fast path, PROVISO_RECORD_FORK=0, PROVISO_RECORD_PYCACHE=0, no
times file). If O also differs from the first old recordings, the difference comes from the tree/environment, not
from v2.3.1. Then compare O with the new-code maps directly."""
import json
import os
import sys

REPO_DIR = os.path.expanduser("~/proviso-dev")
sys.path.insert(0, os.path.join(REPO_DIR, "research/v2"))
import record_speed_check as RSC  # noqa: E402

repo = "sqlalchemy"
work = os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2"))
maps = os.path.join(work, "record_speed_maps")
tree = os.path.join(work, repo, "trees", "incr")
times = os.path.join(tree, ".dc-engine", "record_times.json")
old_src = os.path.expanduser("~/proviso-old/src")
scratch = os.path.expanduser("~/proviso-scratch/src-nofastpath")
W = int(os.environ.get("DIAG_WORKERS", "8"))
L = lambda n: json.load(open(os.path.join(maps, f"{repo}-{n}.json")))  # noqa: E731
old1, old2 = L("old1"), L("old2")
noise = RSC.differing(old1, old2)
out = {}
for name, src, env in [("O0", old_src, {}), ("O1", old_src, {}),
                       ("E0", scratch, {"PROVISO_RECORD_FORK": "0", "PROVISO_RECORD_PYCACHE": "0"})]:
    if os.path.exists(times):
        os.remove(times)
    os.environ.update(env)
    secs = RSC.record(src, repo, os.path.join(maps, f"{repo}-ctl{name}.json"), W)
    for k in env:
        os.environ.pop(k, None)
    m = L(f"ctl{name}")
    out[name] = {"seconds": secs, "vs_old1": len(RSC.differing(old1, m)),
                 "beyond_noise": len(RSC.differing(old1, m) - noise)}
    print(name, json.dumps(out[name]), flush=True)
O0, O1, E0, A0, B0, C0 = L("ctlO0"), L("ctlO1"), L("ctlE0"), L("diagA0"), L("diagB0"), L("diagC0")
pairs = {"O0 vs O1 (old now, noise)": (O0, O1), "O0 vs new (freeze run)": (O0, L("new")), "O0 vs A0": (O0, A0),
         "O0 vs B0": (O0, B0), "O0 vs C0": (O0, C0), "O0 vs E0 (all v2.3.1 off)": (O0, E0),
         "old1 vs O0 (old then vs old now)": (old1, O0)}
for k, (a, b) in pairs.items():
    n = len(RSC.differing(a, b))
    out[k] = n
    print(f"{k}: {n} tests differ", flush=True)
json.dump(out, open(os.path.expanduser("~/proviso-logs/diag_control_sqlalchemy.json"), "w"), indent=1)
print("== DIAG CONTROL DONE")
