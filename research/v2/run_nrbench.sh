#!/usr/bin/env bash
# Proviso on NameRTS's benchmark (ISSTA 2026), scored with NameRTS's metric. No API cost; resumable.
#   bash research/v2/run_nrbench.sh                  # every project below, small to large; pushed after each
#   bash research/v2/run_nrbench.sh pylint sphinx    # only these
# One venv per project (test dependencies as in NameRTS's build_env.md). The tests import the code under test from
# the checked-out commit (PYTHONPATH), so the venv only supplies third-party packages.
# Not run: matplotlib and scikit-learn (compiled extensions would need a rebuild at every commit).
set -uo pipefail
cd "$(dirname "$0")/../.."
REPO_DIR=$(pwd)
export PROVISO_WORK=${PROVISO_WORK:-$HOME/proviso-work/v2}
export NAMERTS_HOME=${NAMERTS_HOME:-$PROVISO_WORK/NameRTS}
[ -d "$NAMERTS_HOME/dataset" ] || git clone -q https://github.com/ZJU-CTAG/NameRTS.git "$NAMERTS_HOME"
ENVS=$PROVISO_WORK/nrbench-venvs
mkdir -p "$ENVS"
PROJECTS=${*:-"loguru pvlib pylint sphinx seaborn xarray dask sympy"}

install_deps() {   # $1 project, $2 venv python, $3 checkout of the project (latest commit) for its own requirements
  local p=$1 py=$2 src=$3
  "$py" -m pip install -q -U pip setuptools wheel
  case $p in
    loguru)  "$py" -m pip install -q -e "$src[dev]" freezegun ;;
    pvlib)   "$py" -m pip install -q -e "$src[all]" pytest setuptools-scm ;;
    pylint)  "$py" -m pip install -q -e "$src" pytest GitPython pytest_benchmark pyenchant; \
             "$py" -m pip install -q -e "$src[all]" 2>/dev/null || true ;;
    sphinx)  "$py" -m pip install -q -e "$src" pytest cython defusedxml setuptools typing_extensions ;;
    seaborn) "$py" -m pip install -q pyparsing "$src[dev,stats]" ;;
    xarray)  "$py" -m pip install -q -e "$src[complete]" pytest hypothesis pytest-timeout ;;
    dask)    "$py" -m pip install -q -e "$src[complete,test]" ;;
    sympy)   "$py" -m pip install -q -e "$src" pytest hypothesis mpmath ;;
  esac
}

for p in $PROJECTS; do
  echo "== $p ($(date +%T))"
  venv=$ENVS/$p
  src=$PROVISO_WORK/nrbench/$p/repo
  if [ ! -x "$venv/bin/python" ]; then
    python3 -m venv "$venv"
    url=$(python3 -c "import sys; sys.path.insert(0, 'research/v2'); import nrbench; print(nrbench.PROJECTS['$p']['url'])")
    [ -d "$src/.git" ] || { mkdir -p "$(dirname "$src")"; git clone -q "$url" "$src"; }
    install_deps "$p" "$venv/bin/python" "$src" || echo "== $p: some dependencies failed to install (see above)"
  fi
  "$venv/bin/python" -c 'import pytest' || { echo "== $p: pytest missing in its venv; skipped"; continue; }
  python3 research/v2/nrbench.py "$p" 50 --python "$venv/bin/python" 2>&1 | tee -a "$PROVISO_WORK/nrbench.log"
  python3 research/v2/nrbench.py report > research/v2/results/nrbench/report.md
  git add research/v2/results/nrbench
  git commit -qm "NameRTS benchmark: $p ($(hostname), $(date +%F))" && { git pull -q --rebase && git push -q && echo "== pushed"; }
done
echo "== finished ($(date +%T))"
