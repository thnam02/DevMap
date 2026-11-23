"""How much a recorded dependency map varies between runs: record a project's map under several hash seeds
(PYTHONHASHSEED; set iteration order changes, and with it which code some tests reach) and compare them test by test.
The evaluation plan reports this as a threat with its size (the sympy finding: some tests reach an edited function under
some seeds only).

Usage: python research/v2/seed_check.py PROJECT [--seeds 0,1,2] [--sample FRACTION]
  The map is recorded at the project's pinned commit (or the newest B1 candidate's parent) with the frozen recorder.
  --sample records only that fraction of the test files (chosen with a fixed seed), as the plan's 10% sample.
Results: results/seed_check/PROJECT.json: per pair of seeds, the tests whose records differ, split by what differs
(functions, classes, files read, directories listed), with examples."""
from __future__ import annotations

import itertools
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
import record_speed_check as RSC  # noqa: E402
from dc_engine import record as REC  # noqa: E402


def main():
    a, seeds, frac = sys.argv[1:], ["0", "1", "2"], 1.0
    if not a:
        sys.exit(__doc__)
    if "--seeds" in a:
        seeds = a[a.index("--seeds") + 1].split(",")
    if "--sample" in a:
        frac = float(a[a.index("--sample") + 1])
    name = a[0]
    b1.use(name)
    rev = PL.CFG.get("commit") or b1.candidates(1)[0][0]
    tree = PL.make_tree("seedcheck", rev)
    targets = PL.CFG["targets"]
    if frac < 1:
        files = sorted(REC.collect_files(tree, PL.PY, targets, PL.env(tree, [PL.PLUG])))
        targets = sorted(random.Random(f"seedcheck-{name}").sample(files, max(1, round(frac * len(files)))))
    maps, secs = {}, {}
    for s in seeds:
        out = os.path.join(PL.WORK, f"seedcheck-{s}.json")
        t = time.time()
        REC.record(tree, PL.CFG["pkg"], out, PL.PY, targets, PL.WORKERS, PL.CFG["before_test"],
                   ["-p", "no:randomly", *PL.CFG["pytest_args"]], PL.env(tree, [PL.PLUG], PYTHONHASHSEED=s))
        secs[s] = round(time.time() - t, 1)
        maps[s] = json.load(open(out))
        print(f"seed {s}: {sum(1 for k in maps[s] if not k.startswith('__'))} tests, {secs[s]} s", flush=True)
    pairs = {}
    union = set()
    for x, y in itertools.combinations(seeds, 2):
        d = RSC.differing(maps[x], maps[y])
        union |= d
        kinds = {}
        for n in d:
            if n in maps[x] and n in maps[y]:
                fx, fy = RSC._full(maps[x], n), RSC._full(maps[y], n)
                for k in ("funcs", "classes", "files", "dirs", "always"):
                    if fx[k] != fy[k]:
                        kinds[k] = kinds.get(k, 0) + 1
            else:
                kinds["only_one_side"] = kinds.get("only_one_side", 0) + 1
        pairs[f"{x}-{y}"] = {"tests_differing": len(d), "by_kind": kinds, "examples": sorted(d)[:15],
                             "global_differs": maps[x].get("__global__") != maps[y].get("__global__")}
    tests = sum(1 for k in maps[seeds[0]] if not k.startswith("__"))
    files = {n.split("::", 1)[0] for n in union}
    result = {"project": name, "commit": maps[seeds[0]]["__base__"]["commit"], "env": b1.fingerprint(),
              "seeds": seeds, "sample": frac, "test_files_recorded": len(targets) if frac < 1 else None,
              "tests": tests, "seconds": secs, "tests_differing_any_pair": len(union),
              "share": round(len(union) / max(1, tests), 4), "files_with_differing_tests": sorted(files)[:40],
              "pairs": pairs}
    d = os.path.join(HERE, "results", "seed_check")
    os.makedirs(d, exist_ok=True)
    json.dump(result, open(os.path.join(d, f"{name}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "pairs"}, indent=1))
    for k, v in pairs.items():
        print(k, v["tests_differing"], v["by_kind"], v["examples"][:3])
    PL.reset(tree)


if __name__ == "__main__":
    main()
