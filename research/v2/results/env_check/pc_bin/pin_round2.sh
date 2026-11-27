#!/bin/bash
# round 2 of pins (see pin_venvs.sh): xarray needs pytest-mypy-plugins 3.x (its addopts use --mypy-only-local-stub,
# gone in 4.x); pvlib needs NameRTS's pandas 2.3.3 / numpy 2.3.5 (pandas 3 drops the 'M' offset alias its tests use)
E=$HOME/proviso-work/v2/nrbench-venvs
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
"$E/xarray/bin/python" -m pip install -q -c "$C" "pytest-mypy-plugins<4" 2>&1 | tail -2
"$E/pvlib/bin/python" -m pip install -q -c "$C" "numpy==2.3.5" "pandas==2.3.3" 2>&1 | tail -3
rm -f "$C"
"$E/xarray/bin/python" -m pip list 2>/dev/null | grep -iE 'pytest-mypy|^numpy |^pandas '
"$E/pvlib/bin/python" -m pip list 2>/dev/null | grep -iE '^numpy |^pandas |^pytest '
