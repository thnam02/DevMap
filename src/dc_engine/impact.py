"""Change impact for Proviso: affected-test interception and ripple replay.

Assets (built once per base commit, in .dc-engine/):
  covmap.json         {test node id: {"funcs": [[file, first line], ...], "time": s, "ok": bool}} from running the
                      suite at the base commit with the recorder (dc_engine.covplugin, via dc_engine.record)
  base_failures.json  test node ids (or test modules) that already fail at the base commit
  probes.json         [[source dialect, run dialect, input], ...]: inputs the test suite already contains, also run in
                      every component that inherits from the input's own (replay.py below)
  ripple_base.json    behaviour of the base commit on those probes
  replay.py           the replay runner (repository-specific behaviour function)

Interception (PreToolUse on Bash): a broad test run (whole suite or test directory, pytest or unittest) is rewritten
to `python -m dc_engine.impact run`, which runs only the tests whose base coverage reaches the code the agent changed
(plus tests the agent added or edited), compares the result with the base failures and prints a short summary.
Anything it cannot place falls back to the full suite.

Ripple replay (Stop): the current tree is run on the probes; outputs that changed in a component other than the one
the input came from (e.g. a MySQL input run as StarRocks) are reported once.
"""

from __future__ import annotations

import ast
import collections
import contextlib
import copy
import types
import functools
import glob
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any

STATE_DIR = ".dc-engine"


# Ablation switches (evaluation only; unset = the normal behaviour). PROVISO_OFF is a comma-separated list of parts to
# turn off: snapshot (no import-time comparison: a statement edit selects the tests that ran any code of its file),
# docs (docstring/format-only function edits count as edits), hints (names in annotations count as reads), callers
# (special methods seed the caller step), bindings (import bindings are read anywhere), newfiles (a new or deleted
# source file runs the full suite), conftest (edits to shared test code select nothing beyond themselves, as in v1),
# byname (v2.1: changed functions found from changed line numbers only), config (v2.1: pytest configuration files
# are not looked at), data (v2.2: changed non-Python files are not looked at);
# recorder parts (subprocess, mp, fixtures, setup) are read by covplugin at recording time. PROVISO_MODE=traditional:
# a change to code that runs at import selects every test (all tests run it), and docstring edits count: the classic
# "every test that executes changed code" rule.
def _off(part: str) -> bool:
    return part in {x.strip() for x in os.environ.get("PROVISO_OFF", "").split(",") if x.strip()}


def _traditional() -> bool:
    return os.environ.get("PROVISO_MODE", "") == "traditional"
RIPPLE_MAX_ITEMS = 5

# --------------------------------------------------------------------------- change -> code units


def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True).stdout


