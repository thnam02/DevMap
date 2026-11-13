"""SWE-bench tasks for the agent study, with Proviso's assets and a free preflight check.

Task rule (fixed before any run): instances of our SWE-bench sample (research/v2/results/swe/sample.json) from the
repositories with fast test suites (xarray, sphinx, pylint, seaborn, flask, pytest) where at least one published agent
patch caused a reproduced regression in eval-v2.3.jsonl (regression-prone tasks); taken round-robin across the six
repositories in sample order; the first N (pilot: 12) that pass the reference-fix check below. Rejected candidates are
skipped by that check alone, never by Proviso's selection or by any run's outcome.

Reference-fix check (free; SWE-bench's own validation, redone in our environments): the instance's reference fix
(source files) applied to the agent's starting copy and graded by dc_eval exactly as an agent's run is graded. Every
FAIL_TO_PASS test must pass; PASS_TO_PASS tests that fail here are environment failures, dropped from the regression
tests (kept in the task as `regression_tests_failing_with_reference_fix`); more than 10% of them failing rejects the
task (its environment does not run its tests). The environments use Python 3.12, which Proviso needs (PEP 669), where
SWE-bench's use 3.9-3.11: flask 2.x's suite, for example, turns 3.12's pkgutil.get_loader deprecation into an error in
every test using its app fixture (pyproject filterwarnings = "error"), so flask's tasks fail this check.

Per task, in EVAL_DIR:
  tasks/<id>.json        dc_eval task: base commit, the issue as the prompt, FAIL_TO_PASS as hidden tests (graded
                         after applying SWE-bench's test patch to the base version: test_patch_only), PASS_TO_PASS as
                         regression tests, and `python`: the prepared SWE-bench environment the run inherits (nothing
                         is installed per run)
  rejected/<id>/         candidates that failed the reference-fix check, with the reason
  impact/<id>/           Proviso's dependency map, base failures and base import-time snapshot, recorded at the plain
                         base commit (without the reference tests: the agent's copy does not have them)
Preflight (free): each instance's reference fix (source files only) applied to the base tree, Proviso's selection
against those assets; it must narrow the tests (median share below 85%), else the paid runs would test nothing.

Missing pieces are built on the spot, the same way the SWE-bench evaluation built them: the instance list (copied from
research/v2/results/swe/instances.jsonl, completed with the issue text and patches from SWE-bench's dataset), the
repository clones, and each (repository, version) environment
(swe_probe.build_env: Python 3.12 via uv, dependencies resolved as of the version's cutoff date). So a fresh machine
(e.g. a Mac) needs only git, uv and network access.
  python3 research/agent/swe_tasks.py EVAL_DIR [--n 12] [--workers W]"""
from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
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
ENV_FAIL_LIMIT = 0.10   # PASS_TO_PASS failing with the reference fix: above this share, the environment is broken


def git(cwd, *a, check=True, inp=None):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check, input=inp).stdout


def pick(n: int | None = None) -> list[dict]:
    """The candidates, in the order of the rule in the module docstring (all of them if n is None)."""
    sample = json.load(open(os.path.join(P.OUT, "sample.json")))["instances"]
    rows = {}
    for line in open(os.path.join(P.OUT, "eval-v2.3.jsonl")):
        r = json.loads(line)
        rows[(r["instance"], r["case"])] = r
    queues = {repo: [x for x in sample if x["repo"] == repo
                     and any((rows.get((x["instance"], k)) or {}).get("reproduced") for k in range(len(x["cases"])))]
              for repo in FAST}
    out = []
    n = n if n is not None else sum(len(q) for q in queues.values())
    while len(out) < n and any(queues.values()):
        for repo in FAST:
            if queues[repo] and len(out) < n:
                out.append(queues[repo].pop(0))
    return out


def _tests(v) -> list[str]:
    return json.loads(v) if isinstance(v, str) else list(v or [])


def env_python(x: dict) -> str:
    return os.path.join(P.WORK, "envs", f"{x['repo']}__{x['version']}", "bin", "python")


FULL_FIELDS = ("problem_statement", "patch", "test_patch")


