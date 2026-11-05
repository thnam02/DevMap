"""Compatibility probe for the SWE-bench agent-regression benchmark (no Proviso run, no API cost).

Proviso's recorder needs Python 3.12+ (sys.monitoring), and many SWE-bench task instances are from 2017-2022. For every
candidate instance (one with a genuine agent regression, issue from --since onwards) this builds an environment and
checks that the instance can be evaluated here:
  1. one Python 3.12 environment per (repository, version): the project's dependencies as of the environment setup
     commit, from packages published no later than max(late 2023, the version's newest issue + 60 days) (late 2023 is
     when the scientific stack had Python 3.12 builds);
  2. per instance: the base commit with the reference tests added (SWE-bench evaluates agent patches with them), the
     project installed from that tree, and the tests the agents broke run at base: they must pass.
An instance whose broken tests all pass at base is usable.

Usage (PC, needs network; uv):
  python3 research/v2/swe_probe.py [--since 2021] [--only sympy__sympy ...] [--python 3.12]
Inputs:  $PROVISO_WORK/swe/instances.jsonl (from swe_regressions.py), research/v2/results/swe/regressions.jsonl
Output:  research/v2/results/swe/probe.jsonl (one row per instance; resumable), probe.md (summary per repository),
         envs.jsonl (one row per environment). Environments and trees live under $PROVISO_WORK/swe."""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "swe")
