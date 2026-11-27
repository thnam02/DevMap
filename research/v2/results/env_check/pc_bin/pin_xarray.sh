#!/bin/bash
# xarray: its pytest addopts need pytest-mypy-plugins (NameRTS built the env from xarray's ci/requirements/environment.yml,
# which has it); install the test plugins and typing deps from that file, keeping NameRTS's numpy/pandas/pytest pins.
PY=$HOME/proviso-work/v2/nrbench-venvs/xarray/bin/python
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
"$PY" -m pip install -q -c "$C" pytest-env pytest-mypy-plugins pytest-timeout pytest-xdist "mypy==1.15" \
  "pandas-stubs<=2.2.3.241126" pyarrow types-PyYAML types-python-dateutil types-pytz types-setuptools 2>&1 | tail -3
"$PY" -c 'import pytest, numpy, pandas, mypy.version; print("xarray venv: pytest", pytest.__version__, "numpy", numpy.__version__, "pandas", pandas.__version__, "mypy", mypy.version.__version__)'
rm -f "$C"