def ensure_instances(needed: list[str]):
    """The SWE-bench instance list where swe_probe expects it, with the issue text and patches. The repository keeps a
    trimmed copy (no problem statement or patches); the full rows come from SWE-bench's dataset on Hugging Face
    (princeton-nlp/SWE-bench, test split, as swe_regressions.py loaded it), fetched with `uv run --with datasets`."""
    path = os.path.join(P.WORK, "instances.jsonl")
    if os.path.exists(path):
        rows = {json.loads(l)["instance_id"]: json.loads(l) for l in open(path)}
        if all(all(rows.get(i, {}).get(f) is not None for f in FULL_FIELDS) for i in needed):
            return
    print("  fetching SWE-bench instance metadata (issue text and patches) from Hugging Face", flush=True)
    os.makedirs(P.WORK, exist_ok=True)
    slim = os.path.join(P.OUT, "instances.jsonl")
    code = ("import json, sys\n"
            "from datasets import load_dataset\n"
            "keep = {json.loads(l)['instance_id'] for l in open(sys.argv[1])}\n"
            "ds = load_dataset('princeton-nlp/SWE-bench', split='test')\n"
            "with open(sys.argv[2], 'w') as fh:\n"
            "    for x in ds:\n"
            "        if x['instance_id'] in keep:\n"
            "            fh.write(json.dumps(dict(x)) + '\\n')\n")
    tmp = path + ".tmp"
    r = subprocess.run(["uv", "run", "--quiet", "--no-project", "--python", "3.12", "--with", "datasets", "python", "-c",
                        code, slim, tmp], capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not os.path.exists(tmp):
        raise RuntimeError(f"could not fetch the SWE-bench metadata: {(r.stderr or r.stdout)[-600:]}")
    rows = {json.loads(l)["instance_id"]: json.loads(l) for l in open(tmp)}
    missing = [i for i in needed if not all(rows.get(i, {}).get(f) is not None for f in FULL_FIELDS)]
    if missing:
        raise RuntimeError(f"the SWE-bench dataset lacks issue text or patches for: {missing}")
    os.replace(tmp, path)


# files a real install generates that the project imports: written into the recording tree and into each agent copy
def generated_files(x: dict) -> dict[str, str]:
    if x["repo"] == "pytest-dev__pytest":
        parts = (x["version"].split(".") + ["0", "0"])[:3]
        v = ".".join(parts) + ".dev0"
        return {"src/_pytest/_version.py": "# written by research/agent/swe_tasks.py (setuptools-scm writes it at install)\n"
                f"__version__ = version = {v!r}\n"
                f"__version_tuple__ = version_tuple = ({int(parts[0])}, {int(parts[1])}, {int(parts[2])}, 'dev0')\n"}
    return {}


def ensure_env(x: dict, meta: dict) -> str:
    """The task's environment, built as swe_probe's main built it if missing: same instance grouping (genuine agent
    regressions, issues from 2021), so the same dependency cutoff date."""
    py = env_python(x)
    if os.path.isfile(py):
        return py
    if not shutil.which("uv"):
        raise RuntimeError("uv is needed to build the environments (https://docs.astral.sh/uv/)")
    groups = collections.defaultdict(list)
    for i in P.broken_tests():
        if i in meta and int((meta[i].get("created_at") or "0000")[:4]) >= 2021:
            groups[(meta[i]["repo"].replace("/", "__"), meta[i]["version"])].append(i)
    insts = groups.get((x["repo"], x["version"])) or [x["instance"]]
    print(f"  building environment {x['repo']} {x['version']} (once; can take several minutes)", flush=True)
    e = P.build_env(x["repo"], x["version"], meta[insts[0]]["environment_setup_commit"],
                    [meta[i]["created_at"] for i in insts], "3.12")
    if not e.get("ok"):
        raise RuntimeError(f"environment {x['repo']} {x['version']} failed: {e.get('error', '')[:400]}")
    return py


def agent_tree(inst: dict, files: dict[str, str] | None = None) -> str:
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
    for rel, content in (files or {}).items():
        os.makedirs(os.path.dirname(os.path.join(tree, rel)), exist_ok=True)
        open(os.path.join(tree, rel), "w").write(content)
    return tree


def build(x: dict, inst: dict, eval_dir: str, workers: int) -> str:
    iid, repo = x["instance"], x["repo"]
    py = env_python(x) if os.path.isfile(env_python(x)) else ensure_env(x, P.load_instances())
    dest = os.path.join(eval_dir, "impact", iid)
    os.makedirs(dest, exist_ok=True)
    os.makedirs(os.path.join(eval_dir, "tasks"), exist_ok=True)
    gen = generated_files(x)
    tree = agent_tree(inst, gen)
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
            "setup": "python -m pip install -e .", "python": py, "files": gen, "test_patch_only": True,
            "source": "SWE-bench", "sample": "core" if x["core"] else "held-out"}
    json.dump(task, open(os.path.join(eval_dir, "tasks", iid + ".json"), "w"), indent=1)
    return f"{iid}: {len(tests)} tests in the map"


