#!/bin/bash
# Pin NameRTS's project venvs to NameRTS's own evaluation environment (NameRTS/environment_313.yml: pytest 8.4.1,
# numpy 2.3.5, pandas 2.3.3; build_env.md: pvlib pytest 8.4.2): the latest pytest 9 / numpy reject the older commits'
# configs (pvlib testpaths, seaborn marks on fixtures) and turn numpy deprecations into errors (xarray, dask).
set -u
E=$HOME/proviso-work/v2/nrbench-venvs
for p in loguru pvlib pylint seaborn sphinx xarray dask sympy; do
  "$E/$p/bin/python" -m pip install -q "pytest==8.4.1" 2>&1 | grep -v '^$' | tail -2
  case $p in xarray|dask) "$E/$p/bin/python" -m pip install -q "numpy==2.3.5" "pandas==2.3.3" 2>&1 | tail -3 ;; esac
  echo "$p: $("$E/$p/bin/python" -c 'import pytest, numpy; print("pytest", pytest.__version__, "numpy", numpy.__version__)' 2>/dev/null || "$E/$p/bin/python" -c 'import pytest; print("pytest", pytest.__version__)')"
done
