#!/bin/bash
# seaborn: NameRTS's numpy/pandas pins (pandas 3 / numpy 2.5 / matplotlib 3.11 fail 423 of 2,273 tests at these commits);
# matplotlib held at 3.10 (the series current when NameRTS's pairs were taken). TDAD deps already installed.
E=$HOME/proviso-work/v2/nrbench-venvs/seaborn/bin/python
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\n' > "$C"
"$E" -m pip install -q -c "$C" "numpy==2.3.5" "pandas==2.3.3" "matplotlib>=3.10,<3.11" 2>&1 | tail -2
"$E" -m pip list 2>/dev/null | grep -iE '^(numpy|pandas|matplotlib|scipy|pytest) '
rm -f "$C"
echo "soft nofile inside the capped service: $(ulimit -Sn)"
