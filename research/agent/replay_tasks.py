"""Agent study, replay design: tasks that start from a published agent's regressing patch.

Each task is one regression of the SWE-bench evaluation (research/v2/results/swe/eval-v2.3.jsonl: a published agent's
patch that broke PASS_TO_PASS tests, reproduced in our environments). The agent gets the issue and a working tree
that already holds that patch, uncommitted, as an earlier attempt to continue from; the prompt does not say that the
attempt breaks anything. Both arms get the same prompt and the same start. The question: does the agent notice and
repair the breakage before it stops, at what time and cost, with and without Proviso choosing the tests it runs?

Case rule (fixed before any run): every reproduced regression of the sample in the repositories whose suites run on
Python 3.12 in reasonable time (sphinx, xarray, pylint, seaborn, pytest; not flask, whose tests cannot run on 3.12,
and not sympy, whose recording takes about 30 minutes per instance), in sample order. A case is kept if
  1. its instance passes the reference-fix check (swe_tasks.gold_check: SWE-bench's own fix passes every
     FAIL_TO_PASS test here; PASS_TO_PASS tests failing with it are environment failures and are dropped), and
  2. the start state reproduces the regression here: graded exactly as an agent's final state is, at least one of the
     regression's broken tests fails (those are the case's `start_broken` tests).
Rejected cases go to rejected/ with the reason, decided before any run and never by Proviso's selection.

Layout, in EVAL_DIR:
  inst/                 per instance: swe_tasks' task and Proviso assets (map at the plain base commit)
  impact/<instance>/    Proviso's assets, shared by the instance's cases (task field "assets")
  tasks/<case>.json     dc_eval task: id <instance>__c<k>, start_patch (the agent's patch, normalised to apply with
                        git apply), start_broken, hidden and regression tests, test_patch_only
  rejected/<case>/      reason.txt
  checks/               the grading logs of the reference-fix and start-state checks (their work folders are deleted)
  cases.jsonl           one row per case: kept or rejected, and the start-state grading

  python3 research/agent/replay_tasks.py EVAL_DIR [--limit N] [--workers W]"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import swe_tasks as S  # noqa: E402
from swe_tasks import E, P  # noqa: E402

REPOS = ["sphinx-doc__sphinx", "pydata__xarray", "pylint-dev__pylint", "mwaskom__seaborn", "pytest-dev__pytest"]
NOTE = ("\n\n---\nAn earlier attempt at this issue has already been made in this repository: its changes are in the "
        "working tree, uncommitted (`git diff` shows them). Continue from there and finish the task.")


def candidates() -> list[dict]:
    """The case rule in the module docstring, in sample order."""
    sample = json.load(open(os.path.join(P.OUT, "sample.json")))["instances"]
    rows = {}
    for line in open(os.path.join(P.OUT, "eval-v2.3.jsonl")):
        r = json.loads(line)
        rows[(r["instance"], r["case"])] = r
    out = []
    for x in sample:
        if x["repo"] not in REPOS:
            continue
        for k, c in enumerate(x["cases"]):
            r = rows.get((x["instance"], k)) or {}
            if r.get("reproduced") and "error" not in r:
                out.append({"x": x, "case": k, "split": c["split"], "submission": c["submission"],
                            "reproduced": list(r["reproduced"]), "id": f"{x['instance']}__c{k}"})
    return out


def patch_path(c: dict) -> str:
    return os.path.join(P.WORK, "patches", c["split"], c["submission"], c["x"]["instance"] + ".diff")


def fetch_patches(cands: list[dict], eval_dir: str):
    want = [[c["split"], c["submission"], c["x"]["instance"]] for c in cands if not os.path.isfile(patch_path(c))]
    if not want:
        return
    lst = os.path.join(eval_dir, "patches-wanted.json")
    json.dump(want, open(lst, "w"))
    r = subprocess.run(["uv", "run", "--quiet", "--no-project", "--python", "3.12", "--with", "boto3", "--with",
                        "pyyaml", "python", os.path.join(HERE, "fetch_patches.py"), lst])
    if r.returncode:
        raise RuntimeError("some agent patches could not be fetched (see above)")


def start_patch(c: dict, inst: dict) -> tuple[str, list[str]]:
    """The agent's patch as SWE-bench's evaluation applied it (its edits to the reference test files left out), applied
    to the agent's starting tree, then written back as a plain git diff that `git apply` takes exactly."""
    raw = open(patch_path(c), encoding="utf-8", errors="replace").read()
    ref_files = set(re.findall(r"(?m)^\+\+\+ b/(\S+)$", inst.get("test_patch") or ""))
    patch, dropped = E.without_files(raw, ref_files)
    if not patch.strip():
        raise ValueError("the agent patch only edits files the reference tests replace")
    tree = S.agent_tree(inst, S.generated_files(c["x"]))
    try:
        E.apply_patch(tree, patch)
        S.git(tree, "add", "-A")
        norm = S.git(tree, "diff", "--cached", "--no-color", "--no-ext-diff")
    finally:
        S.git(tree, "reset", "-q")
        S.git(tree, "checkout", "-q", "-f", inst["base_commit"])
        S.git(tree, "clean", "-q", "-fdx")
    if not norm.strip():
        raise ValueError("the agent patch changes nothing here")
    return norm, dropped


