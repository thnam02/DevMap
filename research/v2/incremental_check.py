"""Validate incremental recording (dc_engine.incremental, v2.4) on a chain of consecutive real commits.

Starting from a full recording at the first commit, the map is brought forward commit by commit: selection against
the previous map, then incremental.update with the selected tests. Every EVERY commits a fresh full recording is
taken at the same commit and compared with the incremental map, two ways:
  maps        test by test, what the fresh map records that the incremental one does not ("missing": the direction
              that matters for safety) and the other way round
  selection   at the next commit, the tests selected with the incremental map against those selected with the fresh
              one; a test only the fresh map selects would be a test incremental recording loses
Times: selection, update (and the re-recording inside it), fresh recording.

Commits: the last N+1 first-parent commits up to the project's base commit that change a non-test Python file under
the package (B1's rule), oldest first; each step measures from the previous chain commit.

  python research/v2/incremental_check.py REPO [--n 20] [--every 5]
Rows: results/incremental/<repo>.jsonl; summary printed and in results/incremental/<repo>.md."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline as PL  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import incremental as INC  # noqa: E402
from dc_engine import record as REC  # noqa: E402

OUT = os.path.join(HERE, "results", "incremental")


def chain(tree: str, base: str, n: int, pkg: str) -> list[str]:
    commits = PL.git(tree, "rev-list", "--first-parent", "--no-merges", "-n", "600", base).split()
    out = []
    for c in commits:
        names = PL.git(tree, "diff-tree", "--no-commit-id", "--name-only", "-r", c).split()
        if any(f.endswith(".py") and f.startswith(pkg.rstrip("/") + "/") and "/tests/" not in f for f in names):
            out.append(c)
        if len(out) == n + 1:
            break
    return list(reversed(out))


def checkout(tree: str, commit: str) -> None:
    PL.git(tree, "checkout", "-qf", "--detach", commit)
    PL.reset(tree)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--every", type=int, default=5)
    a = ap.parse_args()
    PL.use(a.repo)
    CFG = PL.CFG
    os.makedirs(OUT, exist_ok=True)
    tree = PL.make_tree("incr", CFG["commit"])
    commits = chain(tree, CFG["commit"], a.n, CFG["pkg"])
    work = os.path.join(PL.WORK, "incr-maps")
    os.makedirs(work, exist_ok=True)
    extra = ["-p", "no:randomly", *CFG["pytest_args"]]

    def record(out: str) -> tuple[dict, float]:
        t = time.time()
        m = REC.record(tree, CFG["pkg"], out, PL.PY, CFG["targets"], PL.WORKERS, CFG["before_test"], extra,
                       PL.env(tree, [PL.PLUG]))
        return m, time.time() - t

    rows_path = os.path.join(OUT, f"{a.repo}.jsonl")
    open(rows_path, "w").close()
    checkout(tree, commits[0])
    cur, full0 = record(os.path.join(work, "map-0.json"))
    print(a.repo, "chain of", len(commits), "commits; first full recording", round(full0, 1), "s", flush=True)
    pending_next = None    # (incremental map, fresh map) to compare selections at the next commit
    for k in range(1, len(commits)):
        checkout(tree, commits[k])
        row = {"k": k, "commit": commits[k], "from": commits[k - 1], "full_record_s_first": round(full0, 2)}
        if pending_next:
            mi, mf = pending_next
            si, _ = I.selection(tree, mi, PL.PY)
            sf, _ = I.selection(tree, mf, PL.PY)
            only_fresh = 0 if si is None else ("full" if sf is None else len(set(sf) - set(si)))
            row["next_selection"] = {
                "incremental": None if si is None else len(si), "fresh": None if sf is None else len(sf),
                "only_fresh": only_fresh,
                "only_fresh_examples": [] if si is None or sf is None else sorted(set(sf) - set(si))[:5],
                "only_incremental": 0 if si is None or sf is None else len(set(si) - set(sf))}
            pending_next = None
        t = time.time()
        sel, why = I.selection(tree, cur, PL.PY)
        row["selection_s"] = round(time.time() - t, 2)
        row["selected"] = None if sel is None else len(sel)
        row["reason"] = why.get("reason")
        t = time.time()
        cur = INC.update(cur, tree, CFG["pkg"], os.path.join(work, f"map-{k}.json"), sel, PL.PY, PL.WORKERS,
                         CFG["before_test"], extra, PL.env(tree, [PL.PLUG]), CFG["targets"])
        row["update_s"] = round(time.time() - t, 2)
        row["incremental"] = cur["__incremental__"]
        if k % a.every == 0 or k == len(commits) - 1:
            fresh, fs = record(os.path.join(work, f"fresh-{k}.json"))
            row["fresh_record_s"] = round(fs, 2)
            row["compare"] = INC.compare(cur, fresh)
            if k == a.every:
                # noise baseline: a second fresh recording of the same commit; what two fresh recordings disagree
                # on is run-to-run variation, not something incremental recording loses
                fresh2, _ = record(os.path.join(work, f"fresh2-{k}.json"))
                row["noise"] = INC.compare(fresh2, fresh)
            pending_next = (cur, fresh)
        with open(rows_path, "a") as f:
            f.write(json.dumps(row) + "\n")
        c = row.get("compare")
        print(k, commits[k][:10], "selected", row["selected"], "update", row["update_s"], "s, re-recorded",
              cur["__incremental__"].get("rerecorded_files"), "of", cur["__incremental__"].get("test_files"),
              ("| compare: differ %d missing %d only_fresh %d" % (c["differ"], c["missing_in_a"], c["only_in_b"]))
              if c else "", flush=True)
    summarise(a.repo)


def summarise(repo: str) -> None:
    rows = [json.loads(l) for l in open(os.path.join(OUT, f"{repo}.jsonl"))]
    cmp_rows = [r for r in rows if "compare" in r]
    nxt = [r["next_selection"] for r in rows if "next_selection" in r]
    full = [r for r in rows if r["incremental"].get("full")]
    upd = sorted(r["update_s"] for r in rows)
    fresh = [r["fresh_record_s"] for r in cmp_rows]
    lines = [f"# Incremental recording check: {repo}", "",
             f"- Steps: {len(rows)}; full re-recordings (selection ran the whole suite, or no clean map): {len(full)}",
             f"- First full recording: {rows[0]['full_record_s_first']} s; fresh recordings at check points: "
             f"median {sorted(fresh)[len(fresh) // 2] if fresh else '-'} s",
             f"- Incremental update: median {upd[len(upd) // 2]} s, max {upd[-1]} s; test files re-recorded: median "
             f"{sorted(r['incremental'].get('rerecorded_files', 0) or 0 for r in rows)[len(rows) // 2]}; "
             f"selection: median {sorted(r['selection_s'] for r in rows)[len(rows) // 2]} s; base snapshot adopted at "
             f"{sum(1 for r in rows if r['incremental'].get('snapshot_adopted'))} of {len(rows)} steps",
             f"- Map comparisons: {len(cmp_rows)}; tests whose fresh record has something the incremental one lacks: "
             f"{sum(r['compare']['missing_in_a'] for r in cmp_rows)}; tests only in the fresh map: "
             f"{sum(r['compare']['only_in_b'] for r in cmp_rows)}; global record missing: "
             f"{sum(r['compare']['global_missing_in_a'] for r in cmp_rows)}",
             *([f"- Noise baseline (two fresh recordings of one commit): {cmp_rows[0]['noise']['differ']} tests differ, "
                f"{cmp_rows[0]['noise']['missing_in_a']} with something only one of them records"]
               if cmp_rows and "noise" in cmp_rows[0] else []),
             f"- Selection at the next commit: {len(nxt)} checks; tests selected only with the fresh map: "
             f"{sum(x['only_fresh'] for x in nxt if isinstance(x['only_fresh'], int))}"]
    for r in cmp_rows:
        if r["compare"]["missing_in_a"] or r["compare"]["only_in_b"]:
            lines.append(f"  - step {r['k']} ({r['commit'][:10]}): {json.dumps(r['compare']['examples'][:2])[:600]}")
    text = "\n".join(lines)
    open(os.path.join(OUT, f"{repo}.md"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
