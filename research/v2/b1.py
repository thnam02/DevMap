"""B1: real, consecutive commit history (evaluation plan: RQ1 effectiveness, RQ2 import-time changes, RQ4 ablation,
RQ7 overhead). Every tool runs on the same commit pairs, in the same environment, with Proviso frozen (v2.3.1).

Commit pairs (parent P, commit C):
  history  projects: the most recent commits on the main branch (first parent) up to a fixed point, newest first, that
           change at least one non-test Python file of the package (not docs/conf.py, scripts, ...); a pair counts only if the suite runs at P ("builds": outcomes for
           at least half of the test files). The first N pairs that build are kept; skipped ones are reported.
  namerts  NameRTS's ten projects: its own published commit pairs (true_parent, current), not reselected, plus its
           ground truth (tests_to_run) and published selection, so its four metrics can be computed side by side.

Per pair, at P: a plain run of the suite (outcomes, per-test times), Proviso's dependency map, and the other tools'
data (testmon database, NameRTS cache, TDAD index), each timed (RQ7). Then two scenarios, each selected by every tool
and run in full:
  S  "behaviour change": the commit's non-test changes applied to P, with P's tests (old tests see new behaviour);
  F  "full commit": the whole commit, its own tests included (B1_FULL=0 leaves it out).
Ground truth, reported separately:
  affected   tests that run changed code, from the recording at P: "exec" (code that runs at import counts as run
             by every test; Proviso's traditional variant, Ekstazi's rule) and "func" (tests that ran a modified
             function: NameRTS's SafeR reference); per test and per test file
  failures   tests failing after the change that passed at P, confirmed: fail in all 3 re-runs of the scenario and
             pass in all 3 re-runs at P (otherwise flaky: excluded and counted). Tests new in the scenario cannot be
             selected from P's data by any tool and are excluded (counted).
Tools: run_all, proviso, traditional (Proviso's variant), testmon, namerts, tdad, ekstap (when installed), and Proviso
with one part off per ablation part (selection-only parts, on the same map; B1_ABLATE=part,part or "all", default
none). A tool that is not installed or fails on a pair gets {"error": ...} in the row, not a guess. In scenario F the
tests of test files the commit adds or edits are counted as selected for every tool (a changed test file runs anyway).

Usage:
  python research/v2/b1.py PROJECT [N] [--workers W]       # resumable; rows in results/b1/<PROJECT>/rows.w*.jsonl
  python research/v2/b1.py PROJECT --list [N]              # the candidate pairs only
  python research/v2/b1.py report [PROJECT ...]            # results/b1/report.md
Env: PROVISO_WORK, PROVISO_WORKERS (cores for one map recording), PROVISO_TEST_TIMEOUT (seconds per suite run,
default 1800 here), B1_FULL (1), B1_ABLATE, B1_RERUNS (3), NAMERTS_HOME, TDAD_SRC, EKSTAP_HOME."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("PROVISO_TEST_TIMEOUT", "1800")
import pipeline as PL  # noqa: E402
import rts as SEL  # noqa: E402
import nrbench as NB  # noqa: E402
from dc_engine import impact as I  # noqa: E402

FULL = os.environ.get("B1_FULL", "1") != "0"
RERUNS = int(os.environ.get("B1_RERUNS", "3"))
SELECTION_PARTS = ["snapshot", "docs", "hints", "callers", "bindings", "newfiles", "conftest", "byname", "config",
                   "data", "syntax", "files"]
_ab = os.environ.get("B1_ABLATE", "")
ABLATE = SELECTION_PARTS if _ab == "all" else [p for p in _ab.split(",") if p]
OUT = os.environ.get("B1_OUT") or os.path.join(HERE, "results", "b1")   # dry runs: B1_OUT=results_smoke/b1

# --------------------------------------------------------------------------------------------- projects
# History projects: the full suite of each (targets as the project runs its own tests). until = the newest commit
# considered (a hash, or a date resolved on the main branch's first-parent history). For our four projects the pinned
# commits of the main benchmark; new held-out projects get a date fixed before their first run.
_D = dict(mutate=None, pythonpath=[], pytest_args=[], before_test="", pip=[])
PROJECTS = {
    "sqlglot": {**PL.REPOS["sqlglot"], "source": "history", "until": PL.REPOS["sqlglot"]["commit"]},
    "pygments": {**PL.REPOS["pygments"], "source": "history", "until": PL.REPOS["pygments"]["commit"]},
    "datasette": {**PL.REPOS["datasette"], "source": "history", "until": PL.REPOS["datasette"]["commit"]},
    # the whole suite (the main benchmark measured test/base and test/sql only)
    "sqlalchemy": {**PL.REPOS["sqlalchemy"], "targets": ["test"], "source": "history",
                   "until": PL.REPOS["sqlalchemy"]["commit"]},
}
for _name, _c in NB.PROJECTS.items():   # NameRTS's projects: its commit pairs, its targets
    PROJECTS[_name] = {**_D, "url": _c["url"], "commit": None, "pkg": _c["pkg"], "targets": _c["targets"],
                       "test_dirs": "tests", "nr_repo": _name, "source": "namerts", "sync": _c.get("sync")}
PROJECTS["sympy"]["pytest_args"] = ["-o", "addopts=", "-p", "noslow"]
PROJECTS["sympy"]["before_test"] = "sympy.core.cache:clear_cache"


def use(name):
    PL.REPOS.setdefault(name, PROJECTS[name])
    PL.REPOS[name] = {**PL.REPOS[name], **PROJECTS[name]}
    PL.use(name)
    os.makedirs(res(), exist_ok=True)


def res():
    return os.path.join(OUT, PL.REPO)


def log(*a):
    print(time.strftime("%H:%M:%S"), PL.REPO, *a, flush=True)


# --------------------------------------------------------------------------------------------- commit pairs

def _resolve_until(src, until):
    if re.fullmatch(r"[0-9a-f]{7,40}", until or ""):
        return until
    head = PL.git(src, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip() or "HEAD"
    got = PL.git(src, "rev-list", "-1", "--first-parent", f"--before={until}", head).strip()
    if not got:
        raise RuntimeError(f"no commit on {head} before {until}")
    return got


def candidates(limit):
    """[(P, C, info)] newest first."""
    C = PL.CFG
    if C["source"] == "namerts":
        got = [(p["true_parent"], p["current"], {"namerts_gt": p["gt"], "namerts_total": p["total_tests"],
                                                  "namerts_published": p["namerts"]}) for p in NB.pairs(PL.REPO)][:limit]
        # pairs can name commits outside the clone's branches (merged PR heads): fetch them by hash, as nrbench does,
        # into the source clone the trees are cloned from
        NB.ensure_commits(PL.src_repo(), *[x for p, c, _ in got for x in (p, c)])
        return got
    src = PL.src_repo()
    until = _resolve_until(src, C["until"])
    out = []
    for line in PL.git(src, "log", "--first-parent", "--format=%H %P", until).splitlines():
        h, *parents = line.split()
        if not parents:
            break
        names = PL.git(src, "diff", "--name-only", "--no-renames", parents[0], h).split()
        pkg = C["pkg"].rstrip("/") + "/"
        if any(f.startswith(pkg) and f.endswith(".py") and not I._is_test_path(f) for f in names):
            out.append((parents[0], h, {"merge": len(parents) > 1, "files": len(names)}))
        if len(out) >= limit:
            break
    return out


def _changed(tree, p, c):
    """[(status, path)] of P..C, renames as delete + add."""
    out = []
    for line in PL.git(tree, "diff", "--name-status", "--no-renames", p, c).splitlines():
        st, f = line.split("\t", 1)
        out.append((st[0], f))
    return out


def apply_source(tree, p, c):
    """Scenario S: the commit's non-test changes on P (test files stay as at P). Returns the changed paths."""
    PL.reset(tree)
    PL.git(tree, "checkout", "-q", "-f", p, check=True)
    done = []
    for st, f in _changed(tree, p, c):
        if I._is_test_path(f):
            continue
        path = os.path.join(tree, f)
        if st == "D":
            if os.path.exists(path):
                os.remove(path)
        else:
            blob = subprocess.run(["git", "show", f"{c}:{f}"], cwd=tree, capture_output=True)
            if blob.returncode == 0:
                os.makedirs(os.path.dirname(path) or tree, exist_ok=True)
                open(path, "wb").write(blob.stdout)
        done.append(f)
    return done


