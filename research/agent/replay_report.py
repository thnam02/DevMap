"""Replay study report: per arm, how often the agent repaired the regression it started from, left any PASS_TO_PASS
test broken, resolved the issue, and what it spent; paired comparisons per case.

  python3 research/agent/replay_report.py TASKS_DIR RESULTS.jsonl [RESULTS.jsonl ...] [--out report.md]

TASKS_DIR holds the replay tasks (each with start_broken). A run counts once (its last row). Paired tests use the
cases where both arms have the repetition: McNemar (exact, two-sided) on "regression repaired" and Wilcoxon signed-rank
on wall time and cost (scipy if installed; otherwise the counts only)."""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics

ARMS = ("baseline", "impact-noreport")


def load(tasks_dir: str, results: list[str]):
    tasks = {}
    for f in os.listdir(tasks_dir):
        if f.endswith(".json"):
            t = json.load(open(os.path.join(tasks_dir, f)))
            tasks[t["id"]] = t
    rows = {}
    for path in results:
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                rows[(r.get("task"), str(r.get("arm")), str(r.get("rep")))] = r
    return tasks, rows


def outcome(r: dict, t: dict) -> dict | None:
    if r.get("status") != "ok":
        return None
    reg = r.get("regression") or {}
    broken = t.get("start_broken") or []
    still = [b for b in broken if reg.get(b) is False]
    any_broken = (r.get("regressions") or 0) > 0
    return {"repaired": not still, "still_broken": len(still), "any_p2p_broken": any_broken,
            # dc_eval's "resolved" is the hidden tests alone; SWE-bench also requires every PASS_TO_PASS test to pass
            "resolved": bool(r.get("resolved")) and not any_broken, "time": r.get("wall_time_s") or 0.0, "cost": r.get("cost_usd") or 0.0,
            "turns": r.get("turns") or 0}


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def wilcoxon(xs: list[float], ys: list[float]) -> str:
    try:
        from scipy.stats import wilcoxon as w
        d = [x - y for x, y in zip(xs, ys) if x != y]
        if len(d) < 6:
            return "too few differing pairs"
        return f"Wilcoxon p = {w(d).pvalue:.3g}"
    except ImportError:
        return "scipy not installed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks_dir")
    ap.add_argument("results", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    tasks, rows = load(a.tasks_dir, a.results)
    out = {arm: [] for arm in ARMS}
    per = collections.defaultdict(dict)
    errors = collections.Counter()
    for (task, arm, rep), r in rows.items():
        if task not in tasks or arm not in ARMS:
            continue
        o = outcome(r, tasks[task])
        if o is None:
            errors[r.get("status")] += 1
            continue
        out[arm].append(o)
        per[(task, rep)][arm] = o
    lines = ["# Replay study", "", f"Cases with tasks: {len(tasks)}; runs counted: "
             f"{sum(len(v) for v in out.values())}; runs with errors (left out): {dict(errors) or 0}", "",
             "| Arm | Runs | Regression repaired | Any PASS_TO_PASS broken at the end | Resolved (SWE-bench) | Median time | "
             "Mean time | Cost |", "|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        o = out[arm]
        if not o:
            continue
        n = len(o)
        lines.append(f"| {arm} | {n} | {sum(x['repaired'] for x in o)} ({100 * sum(x['repaired'] for x in o) / n:.1f}%)"
                     f" | {sum(x['any_p2p_broken'] for x in o)} | {sum(x['resolved'] for x in o)} | "
                     f"{statistics.median(x['time'] for x in o):.0f} s | {statistics.mean(x['time'] for x in o):.0f} s | "
                     f"${sum(x['cost'] for x in o):.2f} |")
    pairs = [(v["baseline"], v["impact-noreport"]) for v in per.values() if len(v) == 2]
    if pairs:
        b = sum(1 for x, y in pairs if x["repaired"] and not y["repaired"])
        c = sum(1 for x, y in pairs if y["repaired"] and not x["repaired"])
        bb = sum(1 for x, y in pairs if not x["any_p2p_broken"] and y["any_p2p_broken"])
        cc = sum(1 for x, y in pairs if not y["any_p2p_broken"] and x["any_p2p_broken"])
        lines += ["", f"Paired (case, repetition): {len(pairs)}", ""]
        if any(t.get("start_broken") for t in tasks.values()):
            lines.append(f"- Regression repaired only by baseline: {b}; only with Proviso: {c}; "
                         f"McNemar exact p = {mcnemar_exact(b, c):.3g}")
        lines += [f"- Finished with no PASS_TO_PASS test broken only by baseline: {bb}; only with Proviso: {cc}; "
                  f"McNemar exact p = {mcnemar_exact(bb, cc):.3g}",
                  f"- Wall time, baseline vs Proviso: median {statistics.median(x['time'] for x, _ in pairs):.0f} s vs "
                  f"{statistics.median(y['time'] for _, y in pairs):.0f} s; "
                  + wilcoxon([x['time'] for x, _ in pairs], [y['time'] for _, y in pairs]),
                  f"- Cost, baseline vs Proviso: ${sum(x['cost'] for x, _ in pairs):.2f} vs "
                  f"${sum(y['cost'] for _, y in pairs):.2f}; "
                  + wilcoxon([x['cost'] for x, _ in pairs], [y['cost'] for _, y in pairs])]
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)


if __name__ == "__main__":
    main()
