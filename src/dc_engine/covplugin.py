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

# (v2.5) a spawned worker starts in whatever directory the test was in: the recording's root travels in the environment
ROOT = os.environ.get("PROVISO_MP_ROOT") or os.getcwd()
PKG = os.path.join(ROOT, os.environ.get("COVMAP_PKG", "sqlglot")) + os.sep
SUBPROC = "subprocess.py"
MPPROC = os.path.join("multiprocessing", "process.py")
# ablation switches (evaluation only; see impact._off): subprocess, mp, fixtures, setup
_OFF = {x.strip() for x in os.environ.get("PROVISO_OFF", "").split(",") if x.strip()}


# (v2.5) Worker processes are recorded instead of marking their test as always selected. A child process (forked, or
# spawned by multiprocessing) runs this recorder too and appends what it runs, as it runs it, to its own file in
# MPDIR, named after the recording target that was current when it was started. The parent merges a target's files
# when the target ends. Anything it cannot account for keeps today's rule: a child still alive at that point, a
# missing or damaged file, the forkserver start method, a child that starts processes itself.
# PROVISO_OFF=mprecord restores v2.3's behaviour.
MPREC = "mprecord" not in _OFF and "mp" not in _OFF and hasattr(os, "register_at_fork")
MPDIR = os.environ.get("PROVISO_MP_DIR", "")
_child = [False]           # this process is a worker of the recorded test process
_leak = [False]            # a worker outlived its test: later tests of this process may use it unseen
_owners: list = []         # recording targets that can own workers, by index


def _forked():
    """os.fork() (multiprocessing's fork context, or a test forking itself): the child may run package code."""
    if "mp" in _OFF:
        return
    try:
        t = _target()
        if MPREC and MPDIR and not _child[0]:
            t.kids += 1
        else:
            t.always = True
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
    __slots__ = ("funcs", "classes", "always", "files", "dirs", "seen", "kids", "oid")

    def __init__(self):
        self.funcs, self.classes, self.always = set(), set(), False
        self.files, self.dirs = set(), set()   # (v2.3) project files opened for reading, directories listed
        self.seen = set()   # (v2.3.1) types whose package classes are already in self.classes (a cache only)
        self.kids, self.oid = 0, None   # (v2.5) worker processes started under this target; its owner number


class _LogSet(set):
    """A set that appends each new element to the worker's record file as it arrives (one short write per element, so
    a worker that is killed has still reported everything it ran)."""
    __slots__ = ("fd", "kind", "gonly")

    def add(self, x):
        # g: run while a package module was being imported (import-time code). A key first seen that way is reported
        # again if it later runs outside an import (a module's code and a function on its first line share a key).
        g = bool(self.kind == "f" and _modstack and (ROOT + os.sep + _modstack[-1][1]).startswith(PKG))
        if x in self and (g or x not in self.gonly):
            return
        set.add(self, x)
        if g:
            self.gonly.add(x)
        else:
            self.gonly.discard(x)
        try:
            os.write(self.fd, (json.dumps([self.kind, x, g]) + "\n").encode())
        except OSError:
            pass

    def update(self, xs):
        for x in xs:
            self.add(x)


class _ChildTarget:
    """The single recording target of a worker process."""

    def __init__(self, fd):
        self.fd, self.seen, self.kids, self.oid, self._always = fd, set(), 0, None, False
        for name, kind in (("funcs", "f"), ("classes", "c"), ("files", "F"), ("dirs", "D")):
            s = _LogSet()
            s.fd, s.kind, s.gonly = fd, kind, set()
            setattr(self, name, s)

    @property
    def always(self):
        return self._always

    @always.setter
    def always(self, v):
        if v and not self._always:
            try:
                os.write(self.fd, b'["A", null, false]\n')
            except OSError:
                pass
        self._always = bool(v)


GLOBAL = Target()          # code run while a PACKAGE module is imported (import-time state: the snapshot's channel)
_fixtures: dict = {}      # key -> Target
_stack: list = []          # recording targets; the top one receives what runs
_map: dict = {}
_own: dict = {}            # node id -> Target of its call phase
_kind: dict = {}
_meth: dict = {}           # (v2.3.1) id(code) -> (key, name of its first argument) for package methods
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


def _set_owner():
    """Name the current recording target in the environment, for the worker processes started under it."""
    if not (MPREC and MPDIR) or _child[0]:
        return
    t = _stack[-1] if _stack else _fixtures.setdefault(SESSION, Target())
    if t.oid is None:
        t.oid = len(_owners)
        _owners.append(t)
    os.environ["PROVISO_MP_OWNER"] = str(t.oid)


def _push(t):
    _stack.append(t)
    _set_owner()
    mon.restart_events()


def _pop():
    _stack.pop()
    _set_owner()
    mon.restart_events()