def apply_full(tree, p, c):
    """Scenario F: the whole commit on P (HEAD stays at P). Returns paths restored by NameRTS's put_current."""
    return NB.put_current(tree, p, c)


def to_parent(tree, p):
    PL.reset(tree)
    PL.git(tree, "checkout", "-q", "-f", p, check=True)
    PL.git(tree, "clean", "-fdqx", "-e", ".dc-engine", "-e", ".tdad")


# --------------------------------------------------------------------------------------------- environment

_FP = None


def fingerprint():
    """The interpreter and every installed distribution (name==version), hashed: rows of one project must share it."""
    global _FP
    if _FP is None:
        r = subprocess.run([PL.PY, "-c", "import sys,importlib.metadata as m;print(sys.version.split()[0]);"
                            "print('\\n'.join(sorted(f'{d.metadata[\"Name\"]}=={d.version}' for d in m.distributions()"
                            " if d.metadata['Name'])))"], capture_output=True, text=True)
        lines = r.stdout.splitlines()
        _FP = {"python": lines[0] if lines else "?", "packages": len(lines) - 1,
               "hash": hashlib.sha256(r.stdout.encode()).hexdigest()[:16]}
    return _FP


_PV = None


def proviso_version():
    """The Proviso code the rows come from: impact's VERSION, the commit of src/ and whether src/ had local edits
    (rows of one benchmark must all come from the frozen version)."""
    global _PV
    if _PV is None:
        root = os.path.dirname(os.path.dirname(HERE))
        # the frozen version's tagged commit when src/ is identical to it, else the last commit that changed src/
        # (not HEAD: results commits move HEAD between and during benchmark runs)
        tag = os.environ.get("PROVISO_TAG", "proviso-v2.3.1")
        tagged = PL.git(root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}").strip()
        same = tagged and subprocess.run(["git", "diff", "--quiet", tagged, "HEAD", "--", "src"], cwd=root).returncode == 0
        commit = tagged if same else PL.git(root, "log", "-1", "--format=%H", "--", "src").strip()
        _PV = {"version": I.VERSION, "commit": commit[:12],
               "src_dirty": bool(PL.git(root, "status", "--porcelain", "--", "src").strip())}
    return _PV


