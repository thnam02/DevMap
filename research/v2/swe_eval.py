"""Proviso on real agent regressions (SWE-bench leaderboard patches that broke previously passing tests).

For each instance of the fixed sample (results/swe/sample.json, in its order; the core sample first):
  1. the base commit with SWE-bench's reference tests added, committed (HEAD); the project installed from it into the
     probe's Python 3.12 environment for its version;
  2. Proviso records its dependency map there (the project's whole test suite, one interpreter per test file);
  3. for each case (one agent patch): the patch applied to the working tree, Proviso selects; the broken tests are run
     after the patch here, and those that fail here (they passed at base, as the probe checked) are the ground truth;
     a case is missed when Proviso's selection leaves out one of them.
Resumable (rows keyed by instance and case, with a format number). No API cost.

Usage (PC, after swe_probe.py):
  python3 research/v2/swe_eval.py [--core] [--limit N] [--workers W]
Output: research/v2/results/swe/eval.jsonl (one row per case), eval.md (summary per repository).
Maps: $PROVISO_WORK/swe/maps/<instance>.json"""
from __future__ import annotations

import argparse
import collections
import fcntl
import re
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import swe_probe as P  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as IS  # noqa: E402
from dc_engine import record as REC  # noqa: E402

OUT = P.OUT
WORK = P.WORK
EVAL_FORMAT = 1
# maps recorded with a per-file limit (see record_map); a map recorded without one is kept
# the package Proviso records (relative to the tree) and the test directories of each repository
LAYOUT = {"sympy__sympy": ("sympy", ["sympy"]), "sphinx-doc__sphinx": ("sphinx", ["tests"]),
          "pydata__xarray": ("xarray", ["xarray/tests"]), "pytest-dev__pytest": ("src", ["testing"]),
          "pylint-dev__pylint": ("pylint", ["tests"]), "mwaskom__seaborn": ("seaborn", ["tests"]),
          "pallets__flask": ("src/flask", ["tests"])}
GIT = ["git", "-c", "user.email=eval@proviso", "-c", "user.name=proviso-eval"]


def git(tree, *a, check=False, **kw):
    r = subprocess.run([*GIT, "-C", tree, *a], capture_output=True, text=True, **kw)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a[:3])}: {r.stderr[-300:]}")
    return r


