"""Full-suite ground truth for the SWE-bench agent regressions: every test the agent patch breaks, not only those
SWE-bench ran (it runs just the test files of the reference test patch, near the bug).

For each instance (after swe_eval.py and swe_eval_namerts.py; their maps and NameRTS caches are reused):
  1. the whole suite at the base commit, twice (one interpreter per test file, in parallel, the same per-file limit
     as Proviso's recorder); a test counts only if it passes in both runs;
  2. per case: the agent patch applied as swe_eval.py applies it; Proviso v2.2's selection and NameRTS's selection
     computed again (both are deterministic; Proviso's is checked against its eval row); the whole suite after the
     patch; the tests that passed at base and fail after are run again after the patch, and those that fail again
     are the ground truth (a test file that no longer collects fails all its tests);
  3. a case is missed by a tool when a ground-truth test is outside its selection; undetected when every one is.
Resumable; one run at a time (swe_eval's lock). No API cost.

Usage (PC): python3 research/v2/swe_fullsuite.py [--held-out|--core] [--skip-repo R,..] [--limit N] [--workers W]
Output: research/v2/results/swe/fullsuite-v<VERSION>.jsonl and fullsuite-v<VERSION>.md"""
from __future__ import annotations

import argparse
import collections
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swe_eval as E  # noqa: E402
import swe_eval_namerts as N  # noqa: E402
import swe_probe as P  # noqa: E402

OUT, WORK = P.OUT, P.WORK
FS_FORMAT = 1
FILE_TIMEOUT = int(os.environ.get("SWE_FULLSUITE_FILE_TIMEOUT", "900"))
PLUG = os.path.join(HERE, "plug")


def run_env(tree: str, py: str) -> dict:
    extra = [os.path.join(tree, "src")] if os.path.isdir(os.path.join(tree, "src")) else []
    return {**os.environ, "PYTHONPATH": os.pathsep.join([tree, *extra, PLUG]), "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": os.path.dirname(py) + os.pathsep + os.environ.get("PATH", "")}


def run_file(tree: str, py: str, f: str, env: dict) -> dict:
    """{node id: True (passed) | False (failed)} for one test file in its own interpreter; {f: None} if it ran out
    of time (its tests are then unknown)."""
    fd, out = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    base = [py, "-m", "pytest", "-p", "outcomes", "-p", "no:cacheprovider", "-p", "no:randomly", "-q", "--tb=no"]
    try:
        for extra in ([], ["-o", "addopts="]):
            try:
                r = subprocess.run([*base, *extra, f], cwd=tree, capture_output=True, text=True,
                                   timeout=FILE_TIMEOUT, env={**env, "OUTCOMES_OUT": out})
            except subprocess.TimeoutExpired:
                return {f: None}
            try:
                res = json.load(open(out))
            except (OSError, ValueError):
                res = {}
            if res or r.returncode not in (3, 4):   # 3/4: internal or usage error (e.g. an addopts plugin missing)
                return {k: bool(v[0]) for k, v in res.items()}
        return {}
    finally:
        if os.path.exists(out):
            os.remove(out)


def run_suite(tree: str, py: str, files: list[str], workers: int) -> dict:
    env = run_env(tree, py)
    res: dict = {}
    with ThreadPoolExecutor(workers) as ex:
        for part in ex.map(lambda f: run_file(tree, py, f, env), files):
            res.update(part)
    return res


def outcome(res: dict, node: str) -> bool | None:
    """True passed, False failed (also when its file no longer collects), None unknown (not run, timed out)."""
    f = node.split("::", 1)[0]
    if node in res:
        return res[node]
    if f in res:
        return None if res[f] is None else (False if res[f] is False else None)
    return None


def gone_files(res: dict, files: list[str], base_files: set[str]) -> dict:
    """A test file that reported tests at base and reports nothing after the patch (pytest stopped before collecting
    it: a conftest or the package no longer imports) fails all its tests."""
    seen = {k.split("::", 1)[0] for k in res}
    return {**res, **{f: False for f in files if f in base_files and f not in seen}}


def base_runs(inst: str, tree: str, py: str, files: list[str], workers: int) -> tuple[dict, dict]:
    d = os.path.join(WORK, "fullsuite", inst)
    os.makedirs(d, exist_ok=True)
    out = []
    for i in (1, 2):
        p = os.path.join(d, f"base{i}.json")
        if os.path.exists(p):
            out.append(json.load(open(p)))
            continue
        E.reset_tree(tree)
        res = run_suite(tree, py, files, workers)
        json.dump(res, open(p, "w"))
        out.append(res)
    return out[0], out[1]


