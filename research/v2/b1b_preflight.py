"""B1b pre-flight: for each SWE environment (repo, version) with instances not yet run, does the first such instance's
suite collect in its environment? (fixed version = base commit + test patch + reference fix, on PYTHONPATH as B1b runs
it; collection only, no install, no environment change). A missing module is named, so it can be added before B1b
reaches that environment.
  python research/v2/b1b_preflight.py [N]     # N: instances per environment (default 1)"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1b as B  # noqa: E402
import pipeline as PL  # noqa: E402
import swe_probe as P  # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    done = B.rows()
    envs = B.envs_ok()
    groups = {}
    for x in B.sample(437):
        if x["instance_id"] in done:
            continue
        groups.setdefault((x["instance_id"].rsplit("-", 1)[0], x["version"]), []).append(x)
    out = []
    t = os.path.join(PL.BASE_WORK, "swe", "preflight-tree")
    for (repo, ver), xs in sorted(groups.items()):
        for x in xs[:n]:
            B.configure(repo, envs[(repo, ver)])
            subprocess.run(["rm", "-rf", t])
            subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", P.repo_clone(repo), t], check=True)
            P.ensure_commit(P.repo_clone(repo), x["base_commit"])
            subprocess.run(["git", "-C", t, "fetch", "-q", P.repo_clone(repo), x["base_commit"]], capture_output=True)
            subprocess.run(["git", "-C", t, "checkout", "-q", "-f", x["base_commit"]], check=True)
            for what in ("test_patch", "patch"):
                if x.get(what):
                    subprocess.run(["git", "-C", t, "apply", "-"], input=x[what] if x[what].endswith("\n") else x[what] + "\n",
                                   text=True, capture_output=True)
            e = PL.env(t, [PL.PLUG])
            try:
                r = subprocess.run([PL.PY, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *PL.CFG["targets"]],
                                   cwd=t, env=e, capture_output=True, text=True, timeout=900)
                text = r.stdout + r.stderr
                code = r.returncode
            except subprocess.TimeoutExpired:
                text, code = "timeout", -1
            m = re.search(r"collected (\d+) items?|(\d+) tests? collected", text)
            ntests = int(m.group(1) or m.group(2)) if m else 0
            mods = sorted(set(re.findall(r"No module named '([\w.]+)'", text)))
            errs = re.search(r"(\d+) errors?", text.splitlines()[-1] if text.splitlines() else "")
            res = {"repo": repo, "version": ver, "instance": x["instance_id"], "left": len(xs), "exit": code,
                   "collected": ntests, "missing_modules": mods, "last": (text.strip().splitlines() or [""])[-1][:150]}
            out.append(res)
            print(json.dumps(res), flush=True)
    subprocess.run(["rm", "-rf", t])
    PL.jdump(out, os.path.join(PL.BASE_WORK, "swe", "preflight.json"))


if __name__ == "__main__":
    main()
