# Recording speed-ups (v2.3.1): same map, less time

Changes:
- `record.py`: one byte-code cache per recording (in a temporary directory outside the tree, deleted afterwards), and test files run longest first, using each file's time at the previous recording (`.dc-engine/record_times.json`).
- `forkrec.py`: a fork server. One interpreter imports pytest, then forks a child per test file that runs `pytest.main` as `python -m pytest` would. The recorder is imported in the child.
- `covplugin.py`: a fast path for package-method events, which adds each type's classes once per recording target.

None of these changes what is recorded. Switches to restore the old behaviour: `PROVISO_RECORD_FORK=0`, `PROVISO_RECORD_PYCACHE=0`.

## Measurements (cloud container, 2 CPUs, 2 workers, same commit as the incremental check's last step)

| | sqlglot (7f1cf60, 1,104 tests, 56 files) | pygments (a43b45d, 5,342 tests, 1,544 files) |
|---|---|---|
| Old code (8e8f0bb) | 164.4 s (repeats 165.5, 151.5) | 394.0 s |
| + byte-code cache, fast path (first run, no file times yet) | 132.2 s | 364.6 s |
| + longest file first | 111.4 s | 373.6 s |
| + fork server (all changes) | **92.0 s (−44%)** | **205.6 s (−48%)** |

## Same map

Comparisons are test by test (each test's own record united with its fixture records), plus `__global__`, `__fixtures__`, `__collected__` and key order.

- **sqlglot:** 0 tests differ in every new recording (byte-code + fast path; + scheduling; + fork server). Two old recordings also differ in 0. `record_speed_check.py`: pass (sqlglot.json).
- **pygments:** the only tests that differ are `tests/test_basic_api.py::test_random_input` (52, 85, 64 of them in the three new recordings). Two old recordings differ in 127 of these same random-input tests. Everything else is identical, including the global record, fixture records and collected files.
- **Unit tests:** `tests/test_record_speed.py` covers:
  - classes of every type a method runs on;
  - the lazy-import charge;
  - fork server + byte-code + scheduling against plain recording, with identical maps and key order and no `__pycache__` left in the tree;
  - timeouts under the fork server;
  - partial recordings leaving file times alone.

  The full suite passes: 323 tests.

## What can still differ: recorded test times

Test durations in the map get shorter, because there is no per-process recompilation and the method fast path is cheaper. Selection uses them only for the 90% shortcut (run the whole suite when the edited functions reach 90% of test time). That shortcut changes cost, never safety.

Re-computing the shortcut's share for all 50 commits of the sqlglot chain with old vs new times:
- **0 decisions flip;**
- shares near the threshold were 0.976–0.998 with either set of times.

## Not done

- **Leaf-method rule:** stop watching a method whose class has no subclasses. It is not provably identical, because a subclass created later inside a test (a lazy import, or `type()`) would be missed, so it was skipped.
- **sympy, sqlalchemy, datasette:** their dependencies are not installed here. Run `record_speed_check.py REPO --old-src <8e8f0bb checkout>/src --new-src src` on the PC.
