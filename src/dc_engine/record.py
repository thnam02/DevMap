"""Record Proviso's coverage map (v2) for a repository: one fresh interpreter per test file, so that results cached
by one file's tests (memoised values, compiled-statement caches) cannot hide another file's dependencies, then merge.

  python -m dc_engine.record --root TREE --pkg PACKAGE_DIR --out covmap.json [--workers N] [--before-test MOD:FN]
                             [--] [pytest targets ...]

Each file runs `python -m pytest -p dc_engine.covplugin FILE`; the partial maps are merged: tests are disjoint,
fixture records with the same key (session-scoped fixtures, the "<session>" record) and the global (package import)
record are unions.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)


def collect_files(root: str, python: str, targets: list[str], env: dict) -> list[str]:
    r = subprocess.run([python, "-m", "pytest", "--collect-only", "-qq", "-p", "no:cacheprovider",
                        "--continue-on-collection-errors", *targets], cwd=root, env=env, capture_output=True, text=True)
    files = []
    for line in r.stdout.splitlines():
        f = line.split("::", 1)[0].split(":", 1)[0].strip()
        # any file pytest collects tests from: test modules, and data files that a conftest turns into tests
        # (e.g. golden-output files); each gets its own interpreter like a test module
        if f and os.path.isfile(os.path.join(root, f)) and f not in files:
            files.append(f)
    return files


def merge(parts: list[dict]) -> dict:
    out: dict = {"__fixtures__": {}, "__global__": {"funcs": []}}
    glob: set = set()
    gfiles: set = set()
    gdirs: set = set()
    file_records = bool(parts)
    for m in parts:
        for k, v in m.items():
            if k == "__fixtures__":
                for fk, r in v.items():
                    cur = out["__fixtures__"].setdefault(fk, {"funcs": set(), "classes": set(), "always": False,
                                                             "files": set(), "dirs": set()})
                    cur["funcs"] |= {tuple(x) for x in r["funcs"]}
                    cur["classes"] |= set(r["classes"])
                    cur["always"] = cur["always"] or r["always"]
                    cur["files"] |= set(r.get("files", ()))
                    cur["dirs"] |= set(r.get("dirs", ()))
            elif k == "__global__":
                glob |= {tuple(x) for x in v["funcs"]}
                gfiles |= set(v.get("files", ()))
                gdirs |= set(v.get("dirs", ()))
                # (v2.3) the map holds file records only if every part was recorded with them (an unrecorded file,
                # a timed-out one, has no part: its tests are always selected anyway)
                file_records = file_records and bool(v.get("file_records"))
            else:
                out[k] = v
    out["__fixtures__"] = {k: {"funcs": sorted(r["funcs"]), "classes": sorted(r["classes"]), "always": r["always"],
                               **({"files": sorted(r["files"])} if r["files"] else {}),
                               **({"dirs": sorted(r["dirs"])} if r["dirs"] else {})}
                           for k, r in out["__fixtures__"].items()}
    out["__global__"] = {"funcs": sorted(glob), "files": sorted(gfiles), "dirs": sorted(gdirs),
                         "file_records": file_records}
    return out


# PROVISO_RECORD_FILE_TIMEOUT (seconds; unset = no limit, the behaviour every v2 result was recorded with): a test file
# whose recording runs longer, or crashes, is not left out of the map: its collected tests are recorded as always
# selected (like a test whose setup failed), so a slow or crashing file costs time, not safety. Each such test is given
# an equal share of the time the file was allowed.
FILE_TIMEOUT = int(os.environ.get("PROVISO_RECORD_FILE_TIMEOUT", "0") or 0)


def _unrecorded(root: str, python: str, f: str, env: dict, spent: int) -> dict:
    r = subprocess.run([python, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-p", "no:randomly", f],
                       cwd=root, env=env, capture_output=True, text=True, timeout=600)
    ids = [line.strip() for line in r.stdout.splitlines() if "::" in line and not line.startswith(" ")]
    share = round(spent / len(ids), 4) if ids and spent else 0.0
    return {nid: {"funcs": [], "classes": [], "always": True, "time": share, "ok": False, "fx": [], "unrecorded": True}
            for nid in ids}


def record(root: str, pkg: str, out: str, python: str | None = None, targets: list[str] | None = None,
           workers: int | None = None, before_test: str = "", extra_args: list[str] | None = None,
           env: dict | None = None) -> dict:
    python = python or sys.executable
    base_commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    base_dirty = bool(subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=no"],
                                     capture_output=True, text=True).stdout.strip())
    root = os.path.abspath(root)
    base_env = dict(env or os.environ)
    base_env["PYTHONPATH"] = os.pathsep.join([SRC, *[p for p in base_env.get("PYTHONPATH", "").split(os.pathsep) if p]])
    base_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    files = collect_files(root, python, targets or [], base_env)
    tmp = tempfile.mkdtemp(prefix="dc-record-")

    def one(i_f):
        i, f = i_f
        part = os.path.join(tmp, f"part{i}.json")
        e = {**base_env, "COVMAP_OUT": part, "COVMAP_PKG": pkg}
        if before_test:
            e["COVMAP_BEFORE_TEST"] = before_test
        cmd = [python, "-m", "pytest", "-p", "dc_engine.covplugin", "-p", "no:cacheprovider", "-q", "--tb=no",
               "-p", "no:randomly", *(extra_args or []), f]
        try:
            subprocess.run(cmd, cwd=root, env=e, capture_output=True, timeout=FILE_TIMEOUT or None)
        except subprocess.TimeoutExpired:
            return _unrecorded(root, python, f, base_env, FILE_TIMEOUT)
        try:
            return json.load(open(part))
        except (OSError, ValueError):
            # the file's recording crashed before writing its part: with the safety setting on, its tests are kept and
            # always selected instead of disappearing from the map
            return _unrecorded(root, python, f, base_env, 0) if FILE_TIMEOUT else {}

    try:
        with ThreadPoolExecutor(max_workers=workers or max(1, (os.cpu_count() or 2) - 1)) as ex:
            parts = list(ex.map(one, enumerate(files)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)  # one folder of per-file parts per recording (19 GB over a benchmark)
    m = merge(parts)
    # (v2.2) the commit the map describes: selection measures changes from it, so commits made after recording
    # still count as changes (and a map from a commit outside the current history is not used)
    m["__base__"] = {"commit": base_commit, "dirty": base_dirty}
    json.dump(m, open(out, "w"))
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m dc_engine.record")
    ap.add_argument("--root", default=".")
    ap.add_argument("--pkg", required=True, help="package directory relative to the root, e.g. sqlglot or lib/sqlalchemy")
    ap.add_argument("--out", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--before-test", default="")
    ap.add_argument("targets", nargs="*")
    a = ap.parse_args(argv)
    m = record(a.root, a.pkg, a.out, a.python, a.targets, a.workers, a.before_test)
    print(json.dumps({"tests": sum(1 for k in m if not k.startswith("__")), "fixture_records": len(m["__fixtures__"]),
                      "import_funcs": len(m["__global__"]["funcs"])}))


if __name__ == "__main__":
    main()
