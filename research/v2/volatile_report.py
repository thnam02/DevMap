"""Write results/v25/volatile_eval.md from the outputs of volatile_eval.py and volatile_history.py."""
import json
import os
import sys

src, out = sys.argv[1], sys.argv[2]
P = ["sqlalchemy", "xarray", "dask", "sphinx"]
L = ["# v2.5: run-varying import-time values, snapshot-level evaluation", "",
     "Branch `v2.5-dev`. Mechanism on = default; off = `PROVISO_OFF=volatile` (the v2.3.2 comparison). Run in the cloud "
     "workspace on Python 3.13 with the four projects cloned at the parents the PC used in NOCHANGE_IMPACT.md. "
     "No test suites were run here: these numbers are about the import-time comparison only. "
     "dask.dataframe does not import here (pyarrow is missing), so its values are not covered.", "",
     "## No-op change (a comment added to the package's `__init__.py`), 20 fresh comparisons each", "",
     "| Project | Values compared | Trials reporting a change, off | Values reported, off | Trials reporting a change, on | "
     "Values reported, on | Base snapshot off (s) | on (s) |", "|---|---|---|---|---|---|---|---|"]
R = {p: json.load(open(os.path.join(src, f"{p}.json"))) for p in P}
for p in P:
    r = R[p]
    n = r["noop"]
    L.append(f"| {p} | {r['keys']} | {n['off']['trials_with_changes']} of {n['off']['trials']} | "
             f"{len(n['off']['keys_ever_changed'])} | {n['on']['trials_with_changes']} of {n['on']['trials']} | "
             f"{len(n['on']['keys_ever_changed'])} | {r['base_seconds_off']} | {r['base_seconds_on']} |")
L += ["", "## What is still compared in each run-varying value", "",
      "Leaves of the value: compared exactly; compared by shape (kind, common start and end, length); by kind only; "
      "not compared. Random edits: 300 single edits to the value (change a leaf, drop or add an element) and how many "
      "the comparison reports.", "",
      "| Project | Value | Exact | Shape | Kind | Not compared | Random edits reported |", "|---|---|---|---|---|---|---|"]
for p in P:
    for k, m in R[p]["mask"].items():
        mu = R[p]["mutate"].get(k)
        L.append(f"| {p} | `{k}` | {m['exact']} | {m['shape']} | {m['kind']} | {m['any']} | "
                 + (f"{mu['detected']} of {mu['edits']}" if mu else "n/a") + " |")
L += ["", "## Seeded real changes (mechanism on)", "",
      "| Project | Edit | Reported | By | Values reported |", "|---|---|---|---|---|"]
for p in P:
    for s in R[p]["seeded"]:
        L.append(f"| {p} | {s['edit']} | {'yes' if s['detected_on'] else 'NO'} | {s['by']} | "
                 f"{', '.join('`' + x.split(':', 1)[1] + '`' for x in (s['changed_on'] or s['guard_adds'])[:4])} |")
L += ["", "## Recent real commits (parent as base, commit as working tree)", "",
      "| Project | Commits | Reported only with the mechanism on | Median values reported, off | on | "
      "Commits with nothing reported, off | on | Removed values that are not run-varying | "
      "Removed values in an edited module (guard puts back) |", "|---|---|---|---|---|---|---|---|---|"]
for p in P:
    f = os.path.join(src, f"{p}_history.json")
    if not os.path.exists(f):
        continue
    rows = [x for x in json.load(open(f))["rows"] if "skip" not in x]
    if not rows:
        continue
    med = lambda v: sorted(v)[len(v) // 2]
    L.append(f"| {p} | {len(rows)} | {sum(len(x['only_on']) for x in rows)} | {med([x['n_off'] for x in rows])} | "
             f"{med([x['n_on'] for x in rows])} | {sum(x['n_off'] == 0 for x in rows)} | {sum(x['n_on'] == 0 for x in rows)} | "
             f"{sum(len(x['removed_not_covered']) for x in rows)} | "
             f"{sum(len(x['removed_in_edited_module']) for x in rows)} ({sum(len(x['guard_puts_back']) for x in rows)}) |")
open(out, "w").write("\n".join(L) + "\n")
print("\n".join(L))
