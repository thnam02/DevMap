"""pytest plugin (Proviso v2): per-test coverage map that also records the code tests depend on through FIXTURE STATE.
Enable with -p covplugin_v2; output path in COVMAP_OUT; package directory in COVMAP_PKG.

A test depends on the code it runs and on code whose results reach it through shared state. Besides the test's own
call (as in covplugin_mon.py), this records:
  fixture instances   code run while pytest sets up a fixture, per instance: (fixture, scope node, parameter). A
                      class-scoped fixture runs once per class but every test of the class uses its result, so each
                      test is linked to every fixture instance in its closure (pytest's own fixture graph).
  setup/teardown      code run during a test's setup or teardown outside any fixture (plugin hooks, e.g. per-class
                      set-up in pytest_runtest_setup; fixture finalizers) is credited to the test's class, or to its
                      module for tests outside classes: such code typically runs once per class.
Output: as covplugin_mon.py, plus
  test["fx"]          keys of the fixture records the test depends on
  "__fixtures__"      {key: {"funcs": [...], "classes": [...], "always": bool}}
"__global__" keeps only code run outside any test's setup, call and teardown (imports, collection).

Recording uses sys.monitoring (PEP 669): a function is reported once per recording target and then switched off
until the target changes (sys.monitoring.restart_events); package methods stay on to record the classes they run on.
"""

import json
import os
import sys

import pytest

ROOT = os.getcwd()
PKG = os.path.join(ROOT, os.environ.get("COVMAP_PKG", "sqlglot")) + os.sep
SUBPROC = "subprocess.py"
MPPROC = os.path.join("multiprocessing", "process.py")
# ablation switches (evaluation only; see impact._off): subprocess, mp, fixtures, setup
_OFF = {x.strip() for x in os.environ.get("PROVISO_OFF", "").split(",") if x.strip()}


def _forked():
    """os.fork() (multiprocessing's fork context, or a test forking itself): the child may run package code."""
    if "mp" in _OFF:
        return
    try:
        _target().always = True
    except Exception:  # noqa: BLE001
        pass
PKG_NAME = os.path.basename(os.path.normpath(os.environ.get("COVMAP_PKG", "sqlglot")))


_LAUNCHERS = {"sh", "bash", "zsh", "dash", "fish", "cmd", "cmd.exe", "powershell", "pwsh", "make", "tox", "nox",
              "uv", "uvx", "poetry", "hatch", "pdm", "pipx", "pip", "pip3", "coverage", "conda", "mamba", "sudo", "su"}
# programs that run the command after them (their own options, VAR=value and numbers are skipped)
_WRAPPERS = {"env", "nice", "nohup", "timeout", "time", "exec", "stdbuf", "ionice", "taskset", "xvfb-run"}


def _runs_project_code(args) -> bool:
    """Whether a subprocess can run the package's own code, which the recorder cannot see: a Python interpreter (or
    pytest), a shell, script or launcher that may start one, or a command named after the package (pylint,
    sphinx-build). Only the program counts, after wrappers such as `env VAR=1` or `timeout 10`: an external tool
    (git, file, latex, dot) cannot run the package even when an argument names Python (platform.architecture() runs
    `file -b /usr/bin/python3.13` at pytest-benchmark's session start, which had marked every pylint test as always
    selected)."""
    if isinstance(args, (str, bytes)):
        line = args.decode(errors="replace") if isinstance(args, bytes) else args
        if any(c in line for c in ";&|`$<>()"):
            return True  # a shell command line (shell=True): any of its commands may run Python
        args = line.split()
    try:
        words = [os.fspath(a) for a in args]
    except TypeError:
        return True  # unknown form: keep the conservative rule
    words = [w.decode(errors="replace") if isinstance(w, bytes) else w for w in words]
    i = 0
    while i < len(words):
        w = words[i]
        if os.path.basename(w).lower() in _WRAPPERS or (i and (w.startswith("-") or "=" in w
                                                                   or w.replace(".", "", 1).isdigit())):
            i += 1
            continue
        break
    if i >= len(words):
        return True  # nothing but wrappers (or no command): keep the conservative rule
    prog = words[i]
    base = os.path.basename(prog).lower()
    if base.startswith(("python", "pypy", "pytest", "py.test")) or prog == sys.executable:
        return True
    if base in _LAUNCHERS or base.endswith((".sh", ".py", ".bat", ".cmd", ".ps1")):
        return True  # shells, scripts and build tools may start Python themselves
    if PKG_NAME and PKG_NAME.lower() in base:
        return True
    return False


TOOL = 3
mon = sys.monitoring
DISABLE = mon.DISABLE


