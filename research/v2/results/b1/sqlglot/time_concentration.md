# sqlglot: test-time concentration and selection of the slowest tests

52 ok B1 pairs; 1326 tests; summed test time over the pairs 3861 s (each test's own duration in the plain run at the parent; not wall time). Share = the test's summed time / all tests' summed time. Selected: in how many pairs each tool's selection contained the test, scenario S (the commit's source changes, the parent's tests) and F (the whole commit; tests of edited test files count as selected for every tool, as in B1's scoring). Selections recomputed from each pair's saved data, without running tests (research/v2/b1_time_concentration.py).

| # | Test | median s per run | share of test time | cumulative | ValueRTS S | ValueRTS F | testmon S | testmon F | NameRTS S | NameRTS F |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `tests/test_executor.py::TestExecutor::test_execute_tpcds` | 26.98 | 38.2% | 38.2% | 50/52 | 50/52 | 26/52 | 27/52 | 33/52 | 33/52 |
| 2 | `tests/test_parser.py::TestParser::test_max_nodes` | 12.24 | 17.0% | 55.2% | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 |
| 3 | `tests/test_executor.py::TestExecutor::test_execute_tpch` | 4.61 | 6.1% | 61.2% | 50/52 | 50/52 | 24/52 | 26/52 | 33/52 | 33/52 |
| 4 | `tests/test_executor.py::TestExecutor::test_optimized_tpch` | 3.65 | 5.1% | 66.4% | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 |
| 5 | `tests/test_optimizer.py::TestOptimizer::test_scope` | 2.08 | 2.9% | 69.3% | 28/52 | 29/52 | 31/52 | 32/52 | 37/52 | 38/52 |
| 6 | `tests/test_optimizer.py::TestOptimizer::test_annotate_funcs` | 1.87 | 2.6% | 71.9% | 32/52 | 34/52 | 39/52 | 41/52 | 37/52 | 38/52 |
| 7 | `tests/test_optimizer.py::TestOptimizer::test_canonicalize` | 1.86 | 2.5% | 74.4% | 50/52 | 50/52 | 35/52 | 36/52 | 37/52 | 38/52 |
| 8 | `tests/test_optimizer.py::TestOptimizer::test_qualify_columns` | 1.43 | 2.1% | 76.5% | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 | 0/52 |
| 9 | `tests/test_optimizer.py::TestOptimizer::test_tpcds` | 1.42 | 2.0% | 78.5% | 19/52 | 21/52 | 22/52 | 24/52 | 37/52 | 38/52 |
| 10 | `tests/test_optimizer.py::TestOptimizer::test_simplify` | 0.60 | 1.0% | 79.4% | 31/52 | 33/52 | 34/52 | 36/52 | 37/52 | 38/52 |
| 11 | `tests/test_serde.py::TestSerde::test_recursion` | 0.53 | 0.9% | 80.4% | 17/52 | 17/52 | 24/52 | 24/52 | 27/52 | 27/52 |
| 12 | `tests/test_optimizer.py::TestOptimizer::test_merge_subqueries` | 0.62 | 0.9% | 81.2% | 23/52 | 25/52 | 27/52 | 29/52 | 37/52 | 38/52 |
| 13 | `tests/test_optimizer.py::TestOptimizer::test_deep_ast_type_annotation` | 0.60 | 0.9% | 82.1% | 20/52 | 22/52 | 27/52 | 29/52 | 37/52 | 38/52 |
| 14 | `tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake` | 0.51 | 0.7% | 82.8% | 38/52 | 40/52 | 42/52 | 43/52 | 36/52 | 38/52 |
| 15 | `tests/test_serde.py::TestSerde::test_serde` | 0.45 | 0.7% | 83.5% | 25/52 | 25/52 | 27/52 | 27/52 | 27/52 | 27/52 |

Denominator = pairs where the tool produced a selection in that scenario (a tool error on a pair, or a scenario a pair lacks, is left out).

Check, recomputed selection size = size recorded in the B1 row:

- ValueRTS S: 52/52 pairs equal
- ValueRTS F: 52/52 pairs equal
- testmon S: 52/52 pairs equal
- testmon F: 52/52 pairs equal
- NameRTS S: 52/52 pairs equal
- NameRTS F: 52/52 pairs equal
