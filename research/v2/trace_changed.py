"""Root-cause helper: does a test reach the functions a change edits, and when?

Checks out the parent commit in a scratch tree, finds the functions and methods whose source differs between parent
and change (by qualified name, non-test files), then runs the given test files at the parent under a sys.monitoring
tracer and reports, per test, whether any edited function ran
  - during the test itself (set-up, call, tear-down), or
  - only before any test (import of the package or test module, collection).
Optionally with extra environment settings (e.g. SYMPY_USE_CACHE=no) to test a caching hypothesis.

python research/v2/trace_changed.py REPO_DIR PARENT CHANGE TESTFILE [TESTFILE...] [--env K=V] [--pythonpath P]
Prints JSON. Python >= 3.12."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile

PLUGIN = r'''
import json, os, sys
_TOOL = 4
_want = set(json.loads(os.environ["TRACE_WANT"]))   # "relpath::qualname"
_root = os.environ["TRACE_ROOT"]
_cur = ["<before tests>"]
_hits = {}
def _start(code, off):
    f = code.co_filename
    if not isinstance(f, str) or not isinstance(_root, str):
        return None
    if f.startswith(_root):
        key = os.path.relpath(f, _root) + "::" + code.co_qualname
        if key in _want:
            _hits.setdefault(_cur[0], set()).add(key)
    return sys.monitoring.DISABLE if not f.startswith(_root) else None
sys.monitoring.use_tool_id(_TOOL, "trace_changed")
sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_START, _start)
sys.monitoring.set_events(_TOOL, sys.monitoring.events.PY_START)
import pytest
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    _cur[0] = item.nodeid
    yield
    _cur[0] = "<between tests>"
_outcome = {}
def pytest_runtest_logreport(report):
    if report.when == "call" or report.outcome != "passed":
        _outcome[report.nodeid] = report.outcome
def pytest_sessionfinish(session):
    json.dump({"hits": {k: sorted(v) for k, v in _hits.items()}, "outcomes": _outcome},
              open(os.environ["TRACE_OUT"], "w"))
'''


def run(cmd, cwd=None, env=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if p.returncode:
        raise RuntimeError(f"{' '.join(cmd[:4])}: {p.stderr[:400]}")
    return p.stdout


def functions(src: str) -> dict[str, str]:
    """{qualname: source segment} for every function/method in a module (nested ones included)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    out = {}

    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + ch.name
                out[q] = ast.dump(ch)          # formatting and comments ignored
                walk(ch, q + ".<locals>.")
            elif isinstance(ch, ast.ClassDef):
                walk(ch, prefix + ch.name + ".")
            else:
                walk(ch, prefix)
    walk(tree, "")
    return out


def edited_functions(repo, parent, change) -> list[str]:
    names = run(["git", "diff", "--name-only", parent, change], cwd=repo).split()
    want = []
    for f in names:
        if not f.endswith(".py") or "/tests/" in f or f.startswith("tests/") or os.path.basename(f).startswith("test_"):
            continue
        old = subprocess.run(["git", "show", f"{parent}:{f}"], cwd=repo, capture_output=True, text=True).stdout
        new = subprocess.run(["git", "show", f"{change}:{f}"], cwd=repo, capture_output=True, text=True).stdout
        a, b = functions(old), functions(new)
        want += [f"{f}::{q}" for q in a if q in b and a[q] != b[q]]     # edited, as recorded at the parent
    return want


def main():
    args = sys.argv[1:]
    env_extra, pyp = {}, []
    while "--env" in args:
        i = args.index("--env")
        k, v = args[i + 1].split("=", 1)
        env_extra[k] = v
        del args[i:i + 2]
    while "--pythonpath" in args:
        i = args.index("--pythonpath")
        pyp.append(args[i + 1])
        del args[i:i + 2]
    repo, parent, change, *tests = args
    want = edited_functions(repo, parent, change)
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        run(["git", "worktree", "add", "-q", "--detach", tree, parent], cwd=repo)
        try:
            open(os.path.join(tmp, "trace_plugin.py"), "w").write(PLUGIN)
            out = os.path.join(tmp, "out.json")
            env = {**os.environ, **env_extra, "TRACE_WANT": json.dumps(want), "TRACE_ROOT": tree + os.sep,
                   "TRACE_OUT": out, "PYTHONPATH": os.pathsep.join([tmp, tree, *pyp, os.environ.get("PYTHONPATH", "")]),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "trace_plugin", "-p", "no:cacheprovider",
                                "-o", "addopts=", *tests], cwd=tree, capture_output=True, text=True, env=env)
            res = json.load(open(out)) if os.path.exists(out) else {"hits": {}, "outcomes": {}, "pytest": (p.stdout + p.stderr)[-1500:]}
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", tree], cwd=repo, capture_output=True)
    hits = res["hits"]
    tests_hit = {t: v for t, v in hits.items() if not t.startswith("<")}
    print(json.dumps({"edited": want, "env": env_extra, "tests_run": len(res["outcomes"]),
                      "outcomes": {k: sum(1 for v in res["outcomes"].values() if v == k)
                                   for k in set(res["outcomes"].values())},
                      "before_tests": hits.get("<before tests>", []), "between_tests": hits.get("<between tests>", []),
                      "tests_running_edited": len(tests_hit), "examples": dict(list(tests_hit.items())[:5]),
                      **({"pytest_tail": res["pytest"]} if "pytest" in res else {})}, indent=1))


if __name__ == "__main__":
    main()
