"""The fixed sample of the SWE-bench agent-regression benchmark, drawn once before any Proviso run (no tuning on it).

From the probe's usable instances (some of the tests the agents broke pass at base under Python 3.12): every usable
instance, in one fixed random order (each repository shuffled with a fixed seed, then taken round-robin so that every
prefix of the order is balanced across repositories; the first CORE form the core sample, evaluated first, and the rest
follow as time allows); per instance up to MAX_CASES distinct regressions, a case
being one agent patch whose genuine broken tests, restricted to those that pass at base here, form a set not seen for
that instance yet (cases drawn at random with the same seed; ties between submissions broken by the draw).

  python3 research/v2/swe_sample.py   -> research/v2/results/swe/sample.json"""
from __future__ import annotations

import collections
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "swe")
SEED = "proviso-swe-2026-11-06"
REPOS = ["sympy__sympy", "sphinx-doc__sphinx", "pydata__xarray", "pylint-dev__pylint", "mwaskom__seaborn",
         "pytest-dev__pytest", "pallets__flask"]
CORE = 80
MAX_CASES = 5


def main():
    probe = {}
    for line in open(os.path.join(OUT, "probe.jsonl")):
        r = json.loads(line)
        if r.get("format") == 2:
            probe[r["instance"]] = r
    usable = {i: set(r["usable_tests"]) for i, r in probe.items() if r.get("usable_tests")}
    patches = collections.defaultdict(list)
    for line in open(os.path.join(OUT, "regressions.jsonl")):
        r = json.loads(line)
        if r["instance"] in usable:
            tests = sorted(set(r.get("p2p_failed_genuine") or []) & usable[r["instance"]])
            if tests and r.get("patch"):
                patches[r["instance"]].append({**r, "tests": tests})
    rnd = random.Random(SEED)
    chosen, by_repo = [], collections.defaultdict(list)
    for i in sorted(patches):
        by_repo[i.rsplit("-", 1)[0]].append(i)
    pools = {}
    for repo in REPOS:
        pools[repo] = sorted(by_repo.get(repo, []))
        rnd.shuffle(pools[repo])
    order = []
    while any(pools.values()):
        for repo in REPOS:
            if pools[repo]:
                order.append(pools[repo].pop(0))
    for pos, inst in enumerate(order):
        repo = inst.rsplit("-", 1)[0]
        if True:
            cands = sorted(patches[inst], key=lambda r: (r["split"], r["submission"]))
            rnd.shuffle(cands)
            seen, cases = set(), []
            for c in cands:
                key = frozenset(c["tests"])
                if key in seen:
                    continue
                seen.add(key)
                cases.append({"split": c["split"], "submission": c["submission"], "patch": c["patch"],
                              "broken": c["tests"], "resolved": c["resolved"]})
                if len(cases) == MAX_CASES:
                    break
            chosen.append({"instance": inst, "repo": repo, "version": probe[inst]["version"], "order": pos,
                           "core": pos < CORE, "created_at": probe[inst]["created_at"], "cases": cases})
    json.dump({"seed": SEED, "core": CORE, "max_cases": MAX_CASES, "instances": chosen},
              open(os.path.join(OUT, "sample.json"), "w"), indent=1)
    for label, xs in (("core", [x for x in chosen if x["core"]]), ("all", chosen)):
        c, k = collections.Counter(x["repo"] for x in xs), collections.Counter()
        for x in xs:
            k[x["repo"]] += len(x["cases"])
        print(f"{label}: {len(xs)} instances, {sum(k.values())} cases")
        for repo in REPOS:
            print(f"  {repo:22s} {c[repo]:3d} instances, {k[repo]:3d} cases")


if __name__ == "__main__":
    main()
