# sqlalchemy freeze-check failure: diagnosis (PC, WSL2, 2026-11-27)

**Verdict: not caused by v2.3.1.** The old code (8e8f0bb), recorded again now on the same tree, differs from the
freeze check's first old recording as much as the new code does. sqlalchemy's full recording (test/base + test/sql,
9,760 tests) is nondeterministic in this environment; the freeze check's two old recordings happened to agree
(15 tests differ), which made the new recording look like the outlier.

Decision rule applied: the difference disappears in neither B (order) nor C (fast path), so proviso-v2.3.1 stays
tagged at 9e6e45f.

## Setup

Same tree for every recording: `$PROVISO_WORK/sqlalchemy/trees/incr` at the pinned commit 10f4d1e2d (clean apart from
`.dc-engine/record_times.json`), shared Python 3.12 venv, 8 recording workers, each job under the cap (systemd user
service; 50% for the freeze check, 80% for the runs below). Compared test by test as `record_speed_check.py` does
(own record united with its fixture records). Reference: the freeze check's `old1`; `old1` vs `old2` = 15 tests (the
"noise" the check allowed).

## Results (tests differing from old1; beyond the 15 noise tests in brackets)

| Recording | src | Switches | vs old1 |
|---|---|---|---|
| freeze check `new` | 9e6e45f | defaults (fresh tree: no times file, so collection order) | 9,732 (9,720) |
| again / fork off / pycache off / both off | 9e6e45f | PROVISO_RECORD_FORK / _PYCACHE | 9,731-9,751 |
| A0, A1 | 9e6e45f | times file present (longest first) | 9,733, 9,733 (9,719) |
| B0, B1 | 9e6e45f | times file removed (collection order) | 9,731, 9,751 |
| C0, C1 | scratch copy, fast path off | times present | 9,732, 9,731 |
| D0, D1 | scratch copy, fast path off | times removed | 9,731, 9,733 |
| E0 | scratch copy, fast path off | + FORK=0, PYCACHE=0, no times (every v2.3.1 change off) | 7,843 (7,832) |
| **O0, O1** | **8e8f0bb (old)** | - | **8,882, 9,734** |

Old against old, recorded now: O0 vs O1 = **9,756** tests differ. Every new-code map also differs from O0 by
9,756. Fixture records differing from old1: 26-107 per run, varying run to run in every variant.

The scratch copy (outside the repository, deleted afterwards) changes one line of `covplugin.py`:
`m = _meth.get(id(code))` -> `m = None`. Nothing under the repository's `src/` was changed.

## What differs

Almost every test gains or loses the same few functions through shared fixture records (session-level records are
unions over all test files): `exc.py` `_code_str` / `_message` / `__str__` / `DBAPIError.instance`,
`pool/base.py:1505`, `util/concurrency.py:is_exit_exception`; and `testing/exclusions.py:OrPredicate` in some tests.
That is an exception path in shared fixtures taken in some recordings and not others, whichever code records.
Recording a single test file 5x old / 5x new (record_pertest_check.py): 49 of the 50 listed tests identical in all 10,
1 noise (pertest/sqlalchemy.json): the variation needs the full suite.

## Consequence for B1

sqlalchemy's maps vary from recording to recording in shared fixture records. That costs selection size (extra
functions make more tests selected), and the `OrPredicate` class missing in some recordings could in principle hide a
test from selection when exclusions.py changes. B1 measures misses directly (confirmed failures vs selection), so it
will show if this matters; worth keeping in mind when reading sqlalchemy's rows.

Raw data: `pc_diag_abcd_sqlalchemy.json`, `pc_diag_control_sqlalchemy.json`; scripts `pc_diag_abcd.py`,
`pc_diag_control.py`.