def _asset(root: str, name: str) -> Any:
    try:
        with open(os.path.join(root, STATE_DIR, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _units(path: str, src: str) -> tuple[list[tuple[str, int, int, bool]], list[tuple[int, int, str]]]:
    """(name, start, end, is_function) for every function and class/module-level statement; class spans with
    their qualified names."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], []
    units, classes = [], []

    def walk(body, prefix):
        for node in body:
            start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
            end = node.end_lineno or node.lineno
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                units.append((prefix + node.name, start, end, True))
            elif isinstance(node, ast.ClassDef):
                classes.append((node.lineno, end, prefix + node.name))
                walk(node.body, prefix + node.name + ".")
            else:
                # imports and other statements run at import time; blocks (if/try/with) may define functions
                units.append((prefix + f"<stmt@{node.lineno}>", start, end, False))
                for field in ("body", "orelse", "finalbody", "handlers"):
                    sub = getattr(node, field, None)
                    if isinstance(sub, list) and sub and isinstance(sub[0], ast.AST):
                        if field == "handlers":
                            for hnd in sub:
                                walk(hnd.body, prefix)
                        else:
                            walk(sub, prefix)
    walk(tree.body, "")
    return units, classes


def _changed_by_name(path: str, old_src: str, new_src: str) -> set[tuple[str, int]]:
    """(v2.1) Base functions whose code differs in the working tree, matched by qualified name. Line numbers alone
    misplace some edits: git places an inserted block that starts with a blank line after the blank line that ends
    a method, so the lines next to the insertion point are the blank line and the NEXT method's `def`; a deleted
    `def` line turns its body into the end of the method above; a second definition of a method appended to a class
    replaces the first. Comparing each function's code by name credits the function that actually changed. A name
    defined a different number of times (a redefinition) credits every base definition of it."""
    old_units, _ = _units(path, old_src)
    new_units, _ = _units(path, new_src)
    if not old_units or not new_units:
        return set()
    old_lines, new_lines = old_src.splitlines(), new_src.splitlines()

    def by_name(units, lines):
        out: dict[str, list[tuple[int, str]]] = {}
        for name, start, end, is_func in units:
            if is_func:
                text = "\n".join(l.rstrip() for l in lines[start - 1:end])
                out.setdefault(name, []).append((start, text))
        return out
    old, new = by_name(old_units, old_lines), by_name(new_units, new_lines)
    hit: set[tuple[str, int]] = set()
    for name, defs in old.items():
        if name not in new:
            continue   # deleted or renamed: the line-based mapping credits it (its old lines changed)
        if len(defs) != len(new[name]):
            hit |= {(path, start) for start, _ in defs}
            continue
        hit |= {(path, start) for (start, text), (_, ntext) in zip(defs, new[name]) if text != ntext}
    return hit


_PYTEST_CONFIGS = {"pytest.ini": None, ".pytest.ini": None, "pytest.toml": None, ".pytest.toml": None,
                   "tox.ini": ("ini", "pytest"), "setup.cfg": ("ini", "tool:pytest"),
                   "pyproject.toml": ("toml", "tool.pytest")}


def _pytest_config_change(root: str) -> str | None:
    """(v2.1) A pytest configuration file added, deleted, renamed or edited where pytest reads it (its options apply
    to every test: an `addopts = --import-mode=prepend` changes how every test imports), as its path, or None.
    pytest.ini, .pytest.ini, pytest.toml and .pytest.toml count whole; tox.ini, setup.cfg and pyproject.toml only
    their pytest section ([pytest], [tool:pytest], [tool.pytest] including ini_options). Any directory counts:
    pytest takes the first configuration file above the tests it runs."""
    specs = [f":(glob)**/{n}" for n in _PYTEST_CONFIGS]
    prefix = _git(root, "rev-parse", "--show-prefix").strip()   # git prints paths from the repository's top
    entries: list[tuple[str, list[str]]] = []   # (status letter, [path(s) from the top])
    # against the base commit (committed edits count too: v2.2), renames detected; then untracked files
    d = subprocess.run(["git", "diff", "--name-status", "-z", "-M", _BASE, "--", *specs], cwd=root,
                       capture_output=True, text=True)
    if d.returncode != 0:
        return None
    fields = d.stdout.split("\0")
    i = 0
    while i < len(fields):
        code = fields[i]
        i += 1
        if not code:
            continue
        n = 2 if code[0] in "RC" else 1
        entries.append((code[0], fields[i:i + n][::-1]))   # a rename/copy lists old then new: report the new path
        i += n
    st = subprocess.run(["git", "status", "--porcelain", "-z", "-uall", "--", *specs], cwd=root,
                        capture_output=True, text=True)
    entries += [("?", [e[3:]]) for e in st.stdout.split("\0") if e.startswith("??")]
    for code, paths in entries:
        for top_rel in paths:
            name = os.path.basename(top_rel)
            if name not in _PYTEST_CONFIGS:
                continue
            rel = top_rel[len(prefix):] if prefix and top_rel.startswith(prefix) else top_rel
            kind = _PYTEST_CONFIGS[name]
            if kind is None or code in "RC":
                return rel
            old = "" if code in "?A" else _git(root, "show", f"{_BASE}:{top_rel}")
            path = os.path.join(root, rel)
            try:
                new = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
            except (OSError, UnicodeDecodeError):
                return rel
            if _config_section(old, *kind) != _config_section(new, *kind):
                return rel
    return None


def _config_section(text: str, fmt: str, section: str):
    """The pytest section of a configuration file's text (None when absent; the raw text when it does not parse)."""
    if not text.strip():
        return None
    try:
        if fmt == "toml":
            import tomllib
            node = tomllib.loads(text)
            for part in section.split("."):
                node = node.get(part) if isinstance(node, dict) else None
            return node
        import configparser
        cp = configparser.RawConfigParser(strict=False, interpolation=None)
        cp.read_string(text)
        return dict(cp.items(section)) if cp.has_section(section) else None
    except Exception:  # noqa: BLE001  (an unparsable file: any edit counts)
        return text


def _changed_old_lines(diff: str) -> dict[str, set[int]]:
    out: dict[str, set[int]] = {}
    cur = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            cur = line[6:] if line.startswith("--- a/") else None
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+", line)
        if m and cur:
            a, b = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            out.setdefault(cur, set()).update(range(a, a + b) if b else {a, a + 1})
    return out


def tests_of(covmap: dict) -> dict:
    """The per-test entries of a coverage map (keys like "__global__" and "__fixtures__" are not tests)."""
    return {n: v for n, v in covmap.items() if not n.startswith("__")}


def map_files(covmap: dict) -> set[str]:
    """Every file with a recorded function: tests' own records, fixture records and the global record."""
    out = {f for v in tests_of(covmap).values() for f, _ in v.get("funcs", [])}
    out |= {f for r in (covmap.get("__fixtures__") or {}).values() for f, _ in r.get("funcs", [])}
    out |= {f for f, _ in (covmap.get("__global__") or {}).get("funcs", [])}
    return out


def test_funcs(covmap: dict, node: str) -> set[tuple[str, int]]:
    """Functions a test depends on: its own call, plus the fixture/setup/import/session records it is linked to (v2
    maps); for analysis code, where building the union per test is affordable."""
    v = covmap.get(node) or {}
    fx = covmap.get("__fixtures__") or {}
    out = {tuple(x) for x in v.get("funcs", [])}
    for k in v.get("fx", []):
        out |= {tuple(x) for x in fx.get(k, {}).get("funcs", [])}
    return out


class _DepView:
    """Per-test dependencies of a coverage map, without building per-test unions (fixture records are shared by many
    tests and can be large): a test reaches a set S if its own functions or one of its linked records reach S."""

    def __init__(self, covmap: dict):
        self.tests = tests_of(covmap)
        self.fx = {k: ({tuple(x) for x in r.get("funcs", [])}, set(r.get("classes", [])), bool(r.get("always")))
                   for k, r in (covmap.get("__fixtures__") or {}).items()}
        self._own: dict = {}
        self._memo: dict = {}

    def own(self, node):
        got = self._own.get(node)
        if got is None:
            got = self._own[node] = {tuple(x) for x in self.tests[node].get("funcs", [])}
        return got

    def reaches(self, node, s: set, tag) -> bool:
        if not s:
            return False
        if self.own(node) & s:
            return True
        for k in self.tests[node].get("fx", ()):
            m = (tag, k)
            if m not in self._memo:
                self._memo[m] = bool(k in self.fx and self.fx[k][0] & s)
            if self._memo[m]:
                return True
        return False

    def classes(self, node) -> set:
        out = set(self.tests[node].get("classes") or [])
        for k in self.tests[node].get("fx", ()):
            if k in self.fx:
                out |= self.fx[k][1]
        return out

    def always(self, node) -> bool:
        v = self.tests[node]
        return bool(v.get("always")) or any(self.fx.get(k, (None, None, False))[2] for k in v.get("fx", ()))


_TEST_SUPPORT_DIRS = {"testing", "testutils", "test_utils", "_testing"}


def _is_test_support(p: str) -> bool:
    """Test-support code shipped inside the package (pylint/testutils, sympy/testing): helpers for tests, not package
    state. Left out of the import-time snapshot (pylint's builds a whole linter at import, too large to fingerprint);
    statement-level edits to it select the tests that ran its code instead."""
    return any(part in _TEST_SUPPORT_DIRS for part in p.split("/")[:-1])


def _snapshot_files(covmap: dict) -> list[str]:
    return sorted(f for f in map_files(covmap) if not _is_test_path(f) and not _is_test_support(f))


def packages(covmap: dict) -> list[str]:
    return sorted({f.split("/", 1)[0] for f in map_files(covmap)})


IMPORT_STATE_MAX_NAMES = 200
EARLY_FULL_SHARE = 0.9  # run everything without a snapshot when edited functions reach this share of test time


def _head_cached(root: str, kind: str, files: list[str], compute):
    """compute(root, files), cached in STATE_DIR per base commit (both analyses below read only HEAD's sources, so
    their result is fixed for an agent session; without the cache every selection re-parses the whole package)."""
    head = _git(root, "rev-parse", _BASE).strip()
    key = hashlib.sha1(json.dumps([head, sorted(files)]).encode()).hexdigest()
    path = os.path.join(root, STATE_DIR, f"{kind}.json")
    try:
        got = json.load(open(path))
        if got.get("key") == key:
            return got["value"]
    except (OSError, ValueError, KeyError):
        pass
    value = compute(root, files)
    try:
        os.makedirs(os.path.join(root, STATE_DIR), exist_ok=True)
        json.dump({"key": key, "value": value}, open(path, "w"))
    except OSError:
        pass
    return value


def _name_index(root: str, files: list[str]) -> dict[tuple[str, int], set[str]]:
    rows = _head_cached(root, "names_index3" + ("-hints" if _off("hints") else ""), files, lambda r, fs: [[f, ln, sorted(ns)] for (f, ln), ns in
                                                                   _name_index_uncached(r, fs).items()])
    return {(f, ln): set(ns) for f, ln, ns in rows}


def _annotations(node) -> list:
    """The annotation expressions a node carries (function parameters and return, annotated assignments inside
    functions; class-level annotations are left alone: dataclasses and the like read them at import)."""
    out = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        a = node.args
        for arg in a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]:
            if arg.annotation is not None:
                out.append(arg.annotation)
        if getattr(node, "returns", None) is not None:
            out.append(node.returns)
        for sub in ast.walk(node):
            if isinstance(sub, ast.AnnAssign) and sub is not node:
                out.append(sub.annotation)
    return out


def _name_index_uncached(root: str, files: list[str]) -> dict[tuple[str, int], set[str]]:
    """(file, first line) of every function and lambda at HEAD -> identifiers it mentions (names, attribute names,
    string constants that look like identifiers). Calls are additionally recorded as 'call:NAME', and each function's
    own name as 'def:NAME', so callers of a function can be found."""
    idx: dict[tuple[str, int], set[str]] = {}
    for f in files:
        try:
            tree = ast.parse(_git(root, "show", f"{_BASE}:{f}"))
        except SyntaxError:
            continue
        # names inside type annotations are not read when the code runs (`x: Optional[int]`, `-> Union[A, B]`):
        # modernising them (Optional[X] -> X | None, dropping a typing import) changes no behaviour
        in_annotation = set() if _off("hints") else \
            {id(sub) for node in ast.walk(tree) for ann in _annotations(node) for sub in ast.walk(ann)}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
                names = idx.setdefault((f, start), set())
                if not isinstance(node, ast.Lambda):
                    names.add(node.name)  # a test that ran the base `m` on a subclass now runs the subclass's `m`
                    names.add("def:" + node.name)
                for sub in ast.walk(node):
                    if id(sub) in in_annotation:
                        continue
                    if isinstance(sub, ast.Call):
                        fn = sub.func
                        nm = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                        if nm:
                            names.add("call:" + nm)
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
                    elif isinstance(sub, ast.Attribute):
                        names.add(sub.attr)
                    elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value.isidentifier():
                        names.add(sub.value)
        # module- and class-level assignments: a name bound at import from an expression that mentions a value
        # (e.g. is_table_value_type = operator.attrgetter("_is_table_value")) reads that value; code using the name
        # reads it too. Recorded as an entry with 'assign:TARGET' and the identifiers the expression mentions.
        def assignments(body):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    assignments(node.body)
                    continue
                if isinstance(node, (ast.If, ast.Try, ast.With)):  # e.g. `if TYPE_CHECKING: ... else: X = ...`
                    assignments(getattr(node, "body", []) + getattr(node, "orelse", []) + getattr(node, "finalbody", [])
                                + [s for h in getattr(node, "handlers", []) for s in h.body])
                    continue
                if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or node.value is None:
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                tnames = {t.id for t in targets if isinstance(t, ast.Name)} | \
                    {e.id for t in targets if isinstance(t, (ast.Tuple, ast.List)) for e in t.elts if isinstance(e, ast.Name)}
                if not tnames:
                    continue
                mentioned = set()
                for sub in ast.walk(node.value):
                    if isinstance(sub, ast.Name):
                        mentioned.add(sub.id)
                    elif isinstance(sub, ast.Attribute):
                        mentioned.add(sub.attr)
                    elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value.isidentifier():
                        mentioned.add(sub.value)
                if mentioned:
                    idx.setdefault((f, node.lineno), set()).update({"assign:" + t for t in tnames} | mentioned)
        assignments(tree.body)
    return idx


_FILE_NAMES: dict[str, dict] = {}  # store path -> {test file path: [stamp, names]}
_DIRTY: set[str] = set()


def _file_names(path: str) -> set[str]:
    """_file_names_uncached, cached in the repository's STATE_DIR per file (keyed by size and mtime: the agent may
    edit tests)."""
    root = os.path.dirname(os.path.abspath(path))
    while root != os.path.dirname(root) and not os.path.exists(os.path.join(root, ".git")):
        root = os.path.dirname(root)
    store = os.path.join(root, STATE_DIR, "file_names.json")
    cache = _FILE_NAMES.get(store)
    if cache is None:
        try:
            cache = json.load(open(store))
        except (OSError, ValueError):
            cache = {}
        _FILE_NAMES[store] = cache
    try:
        st = os.stat(path)
        stamp = f"{st.st_size}:{st.st_mtime_ns}"
    except OSError:
        return set()
    got = cache.get(path)
    if got and got[0] == stamp:
        return set(got[1])
    names = _file_names_uncached(path)
    cache[path] = [stamp, sorted(names)]
    _DIRTY.add(store)
    return names


def _flush_file_names() -> None:
    for store in list(_DIRTY):
        try:
            os.makedirs(os.path.dirname(store), exist_ok=True)
            json.dump(_FILE_NAMES[store], open(store, "w"))
        except OSError:
            pass
        _DIRTY.discard(store)


def _file_names_uncached(path: str) -> set[str]:
    """Every identifier, attribute name and identifier-like string in a file (empty if it does not parse)."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError):
        return set()
    out: set[str] = set()
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Name):
            out.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            out.add(sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value.isidentifier():
            out.add(sub.value)
    return out


def _new_top_level_defs(root: str, files: set[str]) -> set[str]:
    """Names bound by top-level `def` or `import` statements in the working tree that the base did not bind."""
    def bound(src: str) -> tuple[set[str], set[str]]:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return set(), set()
        defs, other = set(), set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                defs.update((a.asname or a.name).split(".")[0] for a in node.names)
            else:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                        other.add(sub.id)
        return defs, other
    out: set[str] = set()
    for f in files:
        old_defs, old_other = bound(_git(root, "show", f"{_BASE}:{f}"))
        try:
            new_defs, _ = bound(open(os.path.join(root, f), encoding="utf-8").read())
        except OSError:
            continue
        out |= new_defs - old_defs - old_other
    return out


def _import_bindings(root: str, files: set[str]) -> dict[str, set[str]]:
    """{file: names bound by top-level import statements, in the base or the working tree}. Such a binding in module
    A (`import warnings`, `from .tools import deprecated`) is read by A's own code; other modules have their own
    bindings, so when it changes or disappears only A's readers count (pvlib: a removed `import warnings` had selected
    every function anywhere that mentions `warnings`)."""
    def bound(src: str) -> set[str]:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return set()
        out = set()
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                out.update((a.asname or a.name).split(".")[0] for a in node.names)
        return out
    res: dict[str, set[str]] = {}
    for f in files:
        names = bound(_git(root, "show", f"{_BASE}:{f}"))
        try:
            names |= bound(open(os.path.join(root, f), encoding="utf-8").read())
        except OSError:
            pass
        res[f] = names
    return res


def _key_module_file(key: str, prefix: str, known: set[str]) -> str | None:
    """'pkg.mod:name' -> 'pkg/mod.py' or 'pkg/mod/__init__.py', whichever is a known file."""
    mod = key.split(":", 1)[0].replace(".", "/")
    for f in (f"{prefix}{mod}.py", f"{prefix}{mod}/__init__.py"):
        if f in known:
            return f
    return None


def _computed_lookup_patterns(root: str, files: list[str]) -> set[tuple[str, str]]:
    return {tuple(x) for x in _head_cached(root, "lookup_patterns", files,
                                           lambda r, fs: sorted(_computed_lookup_patterns_uncached(r, fs)))}


def _computed_lookup_patterns_uncached(root: str, files: list[str]) -> set[tuple[str, str]]:
    """(prefix, suffix) of every attribute lookup by computed name (getattr/hasattr/setattr whose name is built
    from constant parts, e.g. getattr(self, f"{key}_sql") -> ("", "_sql")). A new attribute whose name fits one can
    be reached without being named, so the classes that gain it are treated like edited classes."""
    pats: set[tuple[str, str]] = set()
    for f in files:
        try:
            tree = ast.parse(_git(root, "show", f"{_BASE}:{f}"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("getattr", "hasattr", "setattr")
                    and len(node.args) >= 2):
                continue
            arg = node.args[1]
            parts: list = []
            if isinstance(arg, ast.JoinedStr):
                parts = [v.value if isinstance(v, ast.Constant) else None for v in arg.values]
            elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                stack, parts = [arg], []
                while stack:
                    n = stack.pop()
                    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                        stack += [n.right, n.left]
                    else:
                        parts.append(n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None)
            else:
                continue
            if not parts:
                continue
            pre = parts[0] if isinstance(parts[0], str) else ""
            suf = parts[-1] if isinstance(parts[-1], str) and len(parts) > 1 else ""
            if pre or suf:
                pats.add((pre, suf))
    return pats


def _key_class(key: str, prefix: str = "") -> str | None:
    """'pkg.mod:Cls.Inner.attr' -> 'pkg/mod.py:Cls.Inner' (the covmap's class naming); prefix: the source directory
    of a src/lib layout ('lib/'), since the covmap names files relative to the repository root."""
    mod, qual = key.split(":", 1)
    if "." not in qual:
        return None
    return f"{prefix}{mod.replace('.', '/')}.py:{qual.rsplit('.', 1)[0]}"


def _layout_prefix(files) -> str:
    """'lib/' or 'src/' when the package files live under such a directory (a src layout), else ''."""
    from .importstate import layout_prefix
    return layout_prefix(files)


def _module_of(path: str, prefix: str = "") -> str | None:
    """'pkg/sub/mod.py' -> 'pkg.sub.mod' ('pkg/sub/__init__.py' -> 'pkg.sub'), the layout prefix ('src/') removed."""
    if not path.endswith(".py"):
        return None
    if prefix and path.startswith(prefix):
        path = path[len(prefix):]
    mod = path[:-3].replace("/", ".")
    return mod[:-9] if mod.endswith(".__init__") else mod


def _import_state_effect(root: str, covmap: dict, python: str, changed_files: set[str], gone: list[str] = ()
                         ) -> tuple[set[str] | None, set[str], dict]:
    """Keys ('module:Name' or 'module:Class.attr') whose import-time values the working tree changes (empty: no
    import-time effect; None: unknown), and classes to treat as edited (they gained an attribute that is looked up
    by computed name, or their bases changed)."""
    from . import importstate
    files = _snapshot_files(covmap)
    base = importstate.base_snapshot(root, files, python, os.path.join(root, STATE_DIR, "importstate_base.json"),
                                     rev=_BASE)
    cur = importstate.snapshot(root, files, python) if base is not None else None
    if base is None or cur is None:
        return None, set(), {"reason": "could not compare import-time state"}
    d = importstate.diff(base, cur, _new_top_level_defs(root, changed_files))
    # values of a module the base did not have (a new source file): new, so no existing code reads them
    base_mods = {k.split(":", 1)[0] for k in base["state"]}
    d["changed"] = [k for k in d["changed"] if k.split(":", 1)[0] in base_mods]
    d["added_class_attrs"] = [k for k in d["added_class_attrs"] if k.split(":", 1)[0] in base_mods]
    # a module the change deletes cannot import and its values disappear; that is the deletion itself (its users are
    # selected by the caller), unlike an existing module that stops importing
    prefix0 = _layout_prefix(files)
    gone_mods = {m for m in (_module_of(g, prefix0) for g in gone) if m}
    if gone_mods:
        inside = lambda m: any(m == g or m.startswith(g + ".") for g in gone_mods)
        d["errors"] = [m for m in d["errors"] if not inside(m)]
        d["changed"] = [k for k in d["changed"] if not inside(k.split(":", 1)[0])]
    if d["errors"]:
        return None, set(), {"reason": f"module {d['errors'][0]} no longer imports"}
    names = set(d["changed"])
    pats = _computed_lookup_patterns(root, files) if d["added_class_attrs"] else set()
    reachable = [k for k in d["added_class_attrs"]
                 if any(k.rsplit(".", 1)[-1].startswith(p) and k.rsplit(".", 1)[-1].endswith(q) for p, q in pats)]
    # a new base class or metaclass changes behaviour without changing any attribute of the class itself
    rebased = [k for k in d["changed"] if k.endswith((".__mro__", ".__class__"))]
    prefix = _layout_prefix(files)
    gained = {c for c in (_key_class(k, prefix) for k in reachable) if c}
    gained |= {c for c in (_key_class(k.rsplit(".", 1)[0] + ".x", prefix) for k in rebased) if c}
    gained |= {c.replace("/__init__.py:", ".py:") for c in gained}
    return names, gained, {"import_state_changed": d["changed"][:200], "import_state_n": len(d["changed"])}


# (v2.2) the commit the change is measured from: the one the coverage map was recorded at (its "__base__" entry),
# not whatever HEAD is now. An agent that commits its work (or a tool that does it for it) moves HEAD; measured from
# HEAD, the committed edits would vanish and nothing would be selected. Maps without the entry (older ones) use HEAD.
_BASE = "HEAD"


def map_base(root: str, covmap: dict) -> tuple[str | None, str]:
    """(revision to compare with, why): the map's recorded commit when it is HEAD or an ancestor of HEAD; None when
    the map was recorded on a commit outside the current history (a rebase, another branch): its line numbers and
    records no longer describe this code."""
    commit = ((covmap.get("__base__") or {}).get("commit") or "").strip()
    if not commit:
        return "HEAD", "the map records no commit: compared with HEAD"
    if subprocess.run(["git", "-C", root, "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True).returncode:
        return None, f"the dependency map was recorded at commit {commit[:10]}, which this repository does not have"
    if subprocess.run(["git", "-C", root, "merge-base", "--is-ancestor", commit, "HEAD"],
                      capture_output=True).returncode:
        # the same code under another commit (re-created, amended without changes, rebased onto itself): HEAD
        if _git(root, "rev-parse", f"{commit}^{{tree}}").strip() == _git(root, "rev-parse", "HEAD^{tree}").strip():
            return "HEAD", "the map's commit has the same code as HEAD"
        return None, f"the dependency map was recorded at commit {commit[:10]}, which is not in the current history"
    return commit, ""


@contextlib.contextmanager
def _measured_from(base: str):
    """Within the block, every read of the original code (git show / diff / archive) uses base."""
    global _BASE
    prev, _BASE = _BASE, base
    try:
        yield
    finally:
        _BASE = prev


def selection(root: str, covmap: dict, python: str | None = None) -> tuple[list[str] | None, dict]:
    """Test node ids to run for the change since the map's commit, or None for the full suite (see _selection)."""
    base, why = map_base(root, covmap)
    if base is None:
        return None, {"reason": why}
    with _measured_from(base):
        return _selection(root, covmap, python)


def _changed_paths(root: str, paths: list[str]) -> list[tuple[str, str]]:
    """(status letter, path) of every file that differs from the base commit under paths: committed or not, staged
    or not (git diff against the base, renames as a deletion and an addition), and untracked files ('?')."""
    out = []
    for line in _git(root, "diff", "--name-status", "--no-renames", _BASE, "--", *paths).splitlines():
        code, _, path = line.partition("\t")
        if path:
            out.append((code[:1], path))
    seen = {p for _, p in out}
    for line in _git(root, "status", "--porcelain", "-uall", "--", *paths).splitlines():
        if line.startswith("??") and line[3:] not in seen:
            out.append(("?", line[3:]))
    return out


# (v2.2) files in the package that are not Python (JSON, YAML, templates, data): code reads them while it runs, and
# nothing records which test reads which file, so a change to one runs the full suite. Byte-code and editor files
# do not count.
_NOT_DATA = (".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".pyi", ".swp", ".orig", ".rej", ".bak", ".tmp", ".log", "~")


def _data_file_change(changed: list[tuple[str, str]], test_files: set[str]) -> str | None:
    """The first changed file that code or tests may read while they run: not Python, not a stub, not byte-code or
    an editor/patch leftover, not a hidden file, and not itself a test (data files that are tests run themselves).
    Test data (fixtures, golden files, sphinx test roots) counts: tests read it."""
    for _, path in changed:
        base = os.path.basename(path)
        if path.endswith(".py") or path in test_files or path.endswith(_NOT_DATA) or "/__pycache__/" in f"/{path}" \
                or base.startswith(".") or ".egg-info" in path:
            continue
        return path
    return None


def _selection(root: str, covmap: dict, python: str | None = None) -> tuple[list[str] | None, dict]:
    """Test node ids to run for the current change, or None for the full suite. Second value: why.

    function edits    tests whose base coverage reaches the function
    class statements  tests that use the class (directly or through a subclass instance)
    module statements and edits to functions that also run at import time: the import-time state of the package is
                      compared with the base commit (importstate); if it is unchanged nothing more is needed, otherwise
                      tests reaching code that reads a changed name are added
    """
    python = python or sys.executable
    pk = packages(covmap)
    dep = _DepView(covmap)
    if not pk:
        return None, {"reason": "empty coverage map"}
    diff = _git(root, "diff", "-U0", _BASE, "--", *pk)
    extra_dirs = ["tests"] if os.path.isdir(os.path.join(root, "tests")) else []
    if os.path.isfile(os.path.join(root, "conftest.py")) or "conftest.py" in _git(root, "ls-files", "conftest.py"):
        extra_dirs.append("conftest.py")  # a root conftest's fixtures are shared by every test
    changed = _changed_paths(root, [*pk, *extra_dirs])
    # porcelain-like lines ("XY path") for the code below: "?? path" untracked, "A  path" added since the base, ...
    status = "\n".join(("?? " if c == "?" else f"{c}  ") + p for c, p in changed)
    new_src = [p for c, p in changed if c in "?A" and not _is_test_path(p) and p.endswith(".py")]
    gone_src = [p for c, p in changed if c == "D" and not _is_test_path(p) and p.endswith(".py")]
    test_files = {n.split("::", 1)[0] for n in tests_of(covmap)}
    data = None if (_off("data") or _traditional()) else _data_file_change(changed, test_files)
    if data:
        return None, {"reason": f"a file the code may read changed ({data}): not tracked per test"}
    # a new source file changes existing code only through what importing it does (a registration, a patched
    # value), which the import-time comparison below sees; its own definitions are new, so nothing existing reads them
    if (new_src or gone_src) and (_off("newfiles") or _traditional() or _off("snapshot")):
        return None, {"reason": f"new or deleted source file {(new_src or gone_src)[0]}"}
    cfg = None if _off("config") else _pytest_config_change(root)
    if cfg:
        return None, {"reason": f"pytest's configuration changed ({cfg})"}
    funcs: set[tuple[str, int]] = set()
    module_level: set[str] = set()
    class_names: set[str] = set()
    support_edits: set[str] = set()   # test-support files with statement-level edits
    for f, lines in _changed_old_lines(diff).items():
        if _is_test_path(f):
            continue  # edited tests run themselves (below)
        src = _git(root, "show", f"{_BASE}:{f}")
        units, cls = _units(f, src)
        for ln in lines:
            inner = [u for u in units if u[1] <= ln <= u[2]]
            best = min(inner, key=lambda u: u[2] - u[1]) if inner else None
            if best is not None and best[3]:
                funcs.add((f, best[1]))
                continue
            if _is_test_support(f):
                # test-support code is not in the snapshot: every test that ran code of this file
                funcs |= {tuple(x) for v in dep.tests.values() for x in v.get("funcs", []) if x[0] == f} | \
                    {k for r in dep.fx.values() for k in r[0] if k[0] == f}
                support_edits.add(f)   # and the tests that name a changed value of it (below)
                continue
            # statements in a class body or at module level run at import: their effect is read off the
            # import-time state below
            module_level.add(f)
        if not _off("byname") and os.path.isfile(os.path.join(root, f)):
            try:
                cur = open(os.path.join(root, f), encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                cur = None
            if cur is not None:
                funcs |= _changed_by_name(f, src, cur)
    # an edit that leaves a function's code as it was (docstrings, comments, formatting) changes no behaviour; only its
    # __doc__ differs, so tests that read docstrings still run it (below)
    doc_only, format_only = (set(), set()) if (_off("docs") or _traditional()) else _docstring_only_edits(root, funcs)
    funcs -= doc_only | format_only
    # the edited functions alone already reach nearly all of the test time: the selection can only grow from here
    # (import-time readers are added, never removed), so run the full suite and skip the import-time snapshot
    if funcs and EARLY_FULL_SHARE < 1:
        times = {n: (v.get("time") or 0) for n, v in dep.tests.items()}
        total = sum(times.values())
        reached = sum(t for n, t in times.items() if dep.reaches(n, funcs, "funcs"))
        if total > 0 and reached / total >= EARLY_FULL_SHARE:
            return None, {"reason": f"your edited functions run in {100 * reached / total:.0f}% of the test time",
                          "functions": len(funcs)}
    glob_funcs = {tuple(x) for x in (covmap.get("__global__") or {}).get("funcs", [])}
    if funcs:
        # functions that run while the package is imported, as recorded by the base snapshot itself (v2): an edit to
        # one can change import-time state however the test runner happened to import the package
        # (an import-only pass: no fingerprints, so plain function edits do not pay for a full snapshot)
        from . import importstate
        imp = importstate.import_funcs_of(root, _snapshot_files(covmap), python,
                                          os.path.join(root, STATE_DIR, "import_funcs.json"), rev=_BASE)
        glob_funcs |= {tuple(x) for x in (imp or [])}
    hit_global = sorted(funcs & glob_funcs)
    why: dict[str, Any] = {"functions": len(funcs), "files": sorted(module_level),
                           "changed_functions": sorted([f, ln] for f, ln in funcs)}
    read_names: set[str] = set()
    if (hit_global or module_level) and _traditional():
        # every test imports the package, so every test executes code that runs at import
        return None, {**why, "reason": "code that runs at import changed (traditional mode)"}
    if (hit_global or module_level) and _off("snapshot"):
        # without the import-time comparison: the tests that ran any code of the files edited at module level
        files_hit = module_level | {f for f, _ in hit_global}
        funcs |= {tuple(x) for v in dep.tests.values() for x in v.get("funcs", []) if x[0] in files_hit} | \
            {k for r in dep.fx.values() for k in r[0] if k[0] in files_hit}
        hit_global, module_level = [], set()
        why["snapshot_off_files"] = sorted(files_hit)
    if new_src:
        why["new_source_files"] = sorted(new_src)
    if hit_global or module_level or new_src:
        names, gained, info = _import_state_effect(root, covmap, python,
                                                   {f for f in _changed_old_lines(diff) if not _is_test_path(f)}
                                                   | set(new_src), gone=gone_src)
        why.update(info)
        if names is None:
            return None, why
        if len({k.rsplit(".", 1)[-1].rsplit(":", 1)[-1] for k in names}) > IMPORT_STATE_MAX_NAMES:
            return None, {**why, "reason": f"your change alters {len(names)} values computed at import time"}
        read_names = set(names)
        class_names |= gained
        # a deleted module: code that still reaches it by name (a lazy `from .x import y`, `pkg.x.f()`) and tests
        # naming it; its own functions were edited away (selected above) and importers that break fail the snapshot
        for g in gone_src:
            mod = _module_of(g, _layout_prefix(map_files(covmap)))
            if mod and "." in mod:
                read_names.add(f"{mod.rsplit('.', 1)[0]}:{mod.rsplit('.', 1)[1]}")
        if gone_src:
            why["deleted_source_files"] = sorted(gone_src)
    # a changed value is read by code that names it; a class attribute only through that class or a subclass,
    # so its readers count only in tests that use the class
    readers_any: set[tuple[str, int]] = set()
    readers_cls: dict[str, set[tuple[str, int]]] = {}
    test_attrs_any: set[str] = set()  # the test code itself may read a changed value
    test_attrs_cls: dict[str, set[str]] = {}
    test_file_names: dict[str, set[str]] = {}
    if read_names:
        idx = _name_index(root, sorted(map_files(covmap)))
        by_name: dict[str, set[tuple[str, int]]] = {}
        for fl, ns in idx.items():
            for n in ns:
                by_name.setdefault(n, set()).add(fl)
        def_name = {fl: n[4:] for fl, ns in idx.items() for n in ns if n.startswith("def:")}

        def readers_of(attr: str, only_file: str | None = None) -> set[tuple[str, int]]:
            # code that names the value, plus the callers of that code: a reader's result is often computed once
            # and cached (e.g. a dispatch table built from TRANSFORMS on first use), after which only its caller
            # runs, so the coverage map credits the reader to whichever test happened to run first
            direct = set(by_name.get(attr, set()))
            if only_file is not None:  # an import binding: read only by its own module's code
                direct = {fl for fl in direct if fl[0] == only_file}
            # names bound at import from the value (aliases), and their aliases in turn: their users read it too
            # (for an import binding, only within its own module: other modules have their own bindings, whose
            # changes the snapshot reports under their own keys)
            here = (lambda fl: fl[0] == only_file) if only_file is not None else (lambda fl: True)
            seen_alias, frontier = set(), {attr}
            for _ in range(3):
                new = {n[7:] for name in frontier for fl in by_name.get(name, ()) if here(fl) for n in idx.get(fl, ())
                       if n.startswith("assign:")} - seen_alias - {attr}
                if not new:
                    break
                seen_alias |= new
                for t in new:
                    direct |= {fl for fl in by_name.get(t, set()) if here(fl)}
                frontier = new
            # (not for special methods: `__init__` is called through its class, and matching every
            # `super().__init__()` call by that name would select nearly everything; coverage already credits a base
            # __init__ to each test that runs it)
            calls = {"call:" + def_name[fl] for fl in direct if fl in def_name
                     and (_off("callers") or not (def_name[fl].startswith("__") and def_name[fl].endswith("__")))}
            callers = {fl for c in calls for fl in by_name.get(c, set())}
            return direct | callers

        prefix = _layout_prefix(map_files(covmap))
        changed_src = {f for f in _changed_old_lines(diff) if not _is_test_path(f)}
        bindings = _import_bindings(root, changed_src)
        for key in read_names:
            cls = _key_class(key, prefix)
            attr = key.rsplit(":", 1)[1].rsplit(".", 1)[-1]
            if cls is None:
                kf = _key_module_file(key, prefix, set(bindings))
                if kf is not None and attr in bindings[kf] and not _off("bindings"):
                    # an import binding: only its own module reads it (and the callers of that code)
                    readers_any |= readers_of(attr, only_file=kf)
                    continue
                fl = readers_of(attr)
                readers_any |= fl
                test_attrs_any.add(attr)
            else:
                fl = readers_of(attr)
                for c in {cls, cls.replace("/__init__.py:", ".py:")}:
                    readers_cls.setdefault(c, set()).update(fl)
                    test_attrs_cls.setdefault(c, set()).add(attr)
    sel = []
    any_change = bool(funcs or module_level)
    for node in dep.tests:
        if any_change and dep.always(node):
            sel.append(node)
            continue
        used = dep.classes(node)
        if class_names and class_names & used:
            sel.append(node)
            continue
        if dep.reaches(node, funcs, "funcs") or dep.reaches(node, readers_any, "readers"):
            sel.append(node)
            continue
        if readers_cls and any(dep.reaches(node, readers_cls[c], ("cls", c)) for c in used & readers_cls.keys()):
            sel.append(node)
            continue
        if test_attrs_any or test_attrs_cls:
            tfile = node.split("::", 1)[0]
            if tfile not in test_file_names:
                test_file_names[tfile] = _file_names(os.path.join(root, tfile))
            names_here = test_file_names[tfile]
            if names_here & test_attrs_any or any(names_here & test_attrs_cls[c] for c in used & test_attrs_cls.keys()):
                sel.append(node)
    # tests the agent added or edited always run
    touched_tests = [l[3:].strip() for l in status.splitlines() if _is_test_path(l[3:].strip())]
    # test modules, and data files that are tests themselves (a test id in the map starts with the file)
    test_files = {n.split("::", 1)[0] for n in tests_of(covmap)}
    extra = sorted({t for t in touched_tests if t.endswith(".py") or t in test_files})
    why["agent_tests"] = extra
    # shared test code: fixtures in conftest.py, other conftest code, helper modules in test directories
    shared, shared_why = (set(), []) if _off("conftest") else \
        _shared_test_code_tests(root, covmap, touched_tests, test_files)
    # test-support modules in the package: a changed constant or class is read by tests that run none of the
    # module's functions (`from pkg.testing import TIMEOUT`), so tests whose file names a changed value are added
    naming = _Naming(root)
    if new_src:
        # tests that find modules by walking the package (pkgutil, importlib) may pick the new one up
        finders = {n for n in tests_of(covmap) if naming.mentions(
            n.split("::", 1)[0], {"walk_packages", "iter_modules", "import_module", "__import__", "pkgutil"})}
        shared |= finders
        shared_why.append(f"new source file(s) {', '.join(sorted(new_src)[:3])}: {len(finders)} test(s) that "
                          f"discover modules")
    if doc_only:
        doc_readers = {n for n in tests_of(covmap) if dep.reaches(n, doc_only, "funcs")
                       and naming.mentions(n.split("::", 1)[0], {"__doc__", "doctest", "getdoc"})}
        shared |= doc_readers
        shared_why.append(f"{len(doc_only)} function(s) with docstring/format-only edits: "
                          f"{len(doc_readers)} test(s) that read docstrings")
    for f in sorted(support_edits):
        names, unnamed = _changed_top_names(_git(root, "show", f"{_BASE}:{f}"), _read(root, f))
        stem = f.rsplit("/", 1)[-1][:-3]
        if names is None or unnamed:   # unparsable, or a changed statement that binds no name: the module itself
            names = (names or set()) | {stem if stem != "__init__" else f.rsplit("/", 2)[-2]}
        if names:
            hit = {n for n in tests_of(covmap) if naming.mentions(n.split("::", 1)[0], names)}
            shared |= hit
            shared_why.append(f"{f}: tests naming {', '.join(sorted(names)[:8])}")
    if shared_why:
        why["shared_test_code"] = shared_why
    _flush_file_names()
    return sorted(set(sel) | shared) + extra, why


def _strip_docstrings(node):
    """A copy of a definition without the docstrings of it and of the definitions inside it."""
    node = copy.deepcopy(node)
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and \
                isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return node


def _func_code(src: str) -> dict[tuple[str, int], tuple[int, str, str]]:
    """{(qualified function name, n-th definition of that name): (first line incl. decorators, code without
    docstrings, code with them)}; comments and formatting are not part of the syntax tree, so they never count. (v2.1)
    A name defined more than once in a scope (property getter and setter, overloads, if/else branches, a method
    defined again) keeps every definition."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    out: dict[tuple[str, int], tuple[int, str, str]] = {}
    seen: collections.Counter = collections.Counter()

    def walk(body, prefix):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = min([d.lineno for d in node.decorator_list] + [node.lineno])
                seen[prefix + node.name] += 1
                out[(prefix + node.name, seen[prefix + node.name])] = (start, ast.dump(_strip_docstrings(node)),
                                                                       ast.dump(node))
            elif isinstance(node, ast.ClassDef):
                walk(node.body, prefix + node.name + ".")
            else:
                for field in ("body", "orelse", "finalbody"):
                    sub = getattr(node, field, None)
                    if isinstance(sub, list):
                        walk(sub, prefix)
                for hnd in getattr(node, "handlers", None) or []:
                    walk(hnd.body, prefix)
    walk(tree.body, "")
    return out


def _docstring_only_edits(root: str, funcs: set[tuple[str, int]]) -> tuple[set, set]:
    """The edited functions whose code is unchanged apart from docstrings, comments and formatting: (those whose
    docstrings changed, those where only comments or formatting did)."""
    doc, fmt = set(), set()
    for f in {f for f, _ in funcs}:
        old, new = _func_code(_git(root, "show", f"{_BASE}:{f}")), _func_code(_read(root, f))
        by_start = {v[0]: (key, v) for key, v in old.items()}
        n_old = collections.Counter(q for q, _ in old)
        n_new = collections.Counter(q for q, _ in new)
        for g, ln in funcs:
            if g == f and ln in by_start:
                key, (_, code, full) = by_start[ln]
                # a name defined a different number of times (a definition added or removed: the later one wins) is
                # never a docstring/format-only edit; otherwise each definition is compared with its counterpart
                if n_old[key[0]] == n_new[key[0]] and key in new and new[key][1] == code:
                    (fmt if new[key][2] == full else doc).add((g, ln))
    return doc, fmt


def _read(root: str, path: str) -> str:
    try:
        return open(os.path.join(root, path), encoding="utf-8").read()
    except OSError:
        return ""


class _Naming:
    """Whether a test file names any of some identifiers (whole words), with file contents cached."""

    def __init__(self, root: str):
        self.root, self.src = root, {}

    def mentions(self, test_file: str, names: set[str]) -> bool:
        if test_file not in self.src:
            self.src[test_file] = _read(self.root, test_file)
        return any(re.search(rf"\b{re.escape(n)}\b", self.src[test_file]) for n in names)


def _bound_names(node) -> set[str]:
    """Names a top-level statement binds (definitions, assignment targets, imports, also inside if/try blocks)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    out: set[str] = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
            out.add(x.id)
        elif isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(x.name)
        elif isinstance(x, (ast.Import, ast.ImportFrom)):
            out.update((a.asname or a.name).split(".")[0] for a in x.names)
    return out


def _refs(node) -> set[str]:
    """Names a definition uses, parameters included (a fixture requests another fixture by parameter name)."""
    return {x.id for x in ast.walk(node) if isinstance(x, ast.Name)} | \
        {x.attr for x in ast.walk(node) if isinstance(x, ast.Attribute)} | \
        {x.arg for x in ast.walk(node) if isinstance(x, ast.arg)}


def _change_closure(tree, changed: set[str]) -> set[str]:
    """`changed` plus the module's own top-level definitions that refer to a changed name, transitively (a helper
    calling a changed helper, a fixture calling either)."""
    refs: dict[str, set[str]] = {}
    for node in tree.body:
        r = _refs(node)
        for b in _bound_names(node):
            refs.setdefault(b, set()).update(r)
    out, grew = set(changed), True
    while grew:
        grew = False
        for b, r in refs.items():
            if b not in out and r & out:
                out.add(b)
                grew = True
    return out


def _changed_top_names(old_src: str, new_src: str) -> tuple[set[str] | None, bool]:
    """(top-level names whose binding statements changed or disappeared, with the module's own definitions that refer
    to them; whether a changed statement binds no name at all, e.g. a registration call). (None, True) if either
    version does not parse."""
    def index(src):
        tree = ast.parse(src)
        by_name: dict[str, list[str]] = {}
        unnamed: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue   # a docstring
            names = _bound_names(node)
            for n in names:
                by_name.setdefault(n, []).append(ast.dump(node))
            if not names:
                unnamed.append(ast.dump(node))
        return tree, by_name, unnamed
    try:
        (_, o, ou), (nt, n, nu) = index(old_src), index(new_src)
    except (SyntaxError, ValueError):
        return None, True
    changed = {k for k, v in o.items() if n.get(k) != v}
    # an import binding is only a means: the definitions using it count (closure), not every test naming `os`
    only_imports = {k for k, v in {**o, **n}.items()
                    if all(d.startswith(("Import(", "ImportFrom(")) for d in o.get(k, []) + n.get(k, []))}
    return _change_closure(nt, changed) - only_imports, sorted(ou) != sorted(nu)


def _flat_statements(body) -> tuple[list, list]:
    """The statements of a module with if/try/with blocks opened up (a fixture defined under `if sys.version_info`
    is compared like any other), and the blocks' own conditions as (description, statements inside the block)."""
    stmts, guards = [], []
    for node in body:
        if isinstance(node, (ast.If, ast.While)):
            g = type(node).__name__ + ":" + ast.dump(node.test)
        elif isinstance(node, ast.Try) or type(node).__name__ == "TryStar":
            g = "Try:" + ",".join(ast.dump(h.type) if h.type else "*" for h in node.handlers)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            g = "With:" + ",".join(ast.dump(it) for it in node.items)
        else:
            stmts.append(node)
            continue
        inner, inner_guards = [], []
        for field in ("body", "orelse", "finalbody"):
            sub = getattr(node, field, None)
            if isinstance(sub, list):
                s2, g2 = _flat_statements(sub)
                inner += s2
                inner_guards += g2
        for hnd in getattr(node, "handlers", None) or []:
            s2, g2 = _flat_statements(hnd.body)
            inner += s2
            inner_guards += g2
        stmts += inner
        guards.append((g, inner + [x for gg in inner_guards for x in gg[1]]))
        guards += inner_guards
    return stmts, guards


_PURE_CALLS = ("pytest.", "os.environ.get", "os.getenv", "os.path.", "Version", "version.parse", "parse_version",
               "packaging.version.", "Path", "pathlib.Path", "importlib.util.find_spec", "str", "int", "float", "bool",
               "tuple", "list", "dict", "set", "frozenset", "len", "sorted", "shutil.which", "sys.platform.startswith")


def _inert(expr) -> bool:
    """An expression without side effects worth tracking: literals, names, attribute and item access, operators, and
    calls of a few pure constructors (pytest.mark.skipif(...), pytest.param(...), Version(...), os.environ.get(...))."""
    for sub in ast.walk(expr):
        if isinstance(sub, ast.Call):
            try:
                name = ast.unparse(sub.func)
            except Exception:  # noqa: BLE001
                return False
            if not any(name == p or (p.endswith(".") and name.startswith(p)) for p in _PURE_CALLS):
                return False
        elif isinstance(sub, (ast.Lambda, ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)):
            return False
    return True


def _new_definition(node, old_names: set[str], old_imported: set[str] = frozenset()) -> bool:
    """A statement that only defines something new: binds at least one name the base did not bind (none of them
    special to pytest) from inert expressions (`requires_x = pytest.mark.skipif(not HAS_X, reason=...)`)."""
    if isinstance(node, ast.Pass) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
        return True
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        # an added import changes nothing existing, unless it rebinds a name that was something else
        return not _bound_names(node) & (old_names - old_imported)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names = _bound_names(node)
        return bool(names) and not names & old_names and not any(n.startswith(("pytest_", "collect_ignore"))
                                                                  for n in names)
    if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
        names = _bound_names(node)
        return bool(names) and not names & old_names and \
            not any(n.startswith(("pytest_", "collect_ignore")) for n in names) and _inert(node.value) and \
            all(isinstance(t, (ast.Name, ast.Tuple, ast.List)) for t in (node.targets if isinstance(node, ast.Assign)
                                                                        else [node.target]))
    return False


def _test_code_changes(root: str, path: str) -> tuple[set[str], set[str], bool, set[str]]:
    """What an edit to shared test code (a conftest.py or a helper module) changes, by comparing its top-level
    definitions in the base and the working tree (blocks such as `if sys.version_info ...:` opened up): (changed
    fixtures, changed other functions/classes, whether other module-level code or a block condition changed, names
    whose import was removed). New definitions and added imports change nothing existing (tests using them were edited
    and run anyway: loguru added two helpers to its conftest); a removed import changes the definitions that use it."""
    def parse(src: str):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return None
        stmts, guards = _flat_statements(tree.body)
        defs: dict[str, tuple[str, bool]] = {}
        # a block is identified by its condition and what it guards (pvlib has several `try: ... except KeyError:`)
        # (definitions inside count by name, not body: an edited fixture under `if sys.version_info` is compared as
        # a fixture, below, and leaves its block unchanged)
        def ident(x):
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return "def:" + x.name
            return ast.dump(x)
        other: list = [(g + "|" + "|".join(ident(x) for x in inner), inner) for g, inner in guards]
        imports: dict[str, set[str]] = {}
        for node in stmts:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                fixture = any("fixture" in ast.unparse(d) for d in getattr(node, "decorator_list", []))
                name = node.name
                for d in getattr(node, "decorator_list", []):
                    if isinstance(d, ast.Call):
                        for kw in d.keywords:
                            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                                name = kw.value.value
                hook = name.startswith("pytest_")  # hooks act on every test
                dump = ast.dump(_strip_docstrings(node))
                defs[name] = (dump, fixture and not hook)
                if hook:
                    other.append((dump, [node]))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports[ast.dump(node)] = {(a.asname or a.name).split(".")[0] for a in node.names}
            elif isinstance(node, ast.Pass):
                continue
            elif not (isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)):
                other.append((ast.dump(node), [node]))   # module-level statements (docstrings aside)
        names = {n for node in stmts for n in _bound_names(node)}
        return defs, other, imports, names
    old_src = _git(root, "show", f"{_BASE}:{path}")
    new_src = _read(root, path)
    old, new = parse(old_src) if old_src else None, parse(new_src) if new_src else None
    if old is None or new is None:   # a new, deleted or unparsable file: assume it affects everything below it
        return set(), set(), True, set()
    (od, oo, oi, onames), (nd, no, ni, _) = old, new
    fixtures = {n for n, (dump, fx) in od.items() if fx and nd.get(n, (None,))[0] != dump}
    helpers = {n for n, (dump, fx) in od.items() if not fx and nd.get(n, (None,))[0] != dump}
    # module-level code: a removed or changed statement (or block condition) counts; an added one only if it does more
    # than define something new (pvlib adds `requires_ecmwf_credentials = pytest.mark.skipif(...)` blocks)
    old_dumps = collections.Counter(d for d, _ in oo)
    new_dumps = collections.Counter(d for d, _ in no)
    removed_other = old_dumps - new_dumps
    surplus = new_dumps - old_dumps
    added_other = []
    for d, inner in no:   # only the surplus copies of a statement are new
        if surplus[d] > 0:
            surplus[d] -= 1
            added_other.append((d, inner))
    imported = set().union(*oi.values()) if oi else set()
    module_level = bool(removed_other) or any(not all(_new_definition(x, onames, imported) for x in inner)
                                              for _, inner in added_other)
    still = set().union(*ni.values()) if ni else set()
    removed = {n for d in set(oi) - set(ni) for n in oi[d]} - still
    return fixtures, helpers, module_level, removed


def _shared_test_code_tests(root: str, covmap: dict, touched: list[str], test_files: set[str]) -> tuple[set, list]:
    """Tests reached by edits to shared test code (a conftest.py, or a helper module in a test directory that is not a
    test module itself). A changed fixture: the tests that used it (fixture records are keyed
    "<conftest dir>::<name>@..."). A changed helper function or class: tests whose test file names it, and users of
    fixtures in the same file that name it. Other module-level changes (settings, hooks): every test below the
    directory. New definitions change nothing."""
    nodes = list(tests_of(covmap))
    out: set[str] = set()
    why: list[str] = []
    file_src: dict[str, str] = {}

    def mentions(test_file: str, names: set[str]) -> bool:
        if test_file not in file_src:
            try:
                file_src[test_file] = open(os.path.join(root, test_file), encoding="utf-8").read()
            except OSError:
                file_src[test_file] = ""
        return any(re.search(rf"\b{re.escape(n)}\b", file_src[test_file]) for n in names)

    for t in touched:
        if not t.endswith(".py"):
            continue
        base = t.rsplit("/", 1)[-1]
        if base != "conftest.py" and (t in test_files or base.startswith("test_") or base.endswith("_test.py")):
            continue   # a test module: runs itself
        d = t.rsplit("/", 1)[0] if "/" in t else ""
        below = [n for n in nodes if not d or n.startswith(d + "/")]
        fixtures, helpers, module_level, removed = _test_code_changes(root, t)
        if module_level:
            out.update(below)
            why.append(f"{t}: every test below {d or 'the root'}")
            continue
        if helpers or fixtures or removed:
            # definitions of this file that use a changed one or a removed import, transitively, are changed in effect
            # (a fixture calling a helper that calls the edited helper)
            try:
                stmts, _ = _flat_statements(ast.parse(_read(root, t)).body)
            except (SyntaxError, ValueError):
                out.update(below)
                continue
            is_fx = {node.name: any("fixture" in ast.unparse(x) for x in node.decorator_list) for node in stmts
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            seeds = fixtures | helpers | removed
            for name in _change_closure(types.SimpleNamespace(body=stmts), seeds) - seeds:
                (fixtures if is_fx.get(name) else helpers).add(name)
        if fixtures and base == "conftest.py":
            prefixes = tuple(f"{d}::{x}@" for x in fixtures)
            users = {n for n in below if any(k.startswith(prefixes) for k in covmap[n].get("fx", []))}
            # a map recorded before every used fixture was kept has no keys for fixtures that ran no package code:
            # then the tests whose file names the fixture
            unknown = {x for x in fixtures
                       if not any(k.startswith(f"{d}::{x}@") for n in below for k in covmap[n].get("fx", []))}
            if unknown:
                users |= {n for n in below if mentions(n.split("::", 1)[0], unknown)}
            out.update(users)
            why.append(f"{t}: tests using fixture(s) {', '.join(sorted(fixtures))}")
        if helpers:
            out.update(n for n in below if mentions(n.split("::", 1)[0], helpers))
            why.append(f"{t}: tests naming {', '.join(sorted(helpers))}")
    return out, why


# --------------------------------------------------------------------------- interception

BROAD_TARGETS = {"", "tests", "tests/", "./tests", "./tests/", "tests/dialects", "tests/dialects/", "."}
_SEG_SPLIT = re.compile(r"(&&|\|\||;|\n)")


@functools.lru_cache(maxsize=None)
def _is_test_path(p: str) -> bool:
    """Test code, wherever it lives (tests/ at the top or inside the package, test_*.py files)."""
    p = p.replace(os.sep, "/")
    base = p.rsplit("/", 1)[-1]
    return p.startswith("tests/") or "/tests/" in p or base.startswith("test_") or base == "conftest.py"


def _broad_targets(seg: str) -> list[str] | None:
    """Targets of a broad test run (the suite, directories or whole test files), [] for no explicit target; None if
    the segment is not a broad test run (explicit test ids, a -k/-m filter, or not a test command)."""
    s = seg.strip()
    if re.search(r"\bmake\s+(unit|test)\b", s):
        return []
    try:
        toks = shlex.split(s)
    except ValueError:
        return None
    if not toks:
        return None

    def dir_like(t: str) -> bool:
        # directories and whole test files; explicit test ids (file::test) are the agent's own choice
        return "::" not in t and not t.startswith(("2>", ">", "|")) and t != "2>&1"

    if "pytest" in " ".join(toks[:4]):
        i = next(i for i, t in enumerate(toks) if "pytest" in t)
        rest = toks[i + 1:]
        targets, skip = [], False
        for t in rest:
            if skip:
                skip = False
                continue
            if t in ("-k", "--deselect", "-m"):
                return None  # filtered runs are already narrow
            if t in ("-p", "-c", "--ignore", "-n", "--tb", "--maxfail", "-o", "--junitxml", "-W", "--rootdir",
                     "--durations", "--timeout"):
                skip = True
                continue
            if t.startswith("-") or t.startswith(("2>", ">", "|")) or t == "2>&1":
                continue
            targets.append(t)
        return targets if all(dir_like(t) for t in targets) else None
    if "unittest" in toks:
        i = toks.index("unittest")
        rest = [t for t in toks[i + 1:] if not t.startswith("-")]
        return [] if not rest or rest[0] == "discover" else None
    if toks[0] in ("bin/test", "./bin/test"):  # sympy's runner: paths are directories or files
        rest = [t for t in toks[1:] if not t.startswith("-")]
        return rest if rest and all(dir_like(t) and "/" in t for t in rest) else None
    return None


def _maxfail(seg: str) -> int | None:
    """N if the test command stops after N failures (-x / --exitfirst: 1, --maxfail N / --maxfail=N)."""
    try:
        toks = shlex.split(seg)
    except ValueError:
        return None
    for i, t in enumerate(toks):
        if t in ("-x", "--exitfirst"):
            return 1
        if t.startswith("--maxfail="):
            return int(t.split("=", 1)[1]) if t.split("=", 1)[1].isdigit() else None
        if t == "--maxfail" and i + 1 < len(toks) and toks[i + 1].isdigit():
            return int(toks[i + 1])
        if t.startswith("-") and not t.startswith("--") and len(t) > 2 and "x" in t[1:] and t[1:].isalpha():
            return 1  # combined short flags, e.g. -xq
    return None


def _is_broad_test(seg: str) -> bool:
    return _broad_targets(seg) is not None


def rewrite(command: str, hook_python: str, test_python: str) -> str | None:
    """Replace each broad test invocation (up to a pipe) with the impact runner. None if nothing to do."""
    parts = _SEG_SPLIT.split(command)
    changed = False
    for i, part in enumerate(parts):
        if part in ("&&", "||", ";", "\n"):
            continue
        head, sep, tail = part.partition("|")
        targets = _broad_targets(head)
        if targets is not None:
            runner = f"{shlex.quote(hook_python)} -m dc_engine.impact run --python {shlex.quote(test_python)}"
            mf = _maxfail(head)
            if mf:
                runner += f" --maxfail {mf}"
            if targets:
                runner += " -- " + " ".join(shlex.quote(t) for t in targets)
            lead = re.match(r"^\s*", head).group(0)
            parts[i] = lead + runner  # the agent's filters (grep/tail) would hide the summary
            changed = True
    return "".join(parts) if changed else None


def pretool(payload: dict[str, Any], root: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if not cfg.get("impact") or payload.get("tool_name") != "Bash":
        return {}
    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not os.path.isfile(os.path.join(root, STATE_DIR, "covmap.json")):
        return {}
    new = rewrite(cmd, sys.executable, cfg.get("python") or sys.executable)
    if not new:
        return {}
    from .proviso import log_event
    log_event(root, {"event": "intercept", "original": cmd[:300]})
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                   "updatedInput": {**(payload.get("tool_input") or {}), "command": new}}}


def _junit(xml: str) -> dict[str, bool]:
    res = {}
    try:
        for c in ET.parse(xml).iter("testcase"):
            if not c.get("classname"):  # a test module that failed to load
                node = (c.get("name") or "").replace(".", "/") + ".py"
                res[node] = not any(ch.tag in ("failure", "error") for ch in c)
                continue
            parts = (c.get("classname") or "").split(".")
            node = f"{'/'.join(parts[:-1])}.py::{parts[-1]}::{c.get('name')}"
            res[node] = not any(ch.tag in ("failure", "error") for ch in c)
    except (OSError, ET.ParseError):
        pass
    return res


OUTCOME_PLUGIN = '''"""pytest plugin written by Proviso: test outcomes keyed by pytest node id."""
import json, os
_res = {}
def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and not report.passed):
        _res[report.nodeid] = bool(report.passed or report.skipped)
def pytest_collectreport(report):
    if report.failed:
        _res[report.nodeid] = False
def pytest_sessionfinish(session, exitstatus):
    json.dump(_res, open(os.environ["DC_OUTCOMES"], "w"))
'''


def _pytest(root: str, python: str, args: list[str], argfile_name: str) -> tuple[dict[str, bool], str]:
    """Run pytest with Proviso's outcome plugin. Returns ({node id: passed}, stdout)."""
    d = os.path.join(root, STATE_DIR)
    plug = os.path.join(d, "dc_outcomes.py")
    with open(plug, "w", encoding="utf-8") as fh:
        fh.write(OUTCOME_PLUGIN)
    out = os.path.join(d, "impact-outcomes.json")
    if os.path.exists(out):
        os.remove(out)
    cmd = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "dc_outcomes", "--tb=short", "--no-header",
           "-rN", "--continue-on-collection-errors"]
    if len(args) > 200:
        argfile = os.path.join(d, argfile_name)
        with open(argfile, "w", encoding="utf-8") as fh:
            fh.write("\n".join(args))
        cmd.append(f"@{argfile}")
    else:
        cmd += args
    env = dict(os.environ)
    env["PYTHONPATH"] = d + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["DC_OUTCOMES"] = out
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env)
    try:
        res = json.load(open(out))
    except (OSError, ValueError):
        res = {}
    return res, r.stdout


