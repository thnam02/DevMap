"""Diagnosis for v2.4 planning, selection only, from saved B1 maps (no test runs; Proviso's src untouched: its functions are
called read-only, and the per-value reader rule of impact._selection is restated here to count tests per value).

  python research/v2/v24_diagnosis.py datasette ID [ID ...]     # part 1 -> $PROVISO_WORK/datasette/v24/<id>.json
  python research/v2/v24_diagnosis.py sqlglot                   # part 2 -> $PROVISO_WORK/sqlglot/v24/sqlglot.json
  python research/v2/v24_diagnosis.py write                     # results/b1/V24_DIAGNOSIS.md from the two

Part 1 (datasette, maps of the superseded first run): per pair, scenario S (the commit's source changes on P), the
import-time values Proviso reports as changed (why["import_state_changed"]); for each: kind (module value / class
attribute / import binding), old and new fingerprint prefix (importstate snapshots of P and of the changed tree), and
the tests it links to (tests reaching code that names it or its callers, as impact._selection; class attributes only in
tests that use the class; plus tests whose file names a module value). Root causes: both versions of each value are
walked (a separate import of P and of the changed tree, same fingerprint rules as importstate: lambdas, closures and
wrappers by code, named functions by name, data by value) and the differing leaves compared; a leaf difference shared
by many values is one root cause. Each cause is matched against the commit's diff.

Part 2 (sqlglot): the 15 slowest tests (b1_time_concentration's ranking) and, per pair, whether ValueRTS (proviso) and
testmon selected each (from b1_time_concentration's recomputed selections). For pairs where ValueRTS selects
test_execute_tpcds and testmon does not: why ValueRTS selected it (changed function it reaches, and through which record;
changed import-time value; class rule; always-run record; test file naming a value) and whether testmon's data says the
test executed the changed lines (testmon's blocks of the old file that contain a changed line, against the block
checksums testmon stored for that test)."""
from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as IS  # noqa: E402

TPCDS = "tests/test_executor.py::TestExecutor::test_execute_tpcds"
MAX_LOAD = float(os.environ.get("V24_MAX_LOAD", "9"))


def wait_load():
    while os.getloadavg()[0] > MAX_LOAD:
        time.sleep(60)


# ------------------------------------------------------------------------------------------- tests per changed value

class Links:
    """impact._selection's reader rule (lines 'a changed value is read by code that names it ...'), per key."""

    def __init__(self, tree, cov):
        self.tree, self.cov = tree, cov
        self.base, _ = I.map_base(tree, cov)
        with I._measured_from(self.base):
            pk = I.packages(cov)
            diff = I._git(tree, "diff", "-U0", I._BASE, "--", *pk)
            self.idx = I._name_index(tree, sorted(I.map_files(cov)))
            self.prefix = I._layout_prefix(I.map_files(cov))
            changed_src = {f for f in I._changed_old_lines(diff) if not I._is_test_path(f)}
            self.bindings = I._import_bindings(tree, changed_src)
        self.by_name = {}
        for fl, ns in self.idx.items():
            for n in ns:
                self.by_name.setdefault(n, set()).add(fl)
        self.def_name = {fl: n[4:] for fl, ns in self.idx.items() for n in ns if n.startswith("def:")}
        self.dep = I._DepView(cov)
        self.names = {}

    def readers_of(self, attr, only_file=None):
        by_name, idx = self.by_name, self.idx
        direct = set(by_name.get(attr, set()))
        if only_file is not None:
            direct = {fl for fl in direct if fl[0] == only_file}
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
        calls = {"call:" + self.def_name[fl] for fl in direct if fl in self.def_name
                 and not (self.def_name[fl].startswith("__") and self.def_name[fl].endswith("__"))}
        return direct | {fl for c in calls for fl in by_name.get(c, set())}

    def file_names(self, node):
        f = node.split("::", 1)[0]
        if f not in self.names:
            self.names[f] = I._file_names(os.path.join(self.tree, f))
        return self.names[f]

    def kind(self, key):
        cls = I._key_class(key, self.prefix)
        if cls is not None:
            return "class attribute", cls
        kf = I._key_module_file(key, self.prefix, set(self.bindings))
        attr = key.rsplit(":", 1)[1].rsplit(".", 1)[-1]
        if kf is not None and attr in self.bindings[kf]:
            return "import binding", kf
        return "module value", None

    def tests(self, key):
        kind, where = self.kind(key)
        attr = key.rsplit(":", 1)[1].rsplit(".", 1)[-1]
        with I._measured_from(self.base):
            fl = self.readers_of(attr, only_file=where if kind == "import binding" else None)
        dep, out = self.dep, set()
        classes = {where, where.replace("/__init__.py:", ".py:")} if kind == "class attribute" else set()
        for node in dep.tests:
            if kind == "class attribute":
                if dep.classes(node) & classes and (dep.reaches(node, fl, ("k", key)) or attr in self.file_names(node)):
                    out.add(node)
            elif dep.reaches(node, fl, ("k", key)) or (kind == "module value" and attr in self.file_names(node)):
                out.add(node)
        return kind, out, len(fl)


# ------------------------------------------------------------------------------------------- value walker (subprocess)