def start_check(c: dict, inst: dict, task: dict, eval_dir: str) -> dict:
    """Grade the start state (base + the agent's patch, no further work) exactly as a run's final state is graded."""
    from dc_eval import grade as G
    from dc_eval import run as R
    from dc_eval import tasks as T
    t = T.Task.from_dict(task)
    tree = S.agent_tree(inst, S.generated_files(c["x"]))
    work = os.path.join(P.WORK, "replay-start", c["id"])
    shutil.rmtree(work, ignore_errors=True)
    repo = os.path.join(work, "repo")
    subprocess.run(["git", "clone", "-q", "--shared", tree, repo], check=True)
    S.git(repo, "checkout", "-q", "-f", inst["base_commit"])
    R.write_task_files(repo, t.files)
    R.apply_start_patch(repo, t.start_patch)
    venv = R.create_run_venv(work, t.python)
    env = R.venv_env(venv)
    env["DC_EVAL_OFFLINE"] = "1"
    py = R.venv_python(venv)
    G.install_test_env(py, repo, env=env)
    R.run_setup(repo, t.setup, env=env)
    g = G.grade_repo(t, repo, python=py, src_repo=tree, run_dir=work)
    log = keep_log(eval_dir, os.path.join(work, G.GRADING_LOG), c["id"] + ".start.log")
    shutil.rmtree(work, ignore_errors=True)  # a checkout and a venv per case: keep only the grading log
    return {"resolved": g["resolved"], "hidden": f"{g['hidden_checks_passed']}/{g['hidden_checks_total']}",
            "regression_failed": g["regression_failed"], "n_regression": len(g["regression"]), "log": log}