def gold_check(x: dict, inst: dict, eval_dir: str) -> str | None:
    """The reference-fix check in the module docstring. Returns why the task is rejected, or None (and then the task's
    regression tests are trimmed to those that pass with the reference fix)."""
    from dc_eval import grade as G
    from dc_eval import run as R
    from dc_eval import tasks as T
    iid = x["instance"]
    path = os.path.join(eval_dir, "tasks", iid + ".json")
    data = json.load(open(path))
    task = T.Task.from_dict(data)
    tree = agent_tree(inst, generated_files(x))
    work = os.path.join(P.WORK, "gold", iid)
    shutil.rmtree(work, ignore_errors=True)
    repo = os.path.join(work, "repo")
    subprocess.run(["git", "clone", "-q", "--shared", tree, repo], check=True)
    git(repo, "checkout", "-q", "-f", inst["base_commit"])
    R.write_task_files(repo, task.files)
    ref = set(P.test_files_of_patch(inst.get("test_patch")))
    patch, _ = E.without_files(inst["patch"], ref)
    E.apply_patch(repo, patch)
    venv = R.create_run_venv(work, task.python)
    env = R.venv_env(venv)
    env["DC_EVAL_OFFLINE"] = "1"
    py = R.venv_python(venv)
    G.install_test_env(py, repo, env=env)
    R.run_setup(repo, task.setup, env=env)
    g = G.grade_repo(task, repo, python=py, src_repo=tree, run_dir=work)
    n_regr = len(g["regression"])
    print(f"  {iid:32s} reference fix: hidden {g['hidden_checks_passed']}/{g['hidden_checks_total']} "
          f"({len(g['hidden_failed'])} failing), PASS_TO_PASS failing {len(g['regression_failed'])} of {n_regr}",
          flush=True)
    if not g["resolved"]:
        return (f"the reference fix does not pass the hidden tests here: {g['hidden_failed'][:5]} "
                f"(grading log: {os.path.join(work, G.GRADING_LOG)})")
    if n_regr and len(g["regression_failed"]) > ENV_FAIL_LIMIT * n_regr:
        return (f"{len(g['regression_failed'])} of {n_regr} PASS_TO_PASS tests fail with the reference fix: the "
                f"environment does not run this task's tests (grading log: {os.path.join(work, G.GRADING_LOG)})")
    failing = set(g["regression_failed"])
    data["regression_tests"] = [t for t in data["regression_tests"] if t not in failing]
    data["regression_tests_failing_with_reference_fix"] = sorted(failing)
    json.dump(data, open(path, "w"), indent=1)
    return None


def reject(eval_dir: str, iid: str, why: str):
    dest = os.path.join(eval_dir, "rejected", iid)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    for sub, name in (("tasks", iid + ".json"), ("impact", iid)):
        src = os.path.join(eval_dir, sub, name)
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest, name))
    open(os.path.join(dest, "reason.txt"), "w").write(why + "\n")


def preflight(x: dict, inst: dict, eval_dir: str) -> float:
    iid, py = x["instance"], env_python(x)
    gen = generated_files(x)
    tree = agent_tree(inst, gen)
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
        for rel, content in gen.items():
            open(os.path.join(tree, rel), "w").write(content)
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
    cands = pick()
    ensure_instances([x["instance"] for x in cands])
    meta = P.load_instances()
    print(f"candidates (rule: regression-prone, round-robin over {', '.join(FAST)}); the first {a.n} that pass the "
          "reference-fix check:", flush=True)
    chosen, rejected = [], []
    for x in cands:
        if len(chosen) == a.n:
            break
        iid = x["instance"]
        print(f"- {iid} ({'core' if x['core'] else 'held-out'})", flush=True)
        try:
            print("  " + build(x, meta[iid], eval_dir, a.workers), flush=True)
            why = gold_check(x, meta[iid], eval_dir)
        except Exception as e:  # noqa: BLE001  (a failure of ours, not of the task: stop rather than skip it)
            sys.exit(f"{iid} ERROR {e!r}"[:600] + "\nfix this before the paid runs")
        if why:
            print(f"  REJECTED: {why}", flush=True)
            reject(eval_dir, iid, why)
            rejected.append(iid)
        else:
            chosen.append(x)
    if len(chosen) < a.n:
        sys.exit(f"only {len(chosen)} candidates pass the reference-fix check")
    keep = {x["instance"] for x in chosen}
    for f in sorted(os.listdir(os.path.join(eval_dir, "tasks"))):
        if f.endswith(".json") and f[:-5] not in keep:  # from an earlier build of this directory
            reject(eval_dir, f[:-5], "not among the first tasks that pass the reference-fix check")
            print(f"  removed earlier task {f[:-5]} (not selected now)", flush=True)
    print(f"tasks: {len(chosen)}; rejected by the reference-fix check: {', '.join(rejected) or 'none'}", flush=True)
    print("preflight (free): does Proviso narrow the tests?", flush=True)
    shares = []
    for x in chosen:
        try:
            shares.append(preflight(x, meta[x["instance"]], eval_dir))
        except Exception as e:  # noqa: BLE001
            print(x["instance"], "PREFLIGHT ERROR", repr(e)[:300], flush=True)
    if len(shares) < len(chosen):
        sys.exit("some tasks failed the preflight; fix them before paid runs")
    med = statistics.median(shares)
    print(f"median share selected: {med:.0%} (limit {LIMIT:.0%})", flush=True)
    if med >= LIMIT:
        sys.exit("Proviso selects nearly everything on most tasks; not starting paid runs.")
    print("OK: ready for the paid runs", flush=True)

if __name__ == "__main__":
    main()