WALKER = r'''
import sys, json, importlib, types, hashlib, functools, re, os, logging, warnings
tree, keys_path, out_path = sys.argv[1:4]
os.chdir(tree)
TREE_NAME = os.path.basename(os.path.abspath(tree))
def lf(kind, text, owner):
    # short text, hash of the full text, hash with digit runs replaced (object ids), hash with the tree's folder name
    # replaced (location); the parent tells id-only and location-only differences apart from real ones
    hs = lambda s: hashlib.sha1(s.encode()).hexdigest()[:10]
    return [kind, text[:120], owner, hs(text), hs(re.sub(r"\d+", "N", text)), hs(text.replace(TREE_NAME, "<tree>"))]
logging.disable(logging.CRITICAL)
warnings.filterwarnings("ignore")
sys.setrecursionlimit(10000)
import random
random.seed(0)
addr = re.compile(r" at 0x[0-9a-fA-F]+")
root = os.path.realpath(tree)
unroot = lambda s: s.replace(root, "<root>").replace(os.path.abspath(tree), "<root>")
def code_hash(co, h):
    h.update(co.co_code); h.update(repr(co.co_names).encode())
    for c in co.co_consts:
        code_hash(c, h) if isinstance(c, types.CodeType) else h.update(addr.sub("", repr(c)).encode())
LIMIT = 6000
def walk(v, path, depth, seen, acc, owner):
    if len(acc) > LIMIT:
        acc["<truncated>"] = ["truncated", "", owner]; return
    t = type(v)
    if t is str:
        acc[path] = lf("str", unroot(repr(v)), owner); return
    if v is None or t in (bool, int, float, complex, bytes):
        acc[path] = lf(t.__name__, repr(v), owner); return
    if depth > 12:
        acc[path] = ["deep", t.__name__, owner]; return
    if isinstance(v, os._Environ):
        acc[path] = ["environ", "", owner]; return
    if isinstance(v, logging.Logger):
        acc[path] = ["logger", f"{v.name}:{v.level}", owner]; return
    if isinstance(v, types.FunctionType):
        q = f"{v.__module__}.{v.__qualname__}"
        wrapper = hasattr(v, "__wrapped__") or getattr(v.__code__, "co_qualname", v.__qualname__) != v.__qualname__
        if "<" in v.__qualname__ or wrapper:
            h = hashlib.sha1(); code_hash(v.__code__, h)
            acc[path + "#code"] = ["fn-code", q + " " + h.hexdigest()[:10], q]
            for i, d in enumerate(v.__defaults__ or ()):
                walk(d, f"{path}.__defaults__[{i}]", depth + 1, seen, acc, q)
            for name, cell in zip(v.__code__.co_freevars, v.__closure__ or ()):
                try:
                    walk(cell.cell_contents, f"{path}.<{name}>", depth + 1, seen, acc, q)
                except ValueError:
                    acc[f"{path}.<{name}>"] = ["empty-cell", "", q]
        else:
            acc[path] = ["fn", q, owner]
        return
    if isinstance(v, functools.partial):
        walk(v.func, path + ".func", depth + 1, seen, acc, "partial")
        walk(v.args, path + ".args", depth + 1, seen, acc, "partial")
        walk(dict(v.keywords or {}), path + ".kw", depth + 1, seen, acc, "partial"); return
    if isinstance(v, (types.BuiltinFunctionType, types.MethodWrapperType, types.WrapperDescriptorType)):
        acc[path] = ["bf", getattr(v, "__qualname__", repr(v)), owner]; return
    if isinstance(v, (classmethod, staticmethod)):
        walk(v.__func__, path + "." + t.__name__, depth + 1, seen, acc, owner); return
    if isinstance(v, property):
        for n in ("fget", "fset", "fdel"):
            walk(getattr(v, n), f"{path}.{n}", depth + 1, seen, acc, owner)
        return
    if isinstance(v, type):
        acc[path] = ["cls", f"{v.__module__}.{v.__qualname__}", owner]; return
    if isinstance(v, types.ModuleType):
        acc[path] = ["mod", v.__name__, owner]; return
    if isinstance(v, types.MethodType):
        walk(v.__func__, path + ".__func__", depth + 1, seen, acc, owner); return
    if id(v) in seen:
        acc[path] = ["cycle", t.__name__, owner]; return
    seen = seen | {id(v)}
    if isinstance(v, (list, tuple)):
        acc[path + "#len"] = ["len", str(len(v)), owner]
        for i, x in enumerate(v):
            walk(x, f"{path}[{i}]", depth + 1, seen, acc, owner)
        return
    if isinstance(v, (set, frozenset)):
        acc[path + "#len"] = ["len", str(len(v)), owner]
        for x in sorted(v, key=lambda x: repr(x)):
            walk(x, f"{path}{{{addr.sub('', repr(x))[:50]}}}", depth + 1, seen, acc, owner)
        return
    if isinstance(v, dict):
        acc[path + "#len"] = ["len", str(len(v)), owner]
        for k, x in list(v.items()):
            walk(x, f"{path}[{addr.sub('', repr(k))[:60]}]", depth + 1, seen, acc, owner)
        return
    try:
        d = vars(v)
    except TypeError:
        d = None
    slots = [n for c in t.__mro__ for n in (getattr(c, "__slots__", ()) or ()) if isinstance(n, str) and n not in ("__dict__", "__weakref__")]
    if d is not None or slots:
        tn = f"{t.__module__}.{t.__qualname__}"
        acc[path + "#type"] = ["obj", tn, owner]
        state = dict(d or {})
        for n in slots:
            if hasattr(v, n):
                state["slot:" + n] = getattr(v, n)
        for k, x in state.items():
            walk(x, f"{path}.{k}", depth + 1, seen, acc, tn)
        return
    try:
        r = repr(v)
    except Exception:
        r = "<unrepr>"
    acc[path] = lf("repr", f"{t.__module__}.{t.__qualname__}:{unroot(addr.sub('', r))}", owner)
out = {}
for key in json.load(open(keys_path)):
    mod, qual = key.split(":", 1)
    try:
        obj = importlib.import_module(mod)
        parts = qual.split(".")
        for i, p in enumerate(parts):
            if p == "__mro__" and i == len(parts) - 1:
                obj = obj.__mro__
            elif p == "__class__" and i == len(parts) - 1:
                obj = type(obj)
            else:
                obj = vars(obj)[p] if p in vars(obj) else getattr(obj, p)
        acc = {}
        walk(obj, "", 0, frozenset(), acc, key)
        out[key] = acc
    except BaseException as e:
        out[key] = {"<error>": ["error", f"{type(e).__name__}: {e}"[:200], key]}
json.dump(out, open(out_path, "w"))
'''


