"""v2.5 run-varying values on real history, snapshot level: for the last K commits that touch the package, compare the
import-time state of the parent (base) with the commit (working tree) with the mechanism off (v2.3.2) and on.

Checks per commit:
  subset     every key reported with the mechanism on is also reported with it off, except keys whose fingerprint the
             set-constant fix made comparable (listed, none expected on Python 3.12)
  removed    keys reported off but not on: each must be a run-varying value of the parent (it has a pattern) that the
             commit's value still fits
  touched    removed keys whose module the commit edits, and whether the edited-statement guard puts them back

Usage: python volatile_history.py PROJECT ROOT PKGDIR OUT.json [--commits K]
ROOT must be a clone this script may check commits out in.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, HERE)
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as S  # noqa: E402
from volatile_eval import git, package_files, with_off  # noqa: E402

PY = sys.executable


def run(project, root, pkgdir, out, k):
    start = git(root, "rev-parse", "HEAD").strip()
    commits = [c for c in git(root, "log", "--no-merges", f"-{k}", "--format=%H", start, "--", pkgdir).split("\n") if c]
    rows = []
    tmp = os.path.dirname(os.path.abspath(out))
    try:
        for c in commits:
            subprocess.run(["git", "-C", root, "checkout", "-q", "-f", c], check=True)
            files = package_files(root, pkgdir)
            parent_files = [f for f in git(root, "ls-tree", "-r", "--name-only", "HEAD~1", pkgdir).split("\n")
                            if f.endswith(".py") and not I._is_test_path(f) and not I._is_test_support(f)]
            files = sorted(set(files) & set(parent_files))
            changed_files = {f for f in git(root, "diff", "--name-only", "HEAD~1", "HEAD").split("\n") if f}
            t0 = time.time()
            base = {}
            for m in ("off", "on"):
                cache = os.path.join(tmp, f"{project}_hist_{m}.json")
                if os.path.exists(cache):
                    os.remove(cache)
                base[m] = with_off(m == "off", lambda: S.base_snapshot(root, files, PY, cache, rev="HEAD~1"))
            if base["on"] is None or base["off"] is None:
                rows.append({"commit": c[:10], "skip": "no base snapshot"})
                continue
            pats = base["on"].get("patterns", {})
            cur = S.snapshot(root, files, PY, heap_pad=7919, tree_keys=sorted(pats))
            if cur is None:
                rows.append({"commit": c[:10], "skip": "commit does not import"})
                continue
            d_off = with_off(True, lambda: S.diff(base["off"], cur))
            d_on = S.diff(base["on"], cur)
            on, off = set(d_on["changed"]), set(d_off["changed"])
            removed = sorted(off - on)
            prefix = I._layout_prefix(files)
            back = []
            for key in d_on["covered"]:
                mod, qual = key.split(":", 1)
                f = next((x for x in changed_files if I._module_of(x, prefix) == mod), None)
                if f is None:
                    continue
                tn = I._changed_top_names(git(root, "show", f"HEAD~1:{f}"), open(os.path.join(root, f)).read())[0]
                if tn is None or qual.split(".", 1)[0] in tn:
                    back.append(key)
            mods_changed = {I._module_of(x, prefix) for x in changed_files}
            rows.append({"commit": c[:10], "files_changed": len(changed_files), "n_off": len(off), "n_on": len(on),
                         "only_on": sorted(on - off), "removed": removed,
                         "removed_not_covered": sorted(set(removed) - set(d_on["covered"])),
                         "removed_in_edited_module": [x for x in removed if x.split(":", 1)[0] in mods_changed],
                         "guard_puts_back": back, "patterns": len(pats), "errors_on": d_on["errors"],
                         "seconds": round(time.time() - t0, 1)})
            print(json.dumps(rows[-1])[:400], flush=True)
    finally:
        subprocess.run(["git", "-C", root, "checkout", "-q", "-f", start])
    json.dump({"project": project, "start": start[:10], "rows": rows}, open(out, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("root")
    ap.add_argument("pkgdir")
    ap.add_argument("out")
    ap.add_argument("--commits", type=int, default=20)
    a = ap.parse_args()
    run(a.project, a.root, a.pkgdir, a.out, a.commits)