def tools_available():
    return {"testmon": subprocess.run([PL.PY, "-c", "import testmon"], capture_output=True).returncode == 0,
            "namerts": PL.nr_available(),
            "tdad": os.path.isdir(os.environ.get("TDAD_SRC", os.path.expanduser("~/proviso-work/v2/TDAD/tdad/src"))),
            "ekstap": bool(os.environ.get("EKSTAP_HOME"))}


# --------------------------------------------------------------------------------------------- one pair

def covmap_at(tree, out, commit, workers=None):
    """Proviso's map of tree at commit; a map left from an earlier run is reused only if it was recorded at that
    commit (else it is recorded again)."""
    old = PL.jload(out, None)
    if old is not None and (old.get("__base__") or {}).get("commit") != commit:
        os.remove(out)
    return PL.covmap(tree, out, workers)


def _files(ns):
    return {n.split("::", 1)[0] for n in ns}


def _timed(fn, *a):
    t = time.time()
    v = fn(*a)
    return v, round(time.time() - t, 2)


def _proviso(tree, cov, universe, off=None):
    """(selected set or None for the full suite, why, cold seconds, warm seconds). Cold includes taking the new
    commit's import-time snapshot (the first selection after a change); warm is a second call (the cache in use)."""
    old = os.environ.get("PROVISO_OFF")
    if off:
        os.environ["PROVISO_OFF"] = off
    try:
        t = time.time()
        I.selection(tree, cov, PL.PY)
        cold = time.time() - t
        t = time.time()
        sel, why = I.selection(tree, cov, PL.PY)
        warm = time.time() - t
    finally:
        if off:
            if old is None:
                os.environ.pop("PROVISO_OFF", None)
            else:
                os.environ["PROVISO_OFF"] = old
    return (None if sel is None else set(sel) & universe), why, round(cold, 2), round(warm, 2)


