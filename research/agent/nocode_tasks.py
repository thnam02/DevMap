"""Agent study on feature-sized tasks: NoCode-bench Verified (Deng et al., arXiv 2507.18130).

A NoCode-bench task asks the agent to implement a feature from its documentation change (the task's
problem_statement: the masked documentation diff plus the names of new entities). The feature's tests (FAIL2PASS)
are hidden; the project's existing tests that must keep passing (PASS2PASS) are the regression tests. In the
benchmark's paper, OpenHands with Claude 4 Sonnet kept every regression test passing in only 55% of the Verified
tasks: on these tasks agents do break existing tests, which is where test selection can matter.

Task rule (fixed before any run): every NoCode-bench Verified instance from the repositories our pipeline runs on
Python 3.12 (seaborn, xarray, pylint, sphinx, pytest; not django, scikit-learn, astropy, matplotlib or requests), in
dataset order, kept if it passes the reference-fix check (swe_tasks.gold_check: the instance's own feature patch
passes every FAIL2PASS test here; PASS2PASS tests failing with it are environment failures and are dropped; more
than 10% failing rejects the instance). An instance whose environment cannot be built here, or whose tests record
nothing, is rejected too. Rejected instances go to rejected/ with the reason, decided before any run.

Environments: one per (repository, version), Python 3.12, the project's dependencies as of 60 days after the newest
base commit of that version's tasks (as swe_probe.build_env does for SWE-bench), shared with the SWE-bench
environments when the version name is the same.

Layout, in EVAL_DIR (the same as swe_tasks.py, so run_replay.sh runs it with PROVISO_AGENT_STUDY=nocode):
  tasks/<id>.json, impact/<id>/, rejected/<id>/reason.txt, checks/<id>.reference-fix.log

  python3 research/agent/nocode_tasks.py EVAL_DIR [--limit N] [--workers W]"""
from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swe_tasks as S  # noqa: E402
from swe_tasks import P  # noqa: E402

REPOS = ["mwaskom__seaborn", "pydata__xarray", "pylint-dev__pylint", "sphinx-doc__sphinx", "pytest-dev__pytest"]


URLS = [  # the dataset was renamed Doc2Feat-bench (arXiv v4); either name serves the same file
    "https://huggingface.co/datasets/NoCode-bench/NoCode-bench_Verified/resolve/main/test/data.jsonl",
    "https://huggingface.co/datasets/Doc2Feat-bench/Doc2Feat-bench_Verified/resolve/main/test/data.jsonl",
]


