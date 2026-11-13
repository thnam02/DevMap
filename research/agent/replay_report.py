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
            "resolved": bool(r.get("resolved")) and not any_broken, "time": r.get("wall_time_s") or 0.0,
            "cost": r.get("cost_usd") or 0.0, "turns": r.get("turns") or 0,
            # the check when the agent finishes (gate arms): runs, times it sent failures back, seconds spent
            "gate_runs": r.get("proviso_gate_runs") or 0, "gate_blocks": r.get("proviso_gate_blocks") or 0,
            "gate_secs": r.get("proviso_gate_secs") or 0.0}


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


def compare(lines: list[str], per: dict, a: str, b: str, with_repair: bool):
    pairs = [(v[a], v[b]) for v in per.values() if a in v and b in v]
    if not pairs:
        return
    rb = sum(1 for x, y in pairs if x["repaired"] and not y["repaired"])
    rc = sum(1 for x, y in pairs if y["repaired"] and not x["repaired"])
    cb = sum(1 for x, y in pairs if not x["any_p2p_broken"] and y["any_p2p_broken"])
    cc = sum(1 for x, y in pairs if not y["any_p2p_broken"] and x["any_p2p_broken"])
    lines += ["", f"### {a} vs {b} (paired runs: {len(pairs)})", ""]
    if with_repair:
        lines.append(f"- Regression repaired only by {a}: {rb}; only by {b}: {rc}; McNemar exact p = "
                     f"{mcnemar_exact(rb, rc):.3g}")
    lines += [f"- Finished with no PASS_TO_PASS test broken only with {a}: {cb}; only with {b}: {cc}; McNemar exact "
              f"p = {mcnemar_exact(cb, cc):.3g}",
              f"- Wall time: median {statistics.median(x['time'] for x, _ in pairs):.0f} s vs "
              f"{statistics.median(y['time'] for _, y in pairs):.0f} s; "
              + wilcoxon([x['time'] for x, _ in pairs], [y['time'] for _, y in pairs]),
              f"- Cost: ${sum(x['cost'] for x, _ in pairs):.2f} vs ${sum(y['cost'] for _, y in pairs):.2f}; "
              + wilcoxon([x['cost'] for x, _ in pairs], [y['cost'] for _, y in pairs])]
    if any(x["gate_runs"] for x, _ in pairs) and any(y["gate_runs"] for _, y in pairs):
        lines.append(f"- Time in the finish check: median {statistics.median(x['gate_secs'] for x, _ in pairs):.0f} s "
                     f"vs {statistics.median(y['gate_secs'] for _, y in pairs):.0f} s; total "
                     f"{sum(x['gate_secs'] for x, _ in pairs):.0f} s vs {sum(y['gate_secs'] for _, y in pairs):.0f} s; "
                     + wilcoxon([x['gate_secs'] for x, _ in pairs], [y['gate_secs'] for _, y in pairs]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks_dir")
    ap.add_argument("results", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    tasks, rows = load(a.tasks_dir, a.results)
    out = collections.defaultdict(list)
    per = collections.defaultdict(dict)
    errors = collections.Counter()
    for (task, arm, rep), r in rows.items():
        if task not in tasks:
            continue
        o = outcome(r, tasks[task])
        if o is None:
            errors[r.get("status")] += 1
            continue
        out[arm].append(o)
        per[(task, rep)][arm] = o
    arms = sorted(out, key=lambda x: (x != "baseline", x))
    with_repair = any(t.get("start_broken") for t in tasks.values())
    lines = ["# Agent study", "", f"Tasks: {len(tasks)}; runs counted: {sum(len(v) for v in out.values())}; runs with "
             f"errors (left out): {dict(errors) or 0}", "",
             "| Arm | Runs | Regression repaired | Any PASS_TO_PASS broken at the end | Resolved (SWE-bench) | "
             "Median time | Mean time | Cost | Finish checks (sent back) | Check time (median / total) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        o = out[arm]
        n = len(o)
        rep = f"{sum(x['repaired'] for x in o)} ({100 * sum(x['repaired'] for x in o) / n:.1f}%)" if with_repair else "-"
        gate = (f"{sum(x['gate_runs'] for x in o)} ({sum(x['gate_blocks'] for x in o)})"
                if any(x["gate_runs"] for x in o) else "-")
        gsecs = (f"{statistics.median(x['gate_secs'] for x in o):.0f} s / {sum(x['gate_secs'] for x in o):.0f} s"
                 if any(x["gate_runs"] for x in o) else "-")
        lines.append(f"| {arm} | {n} | {rep} | {sum(x['any_p2p_broken'] for x in o)} | {sum(x['resolved'] for x in o)} | "
                     f"{statistics.median(x['time'] for x in o):.0f} s | {statistics.mean(x['time'] for x in o):.0f} s | "
                     f"${sum(x['cost'] for x in o):.2f} | {gate} | {gsecs} |")
    lines += ["", "## Paired comparisons"]
    for other in arms[1:]:
        compare(lines, per, "baseline", other, with_repair)
    if "gate-full" in out and "gate-proviso" in out:
        compare(lines, per, "gate-full", "gate-proviso", with_repair)
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)

if __name__ == "__main__":
    main()
