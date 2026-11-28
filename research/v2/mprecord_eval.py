"""v2.5-dev worker recording (mprecord) evaluated on saved B1 data. Run from a checkout whose src/ has v2.5-dev's
recorder (covplugin.py): research/v2/results/v25/. B1 and B1b are not touched (own trees, lowest priority).

  python research/v2/mprecord_eval.py partA            # sqlglot, one parent: tests/test_executor.py, pool vs in-process
  python research/v2/mprecord_eval.py partB PROJECT    # every ok B1 pair: re-record the always tests of the files that
                                                       # use worker processes, replace their records, re-select, score
  python research/v2/mprecord_eval.py write            # results/v25/mprecord_eval.md

Part B per pair (parent P): the saved map's tests that are always selected and sit in a test file that starts worker
processes (multiprocessing, ProcessPoolExecutor, os.fork) are recorded again with v2.5-dev's recorder (only those tests:
record(nodes=...)); in a copy of the map their entries, and the fixture records of their file, are replaced; ValueRTS's
selection is computed for scenarios S and F with both maps (same Proviso code, on the same tree states as b1.py) and
scored against the confirmed failures already in the B1 row (b1.score's rule)."""
from __future__ import annotations

import copy
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import record as REC  # noqa: E402

OUT = os.path.join(HERE, "results", "v25")
MAX_LOAD = float(os.environ.get("V25_MAX_LOAD", "9"))
WORKER_USE = re.compile(r"\bmultiprocessing\b|ProcessPoolExecutor|\bos\.fork\b|get_context\(")
TPCDS = "tests/test_executor.py::TestExecutor::test_execute_tpcds"
TPCH = "tests/test_executor.py::TestExecutor::test_execute_tpch"


def wait_load():
    while os.getloadavg()[0] > MAX_LOAD:
        time.sleep(60)


def recorder_is_v25():
    src = open(os.path.join(os.path.dirname(I.__file__), "covplugin.py")).read()
    return "MPREC" in src


def always_tests(cov):
    fx = cov.get("__fixtures__") or {}
    return {n for n, v in I.tests_of(cov).items()
            if v.get("always") or any((fx.get(k) or {}).get("always") for k in v.get("fx", ()))}


def run_pytest(tree, out, nodes, extra_env=None):
    """One recording process, as record._one runs it, keeping the worker record folder (out + '.mp')."""
    e = PL.env(tree, [PL.PLUG])
    e["PYTHONPATH"] = os.pathsep.join([REC.SRC, e.get("PYTHONPATH", "")])
    e.update({"COVMAP_OUT": out, "COVMAP_PKG": PL.CFG["pkg"], "PYTHONDONTWRITEBYTECODE": "1", **(extra_env or {})})
    t = time.time()
    r = subprocess.run([PL.PY, "-m", "pytest", "-p", "dc_engine.covplugin", "-p", "no:cacheprovider", "-q", "--tb=short",
                        "-p", "no:randomly", *PL.CFG["pytest_args"], *nodes], cwd=tree, env=e, capture_output=True,
                       text=True, timeout=7200)
    return PL.jload(out, {}), round(time.time() - t, 1), r


def mp_files(out):
    """Worker record files left by a recording: per owner, files, incomplete ones, 'always' lines, functions."""
    res = {}
    for f in sorted(glob.glob(os.path.join(out + ".mp", "*.rec"))):
        owner, pid = os.path.basename(f)[:-4].rsplit("-", 1)
        raw = open(f, "rb").read()
        lines = raw.splitlines()
        o = res.setdefault(owner, {"files": 0, "incomplete": 0, "always_lines": 0, "funcs": set()})
        o["files"] += 1
        o["incomplete"] += bool(raw and not raw.endswith(b"\n"))
        for line in lines:
            try:
                kind, x, g = json.loads(line)
            except ValueError:
                o["incomplete"] += 1
                continue
            if kind == "A":
                o["always_lines"] += 1
            elif kind == "f":
                o["funcs"].add(tuple(x))
    return {k: {**v, "funcs": len(v["funcs"])} for k, v in res.items()}


