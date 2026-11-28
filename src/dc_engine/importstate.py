"""Import-time state of a package, for change-impact selection.

Many edits touch code that also runs while modules load (module constants, class tables built by metaclasses, a
parser that is exercised at import). Selection cannot treat those edits like ordinary function edits, because their
effect is baked into state that every test then reads. Instead of falling back to the full suite, we compare that
state directly: import the package at the base commit and in the working tree, fingerprint every module-level value
and every class attribute of classes defined in the package, and diff.

  no difference   the edit has no import-time effect; function-level selection is sound
  differences     the names whose values changed (STRICT_TIME_FORMATS, Hive.TIME_MAPPING, ...); tests are selected
                  by which code reads those names (impact.selection)

Fingerprints: plain data by value (sets/dicts order-free), functions by qualified name plus a hash of their code
(so a changed lambda inside a table counts), classes and modules by identity (classes are fingerprinted on their
own), other objects by type and attributes, memory addresses stripped.

Usage inside the subprocess: python importstate.py TREE PACKAGE_FILES.json OUT.json
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.abspath(__file__)
SNAPSHOT_TIMEOUT = 300
FORMAT = 23  # bump when fingerprints, recording or selection change: cached base snapshots and result rows of another format are recomputed
# bookkeeping that changes whenever lines move, or that Python fills in itself
IGNORED_CLASS_KEYS = {"__dict__", "__weakref__", "__doc__", "__module__", "__qualname__", "__annotations__",
                      "__firstlineno__", "__static_attributes__", "__annotate__", "__annotate_func__",
                      "__annotations_cache__", "_abc_impl"}


SRC_DIRS = ("src", "lib")  # src layouts: the importable package lives in one of these, which is not a package itself


def layout_prefix(files) -> str:
    """'src/' or 'lib/' if the package files are under such a directory, else ''."""
    tops = {f.split("/", 1)[0] for f in files if "/" in f}
    return f"{next(iter(tops))}/" if len(tops) == 1 and next(iter(tops)) in SRC_DIRS else ""


def _module_name(rel: str) -> str | None:
    if not rel.endswith(".py"):
        return None
    parts = rel[:-3].split("/")
    if len(parts) > 1 and parts[0] in SRC_DIRS:
        parts = parts[1:]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or parts[-1] == "__main__":
        return None
    return ".".join(parts)


def _snapshot_main(tree: str, files_path: str, out_path: str) -> None:
    import functools
    import importlib
    import logging
    import pathlib
    import re
    import types
    import warnings
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    sys.setrecursionlimit(10000)
    addr = re.compile(r" at 0x[0-9a-fA-F]+")
    # (v2.3.2) pydantic builds its core schema with references that embed id(cls) ("pkg.mod.Model:140231..."), and its
    # compiled SchemaSerializer/SchemaValidator print raw pointers and their fields in a per-process hash-map order.
    # Within pydantic values (pydantic's own objects, and the __pydantic_*__ attributes of models) those per-process
    # parts are removed; the schema itself is still fingerprinted, so a changed model still counts.
    pyd_ref = re.compile(r"\b([A-Za-z_][\w.]*):\d{4,}\b")
    pyd_ptr = re.compile(r"0x[0-9a-fA-F]+")
    files = json.load(open(files_path))
    # import-time code may draw random numbers (sympy's combinatorics uses randomised algorithms); generators seeded
    # from the OS would make the state differ on every run, so unseeded generators get a fixed seed here
    import random
    _orig_seed = random.Random.seed

    def _fixed_seed(self, a=None, version=2):
        return _orig_seed(self, 0 if a is None else a, version)
    random.Random.seed = _fixed_seed
    random.seed(0)
    # shift the heap so that values whose order depends on memory addresses (tuple(set_of_classes)) come out
    # differently between the base runs and can be recognised as order-unstable
    pad = [object() for _ in range(int(os.environ.get("DC_HEAP_PAD", "0")))]  # noqa: F841
    pad_bytes = [bytearray(64 * (i % 7 + 1)) for i in range(int(os.environ.get("DC_HEAP_PAD", "0")) // 3)]  # noqa: F841
    # (v2.5) some base samples run with the clock moved, so that a value made from the time of import shows up as
    # run-varying even when it is coarser than the few seconds the samples take (sphinx's `ctime`, to the minute).
    # Only the time module's functions are wrapped; the wrappers are fingerprinted as the functions they wrap.
    clock_alias: dict = {}
    shift = float(os.environ.get("DC_CLOCK_SHIFT", "0") or 0)
    if shift:
        import time as _t
        _time, _ns, _lt, _gt, _sf, _ct, _at = _t.time, _t.time_ns, _t.localtime, _t.gmtime, _t.strftime, _t.ctime, _t.asctime
        wrappers = {
            "time": lambda: _time() + shift,
            "time_ns": lambda: _ns() + int(shift * 1e9),
            "localtime": lambda secs=None: _lt(_time() + shift if secs is None else secs),
            "gmtime": lambda secs=None: _gt(_time() + shift if secs is None else secs),
            "strftime": lambda fmt, t=None: _sf(fmt, _lt(_time() + shift) if t is None else t),
            "ctime": lambda secs=None: _ct(_time() + shift if secs is None else secs),
            "asctime": lambda t=None: _at(_lt(_time() + shift) if t is None else t),
        }
        for n, w in wrappers.items():
            clock_alias[id(w)] = f"bf:{n};"
            setattr(_t, n, w)
    mods = {}
    errors = {}
    # which package functions run while the package is imported: an edit to one of them can change import-time state
    # (recorded here, independent of when a test runner happens to import the package)
    base_dir = os.path.realpath(tree)
    wanted = {os.path.join(base_dir, f) for f in files}
    # where the tree lives is not part of its state: the base snapshot is taken from an export in a temporary folder,
    # the current one from the working tree, and values may hold the package's own path (loguru keeps its file path
    # inside `logger`); both spellings of the location are replaced by one placeholder
    roots = sorted({base_dir, os.path.abspath(tree)}, key=len, reverse=True)

    def unroot(text: str) -> str:
        for r in roots:
            if r in text:
                text = text.replace(r, "<root>")
        return text
    import_funcs: set = set()
    mon = getattr(sys, "monitoring", None)
    if mon is not None:
        def _seen(code, offset):
            fn = code.co_filename if code.co_filename in wanted else os.path.realpath(code.co_filename)
            if fn in wanted:
                import_funcs.add((os.path.relpath(fn, base_dir), code.co_firstlineno))
            return mon.DISABLE
        mon.use_tool_id(4, "proviso-importstate")
        mon.register_callback(4, mon.events.PY_START, _seen)
        mon.set_events(4, mon.events.PY_START)
    for rel in files:
        name = _module_name(rel)
        if not name:
            continue
        try:
            mods[name] = importlib.import_module(name)
        except BaseException as e:  # noqa: BLE001
            errors[name] = type(e).__name__
    if mon is not None:
        mon.set_events(4, 0)
        mon.free_tool_id(4)
    if os.environ.get("DC_IMPORT_ONLY") == "1":
        # only which functions run at import (cheap): no fingerprints
        json.dump({"state": {}, "overrides": [], "errors": errors, "import_funcs": sorted(import_funcs)},
                  open(out_path, "w"))
        return

    def code_hash(co, h):
        h.update(co.co_code)
        h.update(repr(co.co_names).encode())
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                code_hash(c, h)
            elif isinstance(c, frozenset):
                # (v2.5) a set constant (`name in {"a", "b"}`) prints in hash order, which differs per process
                h.update(repr(sorted(addr.sub("", repr(x)) for x in c)).encode())
            else:
                h.update(addr.sub("", repr(c)).encode())

    sha = lambda x: hashlib.sha1(x.encode()).hexdigest()
    # Each object is fingerprinted once per snapshot and reused wherever it is reached again (sympy reaches the same
    # tables and singletons from thousands of attributes). A fingerprint is reused only if computing it met no cycle
    # and no depth cut-off, the two things that make it depend on the path it was reached by. Objects are kept
    # alive in `keep` so that a memoised id is never reused by another object.
    memo: dict = {}
    keep: list = []
    USE_MEMO = os.environ.get("DC_NO_MEMO") != "1"  # for checking the memoisation against plain fingerprinting
    impure = [0]

    class OverBudget(Exception):
        pass

    # A value whose object graph is too large to fingerprint in reasonable time (pylint's test helpers build a whole
    # linter at import) is recorded as unknown instead of letting one value time out the whole snapshot; unknown
    # values always count as changed (diff), so their readers are selected.
    BUDGET = int(os.environ.get("DC_VALUE_BUDGET", "200000"))
    budget = {"left": BUDGET}

    def dig(v, depth, seen):
        t = type(v)
        if t is str:
            r = "str:" + repr(unroot(pyd_ref.sub(r"\1:<id>", v) if mode["pyd"] else v))
            return r if len(r) <= 40 else "h:" + sha(r)
        if v is None or t in (bool, int, float, complex, bytes):
            r = t.__name__ + ":" + repr(v)
            return r if len(r) <= 40 else "h:" + sha(r)
        if depth > 80:
            impure[0] += 1
            return "<deep>"
        key = (id(v), mode["ordered"], mode["pyd"])
        got = memo.get(key) if USE_MEMO else None
        if got is not None:
            if got[1]:
                mode["seq"] = True
            return got[0]
        imp0, seq0 = impure[0], mode["seq"]
        mode["seq"] = False
        budget["left"] -= 1
        if budget["left"] < 0:
            raise OverBudget
        r = body(v, t, depth, seen)
        r = r if len(r) <= 40 else "h:" + sha(r)
        has_seq = mode["seq"]
        mode["seq"] = seq0 or has_seq
        if impure[0] == imp0:
            memo[key] = (r, has_seq)
            keep.append(v)
        return r

    def dict_body(name, items, depth, seen):
        return name + "{" + ",".join(sorted(sha(dig(k, depth + 1, seen) + "=" + dig(x, depth + 1, seen))
                                            for k, x in items)) + "}"

    def body(v, t, depth, seen):
        if not mode["pyd"] and (getattr(t, "__module__", None) or "").split(".", 1)[0] in ("pydantic", "pydantic_core"):
            mode["pyd"] = True
            try:
                return body(v, t, depth, seen)
            finally:
                mode["pyd"] = False
        if isinstance(v, os._Environ):
            # the process environment (e.g. `from os import environ`): set by whoever starts Python, never by the code,
            # and different in every snapshot process, so it is not import-time state of the package
            return "environ;"
        if isinstance(v, logging.Logger):
            # a logger's own settings only: its parent chain leads to the process-wide registry and the parent's level
            # cache, which differ with anything that logged during import (e.g. a missing generated _version.py), so
            # walking them made every module logger look changed
            return (f"logger:{v.name}:{v.level}:{v.propagate}:{v.disabled}:"
                    + ",".join(type(h).__name__ for h in getattr(v, "handlers", [])) + ";")
        if isinstance(v, types.FunctionType):
            if id(v) in clock_alias:
                return clock_alias[id(v)]
            r = f"fn:{v.__module__}.{v.__qualname__};"
            # a wrapper made at import (functools.wraps gives it the wrapped function's name, so its code's own name
            # differs): like a lambda or closure, the values it carries (deprecated(since=...)) are part of its state
            wrapper = hasattr(v, "__wrapped__") or getattr(v.__code__, "co_qualname", v.__qualname__) != v.__qualname__
            if "<" in v.__qualname__ or wrapper:
                # lambdas and closures made at import time: their body lives inside a table or a factory call,
                # not in a function the line-level rule can see, so their code and captured values count
                h = hashlib.sha1()
                code_hash(v.__code__, h)
                r += h.hexdigest()
                if v.__defaults__:
                    r += dig(v.__defaults__, depth + 1, seen)
                for cell in v.__closure__ or ():
                    try:
                        r += dig(cell.cell_contents, depth + 1, seen)
                    except ValueError:
                        r += "<empty cell>"
            return r
        if isinstance(v, functools.partial):
            return "partial" + dig(v.func, depth + 1, seen) + dig(v.args, depth + 1, seen) + \
                dict_body("kw", sorted((v.keywords or {}).items()), depth + 1, seen)
        if isinstance(v, (types.BuiltinFunctionType, types.MethodWrapperType, types.WrapperDescriptorType)):
            return f"bf:{getattr(v, '__qualname__', repr(v))};"
        if isinstance(v, (classmethod, staticmethod)):
            return t.__name__ + dig(v.__func__, depth + 1, seen)
        if isinstance(v, property):
            return "prop" + "".join(dig(f, depth + 1, seen) for f in (v.fget, v.fset, v.fdel))
        if isinstance(v, type):
            return f"cls:{v.__module__}.{v.__qualname__};"
        if isinstance(v, types.ModuleType):
            return f"mod:{v.__name__};"
        if isinstance(v, types.MethodType):
            return "bound" + dig(v.__func__, depth + 1, seen)
        if isinstance(v, pathlib.PurePath):
            # (v2.3.2) a path is its text with the tree's location removed, as in plain strings: walked as an object,
            # its cached parts (_tail_cached) hold the location as separate components that unroot cannot reach, so
            # a path into the package (datasette's app_root) differed between the base export and the working tree
            return f"path:{t.__name__}:" + repr(unroot(str(v)))
        if id(v) in seen:
            impure[0] += 1
            return "<cycle>"
        seen = seen | {id(v)}
        if isinstance(v, (list, tuple)):
            mode["seq"] = True
            parts = [dig(x, depth + 1, seen) for x in v]
            return "[" + ",".join(parts) + "]" if mode["ordered"] else "[~" + ",".join(sorted(parts)) + "]"
        if isinstance(v, (set, frozenset)):
            return "{" + ",".join(sorted(dig(x, depth + 1, seen) for x in v)) + "}"
        if isinstance(v, dict):
            return dict_body(t.__name__, v.items(), depth, seen)
        try:
            d = vars(v)
        except TypeError:
            d = None
        slots = [n for c in t.__mro__ for n in (getattr(c, "__slots__", ()) or ())
                 if isinstance(n, str) and n not in ("__dict__", "__weakref__")]
        if d is not None or slots:
            state = dict(d or {})
            for n in slots:
                if hasattr(v, n):
                    state["slot:" + n] = getattr(v, n)
            # a cached hash (e.g. sympy's _mhash) is derived data whose value can depend on memory addresses
            try:
                own = hash(v)
            except Exception:  # noqa: BLE001
                own = None
            if own is not None:
                state = {k: x for k, x in state.items() if not (type(x) is int and x == own)}
            return f"obj:{t.__module__}.{t.__qualname__}" + dict_body("dict", state.items(), depth, seen)
        try:
            r = repr(v)
        except Exception:  # noqa: BLE001
            r = "<unrepr>"
        r = unroot(addr.sub('', r))
        if mode["pyd"]:
            r = "\n".join(sorted(pyd_ptr.sub("0x", pyd_ref.sub(r"\1:<id>", r)).splitlines()))
        return f"{t.__module__}.{t.__qualname__}:{r};"

    mode = {"ordered": True, "seq": False, "pyd": False}

    def one(v):
        # the two fingerprints differ only in how lists and tuples are hashed: without any, the second pass is skipped
        res = []
        mode["seq"] = False
        for ordered in (True, False):
            if not ordered and not mode["seq"]:
                break
            mode["ordered"] = ordered
            budget["left"] = BUDGET
            try:
                d = dig(v, 0, frozenset())
            except OverBudget:
                return UNKNOWN
            except Exception as e:  # noqa: BLE001
                d = f"<error {type(e).__name__}>"
            res.append(sha(d)[:16])
        return res[0] if len(res) == 1 or res[0] == res[1] else f"{res[0]}~{res[1]}"

    # (v2.5) Run-varying values. For the keys the base found to differ between imports of the same code, the value is
    # also written as a tree (same walk as dig, nothing hashed), so that the parts that vary can be told from the
    # parts that do not (generalise, below). An integer that is the address of a live object (an id()-keyed registry)
    # is written as what it points to.
    tree_keys = set(json.load(open(os.environ["DC_TREE_KEYS"]))) if os.environ.get("DC_TREE_KEYS") else set()
    TREE_BUDGET = int(os.environ.get("DC_TREE_BUDGET", "60000"))
    trees: dict = {}
    tree_errors: dict = {}
    idmap: dict = {}
    refmemo: dict = {}
    REF_BUDGET = 400
    tleft = [0]

    def ref_of(n):
        if not idmap:
            import gc
            idmap.update((id(o), o) for o in gc.get_objects())
        o = idmap.get(n)
        if o is None:
            return None
        if isinstance(o, type):
            return f"cls:{o.__module__}.{o.__qualname__}"
        if isinstance(o, types.FunctionType):
            return f"fn:{o.__module__}.{o.__qualname__}"
        if isinstance(o, types.ModuleType):
            return f"mod:{o.__name__}"
        return o

    def tleaf(tag, text):
        return ["s", tag, text] if len(text) <= 20000 else ["s", tag + "#", sha(text)]

    def tdig(v, depth, seen):
        tleft[0] -= 1
        if tleft[0] < 0:
            raise OverBudget
        t = type(v)
        if t is str:
            return tleaf("str", unroot(pyd_ref.sub(r"\1:<id>", v) if mode["pyd"] else v))
        if t is int and v >= 1 << 24:
            r = ref_of(v)
            if isinstance(r, str):
                return ["s", "ref", r]
            if r is not None:
                # another object: what it is, as far as a small part of the budget goes (a registry of many large
                # objects falls back to their types)
                got = refmemo.get(v)
                if got is None:
                    keep_left = tleft[0]
                    tleft[0] = REF_BUDGET
                    try:
                        got = ["l", "ref", [tdig(r, depth + 1, seen)]]
                    except Exception:  # noqa: BLE001  (over the budget, or an attribute that cannot be read)
                        got = ["s", "ref", f"obj:{type(r).__module__}.{type(r).__qualname__}"]
                    tleft[0] = keep_left
                    refmemo[v] = got
                return got
        if v is None or t in (bool, int, float, complex, bytes):
            return tleaf(t.__name__, repr(v))
        if depth > 80:
            return ["s", "atom", "<deep>"]
        if not mode["pyd"] and (getattr(t, "__module__", None) or "").split(".", 1)[0] in ("pydantic", "pydantic_core"):
            mode["pyd"] = True
            try:
                return tdig(v, depth, seen)
            finally:
                mode["pyd"] = False
        if isinstance(v, os._Environ):
            return ["s", "atom", "environ;"]
        if isinstance(v, logging.Logger):
            return ["s", "atom", f"logger:{v.name}:{v.level}:{v.propagate}:{v.disabled}:"
                    + ",".join(type(h).__name__ for h in getattr(v, "handlers", []))]
        if isinstance(v, types.FunctionType):
            if id(v) in clock_alias:
                return ["s", "atom", clock_alias[id(v)][:-1]]
            name = f"fn:{v.__module__}.{v.__qualname__}"
            wrapper = hasattr(v, "__wrapped__") or getattr(v.__code__, "co_qualname", v.__qualname__) != v.__qualname__
            if "<" in v.__qualname__ or wrapper:
                h = hashlib.sha1()
                code_hash(v.__code__, h)
                kids = [tdig(v.__defaults__, depth + 1, seen)] if v.__defaults__ else []
                for cell in v.__closure__ or ():
                    try:
                        kids.append(tdig(cell.cell_contents, depth + 1, seen))
                    except ValueError:
                        kids.append(["s", "atom", "<empty cell>"])
                return ["l", name + ":" + h.hexdigest(), kids]
            return ["s", "atom", name]
        if isinstance(v, functools.partial):
            return ["l", "partial", [tdig(v.func, depth + 1, seen), tdig(v.args, depth + 1, seen),
                                     tdig(dict(v.keywords or {}), depth + 1, seen)]]
        if isinstance(v, (types.BuiltinFunctionType, types.MethodWrapperType, types.WrapperDescriptorType)):
            return ["s", "atom", f"bf:{getattr(v, '__qualname__', repr(v))}"]
        if isinstance(v, (classmethod, staticmethod)):
            return ["l", t.__name__, [tdig(v.__func__, depth + 1, seen)]]
        if isinstance(v, property):
            return ["l", "prop", [tdig(f, depth + 1, seen) for f in (v.fget, v.fset, v.fdel)]]
        if isinstance(v, type):
            return ["s", "atom", f"cls:{v.__module__}.{v.__qualname__}"]
        if isinstance(v, types.ModuleType):
            return ["s", "atom", f"mod:{v.__name__}"]
        if isinstance(v, types.MethodType):
            return ["l", "bound", [tdig(v.__func__, depth + 1, seen)]]
        if isinstance(v, pathlib.PurePath):
            return tleaf(f"path:{t.__name__}", unroot(str(v)))
        if id(v) in seen:
            return ["s", "atom", "<cycle>"]
        seen = seen | {id(v)}
        if isinstance(v, (list, tuple)):
            return ["l", t.__name__, [tdig(x, depth + 1, seen) for x in v]]
        if isinstance(v, (set, frozenset)):
            return ["b", t.__name__, [tdig(x, depth + 1, seen) for x in v]]
        if isinstance(v, dict):
            return ["m", t.__name__, [[tdig(k, depth + 1, seen), tdig(x, depth + 1, seen)] for k, x in list(v.items())]]
        try:
            d = vars(v)
        except TypeError:
            d = None
        slots = [n for c in t.__mro__ for n in (getattr(c, "__slots__", ()) or ())
                 if isinstance(n, str) and n not in ("__dict__", "__weakref__")]
        if d is not None or slots:
            state = dict(d or {})
            for n in slots:
                if hasattr(v, n):
                    state["slot:" + n] = getattr(v, n)
            try:
                own = hash(v)
            except Exception:  # noqa: BLE001
                own = None
            if own is not None:
                state = {k: x for k, x in state.items() if not (type(x) is int and x == own)}
            return ["m", f"obj:{t.__module__}.{t.__qualname__}",
                    [[tdig(k, depth + 1, seen), tdig(x, depth + 1, seen)] for k, x in state.items()]]
        try:
            r = repr(v)
        except Exception:  # noqa: BLE001
            r = "<unrepr>"
        r = unroot(addr.sub('', r))
        if mode["pyd"]:
            r = "\n".join(sorted(pyd_ptr.sub("0x", pyd_ref.sub(r"\1:<id>", r)).splitlines()))
        return tleaf(f"repr:{t.__module__}.{t.__qualname__}", r)

    def tree_of(key, v):
        if key not in tree_keys:
            return
        tleft[0] = TREE_BUDGET
        try:
            trees[key] = tdig(v, 0, frozenset())
        except OverBudget:
            tree_errors[key] = "over budget"   # no tree: the key keeps counting as changed whenever it differs
        except Exception as e:  # noqa: BLE001
            tree_errors[key] = f"{type(e).__name__}: {e}"[:200]

    out: dict[str, str] = {}
    overrides: list[str] = []
    done_classes = set()

    def do_class(modname, cls, prefix):
        if id(cls) in done_classes:
            return
        done_classes.add(id(cls))
        out[f"{modname}:{prefix}.__mro__"] = one(cls.__mro__)
        if type(cls) is not type:
            out[f"{modname}:{prefix}.__class__"] = one(type(cls))
        for k, v in list(vars(cls).items()):
            if k in IGNORED_CLASS_KEYS:
                continue
            key = f"{modname}:{prefix}.{k}"
            mode["pyd"] = k.startswith("__pydantic_")   # a model's schema, validator, serializer, decorators
            try:
                out[key] = one(v)
                tree_of(key, v)
            finally:
                mode["pyd"] = False
            if any(k in vars(b) for b in cls.__mro__[1:] if b is not object):
                overrides.append(key)
            if isinstance(v, type) and v.__module__ == modname and v.__qualname__ == f"{cls.__qualname__}.{k}":
                do_class(modname, v, f"{prefix}.{k}")

    def generated_module(v) -> bool:
        """A submodule that is not part of the recorded sources: version modules written at install time
        (setuptools-scm's _version.py) or another untracked file in the tree. Whether it is importable depends on how
        the tree was installed, not on the change."""
        if not isinstance(v, types.ModuleType):
            return False
        if v.__name__.rsplit(".", 1)[-1] in ("_version", "version"):
            return True
        f = getattr(v, "__file__", None)
        if not f:
            return False
        f = os.path.realpath(f)
        return f.startswith(base_dir + os.sep) and f not in wanted

    for name, m in mods.items():
        for k, v in list(vars(m).items()):
            if k.startswith("__") and k.endswith("__"):
                continue
            if generated_module(v):
                continue
            out[f"{name}:{k}"] = one(v)
            tree_of(f"{name}:{k}", v)
            if isinstance(v, type) and v.__module__ == name and v.__qualname__ == k:
                do_class(name, v, k)
    res = {"state": out, "overrides": sorted(overrides), "errors": errors, "import_funcs": sorted(import_funcs)}
    if tree_keys:
        res["trees"] = trees
        res["tree_errors"] = tree_errors
    json.dump(res, open(out_path, "w"))


UNKNOWN = "<unknown>"   # a value too large to fingerprint (see the budget in _snapshot_main): always counts as changed


def snapshot(tree: str, files: list[str], python: str, heap_pad: int = 0, import_only: bool = False,
             tree_keys=None, clock_shift: float = 0) -> dict | None:
    """Import-time state of `tree` (only `tree` importable). None if the snapshot could not be taken."""
    fd, files_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    out_path = files_path + ".out"
    try:
        json.dump(files, open(files_path, "w"))
        keys_path = files_path + ".keys"
        if tree_keys:
            json.dump(sorted(tree_keys), open(keys_path, "w"))
        path = os.pathsep.join([tree] + [os.path.join(tree, d) for d in SRC_DIRS if os.path.isdir(os.path.join(tree, d))
                                         and not os.path.exists(os.path.join(tree, d, "__init__.py"))])
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": path, "HOME": os.environ.get("HOME", "/tmp"),
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": str(heap_pad % 97),
               "DC_HEAP_PAD": str(heap_pad), "DC_IMPORT_ONLY": "1" if import_only else "0",
               "DC_VALUE_BUDGET": os.environ.get("DC_VALUE_BUDGET", "200000")}
        if clock_shift:
            env["DC_CLOCK_SHIFT"] = str(clock_shift)
        if tree_keys:
            env["DC_TREE_KEYS"] = keys_path
            env["DC_TREE_BUDGET"] = os.environ.get("DC_TREE_BUDGET", "60000")
        r = subprocess.run([python, HERE, tree, files_path, out_path], cwd=tree, env=env, capture_output=True,
                           text=True, timeout=SNAPSHOT_TIMEOUT)
        if r.returncode != 0 or not os.path.exists(out_path):
            return None
        return json.load(open(out_path))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    finally:
        for p in (files_path, out_path, files_path + ".keys"):
            if os.path.exists(p):
                os.remove(p)


def cache_key(root: str, tops: list[str], python: str, files: list[str] | None = None, rev: str = "HEAD") -> str:
    """Content of the base commit's package directories (git tree hashes, so a copy of the same code in another
    repository matches) and the interpreter (bytecode differs between versions)."""
    trees = [subprocess.run(["git", "-C", root, "rev-parse", f"{rev}:{t}"], capture_output=True, text=True).stdout.strip()
             for t in tops]
    ver = subprocess.run([python, "-c", "import sys; print(sys.version)"], capture_output=True, text=True).stdout.strip()
    return hashlib.sha1(json.dumps([trees, ver, sorted(files or [])]).encode()).hexdigest()


# (v2.2) the base snapshot's cache format: more samples for finding order-unstable values (the maps keep FORMAT)
# (v2.3.2) .b3: path and pydantic fingerprints changed, so base snapshots cached by v2.3.1 are taken again
BASE_FORMAT = f"{FORMAT}.b4"
# heap shifts and export locations of the extra base samples. Values whose order follows memory addresses (sympy's
# multipledispatch orderings: a topological sort over a set of classes) can come out in another order in any process;
# with only two extra samples at one location such a value often looked stable and then "changed" on every edit.
UNSTABLE_SAMPLES = [(0, 5003), (0, 20011), (1, 0), (1, 5003), (1, 20011), (2, 0), (2, 7919), (2, 30011)]
# (v2.5) one more sample location: a git checkout of the same commit with only the package directories (location 3).
# The working tree is a git checkout and the exports are not, so a value derived from git (sphinx puts the commit in
# its version text, versioneer derives the version from tags) differed between base and working tree on every change;
# sampled here, it is seen to vary without a code change like any other run-varying value.
GIT_SAMPLES = [(3, 0), (3, 7919)]
# (v2.5) the samples at export location 2 run with the clock moved by this much (every field of a date and time
# differs: year, month, day, hour, minute, second)
CLOCK_SHIFT = 400 * 86400 + 7 * 3600 + 13 * 60 + 17


def _off(part: str) -> bool:
    return part in {x.strip() for x in os.environ.get("PROVISO_OFF", "").split(",") if x.strip()}


# ---- (v2.5) run-varying values: which parts of a value differ between imports of the same code -------------------
# A tree (written by the snapshot process) is one of
#   ["s", tag, text]            a leaf: a string, a number, an object known by name or repr
#   ["l", tag, [child, ...]]    an ordered sequence
#   ["b", tag, [child, ...]]    a set (order-free)
#   ["m", tag, [[key, value], ...]]   a dict or an object's attributes
# A pattern is a tree that may also contain
#   ["w", tag, prefix, suffix, length]   a leaf of this kind whose text starts and ends like this (length -1: any)
#   ["*"]                                anything
# generalise(pattern, tree) is the least general pattern (within these forms) that covers both. The base's pattern is
# the generalisation of its samples; a current value is unchanged iff generalising with it does not change the
# pattern, i.e. it differs from the base samples only where they differ from each other.
_NUMERIC = ("int", "float", "complex", "bool")
_BAG_LIMIT = 3000


def _ck(n, memo: dict) -> str:
    """Canonical hash of a tree or pattern (sets and dicts order-free)."""
    i = id(n)
    got = memo.get(i)
    if got is not None:
        return got[0]
    k = n[0]
    if k in ("s", "w", "*"):
        r = json.dumps(n)
    elif k == "l":
        r = "l" + n[1] + "[" + ",".join(_ck(c, memo) for c in n[2]) + "]"
    elif k == "b":
        r = "b" + n[1] + "{" + ",".join(sorted(_ck(c, memo) for c in n[2])) + "}"
    else:
        r = "m" + n[1] + "{" + ",".join(sorted(_ck(a, memo) + "=" + _ck(b, memo) for a, b in n[2])) + "}"
    r = hashlib.sha1(r.encode()).hexdigest()
    memo[i] = (r, n)   # the node is kept alive so that its id is not reused
    return r


def _common_prefix(a: str, b: str) -> str:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return a[:i]


def _common_suffix(a: str, b: str) -> str:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[-1 - i] == b[-1 - i]:
        i += 1
    return a[len(a) - i:]


def _gen_leaf(p, t):
    if p[1] != t[1]:
        return ["*"]
    tag, text = p[1], t[2]
    if tag in _NUMERIC:
        return ["w", tag, "", "", -1]
    if p[0] == "s":
        pre = _common_prefix(p[2], text)
        suf = _common_suffix(p[2][len(pre):], text[len(pre):])
        ln = len(text) if len(p[2]) == len(text) else -1
    else:
        pre = _common_prefix(p[2], text)
        suf = _common_suffix(p[3], text[len(pre):])
        ln = p[4] if p[4] == len(text) else -1
    return ["w", tag, pre, suf, ln]


def _gen_bag(P: list, T: list, memo: dict):
    """Generalise two multisets of nodes: equal ones pair up; a current node that a remaining pattern node already
    covers pairs with it; what is left is paired by shape. None if the sizes differ (the whole collection varies)."""
    if len(P) != len(T):
        return None
    left: dict[str, list] = {}
    for t in T:
        left.setdefault(_ck(t, memo), []).append(t)
    out, rp = [], []
    for q in P:
        same = left.get(_ck(q, memo))
        if same:
            same.pop()
            out.append(q)
        else:
            rp.append(q)
    rt = [t for k in sorted(left) for t in left[k]]
    if len(rp) > _BAG_LIMIT:
        return None
    used = [False] * len(rp)
    rest = []
    for t in rt:
        for i, q in enumerate(rp):
            if used[i] or q[0] == "s":
                continue
            if q[0] != "*" and q[0] != t[0] and (q[0], t[0]) != ("w", "s"):
                continue
            if _ck(_gen(q, t, memo), memo) == _ck(q, memo):
                used[i] = True
                out.append(q)
                break
        else:
            rest.append(t)

    def shape(n):
        return (n[0] if n[0] != "w" else "s", n[1] if len(n) > 1 else "", len(n[2]) if n[0] in "lbm" else 0)
    rq = sorted((q for i, q in enumerate(rp) if not used[i]), key=lambda n: (shape(n), _ck(n, memo)))
    rest.sort(key=lambda n: (shape(n), _ck(n, memo)))
    out.extend(_gen(q, t, memo) for q, t in zip(rq, rest))
    return out


def _gen(p, t, memo: dict):
    if p[0] == "*" or _ck(p, memo) == _ck(t, memo):
        return p
    pk, tk = p[0], t[0]
    if pk in ("s", "w") and tk == "s":
        return _gen_leaf(p, t)
    if pk in ("l", "b") and tk in ("l", "b") and p[1] == t[1]:
        if pk == "l" and tk == "l":
            if len(p[2]) != len(t[2]):
                return ["*"]
            if sorted(_ck(c, memo) for c in p[2]) == sorted(_ck(c, memo) for c in t[2]):
                return ["b", p[1], p[2]]   # the same elements in another order: order-free from here on
            return ["l", p[1], [_gen(a, b, memo) for a, b in zip(p[2], t[2])]]
        kids = _gen_bag(p[2], t[2], memo)
        return ["*"] if kids is None else ["b", p[1], kids]
    if pk == "m" and tk == "m" and p[1] == t[1]:
        if len(p[2]) != len(t[2]):
            return ["*"]
        by_key: dict[str, list] = {}
        for kv in t[2]:
            by_key.setdefault(_ck(kv[0], memo), []).append(kv)
        out, rp = [], []
        for kv in p[2]:
            c = by_key.get(_ck(kv[0], memo))
            if c:
                # several entries under one key (addresses of objects of one kind): prefer the equal value
                vk = _ck(kv[1], memo)
                j = next((i for i, x in enumerate(c) if _ck(x[1], memo) == vk), 0)
                out.append([kv[0], _gen(kv[1], c.pop(j)[1], memo)])
            else:
                rp.append(kv)
        rt = [kv for k in sorted(by_key) for kv in by_key[k]]
        pairs = _gen_bag([["l", "pair", kv] for kv in rp], [["l", "pair", kv] for kv in rt], memo)
        if pairs is None or any(x[0] != "l" for x in pairs):
            return ["*"]
        return ["m", p[1], out + [x[2] for x in pairs]]
    return ["*"]


def generalise(pattern, tree):
    return _gen(pattern, tree, {})


def covers(pattern, tree) -> bool:
    """Whether `tree` differs from the base samples only where they differ from each other."""
    memo: dict = {}
    return _ck(_gen(pattern, tree, memo), memo) == _ck(pattern, memo)


def _git_sample_dir(root: str, tops: list[str], rev: str) -> tuple[str, str] | None:
    """(temporary clone, tree inside it): a checkout of `rev` with only the package directories and a .git that
    answers like the user's repository (same commit, same tags). The user's repository is only read."""
    def run(*a):
        return subprocess.run(["git", *a], capture_output=True, text=True)
    top = run("-C", root, "rev-parse", "--show-toplevel").stdout.strip()
    sha = run("-C", root, "rev-parse", rev).stdout.strip()
    prefix = run("-C", root, "rev-parse", "--show-prefix").stdout.strip()
    if not top or not sha:
        return None
    tmp = tempfile.mkdtemp(prefix="dc-git-")
    ok = run("clone", "-q", "--shared", "--no-checkout", top, tmp).returncode == 0 \
        and run("-C", tmp, "sparse-checkout", "set", "--no-cone", *[f"/{prefix}{t}/" for t in tops]).returncode == 0 \
        and run("-C", tmp, "checkout", "-q", "--detach", sha).returncode == 0
    if not ok:
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    return tmp, os.path.join(tmp, prefix) if prefix else tmp


def base_snapshot(root: str, files: list[str], python: str, cache_path: str, rev: str = "HEAD") -> dict | None:
    """Snapshot of the base commit (rev, HEAD by default; exported to a temporary directory), cached per commit. Keys whose fingerprint
    differs between the first snapshot and any of the extra samples (other heap shifts, other export locations, run
    in parallel) are recorded as order-unstable: diff() compares them without order."""
    tops = sorted({f.split("/", 1)[0] for f in files})
    head = cache_key(root, tops, python, files, rev)
    try:
        cached = json.load(open(cache_path))
        if cached.get("head") == head and cached.get("format") == BASE_FORMAT:
            return cached["snapshot"]
    except (OSError, ValueError, KeyError):
        pass
    arch = subprocess.run(["git", "-C", root, "archive", rev, *tops], capture_output=True)
    if arch.returncode != 0:
        return None
    # three export locations with different path lengths (the location shapes what is allocated at import)
    tmps = [tempfile.mkdtemp(prefix=p) for p in ("dc-base-", "dc-base-location-two-", "dc-b3-")]
    samples = list(UNSTABLE_SAMPLES)
    git_tmp = None
    try:
        for t in tmps:
            subprocess.run(["tar", "-x", "-C", t], input=arch.stdout, capture_output=True)
        if not _off("volatile"):
            got = _git_sample_dir(root, tops, rev)
            if got is not None:
                git_tmp = got[0]
                tmps.append(got[1])
                samples += GIT_SAMPLES
        snap = snapshot(tmps[0], files, python)
        shift_of = lambda s: CLOCK_SHIFT if s[0] == 2 and not _off("volatile") else 0
        if snap is not None:
            from concurrent.futures import ThreadPoolExecutor
            # at most 4 at a time: each imports the whole package (about 1 GB for sympy)
            workers = max(1, min(4, (os.cpu_count() or 2) // 2))
            with ThreadPoolExecutor(workers) as ex:
                others = list(ex.map(lambda s: snapshot(tmps[s[0]], files, python, heap_pad=s[1],
                                                        clock_shift=shift_of(s)), samples))
            # a sample that failed (a timeout under load) is taken again on its own; if it fails again it is left
            # out, unless every extra sample failed (then the import itself is unreliable: no base)
            others = [o if o is not None else snapshot(tmps[s[0]], files, python, heap_pad=s[1],
                                                       clock_shift=shift_of(s))
                      for o, s in zip(others, samples)]
            # a sample in which other modules fail to import ran under other conditions than the code's own
            if not _off("volatile"):
                others = [o for o in others if o is None or o["errors"] == snap["errors"]]
            others = [o for o in others if o is not None]
            if not others:
                snap = None
            else:
                unstable = {k for o in others for k, v in snap["state"].items() if o["state"].get(k) != v}
                snap["unstable"] = sorted(unstable)
                snap["unstable_samples"] = len(others)
                # (v2.5) keys whose contents, not only their order, differ between the samples: a second round of
                # samples writes them as trees, and their generalisation says which parts vary
                free = lambda fp: fp.split("~")[-1]
                varying = sorted(k for k in unstable if snap["state"][k] != UNKNOWN and
                                 any(o["state"].get(k) is None or free(o["state"][k]) != free(snap["state"][k])
                                     for o in others))
                if varying and not _off("volatile"):
                    with ThreadPoolExecutor(workers) as ex:
                        tr = list(ex.map(lambda s: snapshot(tmps[s[0]], files, python, heap_pad=s[1],
                                                            tree_keys=varying, clock_shift=shift_of(s)),
                                         [(0, 0)] + samples))
                    tr = [o["trees"] for o in tr if o is not None and "trees" in o and o["errors"] == snap["errors"]]
                    patterns = {}
                    if len(tr) >= 3:
                        for k in varying:
                            if all(k in o for o in tr):
                                pat = tr[0][k]
                                for o in tr[1:]:
                                    pat = generalise(pat, o[k])
                                if pat[0] != "*":
                                    patterns[k] = pat
                    snap["patterns"] = patterns
                    snap["pattern_samples"] = len(tr)
    finally:
        for t in tmps[:3]:
            shutil.rmtree(t, ignore_errors=True)
        if git_tmp:
            shutil.rmtree(git_tmp, ignore_errors=True)
    if snap is not None:
        try:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            json.dump({"head": head, "format": BASE_FORMAT, "snapshot": snap}, open(cache_path, "w"))
        except OSError:
            pass
    return snap


def keep_clean_snapshot(root: str, files: list[str], python: str, snap: dict, path: str) -> None:
    """(v2.4) Keep a snapshot of the working tree when it is exactly HEAD in the package directories (no edits, no
    untracked files there), keyed like a base snapshot of HEAD: incremental recording installs it as the next base
    (adopt_base) instead of taking nine new samples."""
    tops = sorted({f.split("/", 1)[0] for f in files})
    st = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", *tops], capture_output=True, text=True)
    if st.returncode != 0 or st.stdout.strip():
        return
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        json.dump({"head": cache_key(root, tops, python, files), "format": BASE_FORMAT, "snapshot": snap}, open(path, "w"))
    except OSError:
        pass


def adopt_base(root: str, files: list[str], python: str, cur_path: str, old_base_path: str, base_path: str) -> bool:
    """(v2.4) Make the kept snapshot of HEAD (keep_clean_snapshot) the cached base snapshot, carrying over the keys
    the previous base found order-unstable. A value that became order-unstable in between is then compared with
    order and may count as changed: more tests selected, never fewer. False when there is nothing to adopt."""
    tops = sorted({f.split("/", 1)[0] for f in files})
    try:
        cur = json.load(open(cur_path))
    except (OSError, ValueError):
        return False
    if cur.get("format") != BASE_FORMAT or cur.get("head") != cache_key(root, tops, python, files):
        return False
    try:
        old = json.load(open(old_base_path)).get("snapshot") or {}
    except (OSError, ValueError):
        old = {}
    snap = dict(cur["snapshot"])
    snap["unstable"] = sorted(set(old.get("unstable", [])))
    snap["unstable_samples"] = old.get("unstable_samples", 0)
    if old.get("patterns"):
        snap["patterns"] = old["patterns"]
    snap.pop("trees", None)
    snap["adopted"] = True
    try:
        json.dump({"head": cur["head"], "format": BASE_FORMAT, "snapshot": snap}, open(base_path, "w"))
    except OSError:
        return False
    return True


def import_funcs_of(root: str, files: list[str], python: str, cache_path: str, rev: str = "HEAD") -> list | None:
    """Functions of the HEAD commit that run while its package is imported (an import-only pass: no fingerprints),
    cached per commit. Used when only function bodies changed, to tell whether an edited function runs at import."""
    tops = sorted({f.split("/", 1)[0] for f in files})
    head = cache_key(root, tops, python, files, rev)
    try:
        cached = json.load(open(cache_path))
        if cached.get("head") == head and cached.get("format") == FORMAT:
            return cached["import_funcs"]
    except (OSError, ValueError, KeyError):
        pass
    tmp = tempfile.mkdtemp(prefix="dc-base-")
    try:
        arch = subprocess.run(["git", "-C", root, "archive", rev, *tops], capture_output=True)
        if arch.returncode != 0:
            return None
        subprocess.run(["tar", "-x", "-C", tmp], input=arch.stdout, capture_output=True)
        snap = snapshot(tmp, files, python, import_only=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if snap is None:
        return None
    try:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        json.dump({"head": head, "format": FORMAT, "import_funcs": snap["import_funcs"]}, open(cache_path, "w"))
    except OSError:
        pass
    return snap["import_funcs"]


def _same(a: str | None, b: str | None, unstable: bool) -> bool:
    """Fingerprints are 'ordered' or 'ordered~unordered'; unstable keys (sequence order differs between two
    imports of the same code, e.g. tuple(set_of_classes)) are compared without order."""
    if a == b:
        return True
    if a is None or b is None or not unstable:
        return False
    return a.split("~")[-1] == b.split("~")[-1]


def diff(base: dict, cur: dict, ignore_added: set[str] = frozenset()) -> dict[str, list[str]]:
    """changed: keys whose value changed or disappeared, plus keys that are new (except module-level names in
    `ignore_added`: new top-level functions and imports, which existing code cannot be reading).
    added_class_attrs: the new class-attribute keys (their classes may dispatch to them by computed name).
    errors: modules that import at base but not now."""
    b, c = base["state"], cur["state"]
    unstable = set(base.get("unstable", []))
    changed = sorted(k for k in b if b[k] == UNKNOWN or c.get(k) == UNKNOWN
                     or not _same(b[k], c.get(k), k in unstable))
    # (v2.5) a run-varying value is unchanged if it differs from the base samples only where they differ from each
    # other; `covered` lists the keys judged this way (the caller still counts one whose own statement was edited)
    patterns = {} if _off("volatile") else base.get("patterns") or {}
    trees = cur.get("trees") or {}
    covered = [k for k in changed if k in patterns and k in trees and b[k] != UNKNOWN and c.get(k) != UNKNOWN
               and covers(patterns[k], trees[k])]
    if covered:
        drop = set(covered)
        changed = [k for k in changed if k not in drop]
    added = sorted(k for k in c if k not in b)
    added_class = [k for k in added if "." in k.split(":", 1)[1]]
    added_mod = [k for k in added if "." not in k.split(":", 1)[1] and k.split(":", 1)[1] not in ignore_added]
    errors = sorted(set(cur.get("errors", {})) - set(base.get("errors", {})))
    return {"changed": changed + added_mod + added_class, "added_class_attrs": added_class, "errors": errors,
            "covered": covered}


if __name__ == "__main__":
    _snapshot_main(sys.argv[1], sys.argv[2], sys.argv[3])