def keep_log(eval_dir: str, src: str, name: str) -> str:
    dest = os.path.join(eval_dir, "checks", name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.isfile(src):
        shutil.copyfile(src, dest)
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_dir")
    ap.add_argument("--limit", type=int, default=0, help="only the first N cases (for a trial build)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    eval_dir = os.path.abspath(a.eval_dir)
    inst_dir = os.path.join(eval_dir, "inst")
    for d in ("tasks", "impact", "rejected", "inst"):
        os.makedirs(os.path.join(eval_dir, d), exist_ok=True)
    cands = candidates()
    if a.limit:
        cands = cands[:a.limit]
    print(f"{len(cands)} cases in {len({c['x']['instance'] for c in cands})} instances "
          f"({', '.join(REPOS)})", flush=True)
    S.ensure_instances(sorted({c["x"]["instance"] for c in cands}))
    fetch_patches(cands, eval_dir)
    meta = P.load_instances()
    log = open(os.path.join(eval_dir, "cases.jsonl"), "a")
    gold: dict[str, str | None] = {}
    kept = 0
    for c in cands:
        iid = c["x"]["instance"]
        inst = meta[iid]
        case_path = os.path.join(eval_dir, "tasks", c["id"] + ".json")
        rej_path = os.path.join(eval_dir, "rejected", c["id"], "reason.txt")
        if os.path.isfile(case_path):
            kept += 1
            continue
        if os.path.isfile(rej_path):
            continue
        print(f"- {c['id']} ({c['submission']})", flush=True)
        try:
            if iid not in gold:
                if not os.path.isfile(os.path.join(inst_dir, "tasks", iid + ".json")) \
                        and not os.path.isfile(os.path.join(inst_dir, "rejected", iid, "reason.txt")):
                    print("  " + S.build(c["x"], inst, inst_dir, a.workers), flush=True)
                    why = S.gold_check(c["x"], inst, inst_dir)
                    gold_work = os.path.join(P.WORK, "gold", iid)
                    keep_log(eval_dir, os.path.join(gold_work, "grading.log"), iid + ".reference-fix.log")
                    shutil.rmtree(gold_work, ignore_errors=True)
                    if why:
                        S.reject(inst_dir, iid, why.replace(os.path.join(gold_work, "grading.log"),
                                                            os.path.join(eval_dir, "checks", iid + ".reference-fix.log")))
                why_path = os.path.join(inst_dir, "rejected", iid, "reason.txt")
                gold[iid] = open(why_path).read().strip() if os.path.isfile(why_path) else None
                if gold[iid] is None and not os.path.isdir(os.path.join(eval_dir, "impact", iid)):
                    shutil.copytree(os.path.join(inst_dir, "impact", iid), os.path.join(eval_dir, "impact", iid))
            why = f"instance rejected: {gold[iid]}" if gold[iid] else None
            row = {"id": c["id"], "instance": iid, "case": c["case"], "submission": c["submission"],
                   "reproduced_on_pc": c["reproduced"]}
            if not why:
                base = json.load(open(os.path.join(inst_dir, "tasks", iid + ".json")))
                try:
                    sp, dropped = start_patch(c, inst)
                except (ValueError, RuntimeError) as e:
                    sp, why = "", f"start patch: {e}"
                if sp:
                    task = {**base, "id": c["id"], "prompt": inst["problem_statement"] + NOTE, "start_patch": sp,
                            "assets": iid, "source": "SWE-bench replay", "replay_of": c["submission"],
                            "start_patch_dropped_files": dropped}
                    st = start_check(c, inst, task, eval_dir)
                    broken = sorted(set(st["regression_failed"]) & set(c["reproduced"]))
                    row.update(start=st, start_broken=broken)
                    if not broken:
                        why = ("the start state does not reproduce the regression here (none of "
                               f"{len(c['reproduced'])} broken tests fails; grading log {st['log']})")
                    else:
                        task.update(start_broken=broken, start_resolved=st["resolved"],
                                    start_regression_failed=st["regression_failed"])
                        json.dump(task, open(case_path, "w"), indent=1)
        except Exception as e:  # noqa: BLE001  (a failure of ours, not of the case: stop rather than skip it)
            sys.exit(f"{c['id']} ERROR {e!r}"[:600] + "\nfix this before the paid runs")
        if why:
            os.makedirs(os.path.dirname(rej_path), exist_ok=True)
            open(rej_path, "w").write(why + "\n")
            print(f"  REJECTED: {why}"[:400], flush=True)
        else:
            kept += 1
            print(f"  kept: start state breaks {len(row['start_broken'])} of the {len(c['reproduced'])} tests "
                  f"(hidden {row['start']['hidden']}, PASS_TO_PASS failing {len(row['start']['regression_failed'])}"
                  f" of {row['start']['n_regression']})", flush=True)
        log.write(json.dumps({**row, "kept": not why, "reason": why}) + "\n")
        log.flush()
    n_rej = len(os.listdir(os.path.join(eval_dir, "rejected")))
    print(f"cases kept: {kept}; rejected: {n_rej}", flush=True)
    if not kept:
        sys.exit("no case kept")
    print("OK: replay tasks ready", flush=True)


if __name__ == "__main__":
    main()
