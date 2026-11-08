#!/usr/bin/env bash
# Proviso v2 evaluation, step by step (no API cost; each step resumable; results pushed as they finish).
#   bash research/v2/run_v2.sh gate     # 1. safety gate: the main benchmark (650 changes) re-scored with v2, its
#                                       #    dependency maps re-recorded by the v2 recorder (v1 maps kept as *.v1.json)
#   bash research/v2/run_v2.sh rescore  # 1 without re-recording (selection rules changed, recorder did not)
#   bash research/v2/run_v2.sh samemaps # 1b. selection logic alone: v2 vs v1 on the same (v1) dependency maps
#   bash research/v2/run_v2.sh ablate PARTS  # ablation on the main benchmark (PARTS: snapshot, docs, ... or traditional)
#   bash research/v2/run_v2.sh ablate-dev PARTS  # the same on the NameRTS development projects
#   bash research/v2/run_v2.sh dev      # 2. NameRTS benchmark, development projects (loguru pylint pvlib) + verify
#   bash research/v2/run_v2.sh test     # 3. NameRTS benchmark, test projects (sphinx seaborn xarray dask sympy)
#                                       #    + verify — run only after 1 and 2 are reviewed
# NameRTS-benchmark results: research/v2/results/nrbench_v<VERSION> for the Proviso version in src (v2.3 in nrbench_v2.3,
# v2.2.1 in nrbench_v2.2.1, v2 in nrbench_v2, v1 in nrbench); main-benchmark rows keep the frozen v2 result as
# "proviso_v2" when a later version re-scores them.
set -uo pipefail
cd "$(dirname "$0")/../.."
export TMPDIR=${TMPDIR:-$HOME/proviso-work/tmp}
mkdir -p "$TMPDIR"
PV=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/dc_engine/impact.py)
export NRBENCH_OUT=${NRBENCH_OUT:-research/v2/results/nrbench_v$PV}
step=${1:-}
case $step in
  gate)
    PROVISO_RERECORD=1 bash research/v2/run_reproviso.sh ;;
  rescore)
    # the gate without re-recording: the current selection logic on the maps the last gate recorded (use when only
    # selection rules changed, not the recorder)
    bash research/v2/run_reproviso.sh ;;
  samemaps)
    # selection logic alone: the current Proviso on the v1 dependency maps, compared with v1 on the same maps.
    # Same interpreter as the gate (the evaluation venv): the import-time snapshot imports the package with it, and
    # a Python without the repository's dependencies makes every snapshot fail on both sides (no change seen)
    export PROVISO_WORK=${PROVISO_WORK:-$HOME/proviso-work/v2}
    # shellcheck disable=SC1091
    . "${PROVISO_VENV:-$HOME/proviso-work/venv}/bin/activate"
    for r in sqlglot sympy sqlalchemy pygments datasette; do
      echo "== $r: samemaps ($(date +%T))"
      python research/v2/pipeline.py "$r" samemaps 2>&1 | tail -3
    done
    cat research/v2/results/*/samemaps.md
    git add research/v2/results
    git commit -qm "v2 safety gate on identical maps: current selection logic vs v1, both on the v1 dependency maps ($(hostname), $(date +%F))" && \
      { git pull -q --rebase && git push -q && echo "== pushed"; } ;;
  ablate|ablate-dev)
    # ablation: one Proviso variant (see the switches in src/dc_engine/impact.py), e.g.
    #   run_v2.sh ablate snapshot           # main benchmark, on the maps the last gate recorded (~10 min)
    #   run_v2.sh ablate docs,hints         # several parts off together
    #   run_v2.sh ablate traditional        # the classic rule: every test that executes changed code
    #   run_v2.sh ablate-dev subprocess     # NameRTS development projects (recorder switches need this: it records)
    v=${2:?which parts to turn off (comma-separated), or traditional}
    if [ "$v" = traditional ]; then export PROVISO_MODE=traditional; name=traditional
    else export PROVISO_OFF="$v"; name="off-$(echo "$v" | tr ',' '\n' | sort | paste -sd- -)"; fi
    if [ "$step" = ablate ]; then
      export PROVISO_WORK=${PROVISO_WORK:-$HOME/proviso-work/v2}
      # shellcheck disable=SC1091
      . "${PROVISO_VENV:-$HOME/proviso-work/venv}/bin/activate"
      for r in sqlglot sympy sqlalchemy pygments datasette; do
        echo "== $r: ablate $name ($(date +%T))"
        python research/v2/pipeline.py "$r" ablate 2>&1 | tail -2
      done
      cat research/v2/results/*/ablate-"$name".md
      git add research/v2/results
    else
      export NRBENCH_OUT=research/v2/results/nrbench_ablate_v${PV}_$name
      bash research/v2/run_nrbench.sh loguru pylint pvlib
      git add "$NRBENCH_OUT"
    fi
    git commit -qm "Ablation $name, Proviso v$PV ($step, $(hostname), $(date +%F))" && { git pull -q --rebase && git push -q && echo "== pushed"; } ;;
  dev|test)
    if [ "$step" = dev ]; then P="loguru pylint pvlib"; else P="sphinx seaborn xarray dask sympy"; fi
    bash research/v2/run_nrbench.sh $P
    python3 research/v2/nrcheck.py verify $P 2>&1 | tee "$NRBENCH_OUT/verify_$step.log"
    git add "$NRBENCH_OUT"
    git commit -qm "Proviso v$PV on NameRTS's benchmark: $step projects verified ($(hostname), $(date +%F))" && \
      { git pull -q --rebase && git push -q && echo "== pushed"; } ;;
  *) sed -n 2,9p "$0"; exit 1 ;;
esac
