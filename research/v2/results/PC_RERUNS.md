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

## 2. B1b old xarray: no install on Python 3.12

Cause: 13 xarray instances (versions 0.12-0.14) failed at `pip install -e`: their versioneer build script uses `configparser.SafeConfigParser`, removed in Python 3.12. Python 3.11 environments were not used: Proviso needs Python 3.12 (sys.monitoring) to record.

Fix (b1b.py): when the install fails for that reason, the instance runs from the tree, which is first on PYTHONPATH, if the package imports from the tree and at least half of its test files collect; otherwise it is excluded with the reason "old build script not runnable on Python 3.12". xarray-5180 (network failure at install) re-run as is. The 14 error rows are kept, marked, in `b1b/superseded.jsonl`.

| instance | cause | re-run status | detail |
|---|---|---|---|
| pydata__xarray-3095 | old build script | ok (no install) | failing 1, F2P reproduced 1 |
| pydata__xarray-3151 | old build script | ok (no install) | failing 1, F2P reproduced 1 |
| pydata__xarray-3156 | old build script | pending | |
| pydata__xarray-3239 | old build script | pending | |
| pydata__xarray-3302 | old build script | pending | |
| pydata__xarray-3305 | old build script | pending | |
| pydata__xarray-3364 | old build script | pending | |
| pydata__xarray-3406 | old build script | pending | |
| pydata__xarray-3520 | old build script | pending | |
| pydata__xarray-3527 | old build script | pending | |
| pydata__xarray-3631 | old build script | pending | |
| pydata__xarray-3637 | old build script | pending | |
| pydata__xarray-3649 | old build script | pending | |
| pydata__xarray-5180 | network | pending | |

Old build script: 13 instances; 2 ok without install, 0 excluded, 0 error, 11 pending. Network: 1 (pending).
