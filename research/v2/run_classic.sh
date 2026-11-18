#!/usr/bin/env bash
# The classic safety measure on the main benchmark (650 changes): which tests that run changed code each selector
# (Proviso, testmon, NameRTS, TDAD) skips. Uses the maps, testmon databases and NameRTS caches already recorded; no
# test is run, no API cost. Resumable. Also classifies the SWE-bench agent patches by whether they edit import-time
# code (importtime_changes.py; the patch files are only on this machine). Run on the machine that holds $PROVISO_WORK.
#   bash research/v2/run_classic.sh                 # all five repositories, then results/classic.md; pushed at the end
#   CLASSIC_SELECTORS=proviso,tdad bash research/v2/run_classic.sh   # a subset of selectors
set -uo pipefail
cd "$(dirname "$0")/../.."
export PROVISO_WORK=${PROVISO_WORK:-$HOME/proviso-work/v2}
export TDAD_SRC=${TDAD_SRC:-$PROVISO_WORK/TDAD/tdad/src}
VENV=${PROVISO_VENV:-$HOME/proviso-work/venv}
# shellcheck disable=SC1091
. "$VENV/bin/activate"
for r in sqlglot pygments datasette sqlalchemy sympy; do
  echo "== $r: classic ($(date +%T))" | tee -a "$PROVISO_WORK/run.log"
  python research/v2/pipeline.py "$r" classic 2>&1 | tee -a "$PROVISO_WORK/run.log"
  grep -h "ERROR" "$PROVISO_WORK/$r"/classic.w*.log 2>/dev/null | tail -5
done
python research/v2/classic_report.py --md research/v2/results/classic.md
# how many agent patches edit code that runs at import (static, no tests run; needs the patches under $PROVISO_WORK/swe)
python research/v2/importtime_changes.py agent | tail -25
python research/v2/importtime_changes.py agent --all | tail -15
git add research/v2/results
git commit -qm "Main benchmark: classic safety measure ($(hostname), $(date +%F))" && \
  git pull -q --rebase && git push -q && echo "== pushed"
echo "== classic finished ($(date +%T))"
