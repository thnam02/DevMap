"""Fetch published SWE-bench agent patches (the regressing patches of research/v2/results/swe/sample.json) to where
the SWE-bench evaluation keeps them: $PROVISO_WORK/swe/patches/<split>/<submission>/<instance>.diff.

The patches come from the public leaderboard exactly as swe_regressions.py fetched them: the submission's logs on
the swe-bench-submissions S3 bucket (unsigned), or the submission's own GitHub repository. Needs boto3 and pyyaml, so
run it through uv:
  uv run --no-project --python 3.12 --with boto3 --with pyyaml python research/agent/fetch_patches.py WANT.json
WANT.json: [[split, submission, instance], ...]. Prints one line per patch and exits non-zero if any is missing."""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "v2"))
import swe_regressions as R  # noqa: E402


def dest_of(split: str, submission: str, inst: str) -> str:
    return os.path.join(R.WORK, "patches", split, submission, inst + ".diff")


def from_git(url: str, inst: str, dest: str, cache: str) -> bool:
    d = os.path.join(cache, "repo")
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(cache, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, d], check=True)
    rel = f"logs/{inst}/patch.diff"
    subprocess.run(["git", "-C", d, "checkout", "-q", "HEAD", "--", rel], check=False, capture_output=True)
    src = os.path.join(d, rel)
    if not os.path.isfile(src):
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(open(src, "rb").read())
    return True


def main():
    want = json.load(open(sys.argv[1]))
    todo = [w for w in want if not os.path.isfile(dest_of(*w))]
    print(f"{len(want)} patches wanted, {len(todo)} to fetch", flush=True)
    if not todo:
        return
    exp = R.experiments_clone()
    client = None
    missing = []
    for split, name, inst in todo:
        dest = dest_of(split, name, inst)
        entry = os.path.join(exp, "evaluation", split, name)
        kind, where = R.log_location(entry, split, name)
        try:
            if kind == "s3":
                client = client or R.s3()
                ok = R.patch_s3(client, where, inst, dest)
            else:
                ok = from_git(where, inst, dest, os.path.join(R.WORK, "reports", split, name))
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  {split}/{name}/{inst}: {e!r}"[:300], flush=True)
        print(f"  {'ok     ' if ok else 'MISSING'} {split}/{name}/{inst}", flush=True)
        if not ok:
            missing.append((split, name, inst))
    if missing:
        sys.exit(f"{len(missing)} patches could not be fetched")


if __name__ == "__main__":
    main()
