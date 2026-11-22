"""Incremental recording (Proviso v2.4): bring a coverage map recorded at an earlier commit up to the current one by
re-recording only the test files that can have changed, instead of the whole suite.

Why keeping the other records is safe (the argument Ekstazi uses for its online mode): a test that selection skipped
ran no changed function, read no changed file and reads no changed import-time value, so it would run as it did at
the map's commit and its record still describes it. Two things do change for it:
  - line numbers: a function is recorded as (file, first line), and an edit above it moves it. Every kept function key
    in a changed file is moved along the unchanged lines of the file (difflib's equal blocks); a key whose line was
    itself edited or deleted cannot be moved, so the tests that depend on it are re-recorded instead of guessed.
  - new tests: test files that pytest now collects and the map does not know are recorded.
Re-recorded: every test file holding a selected test, every changed or new test file, every test file whose record
(or one of its fixture records) has a key that cannot be moved, and every test recorded as unrecorded. selected=None
(selection fell back to the whole suite) records everything again.

The global (import and collection) record keeps its moved keys; when one cannot be moved and no test file is
re-recorded, the cheapest test file is re-recorded to refresh it. Fixture records are moved like tests' records;
those used by re-recorded tests are united with their new recording (merge's rule for fixture records).

The import-time snapshot needs no hand-off here: the base snapshot is cached per commit (importstate), so the next
selection takes it at the new map's commit when a change touches import-time code.

  python -m dc_engine.incremental --root TREE --pkg PACKAGE_DIR --map OLD.json --selected SELECTED.json --out NEW.json
  python -m dc_engine.incremental --compare A.json B.json      # how two maps of the same commit differ
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
import tempfile
import time

from . import record as REC

VERSION = "2.4"


def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def _show(root: str, rev: str, path: str) -> str | None:
    p = subprocess.run(["git", "-C", root, "show", f"{rev}:{path}"], capture_output=True)
    return p.stdout.decode("utf-8", errors="replace") if p.returncode == 0 else None


def changed_paths(root: str, old: str, new: str) -> dict[str, str]:
    """{path: status letter} for every file that differs between two commits (a rename counts as delete + add)."""
    out = {}
    for line in _git(root, "diff", "--name-status", "--no-renames", old, new).splitlines():
        status, path = line.split("\t", 1)
        out[path] = status[0]
    return out


def line_map(old_src: str, new_src: str) -> dict[int, int]:
    """old line -> new line for each line that is unchanged between the two versions (1-based)."""
    a, b = old_src.splitlines(), new_src.splitlines()
    out = {}
    for tag, i1, i2, j1, _ in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k + 1] = j1 + k + 1
    return out


def _move(funcs, maps: dict, changed: set) -> tuple[list, bool]:
    """Function keys moved to their new lines; False when some key cannot be moved (its line was edited or its file
    deleted)."""
    out, ok = [], True
    for f, line in funcs:
        if f not in changed:
            out.append([f, line])
            continue
        m = maps.get(f)
        if m is None or line not in m:
            ok = False
            continue
        out.append([f, m[line]])
    return out, ok


def _test_file(nid: str) -> str:
    return nid.split("::", 1)[0]


def _record_env(env: dict | None) -> dict:
    e = dict(env or os.environ)
    e["PYTHONPATH"] = os.pathsep.join([REC.SRC, *[p for p in e.get("PYTHONPATH", "").split(os.pathsep) if p]])
    e.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return e


def update(covmap: dict, root: str, pkg: str, out: str, selected: list[str] | None, python: str | None = None,
           workers: int | None = None, before_test: str = "", extra_args: list[str] | None = None,
           env: dict | None = None, targets: list[str] | None = None) -> dict:
    """The map for root's HEAD, from covmap (recorded at an earlier commit) and the tests selection chose for the
    change between the two. Writes it to out and returns it; m["__incremental__"] says what was re-recorded.
    targets, before_test, extra_args and env: as given to record.record for the original map (the same test targets
    decide which test files exist)."""
    t0 = time.time()
    python = python or sys.executable
    base = covmap.get("__base__") or {}
    old = (base.get("commit") or "").strip()
    new = _git(root, "rev-parse", "HEAD").strip()
    dirty = bool(_git(root, "status", "--porcelain", "--untracked-files=no").strip())
    full_reason = None
    if selected is None:
        full_reason = "selection ran the whole suite"
    elif not old or base.get("dirty"):
        full_reason = "the map records no clean commit"
    elif subprocess.run(["git", "-C", root, "merge-base", "--is-ancestor", old, "HEAD"], capture_output=True).returncode:
        full_reason = "the map's commit is not an ancestor of HEAD"
    if full_reason:
        m = REC.record(root, pkg, out, python, targets, workers, before_test, extra_args, env)
        m["__incremental__"] = {"version": VERSION, "from": old, "full": full_reason, "seconds": round(time.time() - t0, 2)}
        json.dump(m, open(out, "w"))
        return m

    changes = changed_paths(root, old, new)
    py_changed = {p for p in changes if p.endswith(".py")}
    maps = {}
    for p in py_changed:
        a, b = _show(root, old, p), _show(root, new, p)
        if a is not None and b is not None:
            maps[p] = line_map(a, b)
    tests = {k: v for k, v in covmap.items() if not k.startswith("__")}
    known_files = {_test_file(n) for n in tests}

    why: dict[str, str] = {}
    for n in selected:
        why.setdefault(_test_file(n), "selected")
    for p in changes:
        if p in known_files:
            why.setdefault(p, "test file changed")

    fixtures, fx_unmovable = {}, set()
    for k, r in (covmap.get("__fixtures__") or {}).items():
        funcs, ok = _move(r.get("funcs", []), maps, py_changed)
        if ok:
            fixtures[k] = {**r, "funcs": funcs}
        else:
            fx_unmovable.add(k)
    kept = {}
    for n, v in tests.items():
        f = _test_file(n)
        if f in why:
            continue
        if v.get("unrecorded"):
            why.setdefault(f, "unrecorded before")
            continue
        if fx_unmovable & set(v.get("fx", ())):
            why.setdefault(f, "fixture record cannot be moved")
            continue
        funcs, ok = _move(v.get("funcs", []), maps, py_changed)
        if not ok:
            why.setdefault(f, "record cannot be moved")
            continue
        kept[n] = {**v, "funcs": funcs}
    kept = {n: v for n, v in kept.items() if _test_file(n) not in why}

    renv = _record_env(env)
    collected = REC.collect_files(root, python, targets or [], renv)
    for f in collected:
        if f not in known_files:
            why.setdefault(f, "new test file")
    redo = sorted(f for f in why if f in set(collected))   # files gone from the suite drop out with their tests

    glob = covmap.get("__global__") or {}
    gfuncs, gok = _move(glob.get("funcs", []), maps, py_changed)
    if not gok and not redo and collected:
        cheapest = min(collected, key=lambda f: sum(v.get("time", 0) for n, v in tests.items() if _test_file(n) == f))
        redo = [cheapest]
        why.setdefault(cheapest, "refresh the import-time record")

    kept_part = {**kept, "__fixtures__": fixtures,
                 "__global__": {"funcs": gfuncs, "files": glob.get("files", []), "dirs": glob.get("dirs", []),
                                "file_records": glob.get("file_records", False)}}
    parts = [kept_part]
    rec_seconds = 0.0
    if redo:
        t1 = time.time()
        with tempfile.TemporaryDirectory(prefix="dc-incr-") as tmp:
            parts.append(REC.record(root, pkg, os.path.join(tmp, "part.json"), python, redo, workers, before_test,
                                    extra_args, env))
        rec_seconds = time.time() - t1
    m = REC.merge(parts)
    used = {k for n, v in m.items() if not n.startswith("__") for k in v.get("fx", ())}
    m["__fixtures__"] = {k: r for k, r in m["__fixtures__"].items() if k in used}
    m["__base__"] = {"commit": new, "dirty": dirty}
    m["__incremental__"] = {
        "version": VERSION, "from": old, "full": None, "changed_files": len(changes),
        "rerecorded_files": len(redo), "test_files": len(collected),
        "kept_tests": len(kept), "tests": sum(1 for n in m if not n.startswith("__")),
        "reasons": {r: sum(1 for f in redo if why.get(f) == r) for r in sorted({why[f] for f in redo})},
        "record_seconds": round(rec_seconds, 2), "seconds": round(time.time() - t0, 2)}
    json.dump(m, open(out, "w"))
    return m


def _norm(v: dict) -> dict:
    return {"funcs": {tuple(x) for x in v.get("funcs", [])}, "classes": set(v.get("classes", [])),
            "files": set(v.get("files", [])), "dirs": set(v.get("dirs", [])), "fx": set(v.get("fx", [])),
            "always": bool(v.get("always"))}


def compare(a: dict, b: dict, examples: int = 5) -> dict:
    """How two maps of the same commit differ, test by test (records, fixture links) and in the global record.
    'missing' in a = something b records that a does not: the direction that matters for safety when a is the
    incremental map and b a fresh recording."""
    ta = {k: v for k, v in a.items() if not k.startswith("__")}
    tb = {k: v for k, v in b.items() if not k.startswith("__")}
    fa, fb = a.get("__fixtures__") or {}, b.get("__fixtures__") or {}

    def full(m, fx, n):   # a test's own record united with its fixture records, as selection uses it
        v = _norm(m[n])
        for k in v["fx"]:
            r = fx.get(k)
            if r:
                v["funcs"] |= {tuple(x) for x in r.get("funcs", [])}
                v["classes"] |= set(r.get("classes", []))
                v["files"] |= set(r.get("files", []))
                v["always"] = v["always"] or bool(r.get("always"))
        return v

    differ, missing_in_a, extra_in_a, ex = 0, 0, 0, []
    for n in sorted(set(ta) & set(tb)):
        va, vb = full(a, fa, n), full(b, fb, n)
        miss = {k: sorted(vb[k] - va[k])[:3] for k in ("funcs", "classes", "files", "dirs") if vb[k] - va[k]}
        extra = {k: sorted(va[k] - vb[k])[:3] for k in ("funcs", "classes", "files", "dirs") if va[k] - vb[k]}
        if vb["always"] and not va["always"]:
            miss["always"] = True
        if miss or extra:
            differ += 1
            missing_in_a += bool(miss)
            extra_in_a += bool(extra)
            if len(ex) < examples:
                ex.append({"test": n, "missing_in_a": miss, "extra_in_a": extra})
    ga, gb = {tuple(x) for x in (a.get("__global__") or {}).get("funcs", [])}, \
        {tuple(x) for x in (b.get("__global__") or {}).get("funcs", [])}
    return {"tests_a": len(ta), "tests_b": len(tb), "only_in_a": len(set(ta) - set(tb)),
            "only_in_b": len(set(tb) - set(ta)), "only_in_b_examples": sorted(set(tb) - set(ta))[:examples],
            "common": len(set(ta) & set(tb)), "differ": differ, "missing_in_a": missing_in_a,
            "extra_in_a": extra_in_a, "global_missing_in_a": len(gb - ga), "global_extra_in_a": len(ga - gb),
            "examples": ex}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m dc_engine.incremental")
    ap.add_argument("--root", default=".")
    ap.add_argument("--pkg")
    ap.add_argument("--map", help="the map to bring up to date")
    ap.add_argument("--selected", help="JSON list of the selected test ids, or null for the whole suite")
    ap.add_argument("--out")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    a = ap.parse_args(argv)
    if a.compare:
        print(json.dumps(compare(json.load(open(a.compare[0])), json.load(open(a.compare[1]))), indent=1))
        return
    m = update(json.load(open(a.map)), a.root, a.pkg, a.out, json.load(open(a.selected)), a.python, a.workers)
    print(json.dumps(m["__incremental__"]))


if __name__ == "__main__":
    main()
