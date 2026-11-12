"""SWE-bench tasks for the agent study, with Proviso's assets and a free preflight check.

Task rule (fixed before any run): instances of our SWE-bench sample (research/v2/results/swe/sample.json) from the
repositories with fast test suites (xarray, sphinx, pylint, seaborn, flask, pytest) where at least one published agent
patch caused a reproduced regression in eval-v2.3.jsonl (regression-prone tasks); taken round-robin across the six
repositories in sample order, the first N (pilot: 12, two per repository).

Per task, in EVAL_DIR:
  tasks/<id>.json        dc_eval task: base commit, the issue as the prompt, FAIL_TO_PASS as hidden tests (graded
                         after applying SWE-bench's test patch), PASS_TO_PASS as regression tests, and `python`: the
                         prepared SWE-bench environment the run inherits (nothing is installed per run)
  impact/<id>/           Proviso's dependency map, base failures and base import-time snapshot, recorded at the plain
                         base commit (without the reference tests: the agent's copy does not have them)
Preflight (free): each instance's reference fix (source files only) applied to the base tree, Proviso's selection
against those assets; it must narrow the tests (median share below 85%), else the paid runs would test nothing.

Runs as the normal user on the PC (it reads the SWE-bench clones and environments in PROVISO_WORK):
  python3 research/agent/swe_tasks.py EVAL_DIR [--n 12] [--workers W]"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "research", "v2"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import swe_eval as E  # noqa: E402
import swe_probe as P  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as IS  # noqa: E402
from dc_engine import record as REC  # noqa: E402

FAST = ["pydata__xarray", "sphinx-doc__sphinx", "pylint-dev__pylint", "mwaskom__seaborn", "pallets__flask",
        "pytest-dev__pytest"]
LIMIT = 0.85


def git(cwd, *a, check=True, inp=None):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check, input=inp).stdout


def pick(n: int) -> list[dict]:
    """The rule in the module docstring."""
    sample = json.load(open(os.path.join(P.OUT, "sample.json")))["instances"]
    rows = {}
    for line in open(os.path.join(P.OUT, "eval-v2.3.jsonl")):
        r = json.loads(line)
        rows[(r["instance"], r["case"])] = r
    queues = {repo: [x for x in sample if x["repo"] == repo
                     and any((rows.get((x["instance"], k)) or {}).get("reproduced") for k in range(len(x["cases"])))]
              for repo in FAST}
    out = []
    while len(out) < n and any(queues.values()):
        for repo in FAST:
            if queues[repo] and len(out) < n:
                out.append(queues[repo].pop(0))
    return out


def _tests(v) -> list[str]:
    return json.loads(v) if isinstance(v, str) else list(v or [])


def env_python(x: dict) -> str:
    return os.path.join(P.WORK, "envs", f"{x['repo']}__{x['version']}", "bin", "python")


def agent_tree(inst: dict) -> str:
    """The plain base commit, as the agent's copy starts (no reference tests), for recording and the preflight."""
    repo = inst["instance_id"].rsplit("-", 1)[0]
    src = P.repo_clone(repo)
    tree = os.path.join(P.WORK, "agent-trees", repo)
    if not os.path.isdir(os.path.join(tree, ".git")):
        os.makedirs(os.path.dirname(tree), exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--shared", src, tree], check=True)
    P.ensure_commit(src, inst["base_commit"])
    git(tree, "fetch", "-q", src, inst["base_commit"])
    git(tree, "checkout", "-q", "-f", inst["base_commit"])
    git(tree, "clean", "-q", "-fdx")
    return tree


def build(x: dict, inst: dict, eval_dir: str, workers: int) -> str:
    iid, repo, py = x["instance"], x["repo"], env_python(x)
    if not os.path.isfile(py):
        raise RuntimeError(f"no prepared environment: {py} (run swe_eval.py on this instance first)")
    dest = os.path.join(eval_dir, "impact", iid)
    os.makedirs(dest, exist_ok=True)
    os.makedirs(os.path.join(eval_dir, "tasks"), exist_ok=True)
    tree = agent_tree(inst)
    cov_path = os.path.join(dest, "covmap.json")
    if not os.path.isfile(cov_path):
        pkg, targets = E.LAYOUT[repo]
        targets = [t for t in targets if os.path.exists(os.path.join(tree, t))]
        extra = [os.path.join(tree, "src")] if os.path.isdir(os.path.join(tree, "src")) else []
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([tree, *extra]), "PYTHONDONTWRITEBYTECODE": "1",
               "PATH": os.path.dirname(py) + os.pathsep + os.environ.get("PATH", "")}
        REC.FILE_TIMEOUT = int(os.environ.get("PROVISO_RECORD_FILE_TIMEOUT", "900"))
        REC.record(tree, pkg, cov_path, py, targets, workers, "", ["-p", "no:randomly"], env)
    cov = json.load(open(cov_path))
    tests = [n for n in cov if not n.startswith("__")]
    if not tests:
        os.remove(cov_path)
        raise RuntimeError(f"{iid}: the dependency map recorded no tests")
    json.dump(sorted(n for n in tests if not cov[n].get("ok", True)), open(os.path.join(dest, "base_failures.json"), "w"))
    files = sorted(f for f in I.map_files(cov) if not I._is_test_path(f))
    if IS.base_snapshot(tree, files, py, os.path.join(dest, "importstate_base.json")) is None:
        raise RuntimeError(f"{iid}: import-time snapshot failed")
    task = {"id": iid, "repo": f"https://github.com/{inst['repo']}.git", "commit": inst["base_commit"],
            "prompt": inst["problem_statement"], "hidden_tests": _tests(inst.get("FAIL_TO_PASS")),
            "test_patch": inst.get("test_patch") or "", "regression_tests": _tests(inst.get("PASS_TO_PASS")),
            "setup": "python -m pip install -e .", "python": py,
            "source": "SWE-bench", "sample": "core" if x["core"] else "held-out"}
    json.dump(task, open(os.path.join(eval_dir, "tasks", iid + ".json"), "w"), indent=1)
    return f"{iid}: {len(tests)} tests in the map"


