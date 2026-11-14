"""Add the test files that fail to load at the base to existing Proviso assets (free; no model calls).

Assets built before this step listed as base failures only the tests the dependency map recorded as failing. A test
module that cannot even be imported at the base (an optional dependency missing from the environment, say) runs no
tests, so it never entered the map, and every later check reported it as a NEW failure: most send-backs in the first
finish-check runs were these. This collects each instance's tests at its plain base commit, exactly as the map was
recorded, and adds every collector that fails to base_failures.json (the list also goes to
base_collection_errors.json). The dependency map and the import-time snapshot are not touched.

  python3 research/agent/base_collect_errors.py REPLAY_DIR [REPLAY_DIR ...]
updates REPLAY_DIR/impact/<instance>/ and, when present, REPLAY_DIR/inst/impact/<instance>/ (replay_tasks.py's copy).
Rerunnable: it rewrites the lists from scratch each time. run_replay.sh copies the assets afresh at every start."""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swe_tasks as S  # noqa: E402
from swe_tasks import E  # noqa: E402


def update(eval_dir: str) -> int:
    tasks: dict[str, dict] = {}
    for f in sorted(os.listdir(os.path.join(eval_dir, "tasks"))):
        if f.endswith(".json"):
            t = json.load(open(os.path.join(eval_dir, "tasks", f)))
            tasks.setdefault(t.get("assets") or t["id"], t)
    bad = 0
    for iid, t in sorted(tasks.items()):
        dests = [d for d in (os.path.join(eval_dir, "impact", iid), os.path.join(eval_dir, "inst", "impact", iid))
                 if os.path.isfile(os.path.join(d, "covmap.json"))]
        if not dests:
            print(f"{iid}: no assets, skipped")
            continue
        repo = iid.rsplit("-", 1)[0]
        tree = S.agent_tree({"instance_id": iid, "base_commit": t["commit"]}, t.get("files") or {})
        py = t["python"]
        _, targets = E.LAYOUT[repo]
        targets = [x for x in targets if os.path.exists(os.path.join(tree, x))]
        try:
            errs = S.base_collection_errors(tree, py, targets, S.record_env(tree, py))
        except (RuntimeError, OSError) as e:
            print(f"{iid}: FAILED: {e}")
            bad += 1
            continue
        for d in dests:
            before = set(json.load(open(os.path.join(d, "base_failures.json"))))
            after = S.write_base_failures(d, json.load(open(os.path.join(d, "covmap.json"))), errs)
            added = sorted(set(after) - before)
        print(f"{iid}: {len(errs)} collection error(s) at the base"
              + (f"; added {len(added)}: " + ", ".join(added[:6]) + (" ..." if len(added) > 6 else "") if added else ""),
              flush=True)
    return bad


def main():
    dirs = [os.path.abspath(a) for a in sys.argv[1:]]
    if not dirs:
        sys.exit(__doc__)
    bad = sum(update(d) for d in dirs)
    print("OK" if not bad else f"{bad} instance(s) failed; see above")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