INPROC = '''"""(v2.5 evaluation, not part of sqlglot) test_executor's TPC-H/TPC-DS tests with the queries run in this process."""
from sqlglot import parse_one
from tests import test_executor as te


class TestInProcess(te.TestExecutor):
    def _mp_execute(self, schema, tables, sqls, tpch):
        te.initializer(schema, tables)
        for i, (args, sql, _) in enumerate(sqls):
            table = te.mp_execute(parse_one(sql), args)
            if table is not None:
                self.subtestHelper(i, table, tpch=tpch)
'''


def partA():
    assert recorder_is_v25(), "run from a checkout with v2.5-dev's recorder"
    b1.use("sqlglot")
    r = sorted((r for r in b1.rows("sqlglot").values() if r.get("status") == "ok"), key=lambda r: r["rank"])[0]
    p = r["parent"]
    tree = PL.make_tree("v25-a", p)
    work = os.path.join(PL.WORK, "v25", "partA")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    res = {"parent": p, "commit": r["id"], "runs": {}}
    wait_load()
    # 1. the whole test file, with the pool (as the suite runs it)
    m, secs, pr = run_pytest(tree, os.path.join(work, "file.json"), ["tests/test_executor.py"])
    res["runs"]["file"] = {"secs": secs, "exit": pr.returncode, "tail": pr.stdout[-400:], "tests": len(I.tests_of(m))}
    fx = m.get("__fixtures__") or {}
    for n in (TPCDS, TPCH):
        v = m.get(n) or {}
        res["runs"]["file"][n] = {"always": v.get("always"), "own_funcs": len(v.get("funcs", [])),
                                  "funcs_with_fixtures": len(I.test_funcs(m, n)),
                                  "always_fixtures": [k for k in v.get("fx", []) if (fx.get(k) or {}).get("always")]}
    res["runs"]["file"]["workers"] = mp_files(os.path.join(work, "file.json"))
    # 2. each test alone (so the worker files belong to it), then the same queries in-process
    open(os.path.join(tree, "tests", "test_v25_inprocess.py"), "w").write(INPROC)
    try:
        for n in (TPCDS, TPCH):
            wait_load()
            key = n.rsplit("::", 1)[1]
            mp, s1, r1 = run_pytest(tree, os.path.join(work, f"{key}.pool.json"), [n])
            ni = f"tests/test_v25_inprocess.py::TestInProcess::{key}"
            mi, s2, r2 = run_pytest(tree, os.path.join(work, f"{key}.inproc.json"), [ni])
            fp, fi = I.test_funcs(mp, n), I.test_funcs(mi, ni)
            res["runs"][key] = {"pool": {"secs": s1, "exit": r1.returncode, "always": (mp.get(n) or {}).get("always"),
                                         "funcs": len(fp), "own_funcs": len((mp.get(n) or {}).get("funcs", [])),
                                         "workers": mp_files(os.path.join(work, f"{key}.pool.json"))},
                                "inproc": {"secs": s2, "exit": r2.returncode, "always": (mi.get(ni) or {}).get("always"),
                                           "funcs": len(fi)},
                                "only_pool": sorted(map(list, fp - fi)), "only_inproc": sorted(map(list, fi - fp))}
            print(time.strftime("%H:%M:%S"), key, {k: res["runs"][key][k] for k in ("pool", "inproc")},
                  "only pool", len(fp - fi), "only in-process", len(fi - fp), flush=True)
    finally:
        os.remove(os.path.join(tree, "tests", "test_v25_inprocess.py"))
    PL.jdump(res, os.path.join(PL.BASE_WORK, "sqlglot", "v25", "partA.json"))


def _replace(cov_old, cov_new, nodes):
    """Copy of cov_old with the given tests' entries from cov_new, and cov_new's fixture records of their files."""
    m = copy.deepcopy(cov_old)
    files = {n.split("::", 1)[0] for n in nodes}
    fx_new = cov_new.get("__fixtures__") or {}
    fx = m.setdefault("__fixtures__", {})
    for n in nodes:
        if n in cov_new:
            m[n] = cov_new[n]
            for k in cov_new[n].get("fx", []):
                if any(f in k for f in files) or k not in fx:   # the file's own records; shared ones stay as recorded
                    if k in fx_new:
                        fx[k] = fx_new[k]
    return m


