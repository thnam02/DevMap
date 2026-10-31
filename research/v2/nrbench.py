"""Proviso on NameRTS's own benchmark, scored with NameRTS's own metric (ISSTA 2026, github.com/ZJU-CTAG/NameRTS).

For each target commit pair of a project in NameRTS's dataset (the 50 pairs of its published RQ1 results):
  1. check out true_parent, record Proviso's dependency map there (every test file in a fresh interpreter);
  2. put the working tree at `current` (HEAD stays at true_parent, so `git diff HEAD` is the change);
  3. Proviso selects tests; selected test files are compared with NameRTS's ground truth (`tests_to_run`, the test
     files that execute a modified code element) and with NameRTS's published selection for the same pair.
Metrics as in NameRTS's paper: safe = every ground-truth test file selected; TestR = 1 - selected files / total test
files (`total_tests` of the ground truth). Also: share of test time selected, from the recorded per-test durations.

Usage (Linux/WSL; one venv per project with its test dependencies, as NameRTS's build_env.md):
  python research/v2/nrbench.py PROJECT [N] [--python /path/to/venv/bin/python]
  python research/v2/nrbench.py report                         # table over every project with results
Results: research/v2/results/nrbench/<project>.jsonl (one row per pair; resumable).
Environment: NAMERTS_HOME (a clone of NameRTS; default $PROVISO_WORK/NameRTS), PROVISO_WORK (default
~/proviso-work/v2; trees go to $PROVISO_WORK/nrbench/<project>), PROVISO_WORKERS (default cores - 1),
PROVISO_EXTRA_PATH (extra import paths for the tests, os.pathsep-separated)."""
from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as IS  # noqa: E402
from dc_engine import record as REC  # noqa: E402

WORK = os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2"))
NR = os.environ.get("NAMERTS_HOME", os.path.join(WORK, "NameRTS"))
OUT = os.path.join(HERE, "results", "nrbench")
WORKERS = int(os.environ.get("PROVISO_WORKERS", max(1, (os.cpu_count() or 2) - 1)))

