"""(v2.3.1) Check that the recording speed-ups leave the map unchanged on a project: record its map at the incr tree's
current commit twice with the old code (to see which tests differ between two plain recordings: random inputs) and once
with the new code, then compare test by test (own record united with its fixture records), plus the global record,
the fixture records and the collected files.

  python research/v2/record_speed_check.py REPO --old-src OLD/src --new-src NEW/src [--workers N]

OLD/src: a checkout of the code before v2.3.1 (e.g. `git worktree add /tmp/old 8e8f0bb`). Pass = every test that differs
between old and new also differs between the two old recordings. Results go to results/record_speed/REPO.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _full(m, n):
    fx = m.get("__fixtures__") or {}
    v = m[n]
    out = {"funcs": {tuple(x) for x in v.get("funcs", [])}, "classes": set(v.get("classes", [])),
           "files": set(v.get("files", [])), "dirs": set(v.get("dirs", [])), "always": bool(v.get("always"))}
    for k in v.get("fx", []):
        r = fx.get(k) or {}
        out["funcs"] |= {tuple(x) for x in r.get("funcs", [])}
        out["classes"] |= set(r.get("classes", []))
        out["files"] |= set(r.get("files", []))
        out["always"] = out["always"] or bool(r.get("always"))
    return out


def differing(a: dict, b: dict) -> set:
    ta = {k for k in a if not k.startswith("__")}
    tb = {k for k in b if not k.startswith("__")}
    return (ta ^ tb) | {n for n in ta & tb if _full(a, n) != _full(b, n)}


def record(src: str, repo: str, out: str, workers: int) -> float:
    code = f"""
import json, os, sys, time
sys.path.insert(0, {src!r})
from dc_engine import record as REC
sys.path.insert(1, {HERE!r})
import pipeline as PL
assert REC.__file__.startswith({src!r}), REC.__file__
PL.use({repo!r}); CFG = PL.CFG
tree = os.path.join(PL.WORK, "trees", "incr")
t = time.time()
REC.record(tree, CFG["pkg"], {out!r}, PL.PY, CFG["targets"], {workers}, CFG["before_test"],
           ["-p", "no:randomly", *CFG["pytest_args"]], PL.env(tree, [PL.PLUG]))
print(time.time() - t)
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    return round(float(r.stdout.strip().splitlines()[-1]), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--old-src", required=True)
    ap.add_argument("--new-src", required=True)
    ap.add_argument("--workers", type=int, default=int(os.environ.get("PROVISO_WORKERS", "2")))
    a = ap.parse_args()
    res = os.path.join(HERE, "results", "record_speed")
    os.makedirs(res, exist_ok=True)
    tmp = os.path.join(os.environ.get("PROVISO_WORK") or tempfile.gettempdir(), "record_speed_maps")
    os.makedirs(tmp, exist_ok=True)
    paths = {k: os.path.join(tmp, f"{a.repo}-{k}.json") for k in ("old1", "old2", "new")}
    secs = {k: record(a.old_src if k.startswith("old") else a.new_src, a.repo, p, a.workers) for k, p in paths.items()}
    old1, old2, new = (json.load(open(paths[k])) for k in ("old1", "old2", "new"))
    noise = differing(old1, old2)
    changed = differing(old1, new)
    same_meta = {k: old1.get(k) == new.get(k) for k in ("__global__", "__collected__")}
    out = {"repo": a.repo, "commit": new["__base__"]["commit"], "seconds": secs,
           "noise_tests": len(noise), "old_vs_new_tests": len(changed), "beyond_noise": sorted(changed - noise)[:50],
           "same": same_meta, "pass": not (changed - noise) and all(same_meta.values())}
    out["tests"] = sum(1 for k in new if not k.startswith("__"))
    os.makedirs(res, exist_ok=True)
    json.dump(out, open(os.path.join(res, f"{a.repo}.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