WORK = os.path.join(os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2")), "swe")
TIMEOUT = int(os.environ.get("SWE_PROBE_TIMEOUT", "1200"))
# what each project needs beyond its own declared dependencies to run its tests
INSTALL = {
    "sympy__sympy": {"extras": "", "pkgs": ["mpmath", "pytest", "hypothesis"], "import": "sympy"},
    "sphinx-doc__sphinx": {"extras": "test", "pkgs": ["pytest"], "import": "sphinx"},
    "pydata__xarray": {"extras": "", "pkgs": ["pytest", "scipy", "hypothesis", "pytest-timeout"], "import": "xarray"},
    "pytest-dev__pytest": {"extras": "testing", "pkgs": [], "import": "_pytest"},
    "psf__requests": {"extras": "", "pkgs": ["pytest", "pytest-httpbin", "pytest-mock", "trustme", "PySocks"],
                      "import": "requests"},
    "pylint-dev__pylint": {"extras": "", "pkgs": ["pytest"], "reqs": "requirements_test_min.txt", "import": "pylint"},
    "mwaskom__seaborn": {"extras": "stats", "pkgs": ["pytest"], "import": "seaborn"},
    "pallets__flask": {"extras": "", "pkgs": ["pytest", "asgiref", "python-dotenv", "blinker"], "import": "flask"},
}


def run(cmd, cwd=None, timeout=1800, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def load_instances() -> dict:
    path = os.path.join(WORK, "instances.jsonl")
    if not os.path.exists(path):
        sys.exit(f"{path} missing: run research/v2/swe_regressions.py first")
    return {json.loads(l)["instance_id"]: json.loads(l) for l in open(path)}


def broken_tests() -> dict[str, set[str]]:
    out = collections.defaultdict(set)
    for line in open(os.path.join(OUT, "regressions.jsonl")):
        r = json.loads(line)
        out[r["instance"]].update(r.get("p2p_failed_genuine") or [])
    return {k: v for k, v in out.items() if v}


def repo_clone(repo: str) -> str:
    d = os.path.join(WORK, "repos", repo)
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        owner, name = repo.split("__", 1)
        run(["git", "clone", "-q", f"https://github.com/{owner}/{name}.git", d], timeout=3600)
    return d


def ensure_commit(d: str, sha: str):
    if run(["git", "-C", d, "cat-file", "-e", f"{sha}^{{commit}}"]).returncode:
        run(["git", "-C", d, "fetch", "-q", "origin", sha], timeout=600)


def cutoff(version_dates: list[str]) -> str:
    newest = max(version_dates)[:10]
    d = max(dt.date(2023, 11, 15), dt.date.fromisoformat(newest) + dt.timedelta(days=60))
    return d.isoformat()


def build_env(repo: str, version: str, setup_commit: str, dates: list[str], py: str) -> dict:
    """Environment for (repo, version): Python `py`, the project's dependencies at its environment setup commit."""
    name = f"{repo}__{version}"
    venv = os.path.join(WORK, "envs", name)
    pyexe = os.path.join(venv, "bin", "python")
    if os.path.exists(os.path.join(venv, ".probe_ok")):
        return {"env": name, "python": pyexe, "ok": True, "cached": True}
    shutil.rmtree(venv, ignore_errors=True)
    spec = INSTALL[repo]
    src = repo_clone(repo)
    ensure_commit(src, setup_commit)
    wt = tempfile.mkdtemp(prefix=f"swe-env-{name}-")
    log = []
    try:
        r = run(["git", "-C", src, "worktree", "add", "-f", "--detach", wt, setup_commit])
        if r.returncode:
            return {"env": name, "ok": False, "error": "worktree: " + r.stderr[-300:]}
        r = run(["uv", "venv", "-q", "--python", py, venv])
        if r.returncode:
            return {"env": name, "ok": False, "error": "venv: " + r.stderr[-300:]}
        when = cutoff(dates)
        target = wt + (f"[{spec['extras']}]" if spec["extras"] else "")
        cmd = ["uv", "pip", "install", "-q", "--python", pyexe, "--exclude-newer", when, "-e", target, *spec["pkgs"]]
        if spec.get("reqs") and os.path.exists(os.path.join(wt, spec["reqs"])):
            cmd += ["-r", os.path.join(wt, spec["reqs"])]
        r = run(cmd, timeout=3600)
        log.append(r.stderr[-1500:])
        if r.returncode and spec.get("reqs"):
            # pinned test requirements (e.g. an astroid without Python 3.12 support): retry without them
            r = run([c for c in cmd if c not in ("-r", os.path.join(wt, spec["reqs"]))], timeout=3600)
            log.append(r.stderr[-1500:])
        if r.returncode:
            return {"env": name, "ok": False, "cutoff": when, "error": "install: " + "\n".join(log)[-800:]}
        open(os.path.join(venv, ".probe_ok"), "w").write(when)
        return {"env": name, "python": pyexe, "ok": True, "cutoff": when}
    finally:
        run(["git", "-C", src, "worktree", "remove", "-f", wt])
        shutil.rmtree(wt, ignore_errors=True)


def test_files_of_patch(patch: str) -> list[str]:
    return sorted({m for m in re.findall(r"^\+\+\+ b/(\S+\.py)$", patch or "", re.M)
                   if re.search(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$", m)})


def junit_outcomes(xml: str, tree: str) -> dict[str, str]:
    """{pytest node id: 'passed'|'failed'|'error'|'skipped'} from a JUnit report (classname split back into the file path
    and the class)."""
    out = {}
    try:
        root = ET.parse(xml).getroot()
    except (ET.ParseError, OSError):
        return out
    for tc in root.iter("testcase"):
        cls, name = tc.get("classname") or "", tc.get("name") or ""
        parts = cls.split(".")
        node = None
        for k in range(len(parts), 0, -1):
            path = "/".join(parts[:k]) + ".py"
            if os.path.exists(os.path.join(tree, path)):
                node = "::".join([path, *parts[k:], name])
                break
        node = node or f"{cls}::{name}"
        kids = {c.tag for c in tc}
        out[node] = ("failed" if "failure" in kids else "error" if "error" in kids
                     else "skipped" if "skipped" in kids else "passed")
    return out


def probe_instance(inst: dict, broken: set[str], env: dict) -> dict:
    repo = inst["instance_id"].rsplit("-", 1)[0]
    tree = os.path.join(WORK, "trees", repo)
    src = repo_clone(repo)
    if not os.path.isdir(os.path.join(tree, ".git")):
        os.makedirs(os.path.dirname(tree), exist_ok=True)
        run(["git", "clone", "-q", "--shared", src, tree])
    ensure_commit(src, inst["base_commit"])
    run(["git", "-C", tree, "fetch", "-q", src, inst["base_commit"]])
    run(["git", "-C", tree, "checkout", "-q", "-f", inst["base_commit"]])
    run(["git", "-C", tree, "clean", "-q", "-fdx"])
    ap = subprocess.run(["git", "-C", tree, "apply", "-"], input=inst.get("test_patch") or "", capture_output=True,
                        text=True)
    if ap.returncode:
        return {"ok": False, "stage": "test_patch", "error": ap.stderr[-300:]}
    py = env["python"]
    r = run(["uv", "pip", "install", "-q", "--python", py, "--no-deps", "-e", tree], timeout=1800)
    if r.returncode:
        return {"ok": False, "stage": "install", "error": r.stderr[-300:]}
    imp = run([py, "-c", f"import {INSTALL[repo]['import']}"], cwd=tree)
    if imp.returncode:
        return {"ok": False, "stage": "import", "error": imp.stderr[-300:]}
    node_ids = all("::" in t for t in broken)
    files = sorted({t.split("::", 1)[0] for t in broken}) if node_ids else test_files_of_patch(inst.get("test_patch"))
    files = [f for f in files if os.path.exists(os.path.join(tree, f))]
    if not files:
        return {"ok": False, "stage": "files", "error": "no test file of the broken tests exists at base"}
    fd, xml = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    t0 = time.time()
    try:
        run([py, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no", "-o", "addopts=", f"--junitxml={xml}",
             *files], cwd=tree, timeout=TIMEOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        res = junit_outcomes(xml, tree)
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "tests", "error": f"timeout after {TIMEOUT} s"}
    finally:
        os.remove(xml)
    status = {}
    for t in sorted(broken):
        if node_ids:
            got = res.get(t)
            if got is None:   # SWE-bench sometimes truncates parametrised ids at a space
                cands = [v for k, v in res.items() if k.startswith(t)]
                got = cands[0] if len(cands) == 1 else None
        else:   # sympy lists test function names
            cands = [v for k, v in res.items() if k.rsplit("::", 1)[-1] == t]
            got = "passed" if cands and all(c == "passed" for c in cands) else (cands[0] if cands else None)
        status[t] = got or "missing"
    c = collections.Counter(status.values())
    return {"ok": c.get("passed", 0) == len(status), "stage": "tests", "broken": len(status),
            "passed_at_base": c.get("passed", 0), "outcomes": dict(c), "tests_run": len(res),
            "not_passing": {t: s for t, s in status.items() if s != "passed"}, "secs": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=2021)
    ap.add_argument("--only", nargs="*", default=list(INSTALL))
    ap.add_argument("--python", default="3.12")
    a = ap.parse_args()
    if not shutil.which("uv"):
        sys.exit("uv is needed (https://docs.astral.sh/uv/)")
    meta, broken = load_instances(), broken_tests()
    cands = sorted(i for i in broken if i in meta and i.rsplit("-", 1)[0] in a.only
                   and int((meta[i].get("created_at") or "0000")[:4]) >= a.since)
    print(f"{len(cands)} candidate instances (issue from {a.since}, genuine agent regression)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    out_path, env_path = os.path.join(OUT, "probe.jsonl"), os.path.join(OUT, "envs.jsonl")
    done = {json.loads(l)["instance"] for l in open(out_path)} if os.path.exists(out_path) else set()
    by_env = collections.defaultdict(list)
    for i in cands:
        by_env[(meta[i]["repo"].replace("/", "__"), meta[i]["version"])].append(i)
    envs = {}
    for (repo, version), insts in sorted(by_env.items()):
        if all(i in done for i in insts):
            continue
        dates = [meta[i]["created_at"] for i in insts]
        e = build_env(repo, version, meta[insts[0]]["environment_setup_commit"], dates, a.python)
        envs[(repo, version)] = e
        with open(env_path, "a") as fh:
            fh.write(json.dumps({"repo": repo, "version": version, **{k: v for k, v in e.items() if k != "python"}})
                     + "\n")
        print(f"[env {repo} {version}] {'ok' if e['ok'] else 'FAILED: ' + e.get('error', '')[:200]}", flush=True)
        for i in insts:
            if i in done:
                continue
            if not e["ok"]:
                row = {"ok": False, "stage": "env", "error": e.get("error", "")[:300]}
            else:
                try:
                    row = probe_instance(meta[i], broken[i], e)
                except Exception as ex:  # noqa: BLE001
                    row = {"ok": False, "stage": "probe", "error": repr(ex)[:300]}
            row = {"instance": i, "repo": repo, "version": version, "created_at": meta[i]["created_at"], **row}
            with open(out_path, "a") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"  {i}: {'usable' if row['ok'] else 'not usable'} ({row.get('stage')}"
                  f"{', ' + str(row.get('passed_at_base')) + '/' + str(row.get('broken')) + ' broken tests pass at base' if 'broken' in row else ''})",
                  flush=True)
    rows = {}
    for line in open(out_path):
        r = json.loads(line)
        rows[r["instance"]] = r
    lines = ["# SWE-bench instances usable with Python " + a.python, "",
             "| repository | candidates | environment ok | imports | all broken tests pass at base (usable) | "
             "some pass |", "|---|---|---|---|---|---|"]
    for repo in INSTALL:
        rs = [r for r in rows.values() if r["repo"] == repo]
        if not rs:
            continue
        lines.append(f"| {repo} | {len(rs)} | {sum(r['stage'] != 'env' for r in rs)} | "
                     f"{sum(r['stage'] in ('tests', 'files') for r in rs)} | {sum(r['ok'] for r in rs)} | "
                     f"{sum(1 for r in rs if r.get('passed_at_base'))} |")
    lines.append(f"| **all** | {len(rows)} | | | {sum(r['ok'] for r in rows.values())} | |")
    open(os.path.join(OUT, "probe.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
