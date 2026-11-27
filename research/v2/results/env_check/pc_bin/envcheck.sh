#!/bin/bash
# STEP 3: env_check.py PROJECT, then --skips, with the project's interpreter (history projects: shared 3.12 venv;
# NameRTS's projects: their 3.13 venv). Usage: envcheck.sh PROJECT [PROJECT ...]
set -u
cd "$HOME/proviso-dev"
export PATH=$HOME/.local/bin:$PATH PROVISO_WORK=$HOME/proviso-work/v2 PROVISO_WORKERS=12 NAMERTS_WORKERS=1
export PROVISO_TEST_TIMEOUT=${PROVISO_TEST_TIMEOUT:-7200}
for p in "$@"; do
  case $p in
    sqlglot|pygments|datasette|sqlalchemy) PY=$HOME/proviso-work/venv/bin/python ;;
    *) PY=$PROVISO_WORK/nrbench-venvs/$p/bin/python ;;
  esac
  # datasette rebuilds a SQLite fixtures database per test; on WSL2's virtual disk every commit waits ~7 ms for fsync
  # (11 s per database vs 0.03 s in RAM): its temporary files go to tmpfs
  if [ "$p" = datasette ]; then export TMPDIR=/dev/shm/proviso-tmp-datasette; mkdir -p "$TMPDIR"; else unset TMPDIR; fi
  echo "== $p collect $(date -u +%T) ($PY)"; s=$(date +%s)
  "$PY" research/v2/env_check.py "$p"; rc=$?
  echo "== $p collect exit $rc after $(( $(date +%s) - s )) s"
  echo "== $p skips $(date -u +%T)"; s=$(date +%s)
  "$PY" research/v2/env_check.py "$p" --skips | head -3
  echo "== $p skips exit ${PIPESTATUS[0]} after $(( $(date +%s) - s )) s"
  "$PY" - "$p" <<'EOF'
import json, sys
r = json.load(open(f"research/v2/results/env_check/{sys.argv[1]}.json"))
print("== RESULT", sys.argv[1], json.dumps({k: r.get(k) for k in ("commit", "tests", "test_files", "files_failing_to_collect",
      "files_skipped_at_collection", "missing_modules", "collect_s", "run_s", "run_exit", "run_completed", "run_summary",
      "skipped_at_run", "skip_missing_modules")}))
EOF
done
echo "== ENVCHECK FINISHED $* $(date -u +%FT%TZ)"