def selections(tree, cov, universe, assets, p, apply_to, changed_src):
    """{tool: set of selected tests (within universe) | {"error": ...}} and per-tool extras (times, reasons).
    apply_to(t) puts another tree at P (NameRTS's) into the same changed state as `tree`."""
    sets, extra = {"run_all": set(universe)}, {}
    s, why, cold, warm = _proviso(tree, cov, universe)
    sets["proviso"] = set(universe) if s is None else s
    extra["proviso"] = {"full": s is None, "reason": why.get("reason"), "selection_cold_s": cold,
                        "selection_s": warm, "changed_functions": len(why.get("changed_functions", [])),
                        "import_state_changed": len(why.get("import_state_changed", []))}
    tsel, twhy = PL._traditional_selection(tree, cov)
    sets["traditional"] = set(universe) if tsel is None else set(tsel) & universe
    extra["traditional"] = {"full": tsel is None, "reason": twhy.get("reason")}
    for part in ABLATE:
        s, why, _, warm = _proviso(tree, cov, universe, part)
        sets[f"proviso-{part}"] = set(universe) if s is None else s
        extra[f"proviso-{part}"] = {"full": s is None, "selection_s": warm}
    always = {n for n in universe if n.split("::", 1)[0] in set(PL._noext_test_files(tree))}
    if assets.get("testmon"):
        try:
            got, secs = _timed(PL.testmon_select, tree, assets["testmon"])
            sets["testmon"] = (set(got) & universe) | always
            extra["testmon"] = {"selection_s": secs}
        except Exception as e:  # noqa: BLE001
            sets["testmon"] = {"error": repr(e)[:300]}
    elif "testmon_error" in assets:
        sets["testmon"] = {"error": assets["testmon_error"]}
    if assets.get("nr_cache"):
        try:
            apply_to(assets["nr_tree"])
            got, secs = _timed(PL.namerts, "select", assets["nr_tree"], assets["nr_cache"])
            sets["namerts"] = {n for n in universe if n.split("::", 1)[0] in set(got)}
            extra["namerts"] = {"selection_s": secs, "files": len(set(got))}
        except Exception as e:  # noqa: BLE001
            sets["namerts"] = {"error": repr(e)[:300]}
        finally:
            to_parent(assets["nr_tree"], p)
    elif "nr_error" in assets:
        sets["namerts"] = {"error": assets["nr_error"]}
    if assets.get("tdad_tree"):
        try:
            import tdad_select as T
            got, secs = _timed(T.select, assets["tdad_tree"], changed_src, 50)
            sets["tdad"] = T.expand(got, universe)
            extra["tdad"] = {"selection_s": secs}
        except Exception as e:  # noqa: BLE001
            sets["tdad"] = {"error": repr(e)[:300]}
    elif "tdad_error" in assets:
        sets["tdad"] = {"error": assets["tdad_error"]}
    if tools_available()["ekstap"]:
        sets["ekstap"] = {"error": "EkstaP integration not written yet"}
    return sets, extra


def affected(tree, cov, universe):
    """The 'affected tests' references for the current change (see the module docstring)."""
    ch = SEL.Change(tree, [PL.CFG["pkg"]])
    tsel, _ = PL._traditional_selection(tree, cov)
    ref = {"exec": set(universe) if tsel is None else set(tsel) & universe}
    if ch.new_files:   # a new source file: no recorded test can have run it; "func" is undefined
        ref["func"] = None
    else:
        funcs, _ = ch.units()
        ref["func"] = {n for n in universe if I.test_funcs(cov, n) & funcs}
    return ref, ch