def walk_values(tree, keys):
    with tempfile.TemporaryDirectory() as t:
        kp, op, wp = (os.path.join(t, n) for n in ("keys.json", "out.json", "walker.py"))
        json.dump(sorted(keys), open(kp, "w"))
        open(wp, "w").write(WALKER)
        r = subprocess.run([PL.PY, wp, tree, kp, op], cwd=tree, env=PL.env(tree), capture_output=True, text=True,
                           timeout=1800)
        if r.returncode:
            raise RuntimeError("walker: " + r.stderr[-500:])
        return json.load(open(op))


def norm(path):
    return re.sub(r"\[\d+\]", "[#]", path)


def _owner(o, key):
    return "<the value>" if o == key else o


def leaf_diff(old, new, key=""):
    """[(token, detail, cls)] of the differing leaves of one value; token = what to group by across values; cls =
    'location' (differs only by the tree's folder name), 'ids' (only by digit runs: object ids, counters) or 'real'."""
    out = []
    for p in sorted(set(old) | set(new)):
        a, b = old.get(p), new.get(p)
        if a == b:
            continue
        if a and b and len(a) == 6 and len(b) == 6 and a[0] == b[0]:
            last = norm(p).rsplit(".", 1)[-1][-50:] or "(the value itself)"
            own = _owner(b[2], key)
            if a[3] == b[3]:
                continue
            if a[5] == b[5]:
                out.append((f"tree location inside {own} {last}", f"{p}: {a[1][:70]} -> {b[1][:70]}", "location"))
                continue
            if a[4] == b[4]:
                out.append((f"object ids inside {own} {last}", f"{p}: {a[1][:70]} -> {b[1][:70]}", "ids"))
                continue
        if a and b and a[0] == "fn-code" and b[0] == "fn-code":
            q = b[2]
            out.append((f"code of {q}", f"{p}: {a[1].split()[-1]} -> {b[1].split()[-1]}", "real"))
        elif a and b:
            last = norm(p).rsplit(".", 1)[-1][-60:]
            out.append((f"{_owner(b[2], key)} {last}: {a[1][:60]} -> {b[1][:60]}",
                        f"{p}: {a[0]} {a[1][:80]} -> {b[0]} {b[1][:80]}", "real"))
        elif b:
            out.append((f"{_owner(b[2], key)}: added {norm(p).rsplit('.', 1)[-1][-60:]}",
                        f"{p}: added {b[0]} {b[1][:80]}", "real"))
        else:
            out.append((f"{_owner(a[2], key)}: removed {norm(p).rsplit('.', 1)[-1][-60:]}",
                        f"{p}: removed {a[0]} {a[1][:80]}", "real"))
    return out


def cover(groups, keys):
    """Greedy cover: fewest leaf-difference tokens explaining every value (an estimate of distinct root causes)."""
    left, picked = set(keys), []
    while left:
        tok = max(groups, key=lambda t: len(groups[t] & left), default=None)
        if tok is None or not groups[tok] & left:
            break
        picked.append((tok, len(groups[tok] & left)))
        left -= groups[tok]
    return picked, left