def _enter_child():
    """Become a worker's recorder: one target, written through to this process's file. Runs in a forked child right
    after the fork, and at start-up in a spawned one (see _mpsite/sitecustomize.py)."""
    if not (MPREC and MPDIR):
        return
    try:
        _child[0] = True
        fd = os.open(os.path.join(MPDIR, f"{os.environ.get('PROVISO_MP_OWNER', '')}-{os.getpid()}.rec"),
                     os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        _stack[:] = [_ChildTarget(fd)]
        _modstack.clear()
        mon.restart_events()
    except Exception:  # noqa: BLE001  (never break the code under test; the parent sees the missing file)
        pass


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    try:
        return open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return True


_merged: set = set()


def _mp_merge(t, wait: float = 3.0) -> bool:
    """Add the records of t's worker processes to t. False (and t is always selected) unless every worker it started
    has a complete file and has ended."""
    import glob
    import time
    deadline = time.time() + wait
    while True:
        files = [f for f in glob.glob(os.path.join(MPDIR, f"{t.oid}-*.rec"))]
        live = [f for f in files if _alive(int(os.path.basename(f)[:-4].rsplit("-", 1)[1]))]
        if (len(files) >= t.kids and not live) or time.time() > deadline:
            break
        time.sleep(0.02)
    ok = len(files) >= t.kids and not live
    try:
        for f in files:
            if f in _merged:
                continue
            _merged.add(f)
            raw = open(f, "rb").read()
            if raw and not raw.endswith(b"\n"):
                ok = False
            for line in raw.splitlines():
                kind, x, g = json.loads(line)
                if kind == "A":
                    t.always = True
                elif kind == "f":
                    key = tuple(x)
                    if not (g and key in GLOBAL.funcs):   # import-time code the parent's import ran too: the snapshot's
                        t.funcs.add(key)
                elif kind == "c":
                    t.classes.add(x)
                elif kind == "F":
                    t.files.add(x)
                elif kind == "D":
                    t.dirs.add(x)
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        t.always = True
    return ok


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
        # multiprocessing (Process, Pool, ProcessPoolExecutor): the child runs code this process cannot see.
        # (v2.5) with worker recording the launch itself is counted below (fork: _forked; spawn: "spawn")
        k = None if (MPREC and MPDIR and not _child[0]) else "process"
    elif code.co_name == "_launch" and fn.endswith(os.path.join("multiprocessing", "popen_spawn_posix.py")):
        k = "spawn" if (MPREC and MPDIR and not _child[0]) else "process"
    elif code.co_name == "_launch" and fn.endswith(os.path.join("multiprocessing", "popen_forkserver.py")):
        k = "process"   # the fork server was started under some earlier target: its children cannot be attributed
    else:
        k = None
    _kind[id(code)] = (code, k)  # keyed by identity: code objects of different files can compare equal
    if k is not None and k not in ("subprocess", "process", "spawn") and k[1]:
        _meth[id(code)] = (k[0], code.co_varnames[0])   # the code object is kept alive by _kind
    return k


def _start(code, offset):
    m = _meth.get(id(code))
    if m is not None and _stack:
        # (v2.3.1) the path below for a package method run inside a recording target, the hot case: methods stay
        # switched on to record the classes they run on. Same records; each type's classes are added once per target.
        t = _stack[-1]
        t.funcs.add(m[0])
        obj = sys._getframe(1).f_locals.get(m[1])
        if obj is None:
            return None
        tp = obj if isinstance(obj, type) else type(obj)
        try:
            if tp in t.seen:
                return None
            t.seen.add(tp)
        except TypeError:   # an unhashable type: _classes_of has nothing for it either
            return None
        t.classes.update(_classes_of(tp))
        return None
    if code.co_name == "<module>" and code.co_filename.startswith(ROOT + os.sep) and (not _stack or _child[0]):
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
    if k == "spawn":
        t.kids += 1      # every launch counts: stays switched on
        return None
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
    global MPDIR
    if MPREC and os.environ.get("PROVISO_MP_PARENT") in (None, "", str(os.getpid())) and not _child[0]:
        # the recorded test process: its workers find the recording through the environment
        MPDIR = os.environ["COVMAP_OUT"] + ".mp"
        os.makedirs(MPDIR, exist_ok=True)
        site = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_mpsite")
        os.environ.update({"PROVISO_MP_DIR": MPDIR, "PROVISO_MP_ROOT": ROOT, "PROVISO_MP_PARENT": str(os.getpid()),
                           "PYTHONPATH": os.pathsep.join([site] + [x for x in os.environ.get("PYTHONPATH", "")
                                                                   .split(os.pathsep) if x and x != site])})
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
        if _leak[0]:
            t.always = True
        if t.kids and not _mp_merge(t):
            _leak[0] = True


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
    os.register_at_fork(before=_forked, after_in_child=_enter_child)


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
    for t in list(_fixtures.values()):   # (v2.5) workers started in fixtures, set-up or teardown
        if t.kids:
            _mp_merge(t)
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