def confirm(tree, failing_now, p, c, scenario, d):
    """(confirmed, flaky_in_scenario, flaky_at_parent): re-run the failing tests' files RERUNS times in the scenario
    and RERUNS times at P."""
    if not failing_now:
        return [], [], []
    targets = PL._rerun_targets(failing_now)
    still = set(failing_now)
    for k in range(RERUNS):
        out = PL.run_tests(tree, os.path.join(d, f"rerun_{scenario}{k}.json"), targets)
        still &= set(PL._still_failing(sorted(still), out)) if out else still
    flaky_s = sorted(set(failing_now) - still)
    to_parent(tree, p)
    at_parent = set()
    for k in range(RERUNS):
        out = PL.run_tests(tree, os.path.join(d, f"rerun_P{scenario}{k}.json"), targets)
        at_parent |= {t for t in still if t in out and not out[t][0]}
    return sorted(still - at_parent), flaky_s, sorted(at_parent)


def score(sets, extra, universe, plain, truth, ref, edited_tests=()):
    T = lambda ns: sum(plain.get(n, 0) for n in ns)
    tot = T(universe) or 1e-9
    files_all = _files(universe)
    edited = {n for n in universe if n.split("::", 1)[0] in set(edited_tests)}
    out = {}
    for name, s in sets.items():
        if isinstance(s, dict):
            out[name] = s
            continue
        s = s | edited
        f = _files(s)
        r = {"selected": len(s), "files": len(f), "testr": round(1 - len(f) / max(1, len(files_all)), 4),
             "time_share": round(T(s) / tot, 4), "test_s": round(T(s), 2),
             "missed": SEL.missed(truth, s)}
        for k, v in ref.items():
            if v is None:
                continue
            r[f"skipped_{k}"] = len(v - s)
            r[f"skipped_{k}_files"] = len(_files(v) - f)
        r.update(extra.get(name, {}))
        out[name] = r
    return out


def scenario(tree, cov, universe, plain, base_fail, assets, p, c, which, d):
    if which == "S":
        changed = apply_source(tree, p, c)
        restored = []
    else:
        restored = apply_full(tree, p, c)
        changed = [f for _, f in _changed(tree, p, c)]
    ref, ch = affected(tree, cov, universe)
    apply_to = (lambda t: apply_source(t, p, c)) if which == "S" else (lambda t: apply_full(t, p, c))
    sets, extra = selections(tree, cov, universe, assets, p, apply_to, ch.files or changed)
    t = time.time()
    try:
        outc = PL.run_tests(tree, os.path.join(d, f"{which}_outcomes.json"))
    except subprocess.TimeoutExpired:
        return {"timeout": True, "changed": len(changed)}
    run_s = round(time.time() - t, 1)
    ok = PL.ok_filter(base_fail)
    fails = sorted(n for n in PL.failing(outc) if ok(n))
    new = sorted(n for n in fails if n not in universe and not ("::" not in n and n in _files(universe)))
    fails = [n for n in fails if n not in new]
    conf, flaky_s, flaky_p = confirm(tree, fails, p, c, which, d)
    edited_tests = [f for f in changed if I._is_test_path(f) and f.endswith(".py")] if which == "F" else []
    return {"changed": len(changed), "changed_src_py": len(ch.files), "new_source_files": len(ch.new_files),
            "run_s": run_s, "outcomes": len(outc), "failing": conf, "flaky": flaky_s, "flaky_at_parent": flaky_p,
            "new_tests_failing": len(new), "ref": {k: (None if v is None else len(v)) for k, v in ref.items()},
            "ref_files": {k: (None if v is None else len(_files(v))) for k, v in ref.items()},
            "tree_repaired": restored[:20], "tools": score(sets, extra, universe, plain, conf, ref, edited_tests)}


