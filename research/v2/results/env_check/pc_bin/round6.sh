#!/bin/bash
# xarray: array_api_strict, pint (the earlier one-line install never ran); dask: moto. NameRTS pins kept.
E=$HOME/proviso-work/v2/nrbench-venvs
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\nbotocore>=1.43.115,<1.43.118\n' > "$C"
"$E/xarray/bin/python" -m pip install -q -c "$C" array_api_strict pint 2>&1 | tail -2
"$E/dask/bin/python" -m pip install -q -c "$C" moto 2>&1 | tail -2
"$E/xarray/bin/python" -c "import array_api_strict, pint, numpy; print('xarray: +array_api_strict +pint; numpy', numpy.__version__)"
"$E/dask/bin/python" -c "import moto, numpy, botocore; print('dask: +moto; numpy', numpy.__version__, 'botocore', botocore.__version__)"
rm -f "$C"