class Target:
    __slots__ = ("funcs", "classes", "always", "files", "dirs")

    def __init__(self):
        self.funcs, self.classes, self.always = set(), set(), False
        self.files, self.dirs = set(), set()   # (v2.3) project files opened for reading, directories listed


GLOBAL = Target()          # code run while a PACKAGE module is imported (import-time state: the snapshot's channel)
_fixtures: dict = {}      # key -> Target
_stack: list = []          # recording targets; the top one receives what runs
_map: dict = {}
_own: dict = {}            # node id -> Target of its call phase
_kind: dict = {}
_mro_cache: dict = {}


# Outside any test, code runs in one of three contexts, told apart by the module being executed at the time:
#   a package module is being imported   -> GLOBAL (import-time state, compared by the snapshot)
#   a test module is being imported      -> "<import>@FILE": every test of that file depends on it
#   anything else (plugin and conftest session set-up, collection hooks) -> "<session>": every test depends on it
_modstack: list = []       # (code object, relative file) of the modules under ROOT being executed (imports)
_watched: set = set()
SESSION = "<session>"


def _context_target():
    if _modstack:
        rel = _modstack[-1][1]
        if (ROOT + os.sep + rel).startswith(PKG):
            return GLOBAL
        if os.path.basename(rel) != "conftest.py":
            return _fixtures.setdefault(f"<import>@{rel}", Target())
    return _fixtures.setdefault(SESSION, Target())


def _target():
    return _stack[-1] if _stack else _context_target()


def _module_start(code):
    """A module under ROOT starts executing (an import): track it until it returns."""
    rel = code.co_filename[len(ROOT) + 1:]
    _modstack.append((code, rel))
    if id(code) not in _watched:
        _watched.add(id(code))
        _kind.setdefault(("watch", id(code)), code)  # keep the code object alive
        mon.set_local_events(TOOL, code, mon.events.PY_RETURN)
    mon.restart_events()


def _module_end(code, offset, arg):
    # a module that failed to import never returns: its entry is dropped when an enclosing module returns
    if any(c is code for c, _ in _modstack):
        while _modstack:
            c, _ = _modstack.pop()
            if c is code:
                break
        mon.restart_events()


def _push(t):
    _stack.append(t)
    mon.restart_events()


def _pop():
    _stack.pop()
    mon.restart_events()


def _classes_of(tp):
    try:
        got = _mro_cache.get(tp)
    except TypeError:
        return []
    if got is None:
        got = []
        for c in getattr(tp, "__mro__", ()):
            mod = sys.modules.get(getattr(c, "__module__", ""), None)
            fn = getattr(mod, "__file__", None) or ""
            if fn.startswith(PKG):
                got.append(f"{os.path.relpath(fn, ROOT)}:{c.__qualname__}")
        _mro_cache[tp] = got
    return got


def _classify(code):
    fn = code.co_filename
    if fn.startswith(PKG):
        method = bool(code.co_argcount and code.co_varnames[0] in ("self", "cls"))
        k = ((fn[len(ROOT) + 1:], code.co_firstlineno), method)
    elif code.co_name == "__init__" and fn.endswith(SUBPROC) and \
            getattr(code, "co_qualname", "Popen.__init__") == "Popen.__init__":   # not CompletedProcess or errors
        k = "subprocess"
    elif code.co_name == "start" and fn.endswith(MPPROC) and \
            getattr(code, "co_qualname", "BaseProcess.start") == "BaseProcess.start":
        k = "process"   # multiprocessing (Process, Pool, ProcessPoolExecutor): the child runs code the recorder cannot see
    else:
        k = None
    _kind[id(code)] = (code, k)  # keyed by identity: code objects of different files can compare equal
    return k


def _start(code, offset):
    if code.co_name == "<module>" and code.co_filename.startswith(ROOT + os.sep) and not _stack:
        _module_start(code)
    got = _kind.get(id(code))
    k = got[1] if got is not None else _classify(code)
    if k is None:
        return DISABLE
    t = _target()
    if k == "process":
        if "mp" not in _OFF:
            t.always = True
        return DISABLE
    if k == "subprocess":
        try:
            popen_args = sys._getframe(1).f_locals.get("args")
        except Exception:  # noqa: BLE001
            popen_args = None
        if popen_args is None or "subprocess" in _OFF or _runs_project_code(popen_args):
            t.always = True
        return DISABLE
    key, method = k
    t.funcs.add(key)
    if not method or not _stack:
        return DISABLE
    obj = sys._getframe(1).f_locals.get(code.co_varnames[0])
    if obj is not None:
        t.classes.update(_classes_of(obj if isinstance(obj, type) else type(obj)))
    return None


