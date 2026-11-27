"""Check that a project's environment runs its whole test suite before any benchmark uses it.

A missing optional dependency does not fail a run loudly: the test files that import it fail to collect (or skip as a
whole), and every tool, Proviso's recording included, silently works on a smaller suite. (In the cloud container,
pytz and duckdb were missing and 3 of sqlglot's 59 test files never ran in any recording.) This script lists:
  - test files that fail to collect, with the missing module names pytest reports;
  - test files skipped as a whole at collection (a module-level importorskip);
  - with --skips, tests skipped at run time, grouped by reason, flagging reasons that name a missing module.
Exit status 1 if any test file fails to collect (the environment is incomplete), else 0.

Usage: python research/v2/env_check.py PROJECT [--commit REV] [--skips]
  PROJECT is any project of b1.py (its targets, pytest arguments and import paths). The check runs on a tree at
  --commit (default: the project's pinned commit, else the newest B1 candidate). Results: results/env_check/PROJECT.json."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402

MISSING = re.compile(r"No module named '([^']+)'|could not import '([^']+)'")


def _missing(msg: str) -> list[str]:
    return sorted({next(g for g in m.groups() if g) for m in MISSING.finditer(msg or "")})


def check(name: str, commit: str | None, skips: bool) -> dict:
    b1.use(name)
    rev = commit or PL.CFG.get("commit") or b1.candidates(1)[0][1]
    tree = PL.make_tree("envcheck", rev)
    b1.use_targets(tree)
    if PL.CFG.get("sync"):   # the commit's own pinned test dependencies, as b1.run_pair applies them
        PL.CFG["sync"](tree, PL.PY)
    out = os.path.join(PL.WORK, "envcheck.json")
    if os.path.exists(out):
        os.remove(out)
    e = PL.env(tree, [PL.PLUG], COLLECTCHECK_OUT=out)
    t = time.time()
    r = subprocess.run([PL.PY, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-p", "collectcheck",
                        "-p", "no:randomly", "--continue-on-collection-errors", *PL.CFG["pytest_args"],
                        *PL.CFG["targets"]], cwd=tree, env=e, capture_output=True, text=True, timeout=3600)
    got = PL.jload(out, None)
    if got is None:
        raise RuntimeError("collection produced no report: " + (r.stdout + r.stderr)[-800:])
    failed = {f: p for f, p in got["problems"].items() if p["outcome"] == "failed"}
    skipped = {f: p for f, p in got["problems"].items() if p["outcome"] == "skipped"}
    result = {"project": name, "commit": PL.git(tree, "rev-parse", "HEAD").strip(), "env": b1.fingerprint(),
              "collect_s": round(time.time() - t, 1), "test_files": len(got["items"]) + len(failed) + len(skipped),
              "tests": sum(got["items"].values()), "files_failing_to_collect": len(failed),
              "files_skipped_at_collection": len(skipped),
              "missing_modules": sorted({m for p in [*failed.values(), *skipped.values()] for m in _missing(p["message"])}),
              "failed": {f: {"missing": _missing(p["message"]), "message": p["message"][-400:]} for f, p in failed.items()},
              "skipped": {f: p["message"][-300:] for f, p in skipped.items()}}
    if skips:
        t = time.time()
        r = subprocess.run([PL.PY, "-m", "pytest", "-q", "-rs", "--tb=no", "-p", "no:cacheprovider", "-p", "no:randomly",
                            "--continue-on-collection-errors", *PL.CFG["pytest_args"], *PL.CFG["targets"]],
                           cwd=tree, env=PL.env(tree), capture_output=True, text=True,
                           timeout=int(os.environ.get("PROVISO_TEST_TIMEOUT", "1800")))
        reasons: dict = {}
        for line in r.stdout.splitlines():
            m = re.match(r"SKIPPED \[(\d+)\] ([^:]+):\d+: (.*)", line)
            if m:
                k = m.group(3)[:200]
                reasons[k] = reasons.get(k, 0) + int(m.group(1))
        result["run_s"] = round(time.time() - t, 1)
        result["skipped_at_run"] = sum(reasons.values())
        result["skip_reasons"] = dict(sorted(reasons.items(), key=lambda kv: -kv[1])[:40])
        result["skip_missing_modules"] = sorted({m for k in reasons for m in _missing(k)} |
                                                {m.group(1) for k in reasons for m in
                                                 re.finditer(r"(?:requires|needs|install) (\w[\w.-]*)", k)})
    PL.reset(tree)
    return result


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    commit = a[a.index("--commit") + 1] if "--commit" in a else None
    r = check(a[0], commit, "--skips" in a)
    d = os.path.join(HERE, "results", "env_check")
    os.makedirs(d, exist_ok=True)
    json.dump(r, open(os.path.join(d, f"{a[0]}.json"), "w"), indent=1)
    print(f"{a[0]} @ {r['commit'][:10]}: {r['tests']} tests in {r['test_files']} test files; "
          f"{r['files_failing_to_collect']} fail to collect, {r['files_skipped_at_collection']} skipped at collection; "
          f"missing modules: {', '.join(r['missing_modules']) or 'none'}")
    for f, x in r["failed"].items():
        print(f"  FAILS  {f}: missing {', '.join(x['missing']) or '?'}")
    for f, m in r["skipped"].items():
        print(f"  SKIPPED {f}: {m.splitlines()[-1][:120] if m else ''}")
    if "skipped_at_run" in r:
        print(f"  run: {r['skipped_at_run']} tests skipped; reasons naming a module: "
              f"{', '.join(r['skip_missing_modules']) or 'none'}")
    sys.exit(1 if r["files_failing_to_collect"] else 0)


if __name__ == "__main__":
    main()