def prepare_assets(tree, p, i, d, avail, side_tree=None):
    """The other tools' data at P, each timed; errors are kept for the rows. side_tree(name) makes another tree at P
    (default: a clone of the project at P; B1b passes clones of its own tree, whose P exists only there)."""
    side_tree = side_tree or (lambda name: PL.make_tree(name, p))
    a, secs = {}, {}
    if avail["testmon"]:
        try:
            t = time.time()
            db = PL.testmon(tree, os.path.join(d, "testmondata"))
            secs["testmon_record_s"] = round(time.time() - t, 1)
            if db:
                a["testmon"] = db
            else:
                a["testmon_error"] = "testmon recorded no executions"
        except Exception as e:  # noqa: BLE001
            a["testmon_error"] = repr(e)[:300]
    else:
        a["testmon_error"] = "not installed"
    if avail["namerts"]:
        try:
            nr_tree = side_tree(f"b1-nr-w{i}")
            t = time.time()
            a["nr_cache"] = PL.nrinit(nr_tree, os.path.join(d, "nr-cache"))
            secs["namerts_init_s"] = round(time.time() - t, 1)
            a["nr_tree"] = nr_tree
        except Exception as e:  # noqa: BLE001
            a["nr_error"] = repr(e)[:300]
    else:
        a["nr_error"] = "not installed"
    if avail["tdad"] and PL.REPO not in PL.TDAD_SKIP:
        try:
            import tdad_select as T
            tt = side_tree(f"b1-tdad-w{i}")
            import shutil
            shutil.rmtree(os.path.join(tt, ".tdad"), ignore_errors=True)
            t = time.time()
            T.index(tt)
            secs["tdad_index_s"] = round(time.time() - t, 1)
            a["tdad_tree"] = tt
        except Exception as e:  # noqa: BLE001
            a["tdad_error"] = repr(e)[:300]
    else:
        a["tdad_error"] = PL.TDAD_SKIP.get(PL.REPO, "not installed")
    return a, secs


def use_targets(tree):
    """The project's test targets that exist in this tree (test layouts move over history, e.g. pvlib's pvlib/tests ->
    tests), as nrbench.run_pair does; pytest refuses a run naming a missing path."""
    want = PROJECTS[PL.REPO]["targets"] if PL.REPO in PROJECTS else PL.CFG["targets"]
    PL.CFG["targets"] = [t for t in want if os.path.exists(os.path.join(tree, t))] or list(want)


