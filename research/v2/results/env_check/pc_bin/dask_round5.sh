#!/bin/bash
# dask: boto3 brought botocore 1.44 but aiobotocore (s3fs) needs botocore <1.43.118: pin botocore into its range
E=$HOME/proviso-work/v2/nrbench-venvs/dask/bin/python
C=$(mktemp); printf 'numpy==2.3.5\npandas==2.3.3\npytest==8.4.1\nbotocore>=1.43.115,<1.43.118\n' > "$C"
"$E" -m pip install -q -c "$C" boto3 botocore 2>&1 | tail -2
"$E" -m pip check 2>&1 | grep -iE 'boto|aiobotocore' || echo "dask: no boto conflicts"
"$E" -m pip list 2>/dev/null | grep -iE '^(boto3|botocore|aiobotocore) '
rm -f "$C"
