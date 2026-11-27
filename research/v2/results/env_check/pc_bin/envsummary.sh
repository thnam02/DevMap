#!/bin/bash
# one line per project from the latest env_check results (results/env_check/P.json)
cd "$HOME/proviso-dev"
python3 - "$@" <<'EOF'
import json, os, sys
ps = sys.argv[1:] or ["sqlglot", "pygments", "datasette", "sqlalchemy", "loguru", "pvlib", "pylint", "seaborn", "sphinx",
                      "xarray", "dask", "sympy"]
for p in ps:
    f = f"research/v2/results/env_check/{p}.json"
    if not os.path.exists(f):
        print(f"{p:10s} (no result)"); continue
    r = json.load(open(f))
    print(f"{p:10s} {r['commit'][:9]} tests={r['tests']:6d} files={r['test_files']:4d} FAIL_COLLECT={r['files_failing_to_collect']} "
          f"skip_coll={r['files_skipped_at_collection']} missing={','.join(r['missing_modules']) or '-'} "
          f"run_s={r.get('run_s')} exit={r.get('run_exit')} completed={r.get('run_completed')} | {r.get('run_summary')}")
EOF
for l in A B C; do echo "lane $l: $(grep -h '^== ' ~/proviso-logs/envcheck_$l.log | tail -1)"; done