def run_pair(p, c, info, i):
    d = os.path.join(PL.WORK, "b1", c[:12])
    os.makedirs(d, exist_ok=True)
    tree = PL.make_tree(f"b1-w{i}", p)
    use_targets(tree)
    if PL.CFG.get("sync"):
        PL.CFG["sync"](tree, PL.PY)
    t = time.time()
    try:
        base = PL.run_tests(tree, os.path.join(d, "base_outcomes.json"))
    except subprocess.TimeoutExpired:
        return {"status": "skip", "why": "the suite timed out at the parent"}
    base_s = round(time.time() - t, 1)
    test_files = {n for n in base if "::" not in n} | _files(n for n in base if "::" in n)
    broken = {n for n in base if "::" not in n and not base[n][0]}
    if not base or len(broken) * 2 > len(test_files):
        return {"status": "skip", "why": f"does not build here: {len(broken)} of {len(test_files)} test files fail to "
                                         f"collect at the parent", "outcomes": len(base)}
    plain = {k: tt for k, (ok_, tt) in base.items()}
    base_fail = PL.failing(base)
    t = time.time()
    workers = max(1, PL.WORKERS // max(1, int(os.environ.get("B1_PAIR_WORKERS", "1"))))
    cov = covmap_at(tree, os.path.join(d, "covmap.json"), p, workers)
    record_s = round(time.time() - t, 1)
    universe = PL.universe_of(cov, base_fail)
    avail = tools_available()
    assets, asset_s = prepare_assets(tree, p, i, d, avail)
    row = {"status": "ok", "base_s": base_s, "base_tests": len(base), "base_failing": len(base_fail),
           "test_files": len(test_files), "collect_errors": len(broken), "collect_error_files": sorted(broken)[:20], "universe": len(universe), "universe_s": round(sum(plain.get(n, 0)
                                                                                           for n in universe), 2),
           "record_s": record_s, **asset_s, "tools_available": avail}
    try:
        row["S"] = scenario(tree, cov, universe, plain, base_fail, assets, p, c, "S", d)
        if FULL:
            to_parent(tree, p)
            row["F"] = scenario(tree, cov, universe, plain, base_fail, assets, p, c, "F", d)
    finally:
        to_parent(tree, p)
    if info.get("namerts_gt") is not None:   # NameRTS's own ground truth and published selection for this pair
        gt, pub = set(info["namerts_gt"]), set(info["namerts_published"])
        prov = row.get("F", row["S"]).get("tools", {}).get("proviso", {})
        row["namerts_metric"] = {"gt_files": len(gt), "total_tests": info["namerts_total"],
                                 "published_files": len(pub), "published_safe": gt <= pub,
                                 "gt_not_recorded": sorted(gt - _files(universe))[:20],
                                 "proviso_files": prov.get("files")}
    return row


# --------------------------------------------------------------------------------------------- driver

def rows(name=None):
    out = {}
    for path in sorted(glob.glob(os.path.join(OUT, name or PL.REPO, "rows.w*.jsonl"))):
        for line in open(path):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("format") == PL.ROW_FORMAT:
                out[r["id"]] = r
    return out


def worker(i, n, limit, want):
    done = rows()
    cands = candidates(limit)
    for k, (p, c, info) in enumerate(cands):
        if k % n != i or c in done:
            continue
        ok_ = sum(r.get("status") == "ok" for r in rows().values())
        if ok_ >= want:
            break
        t = time.time()
        try:
            r = run_pair(p, c, info, i)
        except Exception as e:  # noqa: BLE001
            r = {"status": "error", "error": repr(e)[:500]}
        r = {"id": c, "parent": p, "rank": k, **{kk: v for kk, v in info.items() if not kk.startswith("namerts_")},
             **r, "secs": round(time.time() - t, 1), "format": PL.ROW_FORMAT, "env": fingerprint(),
             "proviso": proviso_version()}
        with open(os.path.join(res(), f"rows.w{i}.jsonl"), "a") as fh:
            fh.write(json.dumps(r) + "\n")
        s = r.get("S", {}).get("tools", {}).get("proviso", {})
        log(f"[{k}] {c[:10]} {r['status']}", r.get("why") or r.get("error") or
            f"S fails {len(r.get('S', {}).get('failing', []))} proviso {s.get('selected')}/{r.get('universe')} "
            f"missed {len(s.get('missed', []))} ({r['secs']} s)")


def main_project(name, want, workers):
    use(name)
    import fcntl
    lock = open(os.path.join(PL.WORK, "b1.lock"), "w")
    try:   # two runs on one project would share its trees (b1-w<i>) and break each other's checkouts
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(f"another b1.py run on {name} is active (lock {lock.name})")
    PL.require_importable() if PL.CFG.get("commit") else None
    limit = want * 3 if PL.CFG["source"] == "history" else want
    candidates(limit)   # fail early (and clone) before starting workers
    if workers <= 1:
        worker(0, 1, limit, want)
        return
    procs = [subprocess.Popen([PL.PY, os.path.abspath(__file__), name, "--worker", str(i), str(workers), str(limit),
                               str(want)], stdout=open(os.path.join(PL.WORK, f"b1.w{i}.log"), "a"),
                              stderr=subprocess.STDOUT) for i in range(workers)]
    for pr in procs:
        pr.wait()


# --------------------------------------------------------------------------------------------- report

def _med(xs, nd=1):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), nd) if xs else "n/a"