# ------------------------------------------------------------------------------------------------------------ keys
# A fixture instance is identified when pytest sets it up: (fixture, base id, scope node, parameter index), where the
# scope node is the node pytest itself attaches the instance to (request.node). Until pytest sets the fixture up again
# or finalises it, that instance is the fixture's current one; when a test runs, every fixture it uses is set up, so
# its current instances are exactly the ones the test uses (no reconstruction of pytest's scoping rules).

_current: dict = {}        # id(fixturedef) -> (fixturedef, key of its current instance)
_item_keys: set = set()    # fixture instances set up during the current test's setup and call


def _fx_key(fixturedef, request):
    node = getattr(request, "node", None)
    return f"{fixturedef.baseid}::{fixturedef.argname}@{node.nodeid if node is not None else ''}" \
           f"[{getattr(request, 'param_index', 0)}]"


def _outside_key(item):
    node = item.getparent(pytest.Class) or item.getparent(pytest.Module)
    return f"<setup/teardown>@{node.nodeid if node is not None else item.nodeid}"


# ------------------------------------------------------------------------------------------------------------ hooks

# (v2.3) Files read and directories listed, per recording target, from Python's audit events (PEP 578): open() and
# os.open for reading, os.listdir / os.scandir / glob.glob. Only paths under the project count, byte-code and
# extension modules excluded. Python sources count when they are read as data (pylint's functional tests read their
# input .py files; inspect.getsource); the import system's own reads are left out (_from_project), since code that runs
# is recorded by function. A file read by C code that bypasses Python's I/O, or by another process, is not seen: tests
# that start a Python process are already always selected.
_AUDITED = frozenset({"open", "os.listdir", "os.scandir", "glob.glob"})
_CODE_EXT = (".pyc", ".pyo", ".so", ".pyd")
_SKIP_DIRS = (".git" + os.sep, ".dc-engine" + os.sep)
_audit_on = [True]


def _static_prefix(pattern: str) -> str:
    """The directory part of a glob pattern before its first wildcard."""
    parts = []
    for part in os.path.normpath(pattern).split(os.sep)[:-1]:
        if any(ch in part for ch in "*?["):
            break
        parts.append(part)
    return os.sep.join(parts) or "."


def _audit(event, args):
    if event not in _AUDITED or not _audit_on[0]:
        return
    try:
        p = args[0]
        if p is None:
            p = "."
        if isinstance(p, int):
            return
        p = os.fsdecode(os.fspath(p))
        if p.startswith("<"):   # a pseudo file name ("<string>", "<unknown>"): nothing on disk
            return
        if event == "open":
            mode, flags = args[1], args[2]
            if isinstance(mode, str):
                if "r" not in mode and "+" not in mode:
                    return
            elif isinstance(flags, int) and flags & os.O_WRONLY and not flags & os.O_RDWR:
                return
        elif event == "glob.glob":
            p = _static_prefix(p)
        full = os.path.abspath(p)
        if full != ROOT and not full.startswith(ROOT + os.sep):
            return
        rel = os.path.relpath(full, ROOT)
        if rel.startswith(_SKIP_DIRS) or (event == "open" and rel.endswith(_CODE_EXT)) or \
                os.sep + "__pycache__" + os.sep in os.sep + rel:
            return
        t = _target()
        if not _from_project(t):
            return
        (t.files if event == "open" else t.dirs).add(rel.replace(os.sep, "/"))
    except Exception:  # noqa: BLE001  (an audit hook must never raise into the code under test)
        return


_LIB_MARKS = ("site-packages", "dist-packages")


def _is_project_file(fn: str) -> bool:
    return (fn.startswith(ROOT + os.sep) and not any(m in fn for m in _LIB_MARKS))


def _from_project(target) -> bool:
    """Whether a read belongs to the code under test rather than to Python's or pytest's own machinery:
      - the import system listing a package directory to find modules (frozen importlib, before any project frame):
        only Python files matter there, and those are recorded as code;
      - pytest walking the tree to collect tests, reading its configuration, or a plugin doing so outside any fixture
        (no project frame on the stack, recorded under the session): new test files run themselves and configuration
        changes have their own rule.
    A library called from project code (json.load, pandas.read_csv, importlib.resources) counts, and so does a plugin
    fixture (pytest-datadir) run for a test: it is recorded under that fixture."""
    f = sys._getframe(2)
    seen_project = False
    while f is not None:
        fn = f.f_code.co_filename
        if fn.startswith("<frozen importlib"):
            if not seen_project:
                return False
        elif _is_project_file(fn):
            seen_project = True
            break
        f = f.f_back
    if seen_project:
        return True
    return target is not _fixtures.get(SESSION)


def _begin():
    # from the moment the plugin is loaded (-p), before conftest files import the package
    mon.use_tool_id(TOOL, "proviso-cov-v2")
    mon.register_callback(TOOL, mon.events.PY_START, _start)
    mon.register_callback(TOOL, mon.events.PY_RETURN, _module_end)
    mon.set_events(TOOL, mon.events.PY_START)
    if "files" not in _OFF:
        sys.addaudithook(_audit)


