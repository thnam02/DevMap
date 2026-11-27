#!/bin/bash
# dask: TDAD's imports (as the other 3.13 venvs) + two more optional test deps its files skip without (boto3, graphviz)
E=$HOME/proviso-work/v2/nrbench-venvs
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
"$E/dask/bin/python" -m pip install -q -c "$C" networkx neo4j pydantic-settings boto3 graphviz 2>&1 | tail -2
"$E/dask/bin/python" -c "import networkx, neo4j, pydantic_settings, boto3, graphviz, numpy, pandas, pytest; print('dask: ok; numpy', numpy.__version__, 'pandas', pandas.__version__, 'pytest', pytest.__version__)"
rm -f "$C"
