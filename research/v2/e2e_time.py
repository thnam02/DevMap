"""End-to-end time on the main benchmark (650 changes): Proviso's selection time plus the test time of the tests it
selects, against running the whole suite. Read from the result rows only (no test is run here).

Per change: full = sum of the plain (untraced) per-test times of the suite at the change's base commit (row "full_s");
Proviso = its warm selection time ("selection_s", measured in score_all / _proviso_row: base caches warm, the changed
tree's import-time snapshot taken in the timed call) + time_share * full. pytest's start-up and collection are left
out of both sides (a selective run pays them too). Rows are filtered exactly like report-all.md (real-commit sample,
flaky failures and tests the change created removed), so the changes are the same 650.

Usage: python research/v2/e2e_time.py [--md OUT.md]"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline as PL  # noqa: E402

REPOS = ["sqlglot", "sympy", "sqlalchemy", "pygments", "datasette"]


def rows_of(repo: str) -> list[dict]:
    PL.use(repo)
    out = []
    for stage in ("select", "realeval"):
        rows = list(PL.merged(stage).values())
        if stage == "realeval":
            ids = {r["id"] for r in PL.real_set()}
            rows = [r for r in rows if r["id"] in ids]
        for r in PL._confirmed(rows, stage):
            p = r["selectors"].get("proviso")
            if not p or "error" in p:
                continue
            full = r["full_s"]
            out.append({"repo": repo, "stage": stage, "id": r["id"], "full": full, "sel": p["selection_s"],
                        "tests": p["time_share"] * full, "share": p["time_share"], "reason": p.get("reason"),
                        "e2e": p["selection_s"] + p["time_share"] * full})
    return out


def summary(rs: list[dict]) -> dict:
    full, e2e = sum(r["full"] for r in rs), sum(r["e2e"] for r in rs)
    return {"changes": len(rs), "full_median": st.median(r["full"] for r in rs),
            "e2e_median": st.median(r["e2e"] for r in rs),
            "e2e_share_of_full_total": e2e / full,
            "e2e_share_median": st.median(r["e2e"] / r["full"] for r in rs),
            "faster": sum(r["e2e"] < r["full"] for r in rs),
            "sel_median": st.median(r["sel"] for r in rs), "sel_p90": sorted(r["sel"] for r in rs)[int(0.9 * len(rs))],
            "sel_max": max(r["sel"] for r in rs), "sel_share_total": sum(r["sel"] for r in rs) / full,
            "full_suite_fallbacks": sum(r["share"] >= 0.999 for r in rs)}


def main() -> None:
    allr = [r for repo in REPOS for r in rows_of(repo)]
    groups = [(repo, [r for r in allr if r["repo"] == repo]) for repo in REPOS] + [("all", allr)]
    lines = ["| Project | Changes | Full suite, median s | Proviso end to end, median s | End to end / full (total) | "
             "End to end / full (median) | Faster than full | Selection median / p90 / max s | Selection / full (total) "
             "| Full-suite selections |", "|---|---|---|---|---|---|---|---|---|---|"]
    for name, rs in groups:
        s = summary(rs)
        lines.append(f"| {name} | {s['changes']} | {s['full_median']:.1f} | {s['e2e_median']:.1f} | "
                     f"{100 * s['e2e_share_of_full_total']:.1f}% | {100 * s['e2e_share_median']:.1f}% | "
                     f"{s['faster']} of {s['changes']} | {s['sel_median']:.2f} / {s['sel_p90']:.2f} / {s['sel_max']:.1f} | "
                     f"{100 * s['sel_share_total']:.1f}% | {s['full_suite_fallbacks']} |")
    slower = [r for r in allr if r["e2e"] >= r["full"]]
    lines += ["", f"Slower than the full suite: {len(slower)} changes; of these {sum(r['share'] >= 0.999 for r in slower)} "
              f"ran the full suite (selection time added on top) and {sum(r['share'] < 0.999 for r in slower)} selected "
              "less but spent longer selecting than the skipped tests take."]
    text = "\n".join(lines)
    print(text)
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(text + "\n")
    json.dump(allr, open(os.path.join(HERE, "results", "e2e_rows.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
