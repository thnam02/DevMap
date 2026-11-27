"""Diagnose a failed record_speed_check: re-record REPO with the new src under each v2.3.1 switch and compare each map
with the two old recordings (same tree, same commit). Diagnostic only; nothing under src/ or research/ is changed.
  python freeze_diag.py REPO"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/proviso-dev/research/v2"))
import record_speed_check as RSC  # noqa: E402

repo = sys.argv[1]
work = os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2"))
d = os.path.join(work, "record_speed_maps")
new_src = os.path.expanduser("~/proviso-dev/src")
workers = int(os.environ.get("PROVISO_WORKERS", "8"))
old1, old2 = (json.load(open(os.path.join(d, f"{repo}-{k}.json"))) for k in ("old1", "old2"))
noise = RSC.differing(old1, old2)
variants = [("again", {}), ("fork0", {"PROVISO_RECORD_FORK": "0"}), ("pycache0", {"PROVISO_RECORD_PYCACHE": "0"}),
            ("fork0-pycache0", {"PROVISO_RECORD_FORK": "0", "PROVISO_RECORD_PYCACHE": "0"})]
out = {"repo": repo, "noise_old1_old2": len(noise), "variants": {}}
for name, env in variants:
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    p = os.path.join(d, f"{repo}-diag-{name}.json")
    t = time.time()
    try:
        secs = RSC.record(new_src, repo, p, workers)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    m = json.load(open(p))
    ch = RSC.differing(old1, m)
    r = {"env": env, "seconds": secs, "vs_old1": len(ch), "beyond_noise": len(ch - noise),
         "same_global": m.get("__global__") == old1.get("__global__"),
         "same_collected": m.get("__collected__") == old1.get("__collected__"), "example": sorted(ch - noise)[:3]}
    out["variants"][name] = r
    print(name, json.dumps(r), flush=True)
os.makedirs(os.path.expanduser("~/proviso-logs"), exist_ok=True)
json.dump(out, open(os.path.expanduser(f"~/proviso-logs/freeze_diag_{repo}.json"), "w"), indent=1)
print("== DIAG DONE", repo)