if os.environ.get("COVMAP_OUT"):
    _begin()


_BEFORE = os.environ.get("COVMAP_BEFORE_TEST", "")


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    key = _fx_key(fixturedef, request)
    _current[id(fixturedef)] = (fixturedef, key)
    _item_keys.add(key)
    _push(_fixtures.setdefault(key, Target()))
    try:
        yield
    finally:
        _pop()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_setup(item):
    _item_keys.clear()
    if _BEFORE:
        import importlib
        mod, fn = _BEFORE.split(":")
        getattr(importlib.import_module(mod), fn)()
    _push(_fixtures.setdefault(_outside_key(item), Target()))
    try:
        yield
    finally:
        _pop()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    t = _own[item.nodeid] = Target()
    _push(t)
    try:
        yield
    finally:
        _pop()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    _push(_fixtures.setdefault(_outside_key(item), Target()))
    try:
        yield
    finally:
        _pop()


_pending: dict = {}


def _closure_keys(item):
    keys = set(_item_keys)
    info = getattr(item, "_fixtureinfo", None)
    if info is not None:
        for defs in info.name2fixturedefs.values():
            for fd in defs:
                cur = _current.get(id(fd))
                if cur is not None and cur[0] is fd:
                    keys.add(cur[1])
    return keys


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    yield
    if call.when == "call":
        _pending[item.nodeid] = _closure_keys(item)   # every fixture the test used is set up and current now
    elif call.when == "teardown" and item.nodeid in _times:
        own = _own.get(item.nodeid) or Target()
        t, ok = _times[item.nodeid]
        keys = _pending.pop(item.nodeid, set()) | {_outside_key(item), SESSION,
                                                  f"<import>@{item.nodeid.split('::', 1)[0]}"}
        _map[item.nodeid] = {"funcs": sorted(own.funcs), "classes": sorted(own.classes), "always": own.always,
                             "time": t, "ok": ok, "fx": sorted(keys)}
        if own.files:
            _map[item.nodeid]["files"] = sorted(own.files)
        if own.dirs:
            _map[item.nodeid]["dirs"] = sorted(own.dirs)


_times: dict = {}


_reported: set = set()      # tests pytest reported anything for
_setup_failed: set = set()  # tests whose setup failed (their body never ran, so they have no record)
_collected: list = []


def pytest_collection_finish(session):
    _collected[:] = [i.nodeid for i in session.items]


def pytest_runtest_logreport(report):
    _reported.add(report.nodeid)
    if report.when == "call":
        _times[report.nodeid] = (round(report.duration, 4), report.passed)
    elif report.when == "setup" and report.failed:
        _setup_failed.add(report.nodeid)


if hasattr(os, "register_at_fork"):
    os.register_at_fork(before=_forked)


def pytest_sessionfinish(session, exitstatus):
    _audit_on[0] = False
    mon.set_events(TOOL, 0)
    mon.free_tool_id(TOOL)
    # a test collected here whose body never ran (its setup failed, or the run stopped before it) has no record of
    # what it depends on: it is always selected, so a recording glitch costs time, not safety (sqlalchemy lost 39
    # tests from one recording). Skipped tests stay out: in the same environment they are skipped again.
    for nid in ([] if "setup" in _OFF else sorted(_setup_failed) + [n for n in _collected if n not in _reported]):
        if nid not in _map:
            _map[nid] = {"funcs": [], "classes": [], "always": True, "time": 0.0, "ok": False, "fx": [],
                         "unrecorded": True}
    used = {k for v in _map.values() for k in v["fx"]}
    _map["__fixtures__"] = {k: {"funcs": sorted(t.funcs), "classes": sorted(t.classes), "always": t.always,
                                **({"files": sorted(t.files)} if t.files else {}),
                                **({"dirs": sorted(t.dirs)} if t.dirs else {})}
                            for k, t in _fixtures.items()
                            if k in used and (t.funcs or t.classes or t.always or t.files or t.dirs)}
    # every test keeps the keys of all the fixture instances it used, also those whose own record is empty (a fixture
    # that only patches the clock): an edit to such a fixture in conftest.py is traced to its users through them
    if "fixtures" in _OFF:
        for v in _map.values():
            if "fx" in v:
                v["fx"] = [k for k in v["fx"] if k in _map["__fixtures__"]]
    _map["__global__"] = {"funcs": sorted(GLOBAL.funcs), "files": sorted(GLOBAL.files), "dirs": sorted(GLOBAL.dirs),
                          "file_records": "files" not in _OFF}
    json.dump(_map, open(os.environ["COVMAP_OUT"], "w"))
