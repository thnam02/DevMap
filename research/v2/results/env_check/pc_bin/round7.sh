#!/bin/bash
E=$HOME/proviso-work/v2/nrbench-venvs/dask/bin/python
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\nbotocore>=1.43.115,<1.43.118\n' > "$C"
"$E" -m pip install -q -c "$C" flask 2>&1 | tail -2
"$E" -c "import flask, numpy; print('dask: +flask; numpy', numpy.__version__)"
rm -f "$C"
