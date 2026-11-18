# Why NameRTS's metric counts 30 of 400 pairs unsafe for Proviso v2.3 (19 Nov 2026)

NameRTS's metric: a pair is unsafe if Proviso skips a test file that NameRTS's ground truth lists ("test files that
execute a modified element", from NameRTS's own instrumented run). Rows: results/nrbench_v2.3/*.jsonl. Every skipped
file that runs here was rerun before and after its commit on the PC: 0 outcome changes (verify_*.jsonl, 21 pairs).
Causes established here with research/v2/trace_changed.py (sys.monitoring: does a test reach an edited function
during the test, only before tests, or not at all) and, for sympy, Proviso's own recorder (dc_engine.record).

| Cause | Pairs | Which |
|---|---|---|
| Skipped test files do not load in our environment (NameRTS counts them; not runnable) | 9 | dask 0194ef495f, ef66102072, 02a9e85487, ba63b71b6a; sympy 09f4667911, 363f2937d4, a96ca753d2, fe5acc309a, d8c57107df |
| Start-up-only contact: the edited function runs only while modules are imported or tests collected, and the import-time state is identical | 11 | loguru 8 (3a901de465, 46fd1b3c59, 620772ad02, 2f7007afcb, b2a5f7328b, 7b6f6e3741, bc2ec9abe9, 92952b912c; safety_breakdown.md); sympy 8fcd3ac174, 4e6ac53cf8 (`convert_to` reached only before tests, 0 of 16 tests during); xarray 7a654ad54a (`attempt_import`, 0 of 21 tests during; edit is behaviour-preserving) |
| The tests that would reach the edited code are skipped in this environment (optional dependency missing, also on the PC) | 4 | xarray 516ec07ef2, c43a3749b3 (iris; only `TestIrisConversion` reaches `decode_cf`); sphinx 342b30e1de, f578eedb10 (graphviz; 5 of 6 tests skipped before the build that runs the edited code; inferred) |
| Formatting-only edit (identical syntax trees) | 1 | pylint 21cf77eb4e |
| sympy's expression cache: the test reaches the edited function only with SYMPY_USE_CACHE=no | 2 | sympy d854b099d0 (`evalf_trig`: 0 tests with cache, 1 without), a9129a848f (`Mod.eval`) |
| Execution path varies with Python's hash seed: the test reaches the edited function in some runs, not others | 3 | sympy f08d10cd2d (`test_issue_17450` reaches `Mod.eval` with seeds 1,2,3,5, not 0,4); 13bb6ab638 (`test_is_nilpotent_number` reaches `RoundFunction.eval` with seed 4 only); 1bc499bbce (`test_gauss_opt` / `test_multivariate_expectation` reach `Derivative.__new__` depending on seed). Proviso's recorder here credited the function in one seed and not another; the PC's recording did not |
| **Total** | **30** | |

None is a defect in how Proviso links recorded execution to changes. Threat to state in the paper: one recorded run
can miss code reached only in other runs (sympy's hash-dependent paths, cache), and the same holds for NameRTS's own
ground truth, which is also one run. In all 21 runnable pairs the skipped files' outcomes did not change.
xarray side note: import_state_changed lists only lock objects in the two pairs that report any, independent of the
edit: likely snapshot noise (cost only).
