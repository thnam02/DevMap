"""RQ7 overhead from B1's rows: what each tool costs and when its one-time data collection pays for itself.

Per pair (scenario S of b1.py, the commit's source change on the parent):
  run_all      the plain suite's wall time at the parent (base_s)
  fixed        the part of a run that is not test time: start-up, collection, teardown = max(0, base_s - test time)
  run(tool)    selection time + fixed + the selected tests' recorded time (a selected run still starts pytest and
               collects; a lower bound on what selection saves)
  collect      the tool's one-time data at the parent: Proviso's recording (record_s), testmon's recording run,
               NameRTS's initial run, TDAD's index
Reported, per project (medians over pairs) and pooled:
  offline      run(tool) / run_all: the cost of one test run once the data exists (Ekstazi's "AE")
  online       (collect + run(tool)) / run_all: collecting afresh at every commit (Ekstazi's "AEC"), the per-commit
               CI worst case
  break-even   collect / (run_all - run(tool)): test runs on one map before collecting has paid off
  agent task   (collect + K * run(tool)) / (K * run_all) with K test runs per task (default 8.8, the mean in Lin et
               al., "To Run or Not to Run", ISSTA 2026): one map per task, recorded before the agent starts

Usage: python research/v2/overhead.py [PROJECT ...] [--runs K]     -> results/b1/overhead.md"""
from __future__ import annotations

import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402

COLLECT = {"proviso": "record_s", "traditional": "record_s", "testmon": "testmon_record_s",
           "namerts": "namerts_init_s", "tdad": "tdad_index_s", "run_all": None}


def pair_costs(r: dict, k_runs: float, scenario: str = "S") -> dict:
    sc = r.get(scenario) or {}
    if r.get("status") != "ok" or sc.get("timeout") or "tools" not in sc:
        return {}
    run_all = r["base_s"]
    fixed = max(0.0, run_all - r.get("universe_s", 0))
    out = {}
    for tool, row in sc["tools"].items():
        if "error" in row or tool not in COLLECT:
            continue
        key = COLLECT[tool]
        collect = r.get(key) if key else 0.0
        if collect is None:
            continue
        run = (row.get("selection_s") or 0) + fixed + row["test_s"]
        if tool == "run_all":
            run = run_all
        saving = run_all - run
        out[tool] = {"run_all": run_all, "run": run, "collect": collect,
                     "offline": run / run_all if run_all else None,
                     "online": (collect + run) / run_all if run_all else None,
                     "break_even": (collect / saving) if saving > 0 else None,
                     "agent_task": (collect + k_runs * run) / (k_runs * run_all) if run_all else None}
    return out


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _fmt(x, pct=False):
    if x is None:
        return "n/a"
    return f"{100 * x:.0f}%" if pct else f"{x:.1f}"


def main():
    k, names, it = 8.8, [], iter(sys.argv[1:])
    for x in it:
        if x == "--runs":
            k = float(next(it))
        else:
            names.append(x)
    if not names and os.path.isdir(b1.OUT):
        names = sorted(d for d in os.listdir(b1.OUT) if os.path.isdir(os.path.join(b1.OUT, d)))
    lines = ["# RQ7: overhead and break-even (B1, scenario S)", "",
             f"Medians over pairs. Agent task = one map per task, {k} test runs per task. Break-even = test runs on one "
             "map before its one-time collection has paid off (n/a: the tool's run is not cheaper than running "
             "everything).", "",
             "| Project | Tool | Pairs | Run all (s) | One-time collection (s) | Run with the tool (s) | Offline | "
             "Online (collect every commit) | Break-even (runs) | Agent task |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    pooled: dict = {}
    for name in names:
        rows = [r for r in b1.rows(name).values()]
        per = [pair_costs(r, k) for r in rows]
        for tool in sorted({t for p in per for t in p}):
            xs = [p[tool] for p in per if tool in p]
            pooled.setdefault(tool, []).extend(xs)
            g = lambda f: _med(x[f] for x in xs)
            no_gain = sum(x["break_even"] is None for x in xs) if tool != "run_all" else 0
            lines.append(f"| {name} | {tool} | {len(xs)} | {_fmt(g('run_all'))} | {_fmt(g('collect'))} | "
                         f"{_fmt(g('run'))} | {_fmt(g('offline'), True)} | {_fmt(g('online'), True)} | "
                         f"{_fmt(g('break_even'))}{f' ({no_gain} never)' if no_gain else ''} | "
                         f"{_fmt(g('agent_task'), True)} |")
    if len(names) > 1:
        for tool, xs in sorted(pooled.items()):
            g = lambda f: _med(x[f] for x in xs)
            lines.append(f"| **all** | {tool} | {len(xs)} | {_fmt(g('run_all'))} | {_fmt(g('collect'))} | "
                         f"{_fmt(g('run'))} | {_fmt(g('offline'), True)} | {_fmt(g('online'), True)} | "
                         f"{_fmt(g('break_even'))} | {_fmt(g('agent_task'), True)} |")
    os.makedirs(b1.OUT, exist_ok=True)
    open(os.path.join(b1.OUT, "overhead.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
