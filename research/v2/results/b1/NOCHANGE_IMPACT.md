# No-change values: impact on selection (sphinx, xarray, dask, sqlalchemy)

Frozen Proviso (v2.3.2; src/ unchanged), selection and snapshots only. Per project one map at one parent (sqlalchemy: a saved full map from the freeze-check diagnosis; the others recorded fresh). The no-op change is a comment line added at the top of the package's `__init__.py`: Proviso treats it as module-level code and compares the import-time snapshot, so everything it reports differs without a behavioural change. `research/v2/nochange_impact.py`.

## Effect: selection for a no-op import-time change

| Project | Map | Tests | Always selected | Selected | % tests | % test time | Tests linked by the no-change values | % of tests | % of test time |
|---|---|---|---|---|---|---|---|---|---|
| sphinx | recorded fresh at eaebbec4d1 | 2308 | 3 (2.67% time) | 720 | 31.2 | 90.44 | 718 | 31.11 | 90.43 |
| xarray | recorded fresh at 60bc816cd1 | 20196 | 21 (3.06% time) | 1962 | 9.71 | 19.86 | 1961 | 9.71 | 19.64 |
| dask | recorded fresh at 08d1856d3e | 16029 | 214 (14.43% time) | 16029 | 100.0 | 100.0 | 16029 | 100.0 | 100.0 |
| sqlalchemy | saved at 10f4d1e2d7 | 9355 | 27 (22.67% time) | 9355 | 100.0 | 100.0 | 9355 | 100.0 | 100.0 |

Always-selected tests run for any change; the rest of the selection comes from the no-change values.

## Per value

Unstable: marked by the base snapshot's 9 samples (3 export locations, heap shifts). Extra samples: 4 more snapshots of an export of the parent, 2 s apart and with other heap shifts (distinct fingerprints, and distinct when order is ignored). Class: (a) links few tests, harmless; (b) varies between processes and should have been caught as unstable; (c) reported on purpose.

| Project | Value | Kind | Tests linked | % test time | Unstable (9 samples) | Extra samples: distinct / ignoring order | Base vs tree equal ignoring order | Class | Why |
|---|---|---|---|---|---|---|---|---|---|
| sphinx | `sphinx.builders.gettext:timestamp` | module value | 718 | 90.43 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: the time of import (time.localtime() unless SOURCE_DATE_EPOCH is set) |
| sphinx | `sphinx.writers.texinfo:TEMPLATE` | module value | 708 | 90.17 | no | 1 / 1 | no | b | differs between the base snapshot and the working tree but not between the base samples: the samples are all exports of the commit (no .git), the working tree is a git checkout. Holds: embeds sphinx.__display_version__, which adds the git commit when imported from a git checkout ('8.3.0+/eaebbec4d') but not from the base snapshot's export ('8.3.0'); every base sample is an export, so none sees it |
| xarray | `xarray.backends.h5netcdf_:HDF5_LOCK` | module value | 1960 | 19.63 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.locks:HDF5_LOCK` | module value | 1960 | 19.63 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.netCDF4_:HDF5_LOCK` | module value | 1960 | 19.63 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.locks:NETCDFC_LOCK` | module value | 1949 | 19.07 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.netCDF4_:NETCDF4_PYTHON_LOCK` | module value | 1949 | 19.07 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.netCDF4_:NETCDFC_LOCK` | module value | 1949 | 19.07 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: a SerializableLock created at import with a random token (str(uuid.uuid4())) |
| xarray | `xarray.backends.locks:SerializableLock._locks` | class attribute | 28 | 1.21 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: registry of the module-level locks, keyed by their random tokens |
| dask | `dask.threaded:main_thread` | module value | 16029 | 100.0 | yes | 4 / 4 | no | b | the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) differ between processes, and unstable values are compared without order only. Holds: threading.current_thread() at import: a Thread object whose ident differs per process |
| dask | `dask.cli:cli` | module value | 248 | 1.38 | no | 1 / 1 | no | b | differs between the base snapshot and the working tree but not between the base samples: the samples are all exports of the commit (no .git), the working tree is a git checkout. Holds: click's --version option holds dask.__version__, derived from git by versioneer: '2025.3.0+21.g08d1856d3' in the working tree, '0+unknown' in the base snapshot's export; every base sample is an export |
| dask | `dask.dataframe.io.sql:_extra_deps` | module value | 28 | 0.54 | yes | 4 / 4 | no | a | links 28 tests (0.54% of test time): harmless |
| dask | `dask.dataframe.dask_expr.io.parquet:_gather_statistics` | module value | 17 | 0.08 | yes | 4 / 4 | no | a | links 17 tests (0.08% of test time): harmless |
| dask | `dask.array.core:ARRAY_TEMPLATE` | module value | 6 | 0.01 | no | 1 / 1 | no | a | links 6 tests (0.01% of test time): harmless |
| sqlalchemy | `sqlalchemy.event.registry:_collection_to_key` | module value | 9355 | 100.0 | yes | 4 / 4 | no | c | an id-keyed registry or marker that differs in every process; reported on purpose (see below) |
| sqlalchemy | `sqlalchemy.event.registry:_key_to_collection` | module value | 9355 | 100.0 | yes | 4 / 4 | no | c | an id-keyed registry or marker that differs in every process; reported on purpose (see below) |
| sqlalchemy | `sqlalchemy.orm.attributes:_NO_STATE_SYMBOLS` | module value | 41 | 7.3 | yes | 4 / 4 | no | c | an id-keyed registry or marker that differs in every process; reported on purpose (see below) |
| sqlalchemy | `sqlalchemy.orm.collections:InstrumentedList._sa_instrumented` | class attribute | 8 | 4.05 | yes | 4 / 4 | no | c | an id-keyed registry or marker that differs in every process; reported on purpose (see below) |
| sqlalchemy | `sqlalchemy.orm.collections:InstrumentedSet._sa_instrumented` | class attribute | 0 | 0.0 | yes | 4 / 4 | no | a | links 0 tests (0.0% of test time): harmless |
| sqlalchemy | `sqlalchemy.orm.mapped_collection:KeyFuncDict._sa_instrumented` | class attribute | 0 | 0.0 | yes | 4 / 4 | no | a | links 0 tests (0.0% of test time): harmless |

Counts per class: dask a: 3; dask b: 2; sphinx b: 2; sqlalchemy a: 2; sqlalchemy c: 4; xarray b: 7.

### Why a value marked unstable is still reported

importstate compares an unstable value by its order-free fingerprint (the part after `~`). That forgives values whose order follows memory addresses, but a value whose contents differ (a random token, a thread id, the time of import, an id-keyed registry) still differs and is reported. The column 'Base vs tree equal ignoring order' shows this per value.

### (c) Reported on purpose

v2.3's own unit test `test_value_differing_between_imports_still_counts_when_code_changes` (tests/test_importstate_noise.py): a value that differs on every import, such as a registry keyed by `id()` or the process id, cannot be compared; Proviso keeps reporting it rather than ignoring it, because ignoring such values hid real changes to SQLAlchemy registries. Sampling marks it unstable, and unstable values are compared without order, which forgives a different order but not different contents.

