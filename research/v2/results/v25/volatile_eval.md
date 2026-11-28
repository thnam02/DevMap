# v2.5: run-varying import-time values, snapshot-level evaluation

Branch `v2.5-dev`. Mechanism on = default; off = `PROVISO_OFF=volatile` (the v2.3.2 comparison). Run in the cloud workspace on Python 3.13 with the four projects cloned at the parents the PC used in NOCHANGE_IMPACT.md. No test suites were run here: these numbers are about the import-time comparison only. dask.dataframe does not import here (pyarrow is missing), so its values are not covered.

## No-op change (a comment added to the package's `__init__.py`), 20 fresh comparisons each

| Project | Values compared | Trials reporting a change, off | Values reported, off | Trials reporting a change, on | Values reported, on | Base snapshot off (s) | on (s) |
|---|---|---|---|---|---|---|---|
| sqlalchemy | 28088 | 20 of 20 | 6 | 0 of 20 | 0 | 12.5 | 29.8 |
| xarray | 7539 | 20 of 20 | 7 | 0 of 20 | 0 | 7.3 | 16.7 |
| dask | 5307 | 20 of 20 | 3 | 0 of 20 | 0 | 15.7 | 37.7 |
| sphinx | 10940 | 20 of 20 | 2 | 0 of 20 | 0 | 8.8 | 21.4 |

## What is still compared in each run-varying value

Leaves of the value: compared exactly; compared by shape (kind, common start and end, length); by kind only; not compared. Random edits: 300 single edits to the value (change a leaf, drop or add an element) and how many the comparison reports.

| Project | Value | Exact | Shape | Kind | Not compared | Random edits reported |
|---|---|---|---|---|---|---|
| sqlalchemy | `sqlalchemy.event.registry:_collection_to_key` | 327 | 0 | 0 | 0 | 300 of 300 |
| sqlalchemy | `sqlalchemy.event.registry:_key_to_collection` | 332 | 0 | 0 | 0 | 300 of 300 |
| sqlalchemy | `sqlalchemy.orm.attributes:_NO_STATE_SYMBOLS` | 16 | 0 | 0 | 0 | 300 of 300 |
| sqlalchemy | `sqlalchemy.orm.collections:InstrumentedList._sa_instrumented` | 1 | 0 | 0 | 0 | 300 of 300 |
| sqlalchemy | `sqlalchemy.orm.collections:InstrumentedSet._sa_instrumented` | 1 | 0 | 0 | 0 | 300 of 300 |
| sqlalchemy | `sqlalchemy.orm.mapped_collection:KeyFuncDict._sa_instrumented` | 1 | 0 | 0 | 0 | 300 of 300 |
| xarray | `xarray.backends.h5netcdf_:HDF5_LOCK` | 3 | 1 | 0 | 0 | 263 of 300 |
| xarray | `xarray.backends.locks:HDF5_LOCK` | 3 | 1 | 0 | 0 | 258 of 300 |
| xarray | `xarray.backends.locks:NETCDFC_LOCK` | 3 | 1 | 0 | 0 | 263 of 300 |
| xarray | `xarray.backends.locks:SerializableLock._locks` | 8 | 4 | 0 | 0 | 261 of 300 |
| xarray | `xarray.backends.netCDF4_:HDF5_LOCK` | 3 | 1 | 0 | 0 | 263 of 300 |
| xarray | `xarray.backends.netCDF4_:NETCDF4_PYTHON_LOCK` | 7 | 2 | 0 | 0 | 269 of 300 |
| xarray | `xarray.backends.netCDF4_:NETCDFC_LOCK` | 3 | 1 | 0 | 0 | 267 of 300 |
| dask | `dask.array.core:ARRAY_TEMPLATE` | 366 | 0 | 1 | 0 | 300 of 300 |
| dask | `dask.cli:cli` | 573 | 0 | 1 | 0 | 300 of 300 |
| dask | `dask.threaded:main_thread` | 34 | 1 | 2 | 0 | 294 of 300 |
| sphinx | `sphinx.builders.gettext:ctime` | 0 | 1 | 0 | 0 | 126 of 300 |
| sphinx | `sphinx.builders.gettext:timestamp` | 1 | 0 | 8 | 0 | 176 of 300 |
| sphinx | `sphinx.writers.texinfo:TEMPLATE` | 0 | 1 | 0 | 0 | 295 of 300 |

## Seeded real changes (mechanism on)

