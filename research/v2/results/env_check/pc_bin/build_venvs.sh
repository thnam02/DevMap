#!/bin/bash
# Per-project venvs (Python 3.13) for NameRTS's projects, as research/v2/run_nrbench.sh builds them (install_deps
# copied verbatim), plus the evaluation's pinned test tools; NameRTS's own pinned deps go to a separate --target dir
# (NAMERTS_DEPS) so they do not change the projects' packages. Also: known gaps of the shared 3.12 venv.
set -uo pipefail
export PATH=$HOME/.local/bin:$PATH
cd "$HOME/proviso-dev"
export PROVISO_WORK=$HOME/proviso-work/v2
ENVS=$PROVISO_WORK/nrbench-venvs
mkdir -p "$ENVS"
NRPY=$(uv python find 3.13)
echo "== $(date -u +%T) Python $("$NRPY" --version) at $NRPY"

echo "== $(date -u +%T) shared venv: known gaps (sqlglot: pytz duckdb; pygments: wcag_contrast_ratio)"
"$HOME/proviso-work/venv/bin/pip" install -q pytz duckdb wcag_contrast_ratio || echo "WARNING: shared venv extras failed"

echo "== $(date -u +%T) NameRTS deps for 3.13 -> $PROVISO_WORK/nr-deps-3.13"
[ -f "$PROVISO_WORK/nr-deps-3.13/.done" ] || { "$NRPY" -m pip --version >/dev/null 2>&1 || true; \
  uv pip install -q --python "$NRPY" --target "$PROVISO_WORK/nr-deps-3.13" -r research/v2/requirements-namerts.txt \
  && touch "$PROVISO_WORK/nr-deps-3.13/.done"; } || echo "WARNING: NameRTS deps failed"

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

for p in "$@"; do
  echo "== $(date -u +%T) $p"
  venv=$ENVS/$p
  src=$PROVISO_WORK/nrbench/$p/repo
  if [ ! -f "$venv/.proviso-deps" ]; then
    [ -x "$venv/bin/python" ] || "$NRPY" -m venv "$venv"
    url=$(python3 -c "import sys; sys.path.insert(0, 'research/v2'); import nrbench; print(nrbench.PROJECTS['$p']['url'])")
    [ -d "$src/.git" ] || { mkdir -p "$(dirname "$src")"; git clone -q "$url" "$src"; }
    install_deps "$p" "$venv/bin/python" "$src" || echo "== $p: some dependencies failed to install (see above)"
    "$venv/bin/python" -m pip install -q pytest==9.1.1 pytest-testmon==2.2.0 coverage==7.10.7 execnet==2.1.1 \
      && touch "$venv/.proviso-deps" || echo "== $p: pinned test tools failed"
  fi
  "$venv/bin/python" -c 'import pytest, testmon; print("  pytest", pytest.__version__, "ok")' || echo "== $p: pytest/testmon missing"
done
echo "== $(date -u +%T) VENVS DONE"