def sync_pinned_test_deps(tree, python, req="requirements_test_min.txt", names=("astroid",)):
    """Install the exact versions a commit pins for its own tests (pylint pins astroid per commit in
    requirements_test_min.txt; a newer astroid makes older commits fail to import). Returns what was installed."""
    path = os.path.join(tree, req)
    if not os.path.isfile(path):
        return {}
    pins = {}
    for line in open(path):
        m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*==\s*([^\s#;]+)", line)
        if m and m.group(1).lower() in names:
            pins[m.group(1).lower()] = m.group(2)
    for name, ver in pins.items():
        r = subprocess.run([python, "-m", "pip", "install", "-q", "--no-deps", f"{name}=={ver}"], capture_output=True,
                           text=True)
        if r.returncode:
            raise RuntimeError(f"could not install {name}=={ver}: {(r.stdout + r.stderr).strip()[-200:]}")
    return pins


# NameRTS's ten projects: code (its result-file suffix), ground-truth file, package directory, test targets.
# pip: extra test dependencies beyond the project's own (installed into the project's venv by the user, see README).
PROJECTS = {
    "loguru": dict(url="https://github.com/Delgan/loguru.git", code="LOG", gt="gt_loguru.json", pkg="loguru",
                   targets=["tests"]),
    "pylint": dict(url="https://github.com/pylint-dev/pylint.git", code="PYL", gt="gt_pylint.json", pkg="pylint",
                   targets=["tests"], sync=sync_pinned_test_deps),
    "sphinx": dict(url="https://github.com/sphinx-doc/sphinx.git", code="SPH", gt="gt_sphinx.json", pkg="sphinx",
                   targets=["tests"]),
    "pvlib": dict(url="https://github.com/pvlib/pvlib-python.git", code="PVL", gt="gt_pvlib.json", pkg="pvlib",
                  targets=["tests", "pvlib/tests"]),
    "xarray": dict(url="https://github.com/pydata/xarray.git", code="XA", gt="gt_xarray.json", pkg="xarray",
                   targets=["xarray/tests"]),
    "seaborn": dict(url="https://github.com/mwaskom/seaborn.git", code="SE", gt="gt_seaborn.json", pkg="seaborn",
                    targets=["tests"]),
    "dask": dict(url="https://github.com/dask/dask.git", code="DAS", gt="gt_dask.json", pkg="dask",
                 targets=["dask"]),
    "sympy": dict(url="https://github.com/sympy/sympy.git", code="SY", gt="gt_sympy.json", pkg="sympy",
                  targets=["sympy"]),
}


def git(cwd, *a, check=True):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check).stdout


def pairs(proj):
    """NameRTS's 50 evaluated pairs (its published RQ1 selection), with ground truth and its selection."""
    C = PROJECTS[proj]
    gt = {(g["true_parent"], g["current"]): g for g in json.load(open(os.path.join(NR, "ground truth", C["gt"])))}
    pub = json.load(open(os.path.join(NR, "results", "rq1", "namerts", f"NameBDP_RTSTest_{C['code']}.json")))
    out = []
    for r in pub:
        g = gt.get((r["true_parent"], r["current"]))
        if g is None:
            continue
        out.append({"true_parent": r["true_parent"], "current": r["current"], "gt": sorted(set(g["tests_to_run"])),
                    "total_tests": g["total_tests"], "namerts": sorted(set(r["tests_to_run"]))})
    return out


def put_current(tree, parent, current):
    """Working tree = `current`, index and HEAD = `parent`; files deleted by the change are removed."""
    git(tree, "checkout", "-q", "-f", parent)
    git(tree, "clean", "-q", "-fdx", "-e", ".dc-engine")
    for line in git(tree, "diff", "--name-status", "--no-renames", parent, current).splitlines():
        st, f = line.split("\t", 1)
        p = os.path.join(tree, f)
        if st.startswith("D"):
            if os.path.exists(p):
                os.remove(p)
        else:
            blob = subprocess.run(["git", "show", f"{current}:{f}"], cwd=tree, capture_output=True)
            if blob.returncode == 0:
                os.makedirs(os.path.dirname(p) or tree, exist_ok=True)
                open(p, "wb").write(blob.stdout)


def file_of(nodeid):
    return nodeid.split("::", 1)[0]


def ensure_commits(tree, *shas):
    """Pairs can name commits outside the default branch (merged PR heads): fetch them by hash."""
    for c in shas:
        if subprocess.run(["git", "cat-file", "-e", f"{c}^{{commit}}"], cwd=tree, capture_output=True).returncode:
            subprocess.run(["git", "fetch", "-q", "origin", c], cwd=tree, capture_output=True)


def run_pair(proj, tree, p, python):
    C = PROJECTS[proj]
    ensure_commits(tree, p["true_parent"], p["current"])
    git(tree, "checkout", "-q", "-f", p["true_parent"])
    git(tree, "clean", "-q", "-fdx")
    extra = [x for x in os.environ.get("PROVISO_EXTRA_PATH", "").split(os.pathsep) if x]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([tree, *extra]), "PYTHONDONTWRITEBYTECODE": "1",
           "PATH": os.path.dirname(python) + os.pathsep + os.environ.get("PATH", "")}
    cov_path = os.path.join(WORK, "nrbench", proj, "covmap.json")
    t0 = time.time()
    synced = C["sync"](tree, python) if C.get("sync") else {}   # the commit's own pinned test dependencies
    targets = [t for t in C["targets"] if os.path.exists(os.path.join(tree, t))]  # test layout moves over history
    REC.record(tree, C["pkg"], cov_path, python, targets, WORKERS, "", ["-p", "no:randomly"], env)
    rec_s = time.time() - t0
    cov = json.load(open(cov_path))
    tests = [n for n in cov if not n.startswith("__")]
    if not tests:
        col = subprocess.run([python, "-m", "pytest", "--collect-only", "-qq", *targets], cwd=tree, env=env,
                             capture_output=True, text=True)
        tail = " | ".join((col.stdout + col.stderr).strip().splitlines()[-4:])
        raise RuntimeError(f"the dependency map recorded no tests; collection says: {tail}")
    files_all = {file_of(n) for n in tests}
    put_current(tree, p["true_parent"], p["current"])
    t0 = time.time()
    sel, why = I.selection(tree, cov, python)
    sel_s = time.time() - t0
    sel_tests = set(tests) if sel is None else set(sel)
    sel_files = {file_of(n) for n in sel_tests}
    # a test file the change adds or edits runs anyway (Proviso's rule); it may be new, so not in the map
    status = git(tree, "status", "--porcelain", "-uall")
    edited_tests = {l[3:] for l in status.splitlines() if I._is_test_path(l[3:]) and l[3:].endswith(".py")}
    sel_files |= edited_tests
    t_all = sum(cov[n].get("time", 0) for n in tests) or 1e-9
    gt = set(p["gt"])
    # ground-truth files that recorded no test here (e.g. a collection error in our environment) cannot be selected
    # from the map; they are reported, and safety is also given without them. The full suite runs every file.
    unrunnable = sorted(gt - files_all)
    missed = [] if sel is None else sorted(gt - sel_files)
    n_files = p["total_tests"] if sel is None else len(sel_files)
    return {"current": p["current"], "true_parent": p["true_parent"], "total_tests": p["total_tests"],
            "recorded_test_files": len(files_all), "recorded_tests": len(tests),
            "gt": len(gt), "proviso_files": n_files, "proviso_full": sel is None, "reason": why.get("reason"),
            "proviso_missed": missed, "proviso_safe": not missed,
            # for analysing misses: edited functions, and import-time values that the snapshot found changed
            "changed_functions": len(why.get("changed_functions", [])),
            "import_state_changed": why.get("import_state_changed", [])[:20],
            "proviso_safe_runnable": not (set(missed) - set(unrunnable)),
            "proviso_time_share": round(sum(cov[n].get("time", 0) for n in sel_tests & set(tests)) / t_all, 4),
            "namerts_files": len(p["namerts"]), "namerts_missed": sorted(gt - set(p["namerts"])),
            "namerts_safe": gt <= set(p["namerts"]), "gt_not_recorded": unrunnable,
            "record_s": round(rec_s), "selection_s": round(sel_s, 2), "pinned_deps": synced}