def diff_hits(tree, base, tokens, pk):
    """For each cause token: lines of the commit's diff (old -> new, package files) that name its function/attribute."""
    d = subprocess.run(["git", "-C", tree, "diff", "-U0", base, "--", *pk], capture_output=True, text=True).stdout
    lines = [l for l in d.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    files = [l[6:] for l in d.splitlines() if l.startswith("+++ b/")]
    stop = {"code", "added", "removed", "datasette", "None", "str", "int", "obj", "self", "repr", "dict", "list"}
    out = {}
    for tok in tokens:
        words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", tok)) - stop
        out[tok] = [l[:160] for l in lines if any(re.search(rf"\b{re.escape(w)}\b", l) for w in words)][:6]
    return out, files


def part1(ids):
    b1.use("datasette")
    sup = {json.loads(l)["id"][:12]: json.loads(l) for l in open(os.path.join(b1.res(), "superseded.jsonl")) if l.strip()}
    outdir = os.path.join(PL.WORK, "v24")
    os.makedirs(outdir, exist_ok=True)
    for i in ids:
        r = sup[i[:12]]
        p, c = r["parent"], r["id"]
        out = os.path.join(outdir, f"{c[:12]}.json")
        if os.path.exists(out):
            continue
        wait_load()
        t0 = time.time()
        cov = PL.jload(os.path.join(PL.WORK, "b1.superseded-20261128", c[:12], "covmap.json"))
        old_tree = PL.make_tree("v24-old", p)
        tree = PL.make_tree("v24", p)
        b1.use_targets(tree)
        b1.apply_source(tree, p, c)
        sel, why = I.selection(tree, cov, PL.PY)
        keys = why.get("import_state_changed", [])
        files = I._snapshot_files(cov)
        with tempfile.TemporaryDirectory() as tmp:
            base_snap = IS.base_snapshot(tree, files, PL.PY, os.path.join(tmp, "b.json"), rev=p)
        cur_snap = IS.snapshot(tree, files, PL.PY)
        # no-change baseline: the same parent checked out at another path, compared with the base snapshot exactly
        # as selection compares the changed tree; whatever differs here is not caused by the commit
        old_snap = IS.snapshot(old_tree, files, PL.PY)
        noise = set(IS.diff(base_snap, old_snap)["changed"]) if base_snap and old_snap else set()
        unstable = set((base_snap or {}).get("unstable", []))
        links = Links(tree, cov)
        vals, tsets = {}, {}
        for k in keys:
            kind, tests, nread = links.tests(k)
            tsets[k] = tests
            vals[k] = {"kind": kind, "old": ((base_snap or {}).get("state") or {}).get(k),
                       "new": ((cur_snap or {}).get("state") or {}).get(k), "tests": len(tests), "readers": nread,
                       "no_change_baseline_differs": k in noise, "unstable_in_base_samples": k in unstable}
        old_w, new_w = walk_values(old_tree, keys), walk_values(tree, keys)
        groups, per_key = {"real": {}, "noise": {}}, {}
        for k in keys:
            ld = leaf_diff(old_w.get(k, {}), new_w.get(k, {}), k)
            per_key[k] = [(t, d) for t, d, _ in ld[:8]]
            cls = {x for _, _, x in ld}
            vals[k]["leaf_class"] = ("real" if "real" in cls else "location" if "location" in cls else
                                     "ids" if "ids" in cls else "no leaf difference found")
            g = groups["noise" if k in noise else "real"]
            for tok, _, x in ld:
                if k in noise or x == "real":
                    g.setdefault(tok, set()).add(k)
        real_keys = [k for k in keys if k not in noise]
        cov_real, left_real = cover(groups["real"], real_keys)
        cov_noise, left_noise = cover(groups["noise"], [k for k in keys if k in noise])
        hits, chfiles = diff_hits(tree, p, [t for t, _ in cov_real[:12]], I.packages(cov))
        u = lambda ks: set().union(*(tsets[k] for k in ks)) if ks else set()
        commit = PL.git(tree, "log", "-1", "--format=%h %s", c).strip()
        res = {"id": c, "parent": p, "commit": commit, "selected": None if sel is None else len(sel),
               "universe": r.get("universe"), "changed_functions": why.get("changed_functions"),
               "files": why.get("files"), "import_state_n": why.get("import_state_n"), "values": vals,
               "noise_n": len(noise & set(keys)), "noise_baseline_total": len(noise), "unstable_n": len(unstable),
               "tests_linked_noise": len(u([k for k in keys if k in noise])), "tests_linked_real": len(u(real_keys)),
               "tests_linked_noise_only": len(u([k for k in keys if k in noise]) - u(real_keys)),
               "per_key": per_key, "groups": {g: {t: sorted(v) for t, v in d.items()} for g, d in groups.items()},
               "cover_real": cov_real, "unexplained_real": sorted(left_real), "cover_noise": cov_noise,
               "unexplained_noise": sorted(left_noise), "diff_hits": hits, "changed_files": chfiles,
               "secs": round(time.time() - t0)}
        PL.jdump(res, out)
        print(time.strftime("%H:%M:%S"), c[:10], f"{len(keys)} values: {res['noise_n']} also differ with no change, "
              f"{len(real_keys)} real ({len(cov_real)} causes, {len(left_real)} unexplained); tests linked: noise "
              f"{res['tests_linked_noise']} (only noise {res['tests_linked_noise_only']}), real "
              f"{res['tests_linked_real']} ({res['secs']} s)", flush=True)
        b1.to_parent(tree, p)


# ------------------------------------------------------------------------------------------- part 2: sqlglot

def testmon_view(db, node, tree, p, diff_lines):
    """Per changed file: did testmon record the test running it, and did it run a block holding a changed line."""
    from testmon.process_code import Module, blob_to_checksums, methods_to_checksums
    con = sqlite3.connect(db)
    te = con.execute("select id from test_execution where test_name = ?", (node,)).fetchall()
    if not te:
        return {"recorded": False}
    fps = con.execute("select f.filename, f.method_checksums from test_execution_file_fp tf join file_fp f "
                      "on f.id = tf.fingerprint_id where tf.test_execution_id = ?", (te[0][0],)).fetchall()
    con.close()
    stored = {fn: set(blob_to_checksums(b)) for fn, b in fps}
    out = {"recorded": True, "files_recorded": len(stored), "changed": {}}
    for f, lines in diff_lines.items():
        src = subprocess.run(["git", "-C", tree, "show", f"{p}:{f}"], capture_output=True, text=True).stdout
        try:
            new = open(os.path.join(tree, f)).read()
        except OSError:
            new = ""
        mod = Module(source_code=src, ext="py")
        blocks = mod.blocks
        hit = []
        for ln in sorted(lines):
            inner = [b for b in blocks if b.start <= ln <= b.end]
            if not inner:
                continue
            b = min(inner, key=lambda b: b.end - b.start)
            cs = methods_to_checksums([b.code])[0]
            hit.append((ln, b.name, b.start, b.end, cs in stored.get(f, set())))
        new_cs = set(Module(source_code=new, ext="py").checksums) if new else set()
        out["changed"][f] = {"file_recorded": f in stored, "blocks_recorded": len(stored.get(f, ())),
                             "changed_lines_in_blocks": [
                                 {"line": ln, "block": nm, "range": f"{s}-{e}", "test_ran_block": ran}
                                 for ln, nm, s, e, ran in hit][:12],
                             "testmon_still_matches": (stored.get(f, set()) <= new_cs) if f in stored else None}
    return out


def why_tpcds(tree, cov, why, node):
    dep = I._DepView(cov)
    v = dep.tests.get(node) or {}
    own = dep.own(node) if node in dep.tests else set()
    out = {"always": dep.always(node) if node in dep.tests else None, "functions": [], "values": [], "classes": None}
    for f, ln in why.get("changed_functions", []):
        via = []
        if (f, ln) in own:
            via.append("own call")
        for k in v.get("fx", ()):
            if k in dep.fx and (f, ln) in dep.fx[k][0]:
                via.append(k)
        if via:
            out["functions"].append({"function": f"{f}:{ln}", "via": via[:6]})
    keys = why.get("import_state_changed", [])
    if keys:
        links = Links(tree, cov)
        for k in keys:
            kind, tests, _ = links.tests(k)
            if node in tests:
                out["values"].append({"key": k, "kind": kind})
    out["shared_test_code"] = why.get("shared_test_code")
    out["agent_tests"] = [t for t in why.get("agent_tests", []) if node.startswith(t)]
    return out


def func_name(tree, p, f, ln):
    src = subprocess.run(["git", "-C", tree, "show", f"{p}:{f}"], capture_output=True, text=True).stdout
    try:
        units, _ = I._units(f, src)
    except Exception:  # noqa: BLE001
        return f"{f}:{ln}"
    for u in units:
        if u[1] == ln:
            return f"{f}:{ln} {u[0] if isinstance(u[0], str) else ''}".strip()
    return f"{f}:{ln}"


def part2():
    b1.use("sqlglot")
    import b1_time_concentration as TC
    per, total, n = TC.durations("sqlglot")
    top = TC.ranked(per)[:15]
    tcdir = os.path.join(PL.WORK, "time_concentration")
    rows = TC.ok_rows("sqlglot")
    matrix, cases = [], []
    for r in rows:
        g = PL.jload(os.path.join(tcdir, f"{r['id'][:12]}.json")) or {}
        sel = g.get("sel") or {}
        m = {"id": r["id"][:10]}
        for sc in ("S", "F"):
            s = sel.get(sc) or {}
            pv, tm = s.get("proviso"), s.get("testmon")
            m[sc] = "".join(("B" if (t in pv and t in tm) else "V" if t in pv else "T" if t in tm else ".")
                            if isinstance(pv, list) and isinstance(tm, list) else "?" for t in top)
            if isinstance(pv, list) and isinstance(tm, list) and TPCDS in pv and TPCDS not in tm:
                cases.append((r, sc))
        matrix.append(m)
    out = {"top": [(t, sum(per[t]) / total) for t in top], "matrix": matrix, "cases": []}
    for r, sc in cases:
        wait_load()
        p, c = r["parent"], r["id"]
        d = os.path.join(PL.WORK, "b1", c[:12])
        cov = PL.jload(os.path.join(d, "covmap.json"))
        tree = PL.make_tree("v24", p)
        b1.use_targets(tree)
        if sc == "S":
            b1.apply_source(tree, p, c)
        else:
            b1.apply_full(tree, p, c)
        sel, why = I.selection(tree, cov, PL.PY)
        diff = PL.git(tree, "diff", "-U0", p, "--", *I.packages(cov))
        dl = {f: l for f, l in I._changed_old_lines(diff).items() if not I._is_test_path(f) and f.endswith(".py")}
        w = why_tpcds(tree, cov, why, TPCDS)
        for x in w["functions"]:
            f, ln = x["function"].rsplit(":", 1)
            x["function"] = func_name(tree, p, f, int(ln))
        tmv = testmon_view(os.path.join(d, "testmondata"), TPCDS, tree, p, dl)
        out["cases"].append({"id": c[:10], "scenario": sc, "commit": PL.git(tree, "log", "-1", "--format=%s", c)
                             .strip()[:90], "proviso_selected": None if sel is None else len(sel),
                             "proviso_reason": why.get("reason"), "changed_functions": len(why.get("changed_functions", [])),
                             "import_state_n": why.get("import_state_n"), "module_level_files": why.get("files"),
                             "why_tpcds": w, "testmon": tmv})
        print(time.strftime("%H:%M:%S"), c[:10], sc, "why:", {k: (len(v) if isinstance(v, list) else v)
                                                            for k, v in w.items()}, flush=True)
        b1.to_parent(tree, p)
    os.makedirs(os.path.join(PL.WORK, "v24"), exist_ok=True)
    PL.jdump(out, os.path.join(PL.WORK, "v24", "sqlglot.json"))


def part3(name, n=3):
    """No-change baseline on a finished project: for n ok pairs (first, middle, last by rank), ValueRTS's own base
    snapshot of the parent (importstate.base_snapshot: an export, 9 samples) against a snapshot of the same parent
    checked out in a second folder, compared with importstate.diff exactly as selection does. Expected: nothing."""
    b1.use(name)
    rows = sorted((r for r in b1.rows(name).values() if r.get("status") == "ok"), key=lambda r: r.get("rank", 0))
    pick = [rows[0], rows[len(rows) // 2], rows[-1]][:n] if len(rows) >= 3 else rows
    out = []
    for r in pick:
        wait_load()
        p, c = r["parent"], r["id"]
        t0 = time.time()
        cov = PL.jload(os.path.join(PL.WORK, "b1", c[:12], "covmap.json"))
        root = PL.make_tree("v24", p)
        second = PL.make_tree("v24-second", p)
        files = I._snapshot_files(cov)
        with tempfile.TemporaryDirectory() as tmp:
            base = IS.base_snapshot(root, files, PL.PY, os.path.join(tmp, "b.json"), rev=p)
        snap = IS.snapshot(second, files, PL.PY)
        if base is None or snap is None:
            out.append({"id": c[:10], "error": "snapshot failed", "base": base is not None, "second": snap is not None})
            continue
        d = IS.diff(base, snap)
        ch = d["changed"]
        out.append({"id": c[:10], "parent": p[:10], "values": len(base["state"]), "unstable": len(base.get("unstable", [])),
                    "samples": base.get("unstable_samples"), "differ": len(ch), "keys": ch[:200],
                    "fingerprints": {k: [base["state"].get(k), snap["state"].get(k)] for k in ch[:50]},
                    "errors": d["errors"], "secs": round(time.time() - t0)})
        print(time.strftime("%H:%M:%S"), name, c[:10], f"{len(base['state'])} values, {len(ch)} differ with no change "
              f"({out[-1]['secs']} s)", flush=True)
    os.makedirs(os.path.join(PL.WORK, "v24"), exist_ok=True)
    PL.jdump({"project": name, "python": PL.PY, "pairs": out}, os.path.join(PL.WORK, "v24", "nochange.json"))


def write():
    import collections
    W = PL.BASE_WORK
    L = ["# V2.4 diagnosis: datasette's import-time values and sqlglot's slowest tests", "",
         "Selection only, from saved B1 maps; no test was run and Proviso's src was not changed. Produced by "
         "`research/v2/v24_diagnosis.py` (per-pair data in `$PROVISO_WORK/datasette/v24/` and "
         "`$PROVISO_WORK/sqlglot/v24/`).", ""]
    # ---------------------------------------------------------------- part 1
    ds = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(W, "datasette", "v24", "*.json")))]
    by = {d["id"][:10]: d for d in ds}
    g = lambda i, k: by[i][k] if i in by else "?"
    L += ["## Summary (interpretation of the data below)", "",
          "**datasette, 5 pairs with more than 80 changed values.**",
          f"- **Not caused by the commit:** 84 of the changed values differ with no code change at all, and they are "
          f"the same 84 in every pair.",
          f"  - **Selection noise.** One of them, `datasette.app:app_root`, a `pathlib.Path`, carries the tree's "
          f"location in its cached path parts (`_tail_cached`). importstate unroots strings but not those parts, and "
          f"the base snapshot is taken from a temporary export while the current one is taken from the working tree. "
          f"So the value always differs, and it links about 2,170-2,190 tests, about 77% of the suite. In d0836ddedc "
          f"(remove a backport), {g('d0836ddedc', 'tests_linked_noise_only')} of the "
          f"{g('d0836ddedc', 'selected')} selected tests come from it alone; the real change links "
          f"{g('d0836ddedc', 'tests_linked_real')}. In e1a4e03635, {g('e1a4e03635', 'tests_linked_noise_only')} of "
          f"{g('e1a4e03635', 'selected')}.",
          "  - **Count noise.** The other 83 (82 attributes of 25 pydantic models: schema refs, validators and "
          "serializers built with per-process object ids; plus FAVICON_PATH, another Path) link no tests or 1 test. "
          "They do count toward the changed-value limit that switches to the full suite.",
          "- **Caused by the commit:** the real changes reduce to a few root causes, each fanning out to many values:",
          "  1. a slot added to a class whose instances are module constants (05ca128c02: `Attribute` gains "
          "`values`, `SpanName` gains `prefix`). One class edit changes 86 registry constants, each linking about "
          "2,100 tests;",
          "  2. edited description strings stored inside such constants (287e8ba3b2: 66 values from about 25 text "
          "edits in one commit);",
          "  3. docstring and comment text copied into values (8e17729ff3, a comments-only commit): pytest's fixture "
          "definitions carry `__doc__`, and an OpenTelemetry instrument carries its description. These link every test "
          "through autouse telemetry fixtures, so the whole suite was selected for an edit that changes no behaviour;",
          "  4. one changed lambda shared by 24 dataclasses (e1a4e03635: `default_factory=lambda: datetime.now(UTC)`);",
          "  5. a changed import binding plus a removed module (d0836ddedc: `copytree`, 27 tests).",
          "",
          "**sqlglot, test_execute_tpcds** (38% of test time).",
          "- **Why ValueRTS selects it:** ValueRTS selects it in 50 of 52 pairs; testmon in 26-27. In every pair where "
          "ValueRTS selects it and testmon does not, ValueRTS's reason is the always rule: the test runs its queries in "
          "a process pool, and the recorder cannot see worker code.",
          "- **What testmon's data shows:** testmon never recorded the test running a changed line. It records only "
          "the parent process, which just parses the queries.",
          "- **Only 2 of the 25 pairs** link the test to the change through the map itself:",
          "  - a6698b765b: the edited function `build_formatted_time`, whose nested closure holds the edit. testmon "
          "shows the closure body was not run in the parent process;",
          "  - 5fc93a9eab: changed function-registry tables, when a new function class was added.",
          ""]
    L += ["## 1. datasette: import-time values reported as changed", "",
          "Pairs: 5 of the 24 (of 40 ok) first-run pairs (maps of the superseded run) whose scenario S reported more "
          "than 80 changed values, chosen to span 86-176 values and different kinds of commit. Per pair, Proviso's selection was re-run on a tree at the parent with the commit's source "
          "changes, and the changed values taken from its reason (`import_state_changed`).", "",
          "**No-change baseline.** The same parent was also checked out at a second path and snapshotted, then "
          "compared with Proviso's base snapshot of the parent exactly as selection compares the changed tree. A value "
          "that differs there differs without any code change.", "",
          "| Pair | Commit | Changed values | Also differ with no change | Real | Real causes (greedy cover) | "
          "Tests linked by no-change values | ... by them only | Tests linked by real values | Proviso selected / universe |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for d in ds:
        n = len(d["values"])
        L.append(f"| {d['id'][:10]} | {d['commit'].split(' ', 1)[1][:60]} | {n} | {d['noise_n']} | {n - d['noise_n']} | "
                 f"{len(d['cover_real'])} | {d['tests_linked_noise']} | {d['tests_linked_noise_only']} | "
                 f"{d['tests_linked_real']} | {d['selected']} / {d['universe']} |")
    noise_sets = [{k for k, v in d["values"].items() if v["no_change_baseline_differs"]} for d in ds]
    same = all(s == noise_sets[0] for s in noise_sets)
    d0 = ds[0]
    nz = sorted(noise_sets[0])
    kinds = collections.Counter(d0["values"][k]["kind"] for k in nz)
    L += ["", f"The no-change values are the same {len(nz)} in every pair ({'identical sets' if same else 'sets differ'}): "
          + ", ".join(f"{v} {k}" for k, v in kinds.items()) + ". Grouped by the leaf that differs:", "",
          "| Values | What differs (both versions walked with importstate's fingerprint rules) | Tests linked |",
          "|---|---|---|"]
    for tok, cnt in d0["cover_noise"]:
        ks = d0["groups"]["noise"].get(tok, [])
        L.append(f"| {cnt} | {tok[:150]} | {max((d0['values'][k]['tests'] for k in ks), default=0)} (max) |")
    if d0["unexplained_noise"]:
        L.append(f"| {len(d0['unexplained_noise'])} | no leaf difference found by the walker: "
                 f"{', '.join(d0['unexplained_noise'][:4])} | |")
    top = sorted(nz, key=lambda k: -d0["values"][k]["tests"])[:3]
    L += ["", "No-change values linking the most tests: " + "; ".join(
        f"`{k}` ({d0['values'][k]['kind']}, {d0['values'][k]['tests']} tests, fingerprint {d0['values'][k]['old']} -> "
        f"{d0['values'][k]['new']})" for k in top) + ".", "",
          "### Per-pair real causes", ""]
    for d in ds:
        real = [k for k, v in d["values"].items() if not v["no_change_baseline_differs"]]
        L += [f"**{d['id'][:10]}** {d['commit'].split(' ', 1)[1][:90]} - changed functions "
              f"{len(d['changed_functions'] or [])}, module-level edits in {', '.join(d['files'] or []) or 'none'}; "
              f"{len(real)} real values, {len(d['cover_real'])} causes:", ""]
        for tok, cnt in d["cover_real"][:6]:
            ks = d["groups"]["real"].get(tok, [])
            mx = max((d["values"][k]["tests"] for k in ks), default=0)
            L.append(f"- {cnt} value(s): {tok[:160]} (up to {mx} tests per value)")
            for h in d["diff_hits"].get(tok, [])[:2]:
                L.append(f"  - diff: `{h[:140]}`")
        rk = sorted(real, key=lambda k: -d["values"][k]["tests"])[:4]
        L += ["- real values linking the most tests: " + "; ".join(
            f"`{k}` ({d['values'][k]['kind']}, {d['values'][k]['tests']})" for k in rk), ""]
    # ---------------------------------------------------------------- no-change baseline on other projects
    L += ["### No-change baseline on the other finished projects", "",
          "Same check, with no commit applied: ValueRTS's own base snapshot of the parent (`importstate.base_snapshot`: "
          "an export with 9 samples across 3 locations; values that vary between samples are marked unstable and "
          "compared without order) against a snapshot of the same parent checked out in a second folder, compared "
          "with `importstate.diff` as selection does. 3 ok pairs per project (first, middle and last by rank). "
          "Expected: no value differs.", "",
          "| Project | Pair (parent) | Values in the snapshot | Marked unstable | Differ with no change | Which |",
          "|---|---|---|---|---|---|"]
    for name in ("sqlglot", "pygments", "loguru"):
        nc = PL.jload(os.path.join(W, name, "v24", "nochange.json"))
        if not nc:
            L.append(f"| {name} | (not run yet: B1 still running on it) | | | | |")
            continue
        for x in nc["pairs"]:
            if "error" in x:
                L.append(f"| {name} | {x['id']} | {x['error']} | | | |")
                continue
            L.append(f"| {name} | {x['id']} ({x['parent']}) | {x['values']} | {x['unstable']} | {x['differ']} | "
                     + (", ".join(f"`{k}`" for k in x["keys"][:10]) or "-") + " |")
    dsn = len(noise_sets[0]) if noise_sets else 0
    L += ["", f"datasette, for comparison: {dsn} values differ with no change in each of its 5 pairs (above).", ""]
    # ---------------------------------------------------------------- part 2
    s = PL.jload(os.path.join(W, "sqlglot", "v24", "sqlglot.json"))
    L += ["## 2. sqlglot: the 15 slowest tests", "",
          "Ranking and shares from `results/b1/sqlglot/time_concentration.md` (each test's own duration in the plain "
          "run at the parent, summed over the 52 ok pairs). Per pair: B = selected by both ValueRTS and testmon, "
          "V = ValueRTS only, T = testmon only, . = neither; columns in rank order.", "",
          "| # | Test | Share of test time |", "|---|---|---|"]
    for k, (t, sh) in enumerate(s["top"], 1):
        L.append(f"| {k} | `{t}` | {100 * sh:.1f}% |")
    L += ["", "Tests 2, 4 and 8 (test_max_nodes, test_optimized_tpch, test_qualify_columns) fail at the parent in all "
          "52 pairs in this environment, so they are outside every tool's universe (failing tests are excluded); "
          "together they are about 24% of the summed test time.", "",
          "| Pair | S: 1..15 | F: 1..15 |", "|---|---|---|"]
    for m in s["matrix"]:
        L.append(f"| {m['id']} | `{m['S']}` | `{m['F']}` |")
    cases = s["cases"]
    pairs = sorted({x["id"] for x in cases})
    al = sum(x["why_tpcds"]["always"] for x in cases)
    fn = [x for x in cases if x["why_tpcds"]["functions"]]
    vl = [x for x in cases if x["why_tpcds"]["values"]]
    L += ["", f"### test_execute_tpcds selected by ValueRTS but not by testmon: {len(pairs)} pairs ({len(cases)} "
          "pair-scenarios)", "",
          f"- **Why ValueRTS selected it:** in all {len(cases)} cases the map marks the test *always* run "
          f"({al}/{len(cases)}). The test runs its queries in a `ProcessPoolExecutor` (`_mp_execute` in "
          "tests/test_executor.py), and the recorder marks any test that starts a process as always selected, because "
          "it cannot see the code the workers run. test_execute_tpch and test_canonicalize (test_optimizer's spawn "
          "pool) are the other always-run tests in the map.",
          f"- **Beyond the always rule:** in {len(fn)} case(s) the test also reaches a changed function in the parent "
          f"process, and in {len(vl)} through changed import-time values. In the other "
          f"{len(cases) - len({id(x) for x in fn + vl})} cases nothing in the test's own record or its fixtures "
          "reaches the change.", ""]
    for x in fn + vl:
        w = x["why_tpcds"]
        what = ("; ".join(f"{f['function']} via {', '.join(f['via'])}" for f in w["functions"]) or
                "; ".join(f"{v['key']} ({v['kind']})" for v in w["values"][:4]))
        L.append(f"  - {x['id']} {x['scenario']} ({x['commit'][:60]}): {what}")
    tm = collections.Counter()
    ran = []
    for x in cases:
        for f, v in (x["testmon"].get("changed") or {}).items():
            r_ = any(b["test_ran_block"] for b in v["changed_lines_in_blocks"])
            tm[(v["file_recorded"], r_)] += 1
            if r_:
                ran.append((x["id"], f))
    L += ["", "- **testmon's data about the changed lines.** For each changed source file in these cases, testmon's "
          "stored fingerprint for the test (parent process only) was checked against testmon's blocks of the old file "
          "that contain a changed line:",
          f"  - file not in the test's testmon record: {tm[(False, False)]} file-cases;",
          f"  - file recorded, but no block holding a changed line among the blocks the test ran: {tm[(True, False)]} "
          "(testmon's fingerprint for the file still matches the new code);",
          f"  - a block holding a changed line was run by the test: {tm[(True, True)]}"
          + (f" ({', '.join(f'{i} {f}' for i, f in ran[:5])})" if ran else "") + ".",
          "  - So by testmon's data the test never executed the changed lines in the parent process. Its parent side "
          "only parses the queries; execution happens in the workers, which testmon (coverage without subprocess "
          "tracking) does not record either. Where the workers run changed code, testmon's skip is unsafe; "
          "ValueRTS's always rule is safe but costs 27 s (38% of the suite's test time) on each of these pairs."]
    open(os.path.join(b1.OUT, "V24_DIAGNOSIS.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    a = sys.argv[1:]
    if a[0] == "datasette":
        part1(a[1:])
    elif a[0] == "sqlglot":
        part2()
    elif a[0] == "nochange":
        part3(a[1])
    elif a[0] == "write":
        write()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
