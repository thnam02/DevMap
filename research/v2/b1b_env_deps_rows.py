"""Add b1b.deps_fingerprint() (env_deps: the SWE environment's packages without the project under test) to B1b rows
written before it existed.

The rows recorded only the full fingerprint's hash and package count, not the package list. So env_deps is computed
from the environment's package list now. This is valid because, since B1b's first start (2026-11-27 18:15:24 UTC), the
only change in any SWE environment has been the project's own editable install. Every other dist-info in the
environments predates it (coverage, execnet and pytest-testmon were added at 18:14; checked from file dates
2026-11-28). Per row, a consistency check: the row's recorded package count must equal the dependencies now plus the
project's own distribution (env_deps_check). Run only while B1b is stopped (rows files are rewritten).
  python research/v2/b1b_env_deps_rows.py [--dry-run]"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1b  # noqa: E402

NOTE = ("from the environment's package list on 2026-11-28; the only change in SWE environments since B1b's first start "
        "is the project's own editable install (file dates)")


def main():
    dry = "--dry-run" in sys.argv
    envs = b1b.envs_ok()
    cache, bad = {}, []
    for path in sorted(glob.glob(os.path.join(b1b.OUT, "rows.w*.jsonl"))):
        lines, changed = [], 0
        for line in open(path):
            if not line.strip():
                continue
            r = json.loads(line)
            if "env_deps" not in r:
                key = (r["repo"], r["version"])
                if key not in cache:
                    cache[key] = b1b.deps_fingerprint(envs[key], r["repo"])
                d = dict(cache[key])
                rec = (r.get("env") or {}).get("packages")
                ok = rec == d["packages"] + 1
                r["env_deps"] = {**d, "backfilled": NOTE}
                r["env_deps_check"] = {"row_packages": rec, "deps_plus_project": d["packages"] + 1, "consistent": ok}
                if not ok:
                    bad.append((r["id"], rec, d["packages"] + 1))
                changed += 1
            lines.append(json.dumps(r) + "\n")
        if changed and not dry:
            open(path, "w").writelines(lines)
        print(f"{os.path.basename(path)}: {changed} rows {'would get' if dry else 'got'} env_deps")
    for k, d in sorted(cache.items()):
        print(f"  {k[0]} {k[1]}: deps hash {d['hash']} ({d['packages']} packages; excluded {d['excluded']})")
    print("package-count check: all consistent" if not bad else f"package-count check: {len(bad)} inconsistent: {bad}")


if __name__ == "__main__":
    main()
