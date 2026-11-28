# PC re-runs (decided 2026-11-28)

## 1. datasette B1: all pairs re-run with httpx installed

Cause: the shared environment had `httpx2` (imported by datasette's newer commits) but not `httpx` (imported by its older commits' `tests/conftest.py`). At those commits the suite produced no outcomes, so b1.py skipped them as not building ("0 of 0 test files"): 110 of 150 candidates, leaving 40 ok pairs.

Fix: `httpx>=0.20,<1.0` (datasette's own pin; resolved httpx 0.29.0, httpcore 1.0.9) installed beside `httpx2` in the shared venv; the two are different modules. All datasette pairs re-run, so every row shares one environment hash. The old rows are kept, marked, in `b1/datasette/superseded.jsonl`; their per-pair work (maps, caches) in `$PROVISO_WORK/datasette/b1.superseded-20261128`.

Also fixed (b1.py): after each pair the worker empties its own TMPDIR subfolder (datasette's TMPDIR is on tmpfs, i.e. memory: the first run left 5.2 GB / 78,916 temporary SQLite files) and kills processes a test started and left running (one `datasette --memory -p 8041` server had run for an hour). Each row records `cleanup`.

| | rows | ok | skip | error | env hashes |
|---|---|---|---|---|---|
| first run (superseded) | 150 | 40 | 110 | 0 | 1 |
| re-run (in progress) | 0 | 0 | 0 | 0 | 0 () |

Re-run cleanup so far: 0 leftover processes killed, 0 MB of temporary files removed.

### Contamination check of the httpx install (2026-11-28 01:54:18 UTC)

- Environment that changed: only the shared venv (`~/proviso-work/venv`, Python 3.12.16), used by B1 sqlglot, pygments, datasette and sqlalchemy. The NameRTS projects (loguru, pvlib, pylint, seaborn, sphinx, xarray, dask, sympy) each use their own venv (`nrbench-venvs/<project>`); B1b runs tests in its SWE environments (`swe/envs/<repo>__<version>`). No other environment contains httpx.
- In flight at the install: B1 loguru 08e7ccc8c7, 46fd1b3c59, 3a901de465 (own venv); B1b mwaskom__seaborn-2979, pydata__xarray-7203, pydata__xarray-4695 (SWE envs). None used the shared venv. The datasette ablation job (shared venv) was stopped before the install. The shared-venv projects' last B1 pairs had finished at 01:15 (datasette), 22:24 and 19:50 the evening before (pygments, sqlglot).
- testmon on those 6 pairs: none selected the full suite (loguru S/F 745/745, 14/189, 29/29 of about 1,500; B1b 102 of 1,165, 90 of 11,753, 4 of 6,519). No rerun needed.
- Environment hash per finished B1 project: sqlglot 52 rows and pygments 52 rows, one hash each (the same pre-install shared venv); loguru (in progress) one hash so far. datasette's re-run will have one (new) hash.
- B1b: an environment's rows carry different hashes because each instance installs its own tree (editable), which changes the project's own version in the package list. The only other packages added to the SWE environments (coverage, execnet, pytest-testmon) were installed at 18:14 on 2026-11-27, before B1b's first start (18:15:24). Since then, the only change in each SWE environment is the project's own editable install.
- Rule from now on: no environment is changed while a job that uses it is running; such jobs are first stopped at a pair boundary.

## 2. B1b old xarray: no install on Python 3.12

Cause: 13 xarray instances (versions 0.12-0.14) failed at `pip install -e`: their versioneer build script uses `configparser.SafeConfigParser`, removed in Python 3.12. Python 3.11 environments were not used: Proviso needs Python 3.12 (sys.monitoring) to record.

Fix (b1b.py): when the install fails for that reason, the instance runs from the tree, which is first on PYTHONPATH, if the package imports from the tree, every FAIL_TO_PASS test is collected, and at least half of the test files pytest sees collect; otherwise it is excluded with the reason "old build script not runnable on Python 3.12" (and which condition failed). Each such row records the test files collected out of the total (files named test_*.py / *_test.py in the targets, plus any other file pytest reported). Rows of the no-install instances run before this check existed got the same fields from their saved outcomes (`collection_backfilled`). xarray-5180 (network failure at install) re-run as is. The 14 error rows are kept, marked, in `b1b/superseded.jsonl`.

| instance | cause | re-run status | test files collected | FAIL_TO_PASS collected | detail |
|---|---|---|---|---|---|
| pydata__xarray-3095 | old build script | ok (no install) | 30/40 (75%; 7 with errors) | 1/1 | failing 1, F2P reproduced 1 |
| pydata__xarray-3151 | old build script | ok (no install) | 30/40 (75%; 7 with errors) | 1/1 | failing 1, F2P reproduced 1 |
| pydata__xarray-3156 | old build script | ok (no install) | 30/40 (75%; 7 with errors) | 1/1 | failing 1, F2P reproduced 1 |
| pydata__xarray-3239 | old build script | ok (no install) | 30/41 (73%; 7 with errors) | 6/6 | failing 6, F2P reproduced 6 |
| pydata__xarray-3302 | old build script | pending | | | |
| pydata__xarray-3305 | old build script | ok (no install) | 30/41 (73%; 7 with errors) | 1/1 | failing 1, F2P reproduced 1 |
| pydata__xarray-3364 | old build script | ok (no install) | 30/41 (73%; 7 with errors) | 2/2 | failing 2, F2P reproduced 2 |
| pydata__xarray-3406 | old build script | pending | | | |
| pydata__xarray-3520 | old build script | pending | | | |
| pydata__xarray-3527 | old build script | pending | | | |
| pydata__xarray-3631 | old build script | ok (no install) | 30/43 (70%; 8 with errors) | 303/303 | failing 1, F2P reproduced 0 |
| pydata__xarray-3637 | old build script | pending | | | |
| pydata__xarray-3649 | old build script | ok (no install) | 30/43 (70%; 8 with errors) | 1/1 | failing 1, F2P reproduced 1 |
| pydata__xarray-5180 | network | pending | | | |

Old build script: 13 instances; 8 ok without install, 0 excluded, 0 error, 5 pending. Network: 1 (pending).