def _collect(root: str, python: str, targets: list[str]) -> list[str] | None:
    """Node ids pytest collects for the targets (None if collection did not work)."""
    env = dict(os.environ)
    r = subprocess.run([python, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "--no-header",
                        "--continue-on-collection-errors", *targets], cwd=root, capture_output=True, text=True, env=env)
    ids = [l.strip() for l in r.stdout.splitlines() if "::" in l and not l.startswith(("=", " "))]
    return ids or None


def _subclasses(root: str, files: list[str]) -> dict[str, set[str]]:
    """Class name -> names of classes that inherit from it (transitively), from the sources at HEAD (by name)."""
    bases: dict[str, set[str]] = {}
    for f in files:
        try:
            tree = ast.parse(_git(root, "show", f"{_BASE}:{f}"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for b in node.bases:
                    nm = b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else None
                    if nm:
                        bases.setdefault(nm, set()).add(node.name)
    out: dict[str, set[str]] = {}

    def subs(c, seen):
        for d in bases.get(c, ()):
            if d not in seen:
                seen.add(d)
                subs(d, seen)
        return seen
    for c in bases:
        out[c] = subs(c, set())
    return out


def impact_report(root: str, covmap: dict, why: dict, selected: list[str] | None, max_items: int = 6) -> list[str]:
    """What the change affects, for the agent: edited functions, import-time values that changed (and the classes
    that inherit a changed class attribute), and which tests depend on it. Empty if there is nothing to say."""
    base, _ = map_base(root, covmap)
    with _measured_from(base or "HEAD"):
        return _impact_report(root, covmap, why, selected, max_items)


def _impact_report(root: str, covmap: dict, why: dict, selected: list[str] | None, max_items: int = 6) -> list[str]:
    lines: list[str] = []
    funcs = [tuple(x) for x in why.get("changed_functions", [])]
    if funcs:
        names = []
        for f, ln in funcs[:max_items]:
            units, _ = _units(f, _git(root, "show", f"{_BASE}:{f}"))
            nm = next((u[0] for u in units if u[1] == ln), f"{f}:{ln}")
            names.append(f"{nm} ({f})")
        more = f" and {len(funcs) - max_items} more" if len(funcs) > max_items else ""
        lines.append(f"  - edited functions: {', '.join(names)}{more}")
    keys = [k for k in why.get("import_state_changed", []) if not k.endswith((".__mro__", ".__class__"))]
    if keys:
        subs = _subclasses(root, sorted(f for f in map_files(covmap) if not _is_test_path(f)))
        groups: dict[tuple[str, str], list[str]] = {}
        for k in keys:
            mod, qual = k.split(":", 1)
            owner, _, attr = qual.rpartition(".")
            groups.setdefault((mod, owner), []).append(attr or qual)
        # the class others inherit from first (where the change was made), then the rest
        order = sorted(groups, key=lambda g: (-len(subs.get(g[1].split(".")[0], ())) if g[1] else 0, g[1], g[0]))
        for mod, owner in order[:max_items]:
            attrs = groups[(mod, owner)]
            shown = ", ".join(attrs[:4]) + (f" (+{len(attrs) - 4})" if len(attrs) > 4 else "")
            if owner:
                inh = sorted(subs.get(owner.split(".")[0], ()))
                entry = f"  - {owner}.{{{shown}}} changed at import ({mod})"
                if inh:
                    entry += f"; inherited by {', '.join(inh[:6])}" + (f" (+{len(inh) - 6})" if len(inh) > 6 else "")
            else:
                entry = f"  - module values {shown} changed at import ({mod})"
            lines.append(entry)
        if len(order) > max_items:
            lines.append(f"  - ... values of {len(order) - max_items} more classes/modules changed at import")
    if selected:
        per_file: dict[str, int] = {}
        for t in selected:
            per_file[t.split("::", 1)[0]] = per_file.get(t.split("::", 1)[0], 0) + 1
        top = sorted(per_file.items(), key=lambda x: -x[1])[:max_items]
        lines.append(f"  - tests that depend on it: {len(selected)} in {len(per_file)} files, e.g. "
                     + ", ".join(f"{f} ({n})" for f, n in top))
    return (["Your change affects:"] + lines) if lines else []


def _report_enabled(root: str) -> bool:
    """The blast-radius report is on unless .dc-engine/proviso.json sets "report": false (an experiment switch)."""
    try:
        with open(os.path.join(root, ".dc-engine", "proviso.json"), encoding="utf-8") as fh:
            return bool(json.load(fh).get("report", True))
    except (OSError, ValueError, AttributeError):
        return True


def run_selected(root: str, python: str, targets: list[str] | None = None, maxfail: int | None = None) -> str:
    """Run what the agent asked for (targets: directories relative to the repository root; [] = the default suite),
    restricted to the tests the change can affect. Tests the coverage map does not know always run."""
    targets = targets or []
    covmap = _asset(root, "covmap.json") or {}
    base_fail = set(_asset(root, "base_failures.json") or [])
    t0 = time.time()
    sel, why = selection(root, covmap, python) if covmap else (None, {"reason": "no coverage map"})
    where = " ".join(targets) if targets else "the test suite"
    collected = _collect(root, python, targets) if sel is not None else None
    if sel is not None and collected is None:
        sel, why = None, {**why, "reason": "could not list the tests"}
    if sel is None:
        res, stdout = _pytest(root, python, ([f"--maxfail={maxfail}"] if maxfail else []) + targets,
                              "impact-args.txt")
        n_scope = len(res)
    else:
        selset = set(sel)
        agent_files = {x for x in sel if "::" not in x}
        run = [n for n in collected if n in selset or n not in covmap or n.split("::", 1)[0] in agent_files]
        n_unknown = sum(1 for n in run if n not in covmap and n not in selset)
        n_scope = len(collected)
        if not run:
            _log_run(root, 0, n_scope, time.time() - t0, [], why)
            return (f"[Proviso] Your changes do not reach any code the {n_scope} existing tests in {where} execute, so "
                    "none of them can change outcome; nothing to run.")
        res, stdout = _pytest(root, python, ([f"--maxfail={maxfail}"] if maxfail else []) + run, "impact-args.txt")
    secs = time.time() - t0
    failing = sorted(n for n, ok in res.items() if not ok)
    new = [n for n in failing if n not in base_fail and n.split("::")[0] not in base_fail]
    old = [n for n in failing if n not in new]
    if sel is not None:
        unk = (f", {n_unknown} of them because Proviso has no coverage record for them" if n_unknown else "")
        stopped = f", stopping at the first {maxfail} failure(s) as you asked" if maxfail else ""
        lines = [f"[Proviso] Ran {len(res)} of the {n_scope} tests in {where} (the ones your changes can affect"
                 f"{unk}{stopped}) in {secs:.0f}s."]
    else:
        lines = [f"[Proviso] Ran all {len(res)} tests in {where} ({why.get('reason', 'change could not be placed')}) "
                 f"in {secs:.0f}s."]
    try:
        if _report_enabled(root):
            lines += impact_report(root, covmap, why, [n for n in res] if sel is not None else None)
    except Exception:  # noqa: BLE001  (the report is informational; never let it break a test run)
        pass
    if new:
        lines.append(f"NEW failures ({len(new)}), not failing before your change:")
        lines += [f"  - {n}" for n in new[:15]]
        details = _failure_details(stdout, new)
        if details:
            lines.append(details)
    else:
        lines.append("No new failures: every selected test that passed before your change still passes.")
    if old:
        lines.append(f"{len(old)} failure(s) that already fail at the original commit (not caused by you).")
    lines.append(f"===== {sum(res.values())} passed, {len(new)} new failed, {len(old)} pre-existing failures "
                 f"(not caused by you) in {secs:.0f}s =====")
    _log_run(root, len(res), n_scope, secs, new, why)
    return "\n".join(lines)


def _failure_details(out: str, new: list[str]) -> str:
    keep, cur, buf = [], None, []
    for line in out.splitlines():
        m = re.match(r"^_+ (.+?) _+$", line)
        if m:
            if cur and buf:
                keep.append("\n".join(buf[:25]))
            cur, buf = m.group(1), [line]
        elif cur:
            if line.startswith("=") or line.startswith("FAILED") or line.startswith("ERROR") or re.match(r"^\d+ (failed|passed)", line):
                keep.append("\n".join(buf[:25]))
                cur, buf = None, []
            else:
                buf.append(line)
    if cur and buf:
        keep.append("\n".join(buf[:25]))
    return "\n".join(keep[:5])[:6000]


def _log_run(root, ran, total, secs, new, why):
    try:
        from .proviso import log_event
        log_event(root, {"event": "impact_run", "ran": ran, "total": total, "secs": round(secs, 1),
                         "new_failures": len(new), **{k: v for k, v in why.items() if k != "agent_tests"}})
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- ripple replay


def _edit(was: str, now: str) -> tuple[str, str]:
    """The differing middle of two strings (common prefix and suffix removed)."""
    i = 0
    while i < min(len(was), len(now)) and was[i] == now[i]:
        i += 1
    j = 0
    while j < min(len(was), len(now)) - i and was[-1 - j] == now[-1 - j]:
        j += 1
    return was[i:len(was) - j], now[i:len(now) - j]


def _window(was: str, now: str, ctx: int = 40, span: int = 70) -> tuple[str, str]:
    """Both strings cut around their first difference, so the change is visible however long they are."""
    i = 0
    while i < min(len(was), len(now)) and was[i] == now[i]:
        i += 1
    start = max(0, i - ctx)

    def cut(x: str) -> str:
        return ("…" if start else "") + x[start:i + span] + ("…" if len(x) > i + span else "")
    return cut(was), cut(now)


def ripple(root: str, cfg: dict[str, Any]) -> tuple[list[dict], dict]:
    """Changed outputs in inheriting components, not reported before. Each item: component, parent, input, was, now,
    and `same`: the parent's output on the same input changed in exactly the same way (inheritance doing its job)."""
    d = os.path.join(root, STATE_DIR)
    runner, probes_p, base_p = (os.path.join(d, n) for n in ("replay.py", "probes.json", "ripple_base.json"))
    if not (os.path.isfile(runner) and os.path.isfile(probes_p) and os.path.isfile(base_p)):
        return [], {"ripple": "no assets"}
    out = os.path.join(d, "ripple_cur.json")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": root, "HOME": os.environ.get("HOME", "/tmp"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    t0 = time.time()
    r = subprocess.run([cfg.get("python") or sys.executable, runner, "run", root, probes_p, out, base_p], cwd=root,
                       env=env, capture_output=True, text=True, timeout=600)
    stats = {"ripple_ms": int((time.time() - t0) * 1000)}
    if r.returncode != 0:
        stats["ripple"] = "runner error"
        return [], stats
    probes = json.load(open(probes_p))
    base = json.load(open(base_p))
    cur = json.load(open(out))
    own = {(p[0], p[2]): str(i) for i, p in enumerate(probes) if p[0] == p[1]}
    from .proviso import load_state, save_state
    st = load_state(root)
    seen = set(st.get("ripple_reported", []))
    changed = [k for k in cur if probes[int(k)][0] != probes[int(k)][1]]
    stats["ripple_changed"] = len(changed)
    fresh = [k for k in changed if k not in seen]
    items = []
    for k in fresh:
        src, dia, sql = probes[int(k)]
        was, now = base.get(k, ""), cur[k]
        pk = own.get((src, sql))
        same = pk is not None and pk in cur and _edit(base.get(pk, ""), cur[pk]) == _edit(was, now)
        items.append({"key": k, "component": dia, "parent": src, "input": sql, "was": was, "now": now, "same": same,
                      "error": now.startswith("EXC")})
    new_items, nstats = _new_input_ripple(root, cfg, probes, env, seen)
    stats.update(nstats)
    items += new_items
    fresh += [i["key"] for i in new_items]
    items.sort(key=lambda i: (i.get("new", False), i["same"], not i["error"], i["component"]))
    st["ripple_reported"] = sorted(seen | set(fresh))
    save_state(root, st)
    stats["ripple_reported"] = len(items)
    stats["ripple_same"] = sum(i["same"] for i in items)
    return items, stats


_NORM_RE = re.compile(r"[`\"\[\]'\s]")


def _same_modulo_quoting(a: str, b: str) -> bool:
    return _NORM_RE.sub("", a).lower() == _NORM_RE.sub("", b).lower()


def _new_input_ripple(root: str, cfg: dict[str, Any], probes: list, env: dict, seen: set[str]
                      ) -> tuple[list[dict], dict]:
    """Inputs from tests the agent added, run in their dialect and in every dialect that inherits from it.

    Ripples mostly surface on the new behaviour itself, which no existing test covers (in sqlglot's history, 7 of 9
    silent child-dialect regressions showed on the inputs the change's own tests added). A child is reported when,
    on such an input, it fails where its parent works, or its output differs from the parent's (quoting, case and
    spacing ignored) -- and only if the child's output also differs from what the original code produced, so the
    difference comes from the agent's change."""
    import importlib.util
    d = os.path.join(root, STATE_DIR)
    spec = importlib.util.spec_from_file_location("dc_replay", os.path.join(d, "replay.py"))
    if spec is None or spec.loader is None:
        return [], {}
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        now_corpus = set(map(tuple, mod.corpus(root)))
    except Exception:  # noqa: BLE001
        return [], {"ripple_new": "corpus error"}
    base_corpus = {(p[0], p[2]) for p in probes if p[0] == p[1]}
    children: dict[str, set[str]] = {}
    for src, dia, _ in probes:
        if src != dia:
            children.setdefault(src, set()).add(dia)
    new = sorted(c for c in now_corpus - base_corpus if children.get(c[0]))
    if not new:
        return [], {"ripple_new_inputs": 0}
    nprobes = []
    for src, sql in new[:200]:
        nprobes.append([src, src, sql])
        nprobes += [[src, ch, sql] for ch in sorted(children[src])]
    pp = os.path.join(d, "ripple_new_probes.json")
    json.dump(nprobes, open(pp, "w"))
    py = cfg.get("python") or sys.executable
    runner = os.path.join(d, "replay.py")
    cur_p, base_p = os.path.join(d, "ripple_new_cur.json"), os.path.join(d, "ripple_new_base.json")
    import shutil
    import tempfile
    tops = sorted({f.split("/", 1)[0] for f in map_files(_asset(root, "covmap.json") or {})})
    tmp = tempfile.mkdtemp(prefix="dc-ripple-base-")
    try:
        arch = subprocess.run(["git", "-C", root, "archive", "HEAD", *tops], capture_output=True)
        subprocess.run(["tar", "-x", "-C", tmp], input=arch.stdout, capture_output=True)
        r1 = subprocess.run([py, runner, "run", root, pp, cur_p], cwd=root, env=env, capture_output=True, timeout=600)
        r2 = subprocess.run([py, runner, "run", tmp, pp, base_p], cwd=tmp, env={**env, "PYTHONPATH": tmp},
                            capture_output=True, timeout=600)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if r1.returncode or r2.returncode:
        return [], {"ripple_new": "runner error"}
    cur, base = json.load(open(cur_p)), json.load(open(base_p))
    own = {(p[0], p[2]): str(i) for i, p in enumerate(nprobes) if p[0] == p[1]}
    items = []
    for i, (src, dia, sql) in enumerate(nprobes):
        if src == dia:
            continue
        k = str(i)
        child, parent, before = cur.get(k, ""), cur.get(own[(src, sql)], ""), base.get(k, "")
        if child == before or parent.startswith("EXC"):
            continue
        crash = child.startswith("EXC")
        if not crash and _same_modulo_quoting(child, parent):
            continue
        key = f"new:{dia}:{sql}:{child}"
        if key in seen:
            continue
        items.append({"key": key, "component": dia, "parent": src, "input": sql, "was": parent, "now": child,
                      "same": False, "error": crash, "new": True})
    return items, {"ripple_new_inputs": len(new), "ripple_new_reported": len(items)}


def ripple_report(items: list[dict], max_items: int = RIPPLE_MAX_ITEMS) -> str:
    """Report for the agent: changes that differ from the parent's in full; identical inherited changes in one line
    per component, since they are usually intended but the user should still hear about them."""
    newi = [i for i in items if i.get("new")]
    diff = [i for i in items if not i["same"] and not i.get("new")]
    same = [i for i in items if i["same"] and not i.get("new")]
    parts = ["Proviso replayed test inputs (from the existing tests and from tests you added) through your changed "
             "code, in every component that inherits from the code you edited."]
    if diff:
        parts.append("These outputs changed in an inheriting component, and not in the way the parent's output "
                     "changed (or the parent's did not change at all), which is how unintended side effects look:")
        for i in diff[:max_items]:
            w, n = _window(i["was"], i["now"])
            parts.append(f"- {i['component']} (inherits from {i['parent']}), input `{i['input'][:100]}`:\n"
                         f"    was `{w}`\n    now `{n}`")
        if len(diff) > max_items:
            parts.append(f"- …and {len(diff) - max_items} more")
    if newi:
        parts.append("On inputs from the tests you added, these inheriting components fail where their parent works, "
                     "or produce different output from the parent's (quoting and case ignored):")
        for i in newi[:max_items]:
            what = "fails" if i["error"] else "gives"
            parts.append(f"- {i['component']} (inherits from {i['parent']}), input `{i['input'][:100]}`:\n"
                         f"    {i['parent']} gives `{i['was'][:140]}`\n    {i['component']} {what} `{i['now'][:140]}`")
        if len(newi) > max_items:
            parts.append(f"- …and {len(newi) - max_items} more")
    if same:
        by = {}
        for i in same:
            by.setdefault((i["component"], i["parent"]), []).append(i)
        lines = []
        for (comp, par), its in sorted(by.items()):
            w, n = _window(its[0]["was"], its[0]["now"], ctx=25, span=35)
            lines.append(f"- {comp} now follows {par}'s change on {len(its)} input(s), e.g. `{w}` → `{n}`")
        parts.append("These inheriting components changed exactly as their parent did, which is usually intended:\n"
                     + "\n".join(lines))
    tail = []
    if diff or newi:
        tail.append("Fix the unintended ones; if a component is meant to differ from its parent here, say so.")
    tail.append("In your final message, tell the user which other components your change affects.")
    parts.append(" ".join(tail))
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m dc_engine.impact")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("run", help="run the tests the current change can affect")
    rp.add_argument("--python", default=sys.executable)
    rp.add_argument("--root", default=None)
    rp.add_argument("--maxfail", type=int, default=None, help="stop after this many failures (the agent's -x)")
    rp.add_argument("targets", nargs="*", help="directories the agent asked to test (relative to the current directory)")
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:  # targets after --
        k = argv.index("--")
        argv = argv[:k] + argv[k + 1:]
    a = ap.parse_args(argv)
    root = a.root or _git(os.getcwd(), "rev-parse", "--show-toplevel").strip() or os.getcwd()
    rel = [os.path.relpath(os.path.join(os.getcwd(), t), root) for t in a.targets]
    rel = [t for t in rel if t != "."]
    text = run_selected(root, a.python, rel, a.maxfail)
    print(text)
    return 1 if "NEW failures" in text else 0


if __name__ == "__main__":
    raise SystemExit(main())
