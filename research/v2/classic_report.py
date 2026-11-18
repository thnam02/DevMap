"""The classic safety measure on the main benchmark, from the classic.w*.jsonl rows (pipeline.py REPO classic), next
to the missed-failure measure from the main rows. Two reference sets (see pipeline._classic_row):
  exec  every test that executes changed code; code run at import counts as executed by every test (Ekstazi's rule)
  func  every test that ran a modified function (NameRTS's SafeR reference)
A selector is classically unsafe on a change if it skips any reference test. Same change set as report-all.md.

Usage: python research/v2/classic_report.py [--md OUT.md]"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline as PL  # noqa: E402

REPOS = ["sqlglot", "sympy", "sqlalchemy", "pygments", "datasette"]
NAMES = ["proviso", "testmon", "namerts", "tdad"]


def rows_of(repo):
    PL.use(repo)
    cl = PL.merged("classic")
    out = []
    for stage in ("select", "realeval"):
        rows = list(PL.merged(stage).values())
        if stage == "realeval":
            ids = {r["id"] for r in PL.real_set()}
            rows = [r for r in rows if r["id"] in ids]
        for r in PL._confirmed(rows, stage):
            c = cl.get(f"{stage}:{r['id']}")
            out.append({"repo": repo, "stage": stage, "id": r["id"], "main": r, "classic": c})
    return out


def table(rows, ref):
    lines = [f"| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped "
             f"(of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |",
             "|---|---|---|---|---|---|"]
    for k in NAMES:
        have = [r for r in rows if r["classic"] and k in r["classic"]["selectors"]
                and "error" not in r["classic"]["selectors"][k] and ref in r["classic"]["ref"]]
        if not have:
            continue
        s = lambda r: r["classic"]["selectors"][k]
        unsafe = [r for r in have if s(r)[f"skipped_{ref}"]]
        tot = sum(r["classic"]["ref"][ref] for r in have)
        skipped = sum(s(r)[f"skipped_{ref}"] for r in have)
        files = sum(1 for r in have if s(r)[f"skipped_{ref}_files"])
        mains = [r for r in have if r["main"]["truth"] and k in r["main"]["selectors"]
                 and "error" not in r["main"]["selectors"][k]]
        missed = sum(1 for r in mains if r["main"]["selectors"][k]["missed"])
        lines.append(f"| {k} | {len(have)} | {len(unsafe)} | {skipped:,} of {tot:,} ({100 * skipped / max(1, tot):.1f}%) | "
                     f"{files} changes | {missed} of {len(mains)} |")
    return lines


def crosstab(rows, k="proviso", ref="exec"):
    have = [r for r in rows if r["classic"] and k in r["classic"]["selectors"]
            and "error" not in r["classic"]["selectors"][k] and r["main"]["truth"]]
    a = lambda r: bool(r["classic"]["selectors"][k][f"skipped_{ref}"])
    b = lambda r: bool(r["main"]["selectors"][k]["missed"])
    return (f"{k}, {ref} reference, changes that break tests ({len(have)}): classically unsafe and missed a failure "
            f"{sum(a(r) and b(r) for r in have)}; classically unsafe, no failure missed {sum(a(r) and not b(r) for r in have)}; "
            f"classically safe but missed a failure {sum(b(r) and not a(r) for r in have)}; both fine "
            f"{sum(not a(r) and not b(r) for r in have)}")


def main():
    rows = [r for repo in REPOS for r in rows_of(repo)]
    missing = [r for r in rows if not r["classic"]]
    out = [f"# Classic safety measure, main benchmark ({len(rows)} changes; {len(missing)} without a classic row)", ""]
    for ref, title in (("exec", "Reference: every test that executes changed code (import-time code: every test)"),
                       ("func", "Reference: every test that ran a modified function (NameRTS's SafeR)")):
        out += [f"## {title}", ""] + table(rows, ref) + ["", crosstab(rows, "proviso", ref), ""]
    imp = [r for r in rows if r["classic"] and r["classic"]["exec_all"]]
    out += [f"Changes whose exec reference is the whole suite (code run at import, or a full-suite rule): {len(imp)}", ""]
    for repo in REPOS:
        out += [f"### {repo}", ""] + table([r for r in rows if r["repo"] == repo], "exec") + [""]
    text = "\n".join(out)
    print(text)
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(text + "\n")


if __name__ == "__main__":
    main()
