"""B1b: real bugs from reversed SWE-bench fixes (evaluation plan, RQ1 and RQ2).

A SWE-bench task comes with a real developer fix and the tests that catch the bug (FAIL_TO_PASS). Start from the fixed
version with its tests (F = base commit + test patch + reference fix, committed), then reverse the fix's source
changes: the change reintroduces a real developer's bug whose failing tests are known (RTSCheck built DefectsEP the same
way from Defects4J). Every tool's data is collected at F; every tool selects for the reversal.

Ground truth: tests that fail after the reversal and passed at F, confirmed as in b1.py (fail in all 3 re-runs of the
reversal, pass in all 3 at F); FAIL_TO_PASS tests are part of it by construction, and whether each failed here is
recorded (a task whose FAIL_TO_PASS tests do not fail here is kept and flagged: the environment differs).
Tools, metrics and the affected-tests references are b1.py's (same functions).

Instances: SWE-bench's full test split ($PROVISO_WORK/swe/instances.jsonl, written by swe_regressions.py, with
patches) for the repositories with a working environment (results/swe/envs.jsonl, built by swe_probe.py), sampled by
repository with a fixed seed, round robin over repositories, at most N.

Usage (PC, after swe_probe.py has built the environments):
  python research/v2/b1b.py [N] [--repos a,b] [--workers W]     # resumable; results/b1b/rows.w*.jsonl
  python research/v2/b1b.py --list [N]                          # the sampled instances
  python research/v2/b1b.py report                              # results/b1b/report.md
Instances that share an environment run one after another (each is installed into it, editable); environments run in
parallel (--workers)."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
import swe_eval as E  # noqa: E402
import swe_probe as P  # noqa: E402
from dc_engine import impact as I  # noqa: E402

OUT = os.path.join(HERE, "results", "b1b")
SEED = "b1b-2026-11-24"
SRC_LAYOUT = {"pytest-dev__pytest": ["src"], "pallets__flask": ["src"]}   # src layout: import paths


def envs_ok() -> dict:
    out = {}
    path = os.path.join(P.OUT, "envs.jsonl")
    for line in open(path) if os.path.exists(path) else []:
        r = json.loads(line)
        if r.get("ok"):
            out[(r["repo"], r["version"])] = os.path.join(P.WORK, "envs", r["env"], "bin", "python")
    return out


def sample(n: int, repos: set | None = None) -> list[dict]:
    meta = P.load_instances()
    envs = envs_ok()
    by_repo: dict = {}
    for iid, x in sorted(meta.items()):
        repo = iid.rsplit("-", 1)[0]
        if repo not in E.LAYOUT or (repos and repo not in repos):
            continue
        if (repo, x.get("version")) not in envs or not x.get("patch") or not x.get("FAIL_TO_PASS"):
            continue
        by_repo.setdefault(repo, []).append(x)
    rnd = random.Random(SEED)
    for v in by_repo.values():
        rnd.shuffle(v)
    out, k = [], 0
    while len(out) < n and any(k < len(v) for v in by_repo.values()):
        for repo in sorted(by_repo):
            if k < len(by_repo[repo]) and len(out) < n:
                out.append(by_repo[repo][k])
        k += 1
    return out


def source_part(patch: str) -> str:
    """The patch's changes to non-test files (the reference fix sometimes touches a test helper too)."""
    keep = []
    for part in re.split(r"(?m)^(?=diff --git )", patch):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", part)
        if m and (I._is_test_path(m.group(1)) or I._is_test_path(m.group(2))):
            continue
        keep.append(part)
    return "".join(keep)


def configure(repo: str, py: str):
    """pipeline's project settings for this repository, under its own work folder (b1b-<repo>)."""
    pkg, targets = E.LAYOUT[repo]
    name = f"b1b-{repo}"
    PL.REPOS[name] = {"url": P.repo_clone(repo), "commit": None, "pkg": pkg, "targets": targets, "mutate": None,
                      "test_dirs": targets[0], "pythonpath": SRC_LAYOUT.get(repo, []), "pytest_args": [],
                      "before_test": "", "nr_repo": repo.split("__", 1)[1], "pip": []}
    PL.use(name)
    PL.PY = py
    b1._FP = None   # the environment fingerprint is per interpreter