def fetch_rows() -> list[dict]:
    """NoCode-bench Verified's rows (Hugging Face, test/data.jsonl), cached in the work directory."""
    import urllib.request
    path = os.path.join(P.WORK, "nocode", "verified.jsonl")
    if not os.path.isfile(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        errors = []
        for url in URLS:
            print(f"  fetching {url}", flush=True)
            try:
                with urllib.request.urlopen(url, timeout=300) as resp:
                    data = resp.read()
                rows = [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]
                if rows and "feature_patch" in rows[0]:
                    open(path + ".tmp", "wb").write(data)
                    os.rename(path + ".tmp", path)
                    break
                errors.append(f"{url}: unexpected content")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{url}: {e!r}"[:200])
        else:
            raise RuntimeError("could not fetch NoCode-bench Verified: " + "; ".join(errors))
    return [json.loads(l) for l in open(path) if l.strip()]


def _tests(v) -> list[str]:
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            v = [v] if v else []
    return [str(t) for t in (v or [])]


def as_instance(row: dict) -> dict:
    """A NoCode-bench row in the shape the SWE-bench helpers read."""
    return {**row, "repo": row["repo"], "instance_id": row["instance_id"], "base_commit": row["base_commit"],
            "patch": row["feature_patch"], "test_patch": row.get("test_patch") or "",
            "problem_statement": row["problem_statement"], "FAIL_TO_PASS": _tests(row.get("FAIL2PASS")),
            "PASS_TO_PASS": _tests(row.get("PASS2PASS"))}


def ensure_env(repo: str, version: str, rows: list[dict]) -> str:
    """The (repository, version) environment, built once from the version's earliest base commit, dependencies as of
    60 days after its newest base commit."""
    x = {"repo": repo, "version": version}
    py = S.env_python(x)
    if os.path.isfile(py):
        return py
    if not shutil.which("uv"):
        raise RuntimeError("uv is needed to build the environments (https://docs.astral.sh/uv/)")
    src = P.repo_clone(repo)
    dates = []
    for r in rows:
        P.ensure_commit(src, r["base_commit"])
        dates.append(subprocess.run(["git", "-C", src, "show", "-s", "--format=%cI", r["base_commit"]],
                                    capture_output=True, text=True).stdout.strip())
    first = min(rows, key=lambda r: dates[rows.index(r)])["base_commit"]
    print(f"  building environment {repo} {version} (once; can take several minutes)", flush=True)
    e = P.build_env(repo, version, first, [d for d in dates if d], "3.12")
    if not e.get("ok"):
        raise RuntimeError(f"environment {repo} {version} failed: {e.get('error', '')[:400]}")
    return py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_dir")
    ap.add_argument("--limit", type=int, default=0, help="only the first N instances (a trial build)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    eval_dir = os.path.abspath(a.eval_dir)
    for d in ("tasks", "impact", "rejected", "checks"):
        os.makedirs(os.path.join(eval_dir, d), exist_ok=True)
    rows = [r for r in fetch_rows() if r["repo"].replace("/", "__") in REPOS]
    if a.limit:
        rows = rows[:a.limit]
    by_env = collections.defaultdict(list)
    for r in rows:
        by_env[(r["repo"].replace("/", "__"), str(r["version"]))].append(r)
    print(f"{len(rows)} NoCode-bench Verified instances in {', '.join(REPOS)}; "
          f"{len(by_env)} environments", flush=True)
    kept, rejected = 0, []
    for r in rows:
        iid = r["instance_id"]
        repo, version = r["repo"].replace("/", "__"), str(r["version"])
        if os.path.isfile(os.path.join(eval_dir, "tasks", iid + ".json")):
            kept += 1
            continue
        if os.path.isfile(os.path.join(eval_dir, "rejected", iid, "reason.txt")):
            rejected.append(iid)
            continue
        print(f"- {iid} ({repo} {version})", flush=True)
        inst = as_instance(r)
        x = {"instance": iid, "repo": repo, "version": version, "core": True}
        log = os.path.join(eval_dir, "checks", iid + ".reference-fix.log")
        try:
            ensure_env(repo, version, by_env[(repo, version)])
            print("  " + S.build(x, inst, eval_dir, a.workers), flush=True)
            path = os.path.join(eval_dir, "tasks", iid + ".json")
            task = json.load(open(path))
            task.update(source="NoCode-bench Verified", sample="nocode")
            json.dump(task, open(path, "w"), indent=1)
            why = S.gold_check(x, inst, eval_dir)
            gold_work = os.path.join(P.WORK, "gold", iid)
            if os.path.isfile(os.path.join(gold_work, "grading.log")):
                shutil.copyfile(os.path.join(gold_work, "grading.log"), log)
            shutil.rmtree(gold_work, ignore_errors=True)
        except Exception as e:  # noqa: BLE001
            msg = repr(e)
            if ("environment" in msg and "failed" in msg) or "recorded no tests" in msg:
                why = f"setup: {msg[:400]}"   # the project cannot run here: a property of the task, not a bug of ours
            else:
                sys.exit(f"{iid} ERROR {msg}"[:600] + "\nfix this before the paid runs")
        if why:
            S.reject(eval_dir, iid, why.replace(os.path.join(P.WORK, "gold", iid, "grading.log"), log))
            rejected.append(iid)
            print(f"  REJECTED: {why}"[:400], flush=True)
        else:
            kept += 1
    print(f"tasks kept: {kept}; rejected: {len(rejected)}", flush=True)
    if not kept:
        sys.exit("no task kept")
    print("OK: NoCode-bench tasks ready", flush=True)


if __name__ == "__main__":
    main()