def preflight(x: dict, inst: dict, eval_dir: str) -> float:
    iid, py = x["instance"], env_python(x)
    tree = agent_tree(inst)
    assets = os.path.join(eval_dir, "impact", iid)
    cov = json.load(open(os.path.join(assets, "covmap.json")))
    os.makedirs(os.path.join(tree, ".dc-engine"), exist_ok=True)
    subprocess.run(["cp", os.path.join(assets, "importstate_base.json"),
                    os.path.join(tree, ".dc-engine", "importstate_base.json")], check=True)
    ref = set(P.test_files_of_patch(inst.get("test_patch")))
    patch, _ = E.without_files(inst["patch"], ref)
    try:
        E.apply_patch(tree, patch)
        sel, why = I.selection(tree, cov, py)
    finally:
        git(tree, "checkout", "-q", "-f", inst["base_commit"])
        git(tree, "clean", "-q", "-fdx", "-e", ".dc-engine")
    n = sum(1 for k in cov if not k.startswith("__"))
    share = 1.0 if sel is None else len(sel) / max(1, n)
    print(f"  {iid:32s} reference fix selects {'all' if sel is None else len(sel):>5} of {n} ({share:.0%})"
          + (f"  reason: {why.get('reason')}" if sel is None else ""), flush=True)
    return share


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_dir")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    eval_dir = os.path.abspath(a.eval_dir)
    meta = P.load_instances()
    chosen = pick(a.n)
    print("tasks (rule: regression-prone, round-robin over", ", ".join(FAST) + "):", flush=True)
    for x in chosen:
        print("  ", x["instance"], "core" if x["core"] else "held-out", flush=True)
    ok = []
    for x in chosen:
        try:
            print(build(x, meta[x["instance"]], eval_dir, a.workers), flush=True)
            ok.append(x)
        except Exception as e:  # noqa: BLE001
            print(x["instance"], "ERROR", repr(e)[:300], flush=True)
    print("preflight (free): does Proviso narrow the tests?", flush=True)
    shares = []
    for x in ok:
        try:
            shares.append(preflight(x, meta[x["instance"]], eval_dir))
        except Exception as e:  # noqa: BLE001
            print(x["instance"], "PREFLIGHT ERROR", repr(e)[:300], flush=True)
    if len(ok) < len(chosen) or len(shares) < len(ok):
        sys.exit("some tasks failed to build or check; fix them before paid runs")
    med = statistics.median(shares)
    print(f"median share selected: {med:.0%} (limit {LIMIT:.0%})", flush=True)
    if med >= LIMIT:
        sys.exit("Proviso selects nearly everything on most tasks; not starting paid runs.")
    print("OK: ready for the paid runs", flush=True)


if __name__ == "__main__":
    main()
