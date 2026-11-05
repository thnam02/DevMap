"""Real regressions made by AI coding agents, from the public SWE-bench leaderboard (github.com/swe-bench/experiments).

Every leaderboard submission publishes, per task instance, the agent's patch and a report.json whose
tests_status.PASS_TO_PASS.failure lists tests that passed before the agent's patch and fail after it: a regression the
agent introduced. This script collects them for the repositories Proviso can run (pytest, no compiled extensions), so
that Proviso's selection can be scored against real agent regressions: one dependency map per task instance (its base
commit), then every agent's regressing patch for that instance.

Note: SWE-bench runs only the test files its reference fix touches, so a regression elsewhere is not listed.

Usage (PC, needs network; no credentials):
  pip install boto3 pyyaml
  python3 research/v2/swe_regressions.py [--splits verified lite test]
Output:
  research/v2/results/swe/regressions.jsonl   one row per (split, submission, instance) whose patch broke a P2P test
  research/v2/results/swe/summary.md           counts per repository
  $PROVISO_WORK/swe/patches/<split>/<submission>/<instance>.diff   the regressing patches (not committed)
Resumable: report.json files are cached under $PROVISO_WORK/swe/reports."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "swe")
WORK = os.path.join(os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2")), "swe")
BUCKET = "swe-bench-submissions"
# repositories whose tests run under pytest without building compiled extensions (as in the NameRTS benchmark setup)
USABLE = ["sympy__sympy", "sphinx-doc__sphinx", "pydata__xarray", "pytest-dev__pytest", "psf__requests",
          "pylint-dev__pylint", "mwaskom__seaborn", "pallets__flask"]


def s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32))


def experiments_clone() -> str:
    d = os.path.join(WORK, "experiments")
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(WORK, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/swe-bench/experiments.git", d],
                       check=True)
    else:
        subprocess.run(["git", "-C", d, "pull", "-q"], check=False)
    return d


def log_location(entry_dir: str, split: str, name: str) -> tuple[str, str]:
    """('s3', prefix) or ('git', repo url) for a submission's logs."""
    import yaml
    try:
        meta = yaml.safe_load(open(os.path.join(entry_dir, "metadata.yaml"))) or {}
    except OSError:
        meta = {}
    assets = meta.get("assets") or {}
    logs = assets.get("logs") or ""
    if logs.startswith("s3://"):
        return "s3", logs[len(f"s3://{BUCKET}/"):].rstrip("/")
    if assets.get("repo"):
        return "git", assets["repo"]
    return "s3", f"{split}/{name}/logs"


def reports_s3(client, prefix: str, cache: str) -> dict[str, dict]:
    """{instance: report} for the usable repositories under an S3 logs prefix (report.json only)."""
    keys = []
    pg = client.get_paginator("list_objects_v2")
    for repo in USABLE:
        for page in pg.paginate(Bucket=BUCKET, Prefix=f"{prefix}/{repo}-"):
            keys += [o["Key"] for o in page.get("Contents", []) if o["Key"].endswith("/report.json")]

    def get(key):
        inst = key.rsplit("/", 2)[-2]
        path = os.path.join(cache, inst + ".json")
        if not os.path.exists(path):
            body = client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
            open(path, "wb").write(body)
        try:
            return inst, json.load(open(path))
        except ValueError:
            return inst, {}
    os.makedirs(cache, exist_ok=True)
    with cf.ThreadPoolExecutor(16) as ex:
        return dict(ex.map(get, keys))


def reports_git(url: str, cache: str) -> tuple[dict[str, dict], str]:
    """Same for a submission hosted in its own GitHub repository (sparse checkout of logs/*/report.json and patches)."""
    d = os.path.join(cache, "repo")
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(cache, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, d], check=True)
    names = subprocess.run(["git", "-C", d, "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True,
                           text=True).stdout.split()
    want = [n for n in names if n.startswith("logs/") and n.endswith(("report.json", "patch.diff"))
            and any(n.split("/")[1].startswith(r + "-") for r in USABLE)]
    for i in range(0, len(want), 200):
        subprocess.run(["git", "-C", d, "checkout", "-q", "HEAD", "--", *want[i:i + 200]], check=False)
    out = {}
    for n in want:
        if n.endswith("report.json"):
            try:
                out[n.split("/")[1]] = json.load(open(os.path.join(d, n)))
            except (OSError, ValueError):
                pass
    return out, d


def patch_s3(client, prefix: str, inst: str, dest: str) -> bool:
    if os.path.exists(dest):
        return True
    try:
        body = client.get_object(Bucket=BUCKET, Key=f"{prefix}/{inst}/patch.diff")["Body"].read()
    except Exception:  # noqa: BLE001
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(body)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", nargs="*", default=["verified", "lite", "test"])
    a = ap.parse_args()
    exp = experiments_clone()
    client = s3()
    os.makedirs(OUT, exist_ok=True)
    rows, scanned = [], collections.Counter()
    for split in a.splits:
        base = os.path.join(exp, "evaluation", split)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            entry = os.path.join(base, name)
            if not os.path.isdir(entry):
                continue
            kind, where = log_location(entry, split, name)
            cache = os.path.join(WORK, "reports", split, name)
            try:
                if kind == "s3":
                    reps, repo_dir = reports_s3(client, where, cache), None
                else:
                    reps, repo_dir = reports_git(where, cache)
            except Exception as e:  # noqa: BLE001
                print(f"[{split}/{name}] could not read logs: {repr(e)[:200]}", flush=True)
                continue
            n_reg = 0
            for inst, rep in reps.items():
                v = rep.get(inst) or (next(iter(rep.values())) if rep else {})
                ts = v.get("tests_status") or {}
                p2f = (ts.get("PASS_TO_PASS") or {}).get("failure") or []
                scanned[inst.rsplit("-", 1)[0]] += 1
                if not p2f or not v.get("patch_successfully_applied", True):
                    continue
                dest = os.path.join(WORK, "patches", split, name, inst + ".diff")
                ok = (patch_s3(client, where, inst, dest) if kind == "s3"
                      else os.path.exists(os.path.join(repo_dir, "logs", inst, "patch.diff")))
                if kind == "git" and ok and not os.path.exists(dest):
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    open(dest, "wb").write(open(os.path.join(repo_dir, "logs", inst, "patch.diff"), "rb").read())
                rows.append({"split": split, "submission": name, "instance": inst, "repo": inst.rsplit("-", 1)[0],
                             "p2p_failed": p2f, "f2p_ok": bool((ts.get("FAIL_TO_PASS") or {}).get("success")),
                             "resolved": bool(v.get("resolved")), "patch": dest if ok else None})
                n_reg += 1
            print(f"[{split}/{name}] {len(reps)} reports in usable repositories, {n_reg} with a regression", flush=True)
    with open(os.path.join(OUT, "regressions.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    by_repo = collections.defaultdict(list)
    for r in rows:
        by_repo[r["repo"]].append(r)
    lines = ["# Real agent regressions on SWE-bench (PASS_TO_PASS tests broken by an agent's patch)", "",
             "| repository | agent patches scanned | regressing patches | distinct instances | distinct broken tests |",
             "|---|---|---|---|---|"]
    for repo in USABLE:
        rs = by_repo.get(repo, [])
        lines.append(f"| {repo} | {scanned[repo]} | {len(rs)} | {len({r['instance'] for r in rs})} | "
                     f"{len({(r['instance'], t) for r in rs for t in r['p2p_failed']})} |")
    lines.append(f"| **all** | {sum(scanned.values())} | {len(rows)} | {len({r['instance'] for r in rows})} | |")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