def main_project(proj, n, python):
    C = PROJECTS[proj]
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{proj}.jsonl")
    # rows of an older snapshot format are recomputed (the file keeps them; report() uses the newest per pair)
    py_ver = subprocess.run([python, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], capture_output=True,
                            text=True).stdout.strip()
    # rows from another interpreter version are recomputed too (results must come from one environment)
    done = {r["current"] for r in _rows(out) if r.get("format") == IS.FORMAT and "error" not in r and r.get("py") == py_ver}
    base = os.path.join(WORK, "nrbench", proj)
    tree = os.path.join(base, "repo")
    if not os.path.isdir(os.path.join(tree, ".git")):
        os.makedirs(base, exist_ok=True)
        subprocess.run(["git", "clone", "-q", C["url"], tree], check=True)
    todo = [p for p in pairs(proj) if p["current"] not in done][: max(0, n - len(done))]
    n_done = len(done)
    for i, p in enumerate(todo):
        t = time.time()
        try:
            row = {**run_pair(proj, tree, p, python), "format": IS.FORMAT, "py": py_ver}
        except Exception as e:  # noqa: BLE001
            row = {"current": p["current"], "true_parent": p["true_parent"], "error": repr(e)[:400], "format": IS.FORMAT, "py": py_ver}
        finally:
            shutil.rmtree(os.path.join(tree, ".dc-engine"), ignore_errors=True)
        with open(out, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"[{proj} {n_done + i + 1}/{n}] {p['current'][:10]} "
              + (f"ERROR {row['error'][:120]}" if "error" in row else
                 f"gt {row['gt']}  proviso {row['proviso_files']} files safe={row['proviso_safe']}  "
                 f"namerts {row['namerts_files']} safe={row['namerts_safe']}  ({round(time.time() - t)} s)"),
              flush=True)


def _rows(path):
    """Rows of a results file, the newest per pair of the current snapshot format (older formats ignored)."""
    if not os.path.exists(path):
        return []
    out = {}
    for line in open(path):
        r = json.loads(line)
        if r.get("format") == IS.FORMAT:
            out[r["current"]] = r
    return list(out.values())


def report():
    lines = ["| Project | Pairs | Proviso safe | Proviso safe (runnable here) | NameRTS safe | Proviso TestR | "
             "NameRTS TestR | Proviso time share | Proviso full suite |", "|---|---|---|---|---|---|---|---|---|"]
    allr = []
    for proj in PROJECTS:
        rows = _rows(os.path.join(OUT, f"{proj}.jsonl"))
        ok = [r for r in rows if "error" not in r]
        if not ok:
            continue
        allr += ok
        tr = lambda k: statistics.mean(1 - r[k] / r["total_tests"] for r in ok)
        lines.append(f"| {proj} | {len(ok)} (+{len(rows) - len(ok)} errors) | "
                     f"{sum(r['proviso_safe'] for r in ok)}/{len(ok)} | {sum(r['proviso_safe_runnable'] for r in ok)}/{len(ok)} | "
                     f"{sum(r['namerts_safe'] for r in ok)}/{len(ok)} | "
                     f"{100 * tr('proviso_files'):.1f}% | {100 * tr('namerts_files'):.1f}% | "
                     f"{100 * statistics.mean(r['proviso_time_share'] for r in ok):.1f}% | "
                     f"{sum(r['proviso_full'] for r in ok)} |")
    if allr:
        lines.append(f"| **all** | {len(allr)} | {sum(r['proviso_safe'] for r in allr)}/{len(allr)} | "
                     f"{sum(r['proviso_safe_runnable'] for r in allr)}/{len(allr)} | "
                     f"{sum(r['namerts_safe'] for r in allr)}/{len(allr)} | | | | {sum(r['proviso_full'] for r in allr)} |")
    print("\n".join(lines))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "report":
        report()
    else:
        py = a[a.index("--python") + 1] if "--python" in a else sys.executable
        a = [x for x in a if x != "--python" and x != py]
        main_project(a[0], int(a[1]) if len(a) > 1 else 50, py)
