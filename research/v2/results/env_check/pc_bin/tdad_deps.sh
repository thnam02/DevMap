#!/bin/bash
# TDAD's imports (networkx, neo4j driver, pydantic-settings) in the 3.13 project venvs, so B1's TDAD column runs there
# as it does in the shared venv (run_overnight.sh installs the same there); NameRTS's pins kept. sympy: TDAD skipped.
E=$HOME/proviso-work/v2/nrbench-venvs
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
for p in "$@"; do
  "$E/$p/bin/python" -m pip install -q -c "$C" networkx neo4j pydantic-settings 2>&1 | tail -2
  "$E/$p/bin/python" -c "import networkx, neo4j, pydantic_settings, pytest; print('$p: tdad deps ok; pytest', pytest.__version__)"
done
rm -f "$C"