def git(tree, *a, check=True, inp=None):
    r = subprocess.run(["git", "-c", "user.email=b1b@proviso", "-c", "user.name=proviso-b1b", "-C", tree, *a],
                       capture_output=True, text=True, input=inp)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a[:2])}: {r.stderr[-300:]}")
    return r.stdout


def fixed_tree(x: dict, i: int) -> tuple[str, str]:
    """(tree, F): the base commit + test patch + reference fix, committed in a worker tree, installed (editable)."""
    repo = x["instance_id"].rsplit("-", 1)[0]
    src = P.repo_clone(repo)
    P.ensure_commit(src, x["base_commit"])
    tree = os.path.join(PL.WORK, "trees", f"w{i}")
    if not os.path.isdir(os.path.join(tree, ".git")):
        os.makedirs(os.path.dirname(tree), exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", src, tree], check=True)
    git(tree, "fetch", "-q", src, x["base_commit"], check=False)
    git(tree, "checkout", "-q", "-f", x["base_commit"])
    git(tree, "clean", "-q", "-fdx", "-e", ".dc-engine")
    for what in ("test_patch", "patch"):
        if x.get(what):
            git(tree, "apply", "-", inp=x[what] if x[what].endswith("\n") else x[what] + "\n")
    git(tree, "add", "-A")
    # a fixed commit date makes F's hash the same in every run, so data recorded at F stays valid on a re-run
    when = git(tree, "log", "-1", "--format=%cI", x["base_commit"]).strip()
    os.environ.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    try:
        git(tree, "commit", "-q", "--allow-empty", "-m", f"{x['instance_id']}: fixed version with its tests")
    finally:
        os.environ.pop("GIT_AUTHOR_DATE", None)
        os.environ.pop("GIT_COMMITTER_DATE", None)
    f = git(tree, "rev-parse", "HEAD").strip()
    r = P.run(["uv", "pip", "install", "-q", "--python", PL.PY, "--no-deps", "-e", tree], timeout=1800)
    if r.returncode:
        if OLD_BUILD in r.stderr:
            # old versioneer build scripts (xarray 0.12-0.14) use configparser.SafeConfigParser, removed in Python
            # 3.12, which Proviso needs (sys.monitoring): no install; the tree is first on PYTHONPATH (pipeline.env)
            return tree, f, {"install": "skipped", "install_why": OLD_BUILD_WHY}
        raise RuntimeError("install: " + r.stderr[-300:])
    return tree, f, {}


OLD_BUILD = "SafeConfigParser"
OLD_BUILD_WHY = "old build script not runnable on Python 3.12"


def collection(tree: str, base: dict, f2p: list, test_patch: str) -> dict:
    """What collected at the fixed version (no install): test files with collected tests, out of the test files on disk
    in the targets (pytest's default names test_*.py, *_test.py); and the FAIL_TO_PASS tests with no collected node."""
    nodes = sorted(n for n in base if "::" in n)
    broken = {n for n in base if "::" not in n and not base[n][0]}
    collected = b1._files(nodes) - broken
    on_disk = set()
    for t in PL.CFG["targets"]:
        for root, dirs, fs in os.walk(os.path.join(tree, t)):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            on_disk |= {os.path.relpath(os.path.join(root, f), tree) for f in fs
                        if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py"))}
    total = len(on_disk | collected | broken)
    tp_files = re.findall(r"(?m)^diff --git a/\S+ b/(\S+)", test_patch)
    missing = [t for t in f2p if not E.resolve(t, nodes, tp_files)]
    return {"collected_test_files": len(collected), "test_files_total": total,
            "collected_share": round(len(collected) / max(1, total), 3), "collect_error_files": len(broken),
            "collect_error_file_names": sorted(broken)[:20], "test_files_seen": len(collected | broken),
            "f2p": len(f2p), "f2p_not_collected": missing[:20], "f2p_not_collected_n": len(missing)}


def importable(tree: str, pkg: str) -> str:
    """'' if the package imports from the tree (the tree's own copy, not an installed one), else the error's tail."""
    code = (f"import {pkg}, os, sys; f = os.path.realpath({pkg}.__file__); "
            f"sys.exit(0 if f.startswith(os.path.realpath(sys.argv[1]) + os.sep) else 'imported from ' + f)")
    r = subprocess.run([PL.PY, "-c", code, tree], cwd=tree, env=PL.env(tree), capture_output=True, text=True,
                       timeout=600)
    return "" if r.returncode == 0 else (r.stderr.strip().splitlines() or ["exit %d" % r.returncode])[-1][:300]


def side_tree(tree: str, f: str):
    def make(name):
        d = os.path.join(PL.WORK, "trees", name)
        if not os.path.isdir(os.path.join(d, ".git")):
            subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", tree, d], check=True)
        git(d, "fetch", "-q", tree, f, check=False)
        git(d, "checkout", "-q", "-f", f)
        git(d, "clean", "-q", "-fdx", "-e", ".dc-engine", "-e", ".tdad")
        return d
    return make


def reverse(tree: str, f: str, fix: str) -> list[str]:
    """The reference fix's source changes undone on F (HEAD stays at F). Returns the changed paths."""
    b1.to_parent(tree, f)
    git(tree, "apply", "-R", "-", inp=fix if fix.endswith("\n") else fix + "\n")
    return sorted(set(re.findall(r"(?m)^diff --git a/\S+ b/(\S+)", fix)))


def run_instance(x: dict, i: int) -> dict:
    fix = source_part(x["patch"])
    if not fix.strip():
        return {"status": "skip", "why": "the reference fix changes test files only"}
    d = os.path.join(PL.WORK, "b1b", x["instance_id"])
    os.makedirs(d, exist_ok=True)
    tree, f, inst = fixed_tree(x, i)
    if inst:   # not installed (old build script): run only if the package imports from the tree and its tests collect
        err = importable(tree, PL.CFG["pkg"])
        if err:
            return {"status": "skip", "why": f"{OLD_BUILD_WHY}; without install: {err}", **inst}
    t = time.time()
    base = PL.run_tests(tree, os.path.join(d, "base_outcomes.json"))
    base_s = round(time.time() - t, 1)
    if not base:
        return {"status": "skip", "why": (f"{OLD_BUILD_WHY}; without install the tests do not collect" if inst else
                                          "the suite produced no outcomes at the fixed version"), **inst}
    f2p = json.loads(x["FAIL_TO_PASS"]) if isinstance(x["FAIL_TO_PASS"], str) else x["FAIL_TO_PASS"]
    if inst:   # how much of the suite collects without install; every FAIL_TO_PASS test must be collected
        inst.update(collection(tree, base, f2p, x.get("test_patch") or ""))
        if inst["f2p_not_collected"]:
            return {"status": "skip", "why": f"{OLD_BUILD_WHY}; without install {inst['f2p_not_collected_n']} of "
                                             f"{len(f2p)} FAIL_TO_PASS tests not collected", **inst}
        if inst["collect_error_files"] * 2 > inst["test_files_seen"]:
            return {"status": "skip", "why": f"{OLD_BUILD_WHY}; without install {inst['collect_error_files']} of "
                                             f"{inst['test_files_seen']} test files fail to collect", **inst}
    plain = {k: tt for k, (ok_, tt) in base.items()}
    base_fail = PL.failing(base)
    t = time.time()
    cov = b1.covmap_at(tree, os.path.join(d, "covmap.json"), f)
    record_s = round(time.time() - t, 1)
    universe = PL.universe_of(cov, base_fail)
    avail = b1.tools_available()
    assets, asset_s = b1.prepare_assets(tree, f, i, d, avail, side_tree(tree, f))
    row = {"status": "ok", **inst, "base_s": base_s, "base_tests": len(base), "base_failing": len(base_fail),
           "universe": len(universe), "universe_s": round(sum(plain.get(n, 0) for n in universe), 2),
           "record_s": record_s, **asset_s, "tools_available": avail,
           "f2p": len(f2p), "f2p_failing_at_fixed": sorted(t_ for t_ in f2p if t_ in base_fail)[:10]}
    try:
        changed = reverse(tree, f, fix)
        ref, ch = b1.affected(tree, cov, universe)
        sets, extra = b1.selections(tree, cov, universe, assets, f, lambda t_: reverse(t_, f, fix),
                                    ch.files or changed)
        t = time.time()
        try:
            outc = PL.run_tests(tree, os.path.join(d, "R_outcomes.json"))
        except subprocess.TimeoutExpired:
            row["R"] = {"timeout": True}
            return row
        run_s = round(time.time() - t, 1)
        ok = PL.ok_filter(base_fail)
        fails = sorted(n for n in PL.failing(outc) if ok(n))
        new = [n for n in fails if n not in universe and not ("::" not in n and n in b1._files(universe))]
        fails = [n for n in fails if n not in new]
        conf, flaky_r, flaky_f = b1.confirm(tree, fails, f, None, "R", d)
        f2p_nodes = {n for t_ in f2p for n in E.resolve(t_, sorted(universe), [])}
        row["R"] = {"changed": changed, "changed_src_py": len(ch.files), "new_source_files": len(ch.new_files),
                    "run_s": run_s, "outcomes": len(outc), "failing": conf, "flaky": flaky_r,
                    "flaky_at_parent": flaky_f, "new_tests_failing": len(new),
                    "f2p_failing": sorted(f2p_nodes & set(conf))[:20], "f2p_resolved": len(f2p_nodes),
                    "other_failing": len(set(conf) - f2p_nodes),
                    "ref": {k: (None if v is None else len(v)) for k, v in ref.items()},
                    "ref_files": {k: (None if v is None else len(b1._files(v))) for k, v in ref.items()},
                    "tools": b1.score(sets, extra, universe, plain, conf, ref)}
    finally:
        b1.to_parent(tree, f)
    return row


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def deps_fingerprint(py: str, repo: str) -> dict:
    """b1.fingerprint() without the project under test: each instance installs its own tree (editable), which changes
    the project's version in the package list (and so the 'env' hash); every other package must stay the same within
    one SWE environment. Same format as b1.fingerprint (interpreter version, then sorted name==version lines)."""
    project = _norm(repo.split("__", 1)[1])
    r = subprocess.run([py, "-c", "import sys,importlib.metadata as m;print(sys.version.split()[0]);"
                        "print('\\n'.join(sorted(f'{d.metadata[\"Name\"]}=={d.version}' for d in m.distributions()"
                        " if d.metadata['Name'])))"], capture_output=True, text=True)
    lines = r.stdout.splitlines()
    head, pk = (lines[0] if lines else "?"), lines[1:]
    deps = [l for l in pk if _norm(l.split("==", 1)[0]) != project]
    text = "\n".join([head, *deps]) + "\n"
    return {"python": head, "packages": len(deps), "excluded": [l for l in pk if l not in deps],
            "hash": hashlib.sha256(text.encode()).hexdigest()[:16]}


def env_check(rs: list) -> list:
    """Report lines: one dependencies-only hash per SWE environment (repo, version)."""
    by: dict = {}
    for r in rs:
        h = (r.get("env_deps") or {}).get("hash")
        by.setdefault((r["repo"], r["version"]), {}).setdefault(h, []).append(r["id"])
    bad = {k: v for k, v in by.items() if len(v) > 1 or None in v}
    lines = ["## Environment check: one dependencies-only hash per SWE environment", "",
             "`env_deps.hash`: the environment's packages without the project under test (whose own editable install "
             "changes per instance, and with it `env.hash`).", "",
             f"{len(by) - len(bad)} of {len(by)} environments with rows have a single dependencies-only hash"
             + ("." if not bad else "; not single:"), ""]
    for (repo, ver), v in sorted(bad.items()):
        lines.append(f"- {repo} {ver}: " + "; ".join(f"{h or 'missing'} x {len(ids)} ({', '.join(ids[:3])})"
                                                      for h, ids in v.items()))
    if bad:
        lines.append("")
    return lines


def rows() -> dict:
    out = {}
    for path in sorted(glob.glob(os.path.join(OUT, "rows.w*.jsonl"))):
        for line in open(path):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("format") == PL.ROW_FORMAT:
                out[r["id"]] = r
    return out


def worker(i: int, n: int, want: int, repos):
    os.makedirs(OUT, exist_ok=True)
    done = rows()
    envs = envs_ok()
    insts = sample(want, repos)
    groups: dict = {}
    for x in insts:
        groups.setdefault((x["instance_id"].rsplit("-", 1)[0], x["version"]), []).append(x)
    for g, key in enumerate(sorted(groups)):
        if g % n != i:
            continue
        repo, version = key
        for x in groups[key]:
            if x["instance_id"] in done:
                continue
            # pause between instances while the pause file exists (another job has priority); an instance is never
            # stopped midway, so its timeouts stay valid
            pause = os.environ.get("B1B_PAUSE_FILE", os.path.join(P.WORK, "b1b.pause"))
            while os.path.exists(pause):
                time.sleep(30)
            t = time.time()
            try:
                configure(repo, envs[key])
                r = run_instance(x, i)
            except Exception as e:  # noqa: BLE001
                r = {"status": "error", "error": repr(e)[:500]}
            r = {"id": x["instance_id"], "repo": repo, "version": version, **r, "secs": round(time.time() - t, 1),
                 "format": PL.ROW_FORMAT, "env": b1.fingerprint(), "env_deps": deps_fingerprint(PL.PY, repo),
                 "proviso": b1.proviso_version()}
            with open(os.path.join(OUT, f"rows.w{i}.jsonl"), "a") as fh:
                fh.write(json.dumps(r) + "\n")
            pv = r.get("R", {}).get("tools", {}).get("proviso", {})
            print(time.strftime("%H:%M:%S"), x["instance_id"], r["status"], r.get("why") or r.get("error") or
                  f"failing {len(r.get('R', {}).get('failing', []))} (F2P {len(r.get('R', {}).get('f2p_failing', []))})"
                  f" proviso {pv.get('selected')}/{r.get('universe')} missed {len(pv.get('missed', []))}"
                  f" ({r['secs']} s)", flush=True)


def report():
    """B1b's tables with b1.py's report layout (one 'project' per repository, scenario R)."""
    rs = list(rows().values())
    by: dict = {}
    for r in rs:
        by.setdefault(r["repo"], []).append(r)
    lines = ["# B1b: reversed SWE-bench fixes", ""]
    for repo, rr in sorted(by.items()):
        ok = [r for r in rr if r.get("status") == "ok" and "tools" in r.get("R", {})]
        f2p_ok = sum(bool(r["R"]["f2p_failing"]) for r in ok)
        lines += [f"## {repo}: {len(ok)} bugs ({sum(r.get('status') == 'skip' for r in rr)} skipped, "
                  f"{sum(r.get('status') == 'error' for r in rr)} errors); FAIL_TO_PASS reproduced in {f2p_ok}", "",
                  "| Tool | Bugs | Bugs with a missed failure | Failing tests missed | Median % tests | Median % time |",
                  "|---|---|---|---|---|---|"]
        for t in sorted({t for r in ok for t in r["R"]["tools"]}):
            xs = [r for r in ok if "error" not in r["R"]["tools"].get(t, {"error": 1})]
            brk = [r for r in xs if r["R"]["failing"]]
            g = lambda r: r["R"]["tools"][t]
            lines.append(f"| {t} | {len(xs)} | {sum(bool(g(r)['missed']) for r in brk)}/{len(brk)} | "
                         f"{sum(len(g(r)['missed']) for r in brk)}/{sum(len(r['R']['failing']) for r in brk)} | "
                         f"{b1._med(100 * g(r)['selected'] / max(1, r['universe']) for r in xs)} | "
                         f"{b1._med(100 * g(r)['time_share'] for r in xs)} |")
        lines.append("")
    lines += env_check(rs)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    a = sys.argv[1:]
    if a and a[0] == "report":
        return report()
    repos = set(a[a.index("--repos") + 1].split(",")) if "--repos" in a else None
    if "--list" in a:
        k = a.index("--list")
        n = int(a[k + 1]) if len(a) > k + 1 and a[k + 1].isdigit() else 500
        for x in sample(n, repos):
            print(x["instance_id"], x["version"])
        return
    if "--worker" in a:
        k = a.index("--worker")
        return worker(int(a[k + 1]), int(a[k + 2]), int(a[k + 3]), repos)
    w, n, it = 1, 500, iter(a)
    for x in it:
        if x == "--workers":
            w = int(next(it))
        elif x == "--repos":
            next(it)
        elif x.isdigit():
            n = int(x)
    if w <= 1:
        return worker(0, 1, n, repos)
    extra = ["--repos", ",".join(sorted(repos))] if repos else []
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "--worker", str(i), str(w), str(n), *extra],
                              stdout=open(os.path.join(P.WORK, f"b1b.w{i}.log"), "a"), stderr=subprocess.STDOUT)
             for i in range(w)]
    for p_ in procs:
        p_.wait()


if __name__ == "__main__":
    main()