def prepare_tree(inst: dict, py: str, trees: str = "eval-trees") -> str:
    """Base commit + reference tests, committed; installed (editable, no dependencies) into the environment."""
    repo = inst["instance_id"].rsplit("-", 1)[0]
    src = P.repo_clone(repo)
    tree = os.path.join(WORK, trees, repo)
    if not os.path.isdir(os.path.join(tree, ".git")):
        os.makedirs(os.path.dirname(tree), exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--shared", src, tree], check=True)
    P.ensure_commit(src, inst["base_commit"])
    git(tree, "fetch", "-q", src, inst["base_commit"])
    git(tree, "checkout", "-q", "-f", inst["base_commit"], check=True)
    git(tree, "clean", "-q", "-fdx")
    ap = subprocess.run(["git", "-C", tree, "apply", "-"], input=inst.get("test_patch") or "", capture_output=True,
                        text=True)
    if ap.returncode:
        raise RuntimeError("test patch does not apply: " + ap.stderr[-300:])
    git(tree, "add", "-A", check=True)
    git(tree, "commit", "-q", "--allow-empty", "-m", "SWE-bench reference tests", check=True)
    r = P.run(["uv", "pip", "install", "-q", "--python", py, "--no-deps", "-e", tree], timeout=1800)
    if r.returncode:
        raise RuntimeError("install: " + r.stderr[-300:])
    return tree


def reset_tree(tree: str):
    git(tree, "checkout", "-q", "--", ".")
    git(tree, "clean", "-q", "-fd", "-e", ".dc-engine", "-e", "*.egg-info")


def record_map(instance: str, repo: str, tree: str, py: str, workers: int) -> tuple[dict, float]:
    path = os.path.join(WORK, "maps", instance + ".json")
    meta = path + ".meta"
    if os.path.exists(path) and os.path.exists(meta) and json.load(open(meta)).get("format") == IS.FORMAT:
        return json.load(open(path)), json.load(open(meta)).get("record_s", 0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pkg, targets = LAYOUT[repo]
    targets = [t for t in targets if os.path.exists(os.path.join(tree, t))]
    extra = [os.path.join(tree, "src")] if os.path.isdir(os.path.join(tree, "src")) else []
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([tree, *extra]), "PYTHONDONTWRITEBYTECODE": "1",
           "PATH": os.path.dirname(py) + os.pathsep + os.environ.get("PATH", "")}
    t = time.time()
    # a test file whose recording exceeds the limit (some sympy files ran for over an hour) or crashes: its tests are
    # always selected rather than missing from the map
    REC.FILE_TIMEOUT = int(os.environ.get("PROVISO_RECORD_FILE_TIMEOUT", "900"))
    REC.record(tree, pkg, path, py, targets, workers, "", ["-p", "no:randomly"], env)
    secs = round(time.time() - t)
    json.dump({"format": IS.FORMAT, "record_s": secs}, open(meta, "w"))
    return json.load(open(path)), secs


def without_files(patch: str, drop: set[str]) -> tuple[str, list[str]]:
    """The patch without its changes to `drop` (SWE-bench's evaluation resets the files of the reference test patch
    before applying it, so an agent's edits to them never take part)."""
    parts = re.split(r"(?m)^(?=diff --git )", patch)
    keep, dropped = [], []
    for part in parts:
        m = re.match(r"diff --git a/(\S+) b/(\S+)", part)
        if m and (m.group(1) in drop or m.group(2) in drop):
            dropped.append(m.group(2))
            continue
        keep.append(part)
    return "".join(keep), dropped


def apply_patch(tree: str, patch: str) -> dict:
    """Apply an agent patch as SWE-bench's harness does: `git apply`, then (our addition) a 3-way merge, then
    `patch --batch --fuzz=5 -p1` (the harness's last fallback; tried dry first, so a failure leaves the tree as it was).
    Binary files in the patch (a screenshot an agent saved) are left out: git cannot apply them without their
    contents, and they take no part in the tests."""
    parts = re.split(r"(?m)^(?=diff --git )", patch)
    binary = [re.match(r"diff --git a/\S+ b/(\S+)", p_).group(1) for p_ in parts
              if p_.startswith("diff --git ") and re.search(r"(?m)^(GIT binary patch|Binary files .* differ)$", p_)]
    patch = "".join(p_ for p_ in parts if not (p_.startswith("diff --git ") and
                                                re.search(r"(?m)^(GIT binary patch|Binary files .* differ)$", p_)))
    info = {"binary_files_dropped": binary} if binary else {}
    if not patch.strip():
        raise RuntimeError("the agent patch only adds binary files")
    if not patch.endswith("\n"):
        patch += "\n"
    errs = []
    for how, cmd in (("git apply", ["git", "-C", tree, "apply", "-"]),
                     ("git apply --3way", ["git", "-C", tree, "apply", "--3way", "-"])):
        r = subprocess.run(cmd, input=patch, capture_output=True, text=True)
        if not r.returncode:
            return {**info, "applied_with": how} if how != "git apply" else info
        errs.append(r.stderr.strip()[-150:])
        git(tree, "checkout", "-q", "--", ".")
        git(tree, "clean", "-q", "-fd", "-e", ".dc-engine", "-e", "*.egg-info")
    dry = subprocess.run(["patch", "--batch", "--fuzz=5", "-p1", "--dry-run"], input=patch, cwd=tree,
                         capture_output=True, text=True)
    if not dry.returncode:
        r = subprocess.run(["patch", "--batch", "--fuzz=5", "-p1", "--no-backup-if-mismatch"], input=patch, cwd=tree,
                           capture_output=True, text=True)
        if not r.returncode:
            return {**info, "applied_with": "patch --fuzz=5"}
    errs.append((dry.stdout + dry.stderr).strip()[-150:])
    raise RuntimeError("agent patch does not apply: " + " | ".join(errs))


def resolve(test: str, nodes: list[str], test_files: list[str]) -> list[str]:
    """The map's node ids for a SWE-bench test name: an exact node id, a node id truncated by SWE-bench at a space
    (prefix), or (sympy) a bare test function name, looked up in the files the reference tests touch."""
    if "::" in test:
        if test in nodes:
            return [test]
        return [n for n in nodes if n.startswith(test)]
    hits = [n for n in nodes if n.rsplit("::", 1)[-1] == test]
    near = [n for n in hits if n.split("::", 1)[0] in test_files]
    return near or hits


def run_tests(tree: str, py: str, tests: list[str], test_files: list[str]) -> dict[str, str]:
    """Outcome of each SWE-bench test name after the patch (pytest on the files that hold them)."""
    files = sorted({t.split("::", 1)[0] for t in tests if "::" in t} | ({*test_files} if any("::" not in t for t in tests)
                                                                         else set()))
    files = [f for f in files if os.path.exists(os.path.join(tree, f))]
    if not files:
        return {t: "missing" for t in tests}
    fd, xml = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    base = [py, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no", f"--junitxml={xml}"]
    try:
        r = P.run([*base, *files], cwd=tree, timeout=P.TIMEOUT, env=env)
        res = P.junit_outcomes(xml, tree)
        if not res or r.returncode in (3, 4):
            P.run([*base, "-o", "addopts=", *files], cwd=tree, timeout=P.TIMEOUT, env=env)
            res = P.junit_outcomes(xml, tree)
    except subprocess.TimeoutExpired:
        return {t: "timeout" for t in tests}
    finally:
        os.remove(xml)
    out = {}
    for t in tests:
        keys = resolve(t, list(res), test_files)
        vals = [res[k] for k in keys]
        out[t] = ("failed" if any(v in ("failed", "error") for v in vals) else
                  "passed" if vals and all(v == "passed" for v in vals) else (vals[0] if vals else "missing"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", action="store_true", help="only the core sample (the first 80 instances)")
    ap.add_argument("--limit", type=int, default=0, help="at most N instances (in the sample's order)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    lock = open(os.path.join(WORK, "swe_eval.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)   # two runs would share the work trees
    except OSError:
        sys.exit("another swe_eval run is active (lock: " + lock.name + ")")
    sample = json.load(open(os.path.join(OUT, "sample.json")))["instances"]
    if a.core:
        sample = [x for x in sample if x["core"]]
    if a.limit:
        sample = sample[:a.limit]
    meta = P.load_instances()
    out_path = os.path.join(OUT, "eval.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r.get("format") == EVAL_FORMAT and r.get("proviso_format") == IS.FORMAT and "error" not in r:
                done.add((r["instance"], r["case"]))
    for x in sample:
        inst, repo = x["instance"], x["repo"]
        todo = [k for k in range(len(x["cases"])) if (inst, k) not in done]
        if not todo:
            continue
        env = os.path.join(WORK, "envs", f"{repo}__{x['version']}", "bin", "python")
        t0 = time.time()
        try:
            tree = prepare_tree(meta[inst], env)
            cov, rec_s = record_map(inst, repo, tree, env, a.workers)
            nodes = sorted(I.tests_of(cov))
            if not nodes:
                raise RuntimeError("the dependency map recorded no tests")
        except Exception as e:  # noqa: BLE001
            for k in todo:
                write(out_path, {"instance": inst, "repo": repo, "case": k, "error": repr(e)[:400]})
            print(f"{inst}: ERROR {repr(e)[:200]}", flush=True)
            continue
        test_files = P.test_files_of_patch(meta[inst].get("test_patch"))
        times = {n: cov[n].get("time", 0) or 0 for n in nodes}
        total = sum(times.values()) or 1e-9
        for k in todo:
            c = x["cases"][k]
            row = {"instance": inst, "repo": repo, "case": k, "submission": c["submission"], "split": c["split"],
                   "broken": c["broken"], "record_s": rec_s, "map_tests": len(nodes)}
            try:
                reset_tree(tree)
                patch = open(c["patch"]).read() if c.get("patch") and os.path.exists(c["patch"]) else None
                if not patch:
                    raise RuntimeError("patch file missing")
                ref_files = set(re.findall(r"(?m)^\+\+\+ b/(\S+)$", meta[inst].get("test_patch") or ""))
                patch, row["dropped_files"] = without_files(patch, ref_files)
                if not patch.strip():
                    raise RuntimeError("the agent patch only edits files the reference tests replace")
                row.update(apply_patch(tree, patch))
                t = time.time()
                sel, why = I.selection(tree, cov, env)
                row["selection_s"] = round(time.time() - t, 2)
                # Proviso's selection: node ids, plus whole test files it runs (test files the patch edits)
                files_run = {e for e in (sel or []) if "::" not in e}
                chosen = set(nodes) if sel is None else \
                    (set(sel) & set(nodes)) | {n for n in nodes if n.split("::", 1)[0] in files_run}
                row.update(full_suite=sel is None, reason=why.get("reason"), selected=len(chosen),
                           time_share=round(sum(times[n] for n in chosen) / total, 4))
                after = run_tests(tree, env, c["broken"], test_files)
                row["after"] = after
                truth = [t_ for t_, v in after.items() if v == "failed"]
                row["reproduced"] = truth
                missed = []
                for t_ in truth:
                    keys = resolve(t_, nodes, test_files)
                    # a broken test is selected when every map entry it names is (a test new in the reference tests
                    # that the map lacks counts as missed)
                    if not keys or not all(k_ in chosen for k_ in keys):
                        missed.append(t_)
                row.update(missed=missed, caught=bool(truth) and not missed)
            except Exception as e:  # noqa: BLE001
                row["error"] = repr(e)[:400]
            finally:
                reset_tree(tree)
            row.update(format=EVAL_FORMAT, proviso_format=IS.FORMAT)
            write(out_path, row)
            status = ("ERROR " + row["error"][:120]) if "error" in row else (
                "not reproduced here" if not row["reproduced"] else
                f"{'caught' if row['caught'] else 'MISSED ' + str(len(row['missed']))} "
                f"({len(row['reproduced'])} broken; selected {row['selected']}/{len(nodes)}, "
                f"{100 * row['time_share']:.0f}% of time)")
            print(f"{inst} case {k}: {status}", flush=True)
        print(f"{inst}: done in {round(time.time() - t0)} s (map {rec_s} s)", flush=True)
    summary(out_path)


def write(path, row):
    with open(path, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def summary(out_path):
    rows = {}
    for line in open(out_path):
        r = json.loads(line)
        rows[(r["instance"], r["case"])] = r
    rows = list(rows.values())
    lines = ["# Proviso on real agent regressions (SWE-bench)", "",
             "| repository | instances | cases | errors | not reproduced here | regressions | missed | "
             "test time selected (mean) | full suite |", "|---|---|---|---|---|---|---|---|---|"]
    allr = []
    for repo in LAYOUT:
        rs = [r for r in rows if r["repo"] == repo]
        if not rs:
            continue
        ok = [r for r in rs if "error" not in r]
        reg = [r for r in ok if r.get("reproduced")]
        allr += reg
        lines.append(f"| {repo} | {len({r['instance'] for r in rs})} | {len(rs)} | {len(rs) - len(ok)} | "
                     f"{len(ok) - len(reg)} | {len(reg)} | {sum(1 for r in reg if r['missed'])} | "
                     f"{100 * statistics.mean(r['time_share'] for r in reg) if reg else 0:.1f}% | "
                     f"{sum(r['full_suite'] for r in reg)} |")
    lines.append(f"| **all** | | {len(rows)} | | | {len(allr)} | {sum(1 for r in allr if r['missed'])} | "
                 f"{100 * statistics.mean(r['time_share'] for r in allr) if allr else 0:.1f}% | "
                 f"{sum(r['full_suite'] for r in allr)} |")
    open(os.path.join(OUT, "eval.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