def _selections(tree, p, c, r, cov, universe):
    out = {}
    for sc in ("S", "F"):
        if sc not in r or r[sc].get("timeout"):
            continue
        b1.to_parent(tree, p)
        if sc == "S":
            b1.apply_source(tree, p, c)
            edited = []
        else:
            b1.apply_full(tree, p, c)
            edited = [f for _, f in b1._changed(tree, p, c) if I._is_test_path(f) and f.endswith(".py")]
        sel, why = I.selection(tree, cov, PL.PY)
        out[sc] = {"sel": None if sel is None else sorted(set(sel) & universe), "edited": edited,
                   "reason": why.get("reason")}
    b1.to_parent(tree, p)
    return out


WHOLE = os.environ.get("V25_WHOLE", "1") == "1"   # re-record the whole test files (default), not only their always tests


def partB(name):
    assert recorder_is_v25(), "run from a checkout with v2.5-dev's recorder"
    b1.use(name)
    work = os.path.join(PL.WORK, "v25", "partB-whole" if WHOLE else "partB")
    os.makedirs(work, exist_ok=True)
    rows = sorted((r for r in b1.rows(name).values() if r.get("status") == "ok"), key=lambda r: r["rank"])
    for k, r in enumerate(rows):
        f = os.path.join(work, f"{r['id'][:12]}.json")
        if os.path.exists(f):
            continue
        wait_load()
        t0 = time.time()
        p, c = r["parent"], r["id"]
        d = os.path.join(PL.WORK, "b1", c[:12])
        cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
        res = {"id": c, "parent": p}
        try:
            tree = PL.make_tree("v25-b", p)
            b1.use_targets(tree)
            al = always_tests(cov)
            files = sorted({n.split("::", 1)[0] for n in al})
            mpfiles = [x for x in files if os.path.exists(os.path.join(tree, x))
                       and WORKER_USE.search(open(os.path.join(tree, x), errors="replace").read())]
            nodes = sorted(n for n in al if n.split("::", 1)[0] in mpfiles)
            res.update(always=len(al), worker_files=mpfiles, rerecorded=len(nodes))
            if nodes:
                out = os.path.join(work, "maps", f"{c[:12]}.new.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                if os.path.exists(out):
                    os.remove(out)
                ts = time.time()
                REC.record(tree, PL.CFG["pkg"], out, PL.PY, mpfiles, 1, PL.CFG["before_test"],
                           ["-p", "no:randomly", *PL.CFG["pytest_args"]], PL.env(tree, [PL.PLUG]),
                           nodes=None if WHOLE else {x: [n for n in nodes if n.startswith(x + "::")] for x in mpfiles})
                res["record_s"] = round(time.time() - ts, 1)
                new = PL.jload(out, {})
                # whole files: every test of those files gets its new record (a worker that outlives its test makes
                # the later tests of the process always: v2.5's leak rule)
                replaced = sorted(n for n in I.tests_of(new) if n.split("::", 1)[0] in mpfiles) if WHOLE else nodes
                cov2 = _replace(cov, new, replaced)
                al2 = always_tests(cov2)
                res["replaced"] = len(replaced)
                res["released"] = sorted(set(nodes) - al2)
                res["still_always"] = sorted(set(nodes) & al2)
                res["newly_always"] = sorted((al2 - al) & set(replaced))
                res["not_rerecorded"] = sorted(n for n in nodes if n not in new)
            else:
                cov2 = cov
                res["released"], res["still_always"], res["not_rerecorded"], res["newly_always"] = [], [], [], []
            universe = set(PL.universe_of(cov, PL.failing(base)))
            plain = {kk: tt for kk, (ok_, tt) in base.items()}
            before = _selections(tree, p, c, r, cov, universe)
            after = _selections(tree, p, c, r, cov2, universe) if nodes else before
            res["scenarios"] = {}
            for sc in before:
                truth = set(r[sc].get("failing", []))
                sb = b1.score({"x": set(universe) if before[sc]["sel"] is None else set(before[sc]["sel"])}, {},
                              universe, plain, truth, {}, before[sc]["edited"])["x"]
                sa = b1.score({"x": set(universe) if after[sc]["sel"] is None else set(after[sc]["sel"])}, {},
                              universe, plain, truth, {}, after[sc]["edited"])["x"]
                sel_after = set(universe) if after[sc]["sel"] is None else set(after[sc]["sel"])
                ed = {n for n in universe if n.split("::", 1)[0] in set(after[sc]["edited"])}
                res["scenarios"][sc] = {
                    "universe": len(universe), "failing": sorted(truth)[:20],
                    "before": {kk: sb[kk] for kk in ("selected", "time_share", "missed")},
                    "after": {kk: sa[kk] for kk in ("selected", "time_share", "missed")},
                    "released_skipped": sorted(set(res["released"]) & (universe - sel_after - ed)),
                    "row_selected": ((r[sc].get("tools") or {}).get("proviso") or {}).get("selected")}
        except Exception as e:  # noqa: BLE001
            res["error"] = repr(e)[:400]
        res["secs"] = round(time.time() - t0)
        PL.jdump(res, f)
        sc = res.get("scenarios", {})
        print(time.strftime("%H:%M:%S"), name, f"[{k + 1}/{len(rows)}] {c[:10]} re-recorded {res.get('rerecorded')} "
              f"released {len(res.get('released', []))}", {s: (v["before"]["selected"], v["after"]["selected"],
                                                              len(v["before"]["missed"]), len(v["after"]["missed"]))
                                                          for s, v in sc.items()}, res.get("error", ""),
              f"({res['secs']} s)", flush=True)


def write():
    L = ["# v2.5-dev worker recording (mprecord): completeness, safety and saving", "",
         "Recorder: branch v2.5-dev (d67b35b), run in a separate checkout (eval-pc's harness with v2.5-dev's "
         "covplugin.py); B1 and B1b stayed on the frozen tool. Selection-only scoring on saved B1 data; no test was run "
         "for scoring. `research/v2/mprecord_eval.py`.", ""]
    a = PL.jload(os.path.join(PL.BASE_WORK, "sqlglot", "v25", "partA.json"))
    if a:
        f = a["runs"]["file"]
        L += ["## A. Completeness (sqlglot, one parent commit)", "",
              f"Parent {a['parent'][:10]} (pair {a['commit'][:10]}). `tests/test_executor.py` recorded whole with "
              f"v2.5-dev ({f['tests']} tests, {f['secs']} s).", "",
              "| Test | always | functions (own record) | functions (with fixtures) | always fixture records |",
              "|---|---|---|---|---|"]
        for n in (TPCDS, TPCH):
            x = f[n]
            L.append(f"| {n.rsplit('::', 1)[1]} | {x['always']} | {x['own_funcs']} | {x['funcs_with_fixtures']} | "
                     f"{', '.join(x['always_fixtures']) or '-'} |")
        L += ["", "Worker record files of that recording (per owner = recording target that started them): "
              + "; ".join(f"owner {o}: {w['files']} files, {w['incomplete']} incomplete, {w['always_lines']} "
                          f"'always' lines, {w['funcs']} functions" for o, w in f["workers"].items()) + ".", "",
              "Each test alone, with the pool and with the same queries run in-process (no pool):", "",
              "| Test | pool: always | pool: functions | worker files (incomplete) | in-process: functions | "
              "only with the pool | only in-process |", "|---|---|---|---|---|---|---|"]
        for key in ("test_execute_tpcds", "test_execute_tpch"):
            x = a["runs"].get(key)
            if not x:
                continue
            wf = sum(w["files"] for w in x["pool"]["workers"].values())
            wi = sum(w["incomplete"] for w in x["pool"]["workers"].values())
            L.append(f"| {key} | {x['pool']['always']} | {x['pool']['funcs']} | {wf} ({wi}) | {x['inproc']['funcs']} | "
                     f"{len(x['only_pool'])} | {len(x['only_inproc'])} |")
        for key in ("test_execute_tpcds", "test_execute_tpch"):
            x = a["runs"].get(key)
            if x and (x["only_pool"] or x["only_inproc"]):
                L += ["", f"{key}: functions only with the pool: "
                      + (", ".join(f"`{p}:{ln}`" for p, ln in x["only_pool"][:30]) or "none")
                      + "; only in-process: " + (", ".join(f"`{p}:{ln}`" for p, ln in x["only_inproc"][:30]) or "none")]
        L.append("")
    L += ["## B. Safety and saving (every finished B1 pair)", "",
          "Per pair: the test files that start worker processes and hold an always test in the saved map are recorded "
          "again at the parent with v2.5-dev; in a copy of the map, the records of their tests (and the files' fixture "
          "records) are replaced; ValueRTS's selection for S and F is computed with the original and the new map and "
          "scored against the B1 row's confirmed failures. Median % tests = selected / universe; % test time = the "
          "selection's share of the universe's plain-run time.", ""]
    gains = []
    for variant, label in (("partB-whole", "Whole test files re-recorded (every test of the file gets its v2.5 "
                                           "record; this includes v2.5's leak rule)"),
                           ("partB", "For comparison: only the always tests re-recorded (misses the leak rule's effect "
                                     "on the file's other tests)")):
        L += [f"### {label}", "",
              "| Project | Pairs | Tests released from always (median per pair; distinct) | Still always | Newly always "
              "(median per pair; pairs) | Pair-scenarios where a released test is skipped | Missed failures before -> "
              "after | Median % tests before -> after | Median % test time before -> after | Errors |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for name in ("sqlglot", "loguru"):
            fs = sorted(glob.glob(os.path.join(PL.BASE_WORK, name, "v25", variant, "*.json")))
            rs = [json.load(open(x)) for x in fs]
            ok = [x for x in rs if "scenarios" in x]
            if not ok:
                L.append(f"| {name} | (not run{' yet' if variant == 'partB-whole' else ''}) | | | | | | | | |")
                continue
            rel = [len(x["released"]) for x in ok]
            distinct = {n for x in ok for n in x["released"]}
            still = {n for x in ok for n in x["still_always"]}
            newly = [len(x.get("newly_always", [])) for x in ok]
            skipped = sum(bool(v["released_skipped"]) for x in ok for v in x["scenarios"].values())
            mb = sum(len(v["before"]["missed"]) for x in ok for v in x["scenarios"].values())
            ma = sum(len(v["after"]["missed"]) for x in ok for v in x["scenarios"].values())
            pt = lambda w: statistics.median(100 * v[w]["selected"] / max(1, v["universe"]) for x in ok
                                             for v in x["scenarios"].values())
            tt = lambda w: statistics.median(100 * v[w]["time_share"] for x in ok for v in x["scenarios"].values())
            L.append(f"| {name} | {len(ok)} | {statistics.median(rel)} ({len(distinct)}) | {len(still)} | "
                     f"{statistics.median(newly)} ({sum(1 for k in newly if k)}) | {skipped} | {mb} -> {ma} | "
                     f"{pt('before'):.1f} -> {pt('after'):.1f} | {tt('before'):.1f} -> {tt('after'):.1f} | "
                     f"{len(rs) - len(ok)} |")
            for x in ok:
                for sc, v in x["scenarios"].items():
                    g = set(v["after"]["missed"]) - set(v["before"]["missed"])
                    if g:
                        gains.append((variant, name, x["id"][:10], sc, sorted(g)))
            if still:
                L.append(f"|  | still always: {', '.join(sorted(still)[:4])} | | | | | | | | |")
        L.append("")
    lk = PL.jload(os.path.join(PL.BASE_WORK, "sqlglot", "v25", "leak.json"))
    if lk:
        L += ["### Why test_canonicalize stays always (sqlglot)", "",
              "At most sqlglot parents, TestOptimizer creates one process pool in `setUpClass` "
              "(`ProcessPoolExecutor(mp_context=get_context(\"spawn\"))`, shut down at class cleanup). The first test "
              "that submits work (test_canonicalize) starts the workers, which outlive it: v2.5 keeps that test always "
              "(its workers are still alive when it ends) and, by its leak rule, every later test of the process. "
              "v2.3 marked only the test that started the workers; the other tests ran their optimizer work in those "
              "workers unseen. Whole-file recordings of tests/test_optimizer.py with v2.5:", "",
              "| Pair (parent) | Tests in the file | Always, v2.3 map | Always, v2.5 | Their time / file time (s) |",
              "|---|---|---|---|---|"]
        for pair, x in lk.items():
            L.append(f"| {pair} ({x['parent']}) | {x['tests_in_file']} | {x['always_v23']} | {x['always_v25']} | "
                     f"{x['always_v25_time_s']} / {x['file_time_s']} |")
        L.append("")
    L += ["Missed failures gained: " + ("none." if not gains else "")]
    for g in gains:
        L.append(f"- {g[0]} {g[1]} {g[2]} {g[3]}: {g[4]}")
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "mprecord_eval.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    a = sys.argv[1:]
    if a[0] == "partA":
        partA()
    elif a[0] == "partB":
        partB(a[1])
    elif a[0] == "write":
        write()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
