#!/usr/bin/env bash
# Proviso v2 evaluation, step by step (no API cost; each step resumable; results pushed as they finish).
#   bash research/v2/run_v2.sh gate     # 1. safety gate: the main benchmark (650 changes) re-scored with v2, its
#                                       #    dependency maps re-recorded by the v2 recorder (v1 maps kept as *.v1.json)
#   bash research/v2/run_v2.sh dev      # 2. NameRTS benchmark, development projects (loguru pylint pvlib) + verify
#   bash research/v2/run_v2.sh test     # 3. NameRTS benchmark, test projects (sphinx seaborn xarray dask sympy)
#                                       #    + verify — run only after 1 and 2 are reviewed
# v2 NameRTS-benchmark results go to research/v2/results/nrbench_v2 (v1 results stay in research/v2/results/nrbench).
set -uo pipefail
cd "$(dirname "$0")/../.."
export TMPDIR=${TMPDIR:-$HOME/proviso-work/tmp}
mkdir -p "$TMPDIR"
export NRBENCH_OUT=research/v2/results/nrbench_v2
step=${1:-}
case $step in
  gate)
    PROVISO_RERECORD=1 bash research/v2/run_reproviso.sh ;;
  dev|test)
    if [ "$step" = dev ]; then P="loguru pylint pvlib"; else P="sphinx seaborn xarray dask sympy"; fi
    bash research/v2/run_nrbench.sh $P
    python3 research/v2/nrcheck.py verify $P 2>&1 | tee "$NRBENCH_OUT/verify_$step.log"
    git add "$NRBENCH_OUT"
    git commit -qm "Proviso v2 on NameRTS's benchmark: $step projects verified ($(hostname), $(date +%F))" && \
      { git pull -q --rebase && git push -q && echo "== pushed"; } ;;
  *) sed -n 2,9p "$0"; exit 1 ;;
esac