| Project | Edit | Reported | By | Values reported |
|---|---|---|---|---|
| sqlalchemy | registry: listener removed (Index after_parent_attach) | yes | snapshot | `_key_to_collection`, `SchemaEventTarget.dispatch`, `DDLEvents.dispatch` |
| sqlalchemy | registry: listener moved to another event name | yes | snapshot | `_collection_to_key`, `_key_to_collection`, `SchemaEventTarget.dispatch`, `DDLEvents.dispatch` |
| sqlalchemy | registry: listener moved to another class | yes | snapshot | `_key_to_collection`, `SchemaEventTarget.dispatch`, `DDLEvents.dispatch` |
| sqlalchemy | id set: another symbol of the same type | yes | snapshot | `_NO_STATE_SYMBOLS` |
| sqlalchemy | id set: one symbol dropped | yes | snapshot | `_NO_STATE_SYMBOLS` |
| sqlalchemy | ordinary table value | yes | snapshot | `_prefix_dict` |
| sqlalchemy | ordinary value in another module | yes | snapshot | `DEFAULT_NAMING_CONVENTION` |
| xarray | lock given a fixed token | yes | snapshot | `HDF5_LOCK`, `HDF5_LOCK`, `SerializableLock._locks`, `HDF5_LOCK` |
| xarray | token made another way, other shape (function edit) | yes | snapshot | `HDF5_LOCK`, `HDF5_LOCK`, `NETCDFC_LOCK`, `SerializableLock._locks` |
| xarray | token made another way, same shape (function edit; expected not visible in the snapshot) | yes | guard | `HDF5_LOCK`, `NETCDFC_LOCK`, `SerializableLock._locks` |
| xarray | lock type changed (function edit) | yes | snapshot | `HDF5_LOCK`, `HDF5_LOCK`, `NETCDFC_LOCK`, `HDF5_LOCK` |
| xarray | one module lock removed from use | yes | snapshot | `SerializableLock._locks`, `NETCDF4_PYTHON_LOCK` |
| dask | main_thread is another thread object | yes | snapshot | `main_thread` |
| dask | ordinary value next to it | yes | snapshot | `default_pool` |
| dask | cli option changed | yes | snapshot | `cli` |
| sphinx | template text edited | yes | snapshot | `TEMPLATE` |
| sphinx | timestamp made another way, same shape (statement edit: guard) | yes | guard | `timestamp` |
| sphinx | timestamp replaced by a fixed value | yes | snapshot | `ctime` |

## Recent real commits (parent as base, commit as working tree)

| Project | Commits | Reported only with the mechanism on | Median values reported, off | on | Commits with nothing reported, off | on | Removed values that are not run-varying | Removed values in an edited module (guard puts back) |
|---|---|---|---|---|---|---|---|---|
| sqlalchemy | 20 | 0 | 6 | 0 | 0 | 14 | 0 | 0 (0) |
| xarray | 20 | 0 | 7 | 0 | 0 | 13 | 0 | 4 (0) |
| dask | 20 | 0 | 3 | 0 | 0 | 11 | 0 | 1 (0) |
| sphinx | 20 | 0 | 3 | 0 | 0 | 11 | 4 | 0 (0) |

Notes on the history table:
- "Removed values that are not run-varying" (sphinx, 4): all four are `sphinx.builders.gettext:ctime`, the time of import to the minute. With the mechanism off the comparison crossed a minute boundary and reported it; with it on, base and commit were snapshotted in the same minute, so the values were simply equal. Not a dropped change.
- "Removed values in an edited module": xarray 245be4b8e1 (a lint refactor of `locks.py`, the lock statements untouched) and dask cebcc04c04 (`array/core.py` reworked, `ARRAY_TEMPLATE` untouched). Read by hand: neither commit changes those values.

## What this does not show
- No tests were run. Whether a dropped value ever hides a failing test needs the PC: re-score recorded pairs (sqlglot, pygments, loguru, datasette) and run the four held projects with the mechanism on.
- The share of tests and test time saved needs the maps on the PC (rerun `nochange_impact.py` on this branch).
- Limits by design: a change that only alters how a run-varying part is drawn, keeping its kind and shape (`uuid4()` to `uuid1()` inside a helper), is invisible to the comparison; the edited-statement guard covers it when the binding statement or a definition it uses is edited in the same module. Values made with `datetime.now()` to the minute or coarser are not sampled with a moved clock (only the `time` module is), so they keep counting as changed.
- Base snapshot time rises about 2.4x on projects that have run-varying values (a second round of samples); projects without them pay only two extra samples.
