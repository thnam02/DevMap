#!/bin/bash
# (1) shared venv rebuilt on uv's CPython 3.12 (bundles SQLite 3.54.1): the system python3.12 (SQLite 3.45.1)
#     segfaults in sqlite3 during sqlalchemy's whole suite (test/orm/test_eager_relations.py, ~23%), uv's runs it through.
#     Same packages as run_all.sh + run_overnight.sh + the known gaps. The old venv is kept as venv-system312.
# (2) dask: optional test deps its files import (skipped at collection), pip-installable ones only (not pyspark: Java;
#     not cupy: GPU), under NameRTS's numpy/pandas/pytest pins.
set -uo pipefail
export PATH=$HOME/.local/bin:$PATH
cd "$HOME/proviso-dev"
V=$HOME/proviso-work/venv
P312=$(uv python find --managed-python 3.12)
echo "== $(date -u +%T) uv python 3.12: $P312"
[ -d "$HOME/proviso-work/venv-system312" ] || mv "$V" "$HOME/proviso-work/venv-system312"
rm -rf "$V"
uv venv -q --seed --python "$P312" "$V"
. "$V/bin/activate"
python -c 'import sys, sqlite3; print("venv:", sys.version.split()[0], "sqlite", sqlite3.sqlite_version)'
pip install -q --upgrade pip
pip install -q pytest==9.1.1 pytest-testmon==2.2.0 coverage==7.10.7 execnet==2.1.1 greenlet typing-extensions mpmath hypothesis
pip install -q -r research/v2/requirements-namerts.txt
pip install -q pydantic-settings gitpython neo4j
pip install -q "asgiref>=3.2.10" "click>=7.1.1" "click-default-group>=1.2.3" "Jinja2>=2.10.3" "hupper>=1.9" \
    "httpx2>=2.0" "pluggy>=1.0" "uvicorn>=0.29" "aiofiles>=0.4" "PyYAML>=5.3" "mergedeep>=1.1.1" "itsdangerous>=1.1" \
    "sqlite-utils>=4.0" "asyncinject>=0.7" setuptools "pydantic>=2" "opentelemetry-api>=1.37" \
    "pytest-asyncio>=1.2.0" "beautifulsoup4>=4.8.1" "pytest-timeout>=1.4.2" "trustme>=0.7" "cogapp>=3.3.0" \
    "multipart-form-data-conformance==0.1a0" "opentelemetry-sdk>=1.37"
pip install -q pytz duckdb wcag_contrast_ratio
touch "$V/.proviso-v2-deps" "$V/.proviso-v2-extra"
echo "shared venv packages: $(pip list 2>/dev/null | wc -l)"
deactivate
echo "== $(date -u +%T) dask optional test deps"
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
D=$HOME/proviso-work/v2/nrbench-venvs/dask/bin/python
"$D" -m pip install -q -c "$C" cachey fastavro requests s3fs scipy scikit-image sparse sqlalchemy xarray ipycytoscape 2>&1 | tail -3
rm -f "$C"
"$D" -c 'import numpy, pandas, pytest; print("dask venv: numpy", numpy.__version__, "pandas", pandas.__version__, "pytest", pytest.__version__)'
echo "== $(date -u +%T) ROUND3 DONE"