def report(names):
    if not names:
        names = sorted(d for d in os.listdir(OUT) if os.path.isdir(os.path.join(OUT, d))) if os.path.isdir(OUT) else []
    lines = ["# B1: real consecutive history", ""]
    for name in names:
        rs = list(rows(name).values())
        ok = [r for r in rs if r.get("status") == "ok"]
        if not rs:
            continue
        lines += [f"## {name}", "", f"Pairs: {len(ok)} ok, {sum(r.get('status') == 'skip' for r in rs)} skipped "
                  f"(do not build here), {sum(r.get('status') == 'error' for r in rs)} errors. Environment hashes: "
                  f"{sorted({r['env']['hash'] for r in rs if 'env' in r})}.", ""]
        for sc in ("S", "F"):
            have = [r for r in ok if sc in r and not r[sc].get("timeout")]
            if not have:
                continue
            brk = [r for r in have if r[sc]["failing"]]
            tools = sorted({t for r in have for t in r[sc]["tools"]})
            lines += [f"### Scenario {sc} ({'behaviour change' if sc == 'S' else 'full commit'}): {len(have)} pairs, "
                      f"{len(brk)} break a test; flaky failures dropped {sum(len(r[sc]['flaky']) for r in have)}, "
                      f"flaky at parent {sum(len(r[sc]['flaky_at_parent']) for r in have)}", "",
                      "| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | "
                      "Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |",
                      "|---|---|---|---|---|---|---|---|---|---|"]
            for t in tools:
                rr = [r for r in have if "error" not in r[sc]["tools"].get(t, {"error": 1})]
                if not rr:
                    err = next(r[sc]["tools"][t]["error"] for r in have if t in r[sc]["tools"])
                    lines.append(f"| {t} | 0 | n/a: {err[:80]} | | | | | | | |")
                    continue
                g = lambda r: r[sc]["tools"][t]
                bb = [r for r in rr if r[sc]["failing"]]
                safe = [r for r in rr if r[sc]["ref"].get("func") is not None]
                lines.append(
                    f"| {t} | {len(rr)} | {sum(bool(g(r)['missed']) for r in bb)}/{len(bb)} | "
                    f"{sum(len(g(r)['missed']) for r in bb)}/{sum(len(r[sc]['failing']) for r in bb)} | "
                    f"{sum(g(r).get('skipped_func_files', 0) == 0 for r in safe)}/{len(safe)} | "
                    f"{_med(g(r).get('skipped_exec') for r in rr)} | "
                    f"{_med(100 * g(r)['selected'] / max(1, r['universe']) for r in rr)} | "
                    f"{_med(100 * g(r)['time_share'] for r in rr)} | "
                    f"{round(100 * statistics.mean(g(r)['testr'] for r in rr), 1)} | "
                    f"{sum(bool(g(r).get('full')) for r in rr)} |")
            lines.append("")
        lines += ["### Overhead (seconds, median over ok pairs)", "",
                  "| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | "
                  "NameRTS init | TDAD index |", "|---|---|---|---|---|---|",
                  f"| {_med(r['base_s'] for r in ok)} | {_med(r['record_s'] for r in ok)} | "
                  f"{_med(r['S']['tools']['proviso'].get('selection_cold_s') for r in ok if 'tools' in r.get('S', {}))} / "
                  f"{_med(r['S']['tools']['proviso'].get('selection_s') for r in ok if 'tools' in r.get('S', {}))} | "
                  f"{_med(r.get('testmon_record_s') for r in ok)} | {_med(r.get('namerts_init_s') for r in ok)} | "
                  f"{_med(r.get('tdad_index_s') for r in ok)} |", ""]
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "report":
        report(a[1:])
    elif "--worker" in a:
        k = a.index("--worker")
        use(a[0])
        worker(int(a[k + 1]), int(a[k + 2]), int(a[k + 3]), int(a[k + 4]))
    elif "--list" in a:
        use(a[0])
        n = int(a[a.index("--list") + 1]) if len(a) > a.index("--list") + 1 else 50
        for p, c, info in candidates(n):
            print(p[:10], c[:10], json.dumps({k: v for k, v in info.items() if not k.startswith("namerts_")}))
    else:
        w, rest, it = 1, [], iter(a)
        for x in it:
            if x == "--workers":
                w = int(next(it))
            else:
                rest.append(x)
        main_project(rest[0], int(rest[1]) if len(rest) > 1 else 50, w)
