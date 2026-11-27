# Environment on the PC (WSL2 Ubuntu 24.04, 2026-11-27)

Machine: Windows 11, i5-14400F (16 threads), 31.8 GB. WSL2 VM capped in `.wslconfig` (80%: 12 CPUs, 25.4 GB); every
job runs as a systemd user service with CPUQuota=1200%, MemoryMax=24G, Nice=10, LimitNOFILE=65536.

## Interpreters and venvs

- **History projects** (sqlglot, pygments, datasette, sqlalchemy): shared venv on uv's CPython **3.12.16** (bundles
  SQLite 3.54.1), packages as `run_all.sh` + `run_overnight.sh` + pytz, duckdb, wcag_contrast_ratio. The system
  python3.12 (SQLite 3.45.1) **segfaults** in sqlite3 during sqlalchemy's whole suite (test/orm/test_eager_relations.py,
  ~23%); uv's runs it through (27,163 passed).
- **NameRTS's projects** (loguru, pvlib, pylint, seaborn, sphinx, xarray, dask, sympy): one venv each on uv's CPython
  **3.13.18**, built as `run_nrbench.sh` does (install_deps copied verbatim), then pinned to **NameRTS's own evaluation
  environment** (NameRTS/environment_313.yml): pytest 8.4.1; numpy 2.3.5 and pandas 2.3.3 for pvlib, seaborn, xarray,
  dask; matplotlib 3.10 for seaborn. With the latest packages (pytest 9, numpy 2.5, pandas 3.1, matplotlib 3.11) the
  older commits fail: pvlib (testpaths must be a list; 'M' offset alias), seaborn (marks on fixtures; 423 failures),
  xarray and dask (numpy deprecations as errors). Extras: xarray from its ci/requirements/environment.yml
  (pytest-mypy-plugins<4, pytest-env, mypy 1.15, pandas-stubs, pyarrow, array_api_strict, pint); dask optional test deps
  (cachey, fastavro, requests, s3fs, scipy, scikit-image, sparse, sqlalchemy, xarray, ipycytoscape, boto3 with
  botocore in aiobotocore's range, graphviz, moto, flask); TDAD's imports (networkx, neo4j, pydantic-settings) in each
  except sympy (TDAD skipped there). NameRTS's pinned deps for 3.13 in a separate --target dir (NAMERTS_DEPS).
- Not installable here: cupy (GPU), pyspark (Java).

## Machine fixes (not code)

- **Slow fsync:** each SQLite commit waits ~7 ms on WSL2's virtual disk; datasette rebuilds a fixtures database per
  test (11 s each on disk, 0.03 s in RAM). datasette's runs use `TMPDIR=/dev/shm/proviso-tmp-datasette`
  (suite: 29:55 -> 2:28, same outcomes).
- **Open files:** datasette's single-process suite leaks file descriptors past the default soft limit of 1,024
  (INTERNALERROR: Too many open files): LimitNOFILE=65536.
- **DNS:** a failed lookup took 10-19 s through WSL's DNS proxy; resolv.conf now uses the LAN router (failed lookups:
  ~12 ms). Backups: /etc/resolv.conf.before-dnsfix, /etc/wsl.conf.before-dnsfix.

## Harness fixes (research/ only, one commit each)

record_speed_check (incr tree on a fresh machine); b1 (fetch NameRTS pair commits missing from the clone); env_check
(apply pylint's pinned astroid as b1 does); b1/env_check (only test targets that exist: pvlib moved its tests);
env_check --skips (plugins on the path: sympy's -p noslow); env_check --skips (record exit code and summary; under -q
too); pipeline.env (pass TMPDIR through).

## Result: 0 test files fail to collect in all 12 projects; every full suite runs to the end

See the per-project JSON files (tests, files skipped at collection, run exit code, pytest summary, run time).
Scripts used: `pc_bin/` (build, pins, env check runner).
