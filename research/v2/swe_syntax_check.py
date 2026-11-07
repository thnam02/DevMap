"""Which SWE-bench cases contain an agent patch that leaves a Python file unparsable (the v2.2.1 parse check fires).

For every case of the sample: the files the agent patch touches (the reference tests' files left out, as swe_eval.py
applies it) are taken from the base commit into a scratch repository, the patch is applied the same way, and each
changed Python file that is not a test file is parsed before and after. Nothing is run and no Proviso map is needed.
The cases found are crossed with the Proviso rows (eval-v2.2.jsonl by default): what v2.2 selected there.

  python3 research/v2/swe_syntax_check.py [--rows eval-v2.2.jsonl]   -> results/swe/syntax_check.md"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swe_eval as E  # noqa: E402
import swe_probe as P  # noqa: E402


def parses(src: bytes) -> bool:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            ast.parse(src)
            return True
        except (SyntaxError, ValueError):
            return False


def broken_files(clone: str, base: str, test_patch: str, patch: str) -> list[str] | str:
    ref = set(re.findall(r"(?m)^\+\+\+ b/(\S+)$", test_patch or ""))
    patch, _ = E.without_files(patch, ref)
    files = sorted(set(re.findall(r"(?m)^diff --git a/\S+ b/(\S+)$", patch)))
    tmp = tempfile.mkdtemp(prefix="swe-syntax-")
    try:
        old = {}
        for f in files:
            r = subprocess.run(["git", "-C", clone, "show", f"{base}:{f}"], capture_output=True)
            if r.returncode == 0:
                os.makedirs(os.path.dirname(os.path.join(tmp, f)) or tmp, exist_ok=True)
                open(os.path.join(tmp, f), "wb").write(r.stdout)
                old[f] = r.stdout
        subprocess.run("git init -q && git add -A && git -c user.email=s@s -c user.name=s commit -qm base "
                       "--allow-empty", shell=True, cwd=tmp, check=True, capture_output=True)
        try:
            E.apply_patch(tmp, patch)
        except RuntimeError as e:
            return f"patch does not apply: {str(e)[:80]}"
        out = []
        for f in files:
            name = os.path.basename(f)
            path = os.path.join(tmp, f)
            if not f.endswith(".py") or not os.path.exists(path) or name.startswith("test_") \
                    or name.endswith("_test.py"):
                continue
            if not parses(open(path, "rb").read()) and (f not in old or parses(old[f])):
                out.append(f)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="eval-v2.2.jsonl")
    a = ap.parse_args()
    meta = P.load_instances()
    rows = {}
    path = os.path.join(P.OUT, a.rows)
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            rows[(r["instance"], r["case"])] = r
    sample = json.load(open(os.path.join(P.OUT, "sample.json")))["instances"]
    hits, problems, n = [], [], 0
    for x in sample:
        inst = x["instance"]
        clone = P.repo_clone(x["repo"])
        base = meta[inst]["base_commit"]
        P.ensure_commit(clone, base) if hasattr(P, "ensure_commit") else None
        for k, case in enumerate(x["cases"]):
            n += 1
            patch = open(case["patch"]).read() if os.path.exists(case.get("patch") or "") else None
            if not patch:
                problems.append((inst, k, "patch file missing"))
                continue
            res = broken_files(clone, base, meta[inst].get("test_patch"), patch)
            if isinstance(res, str):
                problems.append((inst, k, res))
            elif res:
                r = rows.get((inst, k), {})
                hits.append((inst, k, x["core"], res, r))
    lines = ["# Agent patches that leave a Python file unparsable (where the v2.2.1 parse check fires)", "",
             f"{n} cases checked; {len(hits)} with a changed non-test Python file that parsed at base and no longer "
             f"parses; {len(problems)} not checkable.", "",
             f"| instance | case | sample | broken file(s) | {a.rows}: reproduced / missed | full suite | test time |",
             "|---|---|---|---|---|---|---|"]
    for inst, k, core, files, r in hits:
        rep = r.get("reproduced")
        lines.append(f"| {inst} | {k} | {'core' if core else 'held-out'} | {', '.join(files)} | "
                     + (f"{len(rep or [])} / {len(r.get('missed') or [])}" if r and "error" not in r else "no row")
                     + f" | {r.get('full_suite', '')} | "
                     + (f"{100 * r['time_share']:.0f}%" if r.get("time_share") is not None else "") + " |")
    if problems:
        lines += ["", "Not checkable: " + "; ".join(f"{i} c{k}: {why}" for i, k, why in problems[:30])]
    open(os.path.join(P.OUT, "syntax_check.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
