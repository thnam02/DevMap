"""Checks on Proviso's v1 results on NameRTS's benchmark (no change to Proviso; no API cost).

  verify PROJECT ...   For every pair where Proviso missed ground-truth test files (files that recorded tests here),
                       run those files at true_parent and at current and compare test outcomes. A missed file whose
                       outcomes do not change could not have caught anything (NameRTS's ground truth counts tests that
                       execute modified code, not tests whose result the change alters); a changed outcome is a real
                       miss. Outcomes at true_parent also show tests that error or skip in this environment.
                       -> research/v2/results/nrbench/verify_<project>.jsonl and a summary
  pylint-diag          Proviso's selection with its reasons on one pylint pair (ad14b5bf..ed596323): on the PC it
                       selected 81 files, in a reproduction elsewhere 10.
  summary              Totals over every verify_*.jsonl.

Usage (WSL, repo root, nothing else running on the benchmark trees):
  python3 research/v2/nrcheck.py verify loguru pvlib pylint sphinx seaborn xarray dask sympy
  python3 research/v2/nrcheck.py pylint-diag
  python3 research/v2/nrcheck.py summary"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nrbench as N  # noqa: E402

OUT = N.OUT
TIMEOUT = int(os.environ.get("NRCHECK_TIMEOUT", "3600"))


def venv_python(proj):
    return os.path.join(N.WORK, "nrbench-venvs", proj, "bin", "python")


def outcomes(proj, tree, files, python):
    """{test: outcome} for the given test files in `tree`, from pytest's JUnit XML report ('passed', 'failed',
    'error', 'skipped'); 'collect-error:<file>' when a file yields no test at all."""
    import tempfile
    import xml.etree.ElementTree as ET
    extra = [x for x in os.environ.get("PROVISO_EXTRA_PATH", "").split(os.pathsep) if x]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([tree, *extra]), "PYTHONDONTWRITEBYTECODE": "1"}
    files = [f for f in files if os.path.exists(os.path.join(tree, f))]
    if not files:
        return {}
    fd, xml_path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    try:
        subprocess.run([python, "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly", "-q", "--tb=no",
                        "-o", "addopts=", f"--junitxml={xml_path}", *files], cwd=tree, env=env, capture_output=True,
                       text=True, timeout=TIMEOUT)
        res = {}
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError):
            root = None
        for tc in (root.iter("testcase") if root is not None else []):
            key = f"{tc.get('classname', '')}::{tc.get('name', '')}"
            kids = {c.tag for c in tc}
            res[key] = ("failed" if "failure" in kids else "error" if "error" in kids
                        else "skipped" if "skipped" in kids else "passed")
    finally:
        os.remove(xml_path)
    for f in files:
        mod = f[:-3].replace("/", ".")
        if not any(k.startswith(mod) for k in res):
            res[f"collect-error:{f}"] = "error"
    return res


def verify(proj):
    path = os.path.join(OUT, f"{proj}.jsonl")
    rows = [r for r in N._rows(path) if "error" not in r]
    todo = [r for r in rows if set(r["proviso_missed"]) - set(r.get("gt_not_recorded", []))]
    out = os.path.join(OUT, f"verify_{proj}.jsonl")
    # a pair counts as verified only for the current Proviso (another version may miss other files)
    done = {r["current"] for r in map(json.loads, open(out)) if r.get("format") == N.IS.FORMAT} \
        if os.path.exists(out) else set()
    tree = os.path.join(N.WORK, "nrbench", proj, "repo")
    py = venv_python(proj)
    C = N.PROJECTS[proj]
    print(f"== {proj}: {len(todo)} pairs with missed files that recorded tests ({len(done)} already verified)")
    for r in todo:
        if r["current"] in done:
            continue
        files = sorted(set(r["proviso_missed"]) - set(r.get("gt_not_recorded", [])))
        t = time.time()
        try:
            N.ensure_commits(tree, r["true_parent"], r["current"])
            N.git(tree, "checkout", "-q", "-f", r["true_parent"])
            N.git(tree, "clean", "-q", "-fdx")
            if C.get("sync"):
                C["sync"](tree, py)
            before = outcomes(proj, tree, files, py)
            N.put_current(tree, r["true_parent"], r["current"])
            if C.get("sync"):
                C["sync"](tree, py)
            after = outcomes(proj, tree, files, py)
            changed = {k: [before.get(k), after.get(k)] for k in sorted(set(before) | set(after))
                       if before.get(k) != after.get(k)}
            ok_before = sum(1 for v in before.values() if v == "passed")
            row = {"current": r["current"], "true_parent": r["true_parent"], "files": files,
                   "tests_before": len(before), "passed_before": ok_before,
                   "not_passed_before": {k: v for k, v in before.items() if v != "passed"},
                   "changed": changed, "real_miss": bool(changed), "secs": round(time.time() - t)}
        except Exception as e:  # noqa: BLE001
            row = {"current": r["current"], "true_parent": r["true_parent"], "files": files, "error": repr(e)[:400]}
        finally:
            N.git(tree, "checkout", "-q", "-f", r["true_parent"], check=False)
            N.git(tree, "clean", "-q", "-fdx", check=False)
        row["format"] = N.IS.FORMAT
        with open(out, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"[{proj}] {r['current'][:10]} files {len(files)}: "
              + (f"ERROR {row['error'][:150]}" if "error" in row else
                 f"{row['tests_before']} tests, {len(row['not_passed_before'])} not passing before, "
                 f"{len(row['changed'])} outcome changes -> {'REAL MISS' if row['real_miss'] else 'harmless'}"
                 f" ({row['secs']} s)"), flush=True)


def real_changes(r):
    """Outcome changes that a selection could have caught: a test present before and after whose outcome differs, or a
    file that no longer loads. A test the change deletes (before: passed, after: absent) is not one: nothing can run
    it after the change (pylint d69d13a459 removed its unnecessary_default_type_args_py313 case)."""
    return {k: v for k, v in r.get("changed", {}).items() if v[1] is not None and (v[0] is not None
                                                                                  or k.startswith("collect-error:"))}


def summary():
    tot = {"pairs": 0, "real": 0, "harmless": 0, "errors": 0, "removed_tests_only": 0}
    for f in sorted(os.listdir(OUT)):
        if not (f.startswith("verify_") and f.endswith(".jsonl")):
            continue
        rows = {}
        for line in open(os.path.join(OUT, f)):
            r = json.loads(line)
            rows[r["current"]] = r   # the newest verification of each pair (rows are appended)
        rows = list(rows.values())
        real = [r for r in rows if "error" not in r and real_changes(r)]
        removed = [r for r in rows if "error" not in r and r.get("changed") and not real_changes(r)]
        err = [r for r in rows if "error" in r]
        fmts = sorted({str(r.get("format", "?")) for r in rows})
        print(f"{f[7:-6]:10s} (format {'/'.join(fmts)}) pairs {len(rows)}: real misses {len(real)}, harmless {len(rows) - len(real) - len(err)},"
              f" errors {len(err)} (of the harmless: {len(removed)} where only tests the change deletes differ)")
        for r in real:
            print("   REAL", r["current"][:10], list(real_changes(r).items())[:3])
        for r in removed:
            print("   deleted tests only", r["current"][:10], list(r["changed"])[:3])
        tot["pairs"] += len(rows)
        tot["real"] += len(real)
        tot["errors"] += len(err)
        tot["removed_tests_only"] += len(removed)
        tot["harmless"] += len(rows) - len(real) - len(err)
    print("all:", tot)


def pylint_diag():
    from dc_engine import impact as I
    from dc_engine import record as REC
    parent, cur = "ad14b5bf9f2eaaf9b69a0daef09d1d944e1b11cf", "ed5963235706741560b095bd7e5a8865e3be1009"
    tree = os.path.join(N.WORK, "nrbench", "pylint", "repo")
    py = venv_python("pylint")
    N.ensure_commits(tree, parent, cur)
    N.git(tree, "checkout", "-q", "-f", parent)
    N.git(tree, "clean", "-q", "-fdx")
    N.sync_pinned_test_deps(tree, py)
    cov_path = os.path.join(N.WORK, "nrbench", "pylint", "diag_covmap.json")
    env = {**os.environ, "PYTHONPATH": tree, "PYTHONDONTWRITEBYTECODE": "1"}
    REC.record(tree, "pylint", cov_path, py, ["tests"], N.WORKERS, "", ["-p", "no:randomly"], env)
    cov = json.load(open(cov_path))
    fn = ["pylint/pyreverse/diagrams.py", 222]
    tests = {k: v for k, v in cov.items() if not k.startswith("__")}
    print("tests in map:", len(tests), "| tests whose own record reaches the edited function:",
          sum(1 for v in tests.values() if fn in v.get("funcs", [])),
          "| in global set:", fn in cov.get("__global__", {}).get("funcs", []))
    try:
        N.put_current(tree, parent, cur)
        t = time.time()
        sel, why = I.selection(tree, cov, py)
        print("selection took", round(time.time() - t), "s; selected",
              "ALL" if sel is None else f"{len(sel)} tests in {len({s.split('::')[0] for s in sel})} files")
        print(json.dumps({k: str(v)[:500] for k, v in why.items()}, indent=1))
    finally:
        N.git(tree, "checkout", "-q", "-f", parent, check=False)
        N.git(tree, "clean", "-q", "-fdx", check=False)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "verify":
        for p in a[1:]:
            verify(p)
        summary()
    elif a[0] == "pylint-diag":
        pylint_diag()
    elif a[0] == "summary":
        summary()
    else:
        sys.exit(__doc__)