def namerts_selection(inst: str, repo: str, meta: dict, case: dict, py: str, workers: int) -> set[str] | None:
    """NameRTS's selected test files for the case, from its cache of the NameRTS pass (None: NameRTS did not run)."""
    cache = os.path.join(WORK, "nr-cache", inst)
    if not os.path.isfile(os.path.join(cache, "nbdp_cache.json")):
        return None
    info = json.load(open(os.path.join(cache, "init.json"))) if os.path.exists(os.path.join(cache, "init.json")) else {}
    tree = os.path.join(WORK, "nr-trees", repo)
    if not os.path.isdir(tree):
        tree = E.prepare_tree(meta, py, trees="nr-trees")
    try:
        E.reset_tree(tree)
        N.apply_patch(tree, meta, case)
        out = N.driver("select", repo, tree, cache, py, workers, os.path.join(WORK, "nr-logs", f"{inst}.fs.select.log"))
    finally:
        E.reset_tree(tree)
    for line in out.splitlines():
        if line.startswith("NAMERTS_SELECTED "):
            sel = json.loads(line[len("NAMERTS_SELECTED "):])
            return {os.path.relpath(f, tree) if os.path.isabs(f) else f for f in sel} | set(info.get("timed_out_files")
                                                                                            or [])
    raise RuntimeError("NameRTS printed no selection")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", action="store_true")
    ap.add_argument("--held-out", action="store_true")
    ap.add_argument("--skip-repo", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    lock = open(os.path.join(WORK, "swe_eval.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit("a swe_eval run is active (lock: " + lock.name + ")")
    tag = f"v{E.I.VERSION}"
    prov = {}
    for line in open(os.path.join(OUT, f"eval-{tag}.jsonl")):
        r = json.loads(line)
        if "error" not in r:
            prov[(r["instance"], r["case"])] = r
    sample = json.load(open(os.path.join(OUT, "sample.json")))["instances"]
    skip = set(filter(None, a.skip_repo.split(",")))
    sample = [x for x in sample if (not a.core or x["core"]) and (not a.held_out or not x["core"])
              and x["repo"] not in skip]
    if a.limit:
        sample = sample[:a.limit]
    meta = P.load_instances()
    out_path = os.path.join(OUT, f"fullsuite-{tag}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r.get("format") == FS_FORMAT and "error" not in r:
                done.add((r["instance"], r["case"]))
    for x in sample:
        inst, repo = x["instance"], x["repo"]
        todo = [k for k in range(len(x["cases"])) if (inst, k) in prov and (inst, k) not in done]
        if not todo:
            continue
        py = os.path.join(WORK, "envs", f"{repo}__{x['version']}", "bin", "python")
        t0 = time.time()
        try:
            E.prepare_tree(meta[inst], py, trees="nr-trees")   # first, so the env's editable install ends on the eval tree
            tree = E.prepare_tree(meta[inst], py)
            cov, _ = E.record_map(inst, repo, tree, py, a.workers)
            nodes = sorted(E.I.tests_of(cov))
            files = sorted({n.split("::", 1)[0] for n in nodes if os.path.exists(os.path.join(tree, n.split("::", 1)[0]))})
            b1, b2 = base_runs(inst, tree, py, files, a.workers)
        except Exception as e:  # noqa: BLE001
            for k in todo:
                E.write(out_path, {"instance": inst, "repo": repo, "case": k, "error": repr(e)[:400], "format": FS_FORMAT})
            print(f"{inst}: ERROR {repr(e)[:200]}", flush=True)
            continue
        stable = {n for n in set(b1) | set(b2) if "::" in n and b1.get(n) is True and b2.get(n) is True}
        base_files = {n.split("::", 1)[0] for n in stable}
        test_files = P.test_files_of_patch(meta[inst].get("test_patch"))
        for k in todo:
            c, pr = x["cases"][k], prov[(inst, k)]
            row = {"instance": inst, "repo": repo, "case": k, "core": x["core"], "submission": c["submission"],
                   "swe_reproduced": pr.get("reproduced") or [], "base_stable": len(stable)}
            try:
                E.reset_tree(tree)
                patch = open(c["patch"]).read()
                ref = set(re.findall(r"(?m)^\+\+\+ b/(\S+)$", meta[inst].get("test_patch") or ""))
                patch, _ = E.without_files(patch, ref)
                E.apply_patch(tree, patch)
                sel, why = E.I.selection(tree, cov, py)
                files_run = {e for e in (sel or []) if "::" not in e}
                chosen = set(nodes) if sel is None else \
                    (set(sel) & set(nodes)) | {n for n in nodes if n.split("::", 1)[0] in files_run}
                row["proviso_selected"] = len(chosen)
                row["proviso_matches_eval"] = len(chosen) == pr.get("selected")
                after = gone_files(run_suite(tree, py, files, a.workers), files, base_files)
                cand = sorted(n for n in stable if outcome(after, n) is False)
                cand_files = sorted({n.split("::", 1)[0] for n in cand})
                again = gone_files(run_suite(tree, py, cand_files, a.workers), cand_files, base_files) if cand else {}
                truth = [n for n in cand if outcome(again, n) is False]
                row["truth"] = truth
                swe_keys = {kk for t in row["swe_reproduced"] for kk in E.resolve(t, nodes, test_files)}
                row["beyond_swebench"] = [n for n in truth if n not in swe_keys]
                p_missed = [n for n in truth if n not in chosen]
                row.update(proviso_missed=p_missed, proviso_undetected=bool(truth) and len(p_missed) == len(truth))
            except Exception as e:  # noqa: BLE001
                row["error"] = repr(e)[:400]
            finally:
                E.reset_tree(tree)
            if "error" not in row:
                try:
                    nsel = namerts_selection(inst, repo, meta[inst], c, py, a.workers)
                except Exception as e:  # noqa: BLE001
                    nsel, row["namerts_error"] = None, repr(e)[:300]
                if nsel is not None:
                    n_missed = [n for n in row["truth"] if n.split("::", 1)[0] not in nsel]
                    row.update(namerts_files=len(nsel), namerts_missed=n_missed,
                               namerts_undetected=bool(row["truth"]) and len(n_missed) == len(row["truth"]))
            row["format"] = FS_FORMAT
            E.write(out_path, row)
            if "error" in row:
                print(f"{inst} case {k}: ERROR {row['error'][:150]}", flush=True)
            else:
                nm = row.get("namerts_missed")
                print(f"{inst} case {k}: {len(row['truth'])} broken in the whole suite "
                      f"({len(row['beyond_swebench'])} beyond SWE-bench's); Proviso missed {len(row['proviso_missed'])}"
                      + ("" if nm is None else f", NameRTS missed {len(nm)}"), flush=True)
        print(f"{inst}: done in {round(time.time() - t0)} s", flush=True)
    summary(out_path)


def summary(out_path: str):
    rows = {}
    for line in open(out_path):
        r = json.loads(line)
        rows[(r["instance"], r["case"])] = r
    ok = [r for r in rows.values() if "error" not in r]
    lines = [f"# Full-suite ground truth: every test the agent patch breaks (Proviso v{E.I.VERSION}, NameRTS)", "",
             "Cases with at least one test that passes twice at base and fails twice after the patch. Missed: a "
             "broken test outside the tool's selection. Undetected: every broken test outside it. NameRTS columns "
             "count only cases where NameRTS ran.", ""]
    for label, part in (("core sample", True), ("held-out instances", False)):
        sub = [r for r in ok if r["core"] == part]
        if not sub:
            continue
        lines += [f"## {label}", "", "| repository | cases | with broken tests | broken tests | beyond SWE-bench's | "
                  "Proviso missed | Proviso undetected | NameRTS ran | NameRTS missed | NameRTS undetected |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        groups = collections.defaultdict(list)
        for r in sub:
            groups[r["repo"]].append(r)
        for label2, rs in [*sorted(groups.items()), ("**all**", sub)]:
            br = [r for r in rs if r["truth"]]
            nr = [r for r in br if "namerts_missed" in r]
            lines.append(f"| {label2} | {len(rs)} | {len(br)} | {sum(len(r['truth']) for r in br)} | "
                         f"{sum(len(r['beyond_swebench']) for r in br)} | {sum(1 for r in br if r['proviso_missed'])} | "
                         f"{sum(1 for r in br if r['proviso_undetected'])} | {len(nr)} | "
                         f"{sum(1 for r in nr if r['namerts_missed'])} | {sum(1 for r in nr if r['namerts_undetected'])} |")
        mism = [r for r in sub if not r.get("proviso_matches_eval", True)]
        lines += ["", f"Proviso's selection differs from its eval row in {len(mism)} case(s).", ""]
    errs = [r for r in rows.values() if "error" in r]
    if errs:
        lines.append(f"Errors: {len(errs)} case(s).")
    md = out_path[:-len(".jsonl")] + ".md"
    open(md, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
