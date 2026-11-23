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

  python research/v2/incremental_check.py REPO [--n 20] [--every 5] [--name NAME] [--budget SECONDS] [--resume]
Rows: results/incremental/<NAME>.jsonl (NAME defaults to the repository); summary printed and in <NAME>.md.
--budget stops cleanly before a step that would not finish in time; --resume continues such a run from its last
complete step (same REPO, --n, --every and --name), with the maps it left in incr-maps-<NAME>."""
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
    ap.add_argument("--name", default="")
    ap.add_argument("--budget", type=float, default=0, help="seconds; 0 = no limit")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    name = a.name or a.repo
    t_start = time.time()
    PL.use(a.repo)
    CFG = PL.CFG
    os.makedirs(OUT, exist_ok=True)
    tree = PL.make_tree("incr", CFG["commit"])
    commits = chain(tree, CFG["commit"], a.n, CFG["pkg"])
    work = os.path.join(PL.WORK, "incr-maps" if name == a.repo else f"incr-maps-{name}")
    os.makedirs(work, exist_ok=True)
    extra = ["-p", "no:randomly", *CFG["pytest_args"]]

    def record(out: str) -> tuple[dict, float]:
        t = time.time()
        m = REC.record(tree, CFG["pkg"], out, PL.PY, CFG["targets"], PL.WORKERS, CFG["before_test"], extra,
                       PL.env(tree, [PL.PLUG]))
        return m, time.time() - t

    rows_path = os.path.join(OUT, f"{name}.jsonl")
    done = [json.loads(l) for l in open(rows_path)] if a.resume and os.path.exists(rows_path) else []
    pending_next = None    # (incremental map, fresh map) to compare selections at the next commit
    if done:
        last = done[-1]["k"]
        assert [r["k"] for r in done] == list(range(1, last + 1)) and done[-1]["commit"] == commits[last], \
            "the rows do not belong to this chain"
        full0 = done[0]["full_record_s_first"]
        cur = json.load(open(os.path.join(work, f"map-{last}.json")))
        if "compare" in done[-1]:
            pending_next = (cur, json.load(open(os.path.join(work, f"fresh-{last}.json"))))
        start = last + 1
        checkout(tree, commits[last])
        print(a.repo, "resuming after step", last, "of", len(commits) - 1, flush=True)
    else:
        open(rows_path, "w").close()
        checkout(tree, commits[0])
        cur, full0 = record(os.path.join(work, "map-0.json"))
        start = 1
        print(a.repo, "chain of", len(commits), "commits; first full recording", round(full0, 1), "s", flush=True)
    step_s = []
    for k in range(start, len(commits)):
        # a step takes about as long as the longest one so far (a whole-suite step re-records everything): stop
        # before one that would not finish within the budget, so --resume continues from a complete step
        if a.budget and step_s and time.time() - t_start + max(step_s) * 1.2 > a.budget:
            print("budget reached after step", k - 1, "; continue with --resume", flush=True)
            return
        t_step = time.time()
        checkout(tree, commits[k])
        row = {"k": k, "commit": commits[k], "from": commits[k - 1], "full_record_s_first": round(full0, 2)}
        sel = None
        if pending_next:
            mi, mf = pending_next
            # v2.3 protocol: the fresh map of the previous commit, with its own 9-sample base snapshot (its cache is
            # set aside, then the incremental run's adopted snapshot put back), timed apart from v2.4's selection
            cache = os.path.join(tree, I.STATE_DIR, "importstate_base.json")
            adopted = open(cache).read() if os.path.exists(cache) else None
            if os.path.exists(cache):
                os.remove(cache)
            t = time.time()
            sf, _ = I.selection(tree, mf, PL.PY)
            t_f = time.time() - t
            if adopted is not None:
                open(cache, "w").write(adopted)
            elif os.path.exists(cache):
                os.remove(cache)
            t = time.time()
            si, why_i = I.selection(tree, mi, PL.PY)
            t_i = time.time() - t
            only_fresh = 0 if si is None else ("full" if sf is None else len(set(sf) - set(si)))
            row["next_selection"] = {
                "incremental": None if si is None else len(si), "fresh": None if sf is None else len(sf),
                "only_fresh": only_fresh,
                "only_fresh_examples": [] if si is None or sf is None else sorted(set(sf) - set(si))[:5],
                "only_incremental": 0 if si is None or sf is None else len(set(si) - set(sf)),
                "v23_selection_s": round(t_f, 2), "v24_selection_s": round(t_i, 2)}
            pending_next = None
            sel, why, row["selection_s"] = si, why_i, round(t_i, 2)
        if "next_selection" not in row:
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
        step_s.append(time.time() - t_step)
    summarise(name)


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
    both = [(prev, r) for prev, r in zip(rows, rows[1:]) if "next_selection" in r and "fresh_record_s" in prev]
    if both:
        v23 = [p["fresh_record_s"] + r["next_selection"]["v23_selection_s"] for p, r in both]
        v24 = [p["update_s"] + r["next_selection"]["v24_selection_s"] for p, r in both]
        same = sum(1 for _, r in both if r["next_selection"]["only_fresh"] == 0 and r["next_selection"]["only_incremental"] == 0)
        med = lambda xs: sorted(xs)[len(xs) // 2]
        lines += ["", "## v2.3 (record from scratch at every commit) vs v2.4 (incremental), same commits", "",
                  "| | v2.3 | v2.4 |", "|---|---|---|",
                  f"| Per-commit cost: recording + selection, median | {med(v23):.1f} s | {med(v24):.1f} s |",
                  f"| Total over {len(both)} commits | {sum(v23):.0f} s | {sum(v24):.0f} s |",
                  f"| Selection alone, median | {med([r['next_selection']['v23_selection_s'] for _, r in both]):.1f} s | "
                  f"{med([r['next_selection']['v24_selection_s'] for _, r in both]):.1f} s |",
                  f"| Commits with identical selected tests | {same} of {len(both)} | |",
                  f"| Tests only v2.3 selects (lost by v2.4) | {sum(r['next_selection']['only_fresh'] for _, r in both if isinstance(r['next_selection']['only_fresh'], int))} | |",
                  f"| Tests only v2.4 selects (extra cost) | {sum(r['next_selection']['only_incremental'] for _, r in both)} | |"]
    for r in cmp_rows:
        if r["compare"]["missing_in_a"] or r["compare"]["only_in_b"]:
            lines.append(f"  - step {r['k']} ({r['commit'][:10]}): {json.dumps(r['compare']['examples'][:2])[:600]}")
    text = "\n".join(lines)
    open(os.path.join(OUT, f"{repo}.md"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
