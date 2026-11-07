"""NameRTS on the same real agent regressions as swe_eval.py (run after it: it reuses its rows and dependency maps).

For each instance of the sample that swe_eval.py evaluated:
  1. the same tree (base commit + SWE-bench's reference tests, committed) in a separate directory (NameRTS rewrites
     source files while it runs), installed into the same Python 3.12 environment;
  2. NameRTS's initial run (namerts_driver.py init: its instrumented, per-test-file isolated run of the whole suite);
  3. per case: the same agent patch (same reduction: the files of the reference tests left out), NameRTS selects
     test FILES (namerts_driver.py select).
Scoring, on the cases where the regression reproduced here (swe_eval.py's `reproduced`, same patch, same environment):
a case is missed when a file holding one of the broken tests is not selected; time share = the test time (from
Proviso's map of that instance, as in the main benchmark) of the tests in the selected files over the whole suite.
Resumable; one run at a time (shares swe_eval.py's lock: both use the same environments). No API cost.

Usage (PC, after swe_eval.py; NameRTS at $NAMERTS_HOME, default $PROVISO_WORK/NameRTS, its dependencies in this venv):
  python3 research/v2/swe_eval_namerts.py [--core] [--limit N] [--repo R] [--workers W]
Output: research/v2/results/swe/eval_namerts.jsonl, eval_compare.md (Proviso and NameRTS on the same cases)."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swe_eval as E  # noqa: E402
import swe_probe as P  # noqa: E402

OUT, WORK = P.OUT, P.WORK
NR_FORMAT = 1
INIT_TIMEOUT = int(os.environ.get("NAMERTS_INIT_TIMEOUT", str(6 * 3600)))
SELECT_TIMEOUT = int(os.environ.get("NAMERTS_SELECT_TIMEOUT", "3600"))
# the same per-test-file limit as Proviso's recorder in swe_eval.py (PROVISO_RECORD_FILE_TIMEOUT, 900 s there): a
# file whose tests run longer in NameRTS's initial run is cut off (plug/nrts_reap.py) and its tests always selected
FILE_TIMEOUT = int(os.environ.get("NAMERTS_FILE_TIMEOUT", "900"))
EXECNET = "execnet==2.1.1"   # NameRTS's pinned version (environment_313.yml); its pytest-xdist needs it in the env


def nr_env(repo: str, tree: str, py: str, workers: int) -> dict:
    base = os.environ.get("PROVISO_WORK", os.path.expanduser("~/proviso-work/v2"))
    extra = ([os.path.join(tree, "src")] if os.path.isdir(os.path.join(tree, "src")) else []) + [os.path.join(HERE, "plug")]
    return {**os.environ,
            "NAMERTS_HOME": os.environ.get("NAMERTS_HOME", os.path.join(base, "NameRTS")),
            "NAMERTS_BIN": os.path.join(HERE, "nrts-bin"), "NAMERTS_DEPS": os.environ.get("NAMERTS_DEPS", ""),
            "NAMERTS_LOGS": os.path.join(WORK, "nr-logs"), "NAMERTS_SCOPE": ",".join(E.LAYOUT[repo][1]),
            "NAMERTS_WORKERS": str(workers), "NAMERTS_TEST_DIRS": "",
            "NAMERTS_EXTRA_PATH": os.pathsep.join(extra),
            "PROVISO_PY": py,   # nrts-bin/pytest runs `$PROVISO_PY -m pytest`: the tests run in the instance's env
            # end each finished per-file worker at once (NameRTS's isolation mode keeps them all until the run ends:
            # hundreds of idle processes on sympy, out of memory); outcomes and NameRTS's records are unchanged
            "NRTS_PYTEST_ARGS": "" if os.environ.get("NAMERTS_NO_REAP") else "-p nrts_reap",
            "PATH": os.path.dirname(py) + os.pathsep + os.environ.get("PATH", "")}


def kill_strays(tree: str) -> int:
    """SIGKILL leftover execnet worker processes (pytest-xdist's `python -c "import sys;exec(eval(...))"` gateways)
    running in this tree: after a timeout or crash they can outlive NameRTS's process group."""
    n = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read()
            if b"exec(eval(sys.stdin.readline()))" in cmd and \
                    os.path.realpath(os.readlink(f"/proc/{pid}/cwd")).startswith(os.path.realpath(tree)):
                os.kill(int(pid), signal.SIGKILL)
                n += 1
        except (OSError, ValueError):
            continue
    return n


def driver(action: str, repo: str, tree: str, cache: str, py: str, workers: int, log: str,
           extra_env: dict | None = None) -> str:
    """namerts_driver.py in its own process group (killed whole on timeout: NameRTS starts pytest through a shell)."""
    cmd = [sys.executable, os.path.join(HERE, "namerts_driver.py"), action, tree, cache,
           "sympy" if repo == "sympy__sympy" else repo.split("__")[1]]
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "w") as fh:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fh, text=True, start_new_session=True,
                             env={**nr_env(repo, tree, py, workers), **(extra_env or {})})
        try:
            out, _ = p.communicate(timeout=INIT_TIMEOUT if action == "init" else SELECT_TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            raise RuntimeError(f"NameRTS {action} exceeded "
                               f"{INIT_TIMEOUT if action == 'init' else SELECT_TIMEOUT} s")
        finally:
            strays = kill_strays(tree)
            if strays:
                fh.write(f"\n[swe_eval_namerts] killed {strays} leftover worker processes\n")
        fh.write("\n--- stdout ---\n" + out)
    if p.returncode:
        raise RuntimeError(f"NameRTS {action} exit {p.returncode}: " + open(log).read()[-400:])
    return out


def ensure_execnet(py: str):
    r = P.run([py, "-c", "import execnet"])
    if r.returncode:
        r = P.run(["uv", "pip", "install", "-q", "--python", py, EXECNET], timeout=600)
        if r.returncode:
            raise RuntimeError("execnet install: " + r.stderr[-300:])


def init(inst: str, repo: str, tree: str, py: str, workers: int) -> tuple[str, dict]:
    cache = os.path.join(WORK, "nr-cache", inst)
    meta = os.path.join(cache, "init.json")
    if os.path.exists(meta) and os.path.isfile(os.path.join(cache, "nbdp_cache.json")):
        return cache, json.load(open(meta))
    shutil.rmtree(cache, ignore_errors=True)
    timed = os.path.join(WORK, "nr-timeouts", inst)
    shutil.rmtree(timed, ignore_errors=True)
    t = time.time()
    out = driver("init", repo, tree, cache, py, workers, os.path.join(WORK, "nr-logs", inst + ".init.log"),
                 {"NRTS_FILE_TIMEOUT": str(FILE_TIMEOUT) if FILE_TIMEOUT else "", "NRTS_TIMEOUT_DIR": timed})
    deps = json.load(open(os.path.join(cache, "dependencies.json"))) if \
        os.path.exists(os.path.join(cache, "dependencies.json")) else {}
    if not (deps or {}).get("dynamic_deps"):
        shutil.rmtree(cache, ignore_errors=True)
        raise RuntimeError("NameRTS's own test run recorded nothing (dynamic_deps empty): " + out[-300:])
    over = set()
    if os.path.isdir(timed):
        for name in os.listdir(timed):
            over |= {l.strip() for l in open(os.path.join(timed, name)) if l.strip()}
    info = {"init_s": round(time.time() - t), "file_timeout": FILE_TIMEOUT, "timed_out_files": sorted(over)}
    for line in out.splitlines():
        if line.startswith("{"):
            try:
                info.update(json.loads(line))
            except ValueError:
                pass
    json.dump(info, open(meta, "w"))
    return cache, info


def apply_patch(tree: str, meta: dict, case: dict) -> list[str]:
    """The agent patch as swe_eval.py applies it (the reference tests' files left out; same fallbacks)."""
    patch = open(case["patch"]).read() if case.get("patch") and os.path.exists(case["patch"]) else None
    if not patch:
        raise RuntimeError("patch file missing")
    ref_files = set(re.findall(r"(?m)^\+\+\+ b/(\S+)$", meta.get("test_patch") or ""))
    patch, dropped = E.without_files(patch, ref_files)
    if not patch.strip():
        raise RuntimeError("the agent patch only edits files the reference tests replace")
    E.apply_patch(tree, patch)
    return dropped


PROVISO_TAG = ""   # --proviso-tag: compare with the rows of a later Proviso version (eval-TAG.jsonl)


def proviso_rows() -> dict:
    rows = {}
    path = os.path.join(OUT, f"eval-{PROVISO_TAG}.jsonl" if PROVISO_TAG else "eval.jsonl")
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            if r.get("format") == E.EVAL_FORMAT and "error" not in r:
                rows[(r["instance"], r["case"])] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", action="store_true")
    ap.add_argument("--held-out", action="store_true", help="only the instances after the core sample")
    ap.add_argument("--proviso-tag", default="", help="compare with eval-TAG.jsonl (e.g. v2.1) instead of eval.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="at most N instances (in the sample's order)")
    ap.add_argument("--repo", default="", help="only these repositories (comma-separated, e.g. pallets__flask)")
    ap.add_argument("--skip-repo", default="", help="leave these repositories out (comma-separated)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    global PROVISO_TAG
    PROVISO_TAG = a.proviso_tag
    lock = open(os.path.join(WORK, "swe_eval.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit("a swe_eval run is active (lock: " + lock.name + "); NameRTS runs after it")
    base = nr_env("sympy__sympy", "/", sys.executable, 1)["NAMERTS_HOME"]
    if not os.path.isdir(os.path.join(base, "src")):
        sys.exit(f"NameRTS not found at {base} (set NAMERTS_HOME)")
    prov = proviso_rows()
    sample = json.load(open(os.path.join(OUT, "sample.json")))["instances"]
    only, skip = set(filter(None, a.repo.split(","))), set(filter(None, a.skip_repo.split(",")))
    sample = [x for x in sample if (not a.core or x["core"]) and (not a.held_out or not x["core"])
              and (not only or x["repo"] in only)
              and x["repo"] not in skip
              and any((x["instance"], k) in prov for k in range(len(x["cases"])))]
    if a.limit:
        sample = sample[:a.limit]
    if not sample:
        sys.exit("no instance with swe_eval.py results to compare on")
    meta = P.load_instances()
    out_path = os.path.join(OUT, "eval_namerts.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r.get("format") == NR_FORMAT and "error" not in r:
                done.add((r["instance"], r["case"]))
    for x in sample:
        inst, repo = x["instance"], x["repo"]
        todo = [k for k in range(len(x["cases"])) if (inst, k) in prov and (inst, k) not in done]
        if not todo:
            continue
        py = os.path.join(WORK, "envs", f"{repo}__{x['version']}", "bin", "python")
        t0 = time.time()
        try:
            cov = json.load(open(os.path.join(WORK, "maps", inst + ".json")))
            tree = E.prepare_tree(meta[inst], py, trees="nr-trees")
            ensure_execnet(py)
            cache, info = init(inst, repo, tree, py, a.workers)
        except Exception as e:  # noqa: BLE001
            for k in todo:
                E.write(out_path, {"instance": inst, "repo": repo, "case": k, "error": repr(e)[:400],
                                   "format": NR_FORMAT})
            print(f"{inst}: ERROR {repr(e)[:200]}", flush=True)
            continue
        nodes = sorted(E.I.tests_of(cov))
        times = {n: cov[n].get("time", 0) or 0 for n in nodes}
        total = sum(times.values()) or 1e-9
        test_files = P.test_files_of_patch(meta[inst].get("test_patch"))
        for k in todo:
            pr = prov[(inst, k)]
            row = {"instance": inst, "repo": repo, "case": k, "submission": pr["submission"],
                   "reproduced": pr["reproduced"], "init_s": info.get("init_s"),
                   "init_test_s": info.get("test_time"), "proviso_record_s": pr.get("record_s")}
            try:
                E.reset_tree(tree)
                row["dropped_files"] = apply_patch(tree, meta[inst], x["cases"][k])
                t = time.time()
                out = driver("select", repo, tree, cache, py, a.workers,
                             os.path.join(WORK, "nr-logs", f"{inst}.{k}.select.log"))
                row["selection_s"] = round(time.time() - t, 2)
                sel = None
                for line in out.splitlines():
                    if line.startswith("NAMERTS_SELECTED "):
                        sel = json.loads(line[len("NAMERTS_SELECTED "):])
                if sel is None:
                    raise RuntimeError("NameRTS printed no selection: " + out[-300:])
                files = {os.path.relpath(f, tree) if os.path.isabs(f) else f for f in sel}
                over = set(info.get("timed_out_files") or [])
                row["nr_timed_out_files"] = len(over)
                files |= over   # cut off in NameRTS's initial run: always selected (Proviso's rule for its own)
                chosen = {n for n in nodes if n.split("::", 1)[0] in files}
                missed = []
                for t_ in pr["reproduced"]:
                    keys = E.resolve(t_, nodes, test_files)
                    need = {k_.split("::", 1)[0] for k_ in keys} or ({t_.split("::", 1)[0]} if "::" in t_ else set())
                    if not need or not need <= files:
                        missed.append(t_)
                row.update(selected_files=len(files), selected=len(chosen),
                           time_share=round(sum(times[n] for n in chosen) / total, 4),
                           missed=missed, caught=bool(pr["reproduced"]) and not missed)
            except Exception as e:  # noqa: BLE001
                row["error"] = repr(e)[:400]
            finally:
                E.reset_tree(tree)
            row["format"] = NR_FORMAT
            E.write(out_path, row)
            status = ("ERROR " + row["error"][:120]) if "error" in row else (
                "not reproduced here" if not row["reproduced"] else
                f"{'caught' if row['caught'] else 'MISSED ' + str(len(row['missed']))} "
                f"({len(row['reproduced'])} broken; {row['selected_files']} files, "
                f"{100 * row['time_share']:.0f}% of time)")
            print(f"{inst} case {k}: NameRTS {status}", flush=True)
        print(f"{inst}: done in {round(time.time() - t0)} s (NameRTS init {info.get('init_s')} s, "
              f"Proviso map {prov[(inst, todo[0])].get('record_s')} s)", flush=True)
    summary()


def summary():
    prov = proviso_rows()
    nr = {}
    for line in open(os.path.join(OUT, "eval_namerts.jsonl")):
        r = json.loads(line)
        nr[(r["instance"], r["case"])] = r
    core = {x["instance"] for x in json.load(open(os.path.join(OUT, "sample.json")))["instances"] if x["core"]}
    version = PROVISO_TAG or "v2"
    lines = [f"# Proviso ({version}) and NameRTS on the same real agent regressions (SWE-bench)", "",
             "Cases where the regression reproduced here and both tools ran. Time share: test time of the selection "
             "over the whole suite (Proviso's per-test times; NameRTS selects whole files). Missed: a case with a "
             "broken test not selected; undetected: no broken test selected.", ""]
    for label, part in (("core sample (development of v2.1)", True), ("held-out instances", False)):
        keys_all = [k for k in nr if (k[0] in core) == part]
        if not keys_all:
            continue
        lines += [f"## {label}", "",
                  "| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso undetected | "
                  "NameRTS undetected | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | "
                  "map / init time (median s) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        allp = []
        for repo in E.LAYOUT:
            keys = [k for k in keys_all if nr[k]["repo"] == repo]
            if not keys:
                continue
            errs = sum(1 for k in keys if "error" in nr[k])
            both = [(prov[k], nr[k]) for k in keys if "error" not in nr[k] and k in prov and prov[k].get("reproduced")]
            allp += both
            lines.append(_line(repo, both, errs))
        lines += [_line("**all**", allp, sum(1 for k in keys_all if "error" in nr[k])), ""]
    open(os.path.join(OUT, f"eval_compare-{PROVISO_TAG}.md" if PROVISO_TAG else "eval_compare.md"), "w").write(
        "\n".join(lines) + "\n")
    print("\n".join(lines))


def _line(label, both, errs):
    if not both:
        return f"| {label} | 0 | 0 | | | | | | | {errs} | |"
    undet = lambda r: bool(r["missed"]) and len(r["missed"]) >= len(r["reproduced"])  # noqa: E731
    rec = [p.get("record_s") or 0 for p, _ in both]
    ini = [n.get("init_s") or 0 for _, n in both]
    return (f"| {label} | {len({p['instance'] for p, _ in both})} | {len(both)} | "
            f"{sum(1 for p, _ in both if p['missed'])} | {sum(1 for _, n in both if n['missed'])} | "
            f"{sum(1 for p, _ in both if undet(p))} | {sum(1 for _, n in both if undet(n))} | "
            f"{100 * statistics.mean(p['time_share'] for p, _ in both):.1f}% | "
            f"{100 * statistics.mean(n['time_share'] for _, n in both):.1f}% | {errs} | "
            f"{statistics.median(rec):.0f} / {statistics.median(ini):.0f} |")


if __name__ == "__main__":
    main()
