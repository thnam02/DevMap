# V2.4 diagnosis: datasette's import-time values and sqlglot's slowest tests

Selection only, from saved B1 maps; no test was run and Proviso's src was not changed. Produced by `research/v2/v24_diagnosis.py` (per-pair data in `$PROVISO_WORK/datasette/v24/` and `$PROVISO_WORK/sqlglot/v24/`).

## Summary (interpretation of the data below)

**datasette, 5 pairs with more than 80 changed values.**
- **Not caused by the commit:** 84 of the changed values differ with no code change at all, and they are the same 84 in every pair.
  - **Selection noise.** One of them, `datasette.app:app_root`, a `pathlib.Path`, carries the tree's location in its cached path parts (`_tail_cached`). importstate unroots strings but not those parts, and the base snapshot is taken from a temporary export while the current one is taken from the working tree. So the value always differs, and it links about 2,170-2,190 tests, about 77% of the suite. In d0836ddedc (remove a backport), 2186 of the 2225 selected tests come from it alone; the real change links 27. In e1a4e03635, 1989 of 2217.
  - **Count noise.** The other 83 (82 attributes of 25 pydantic models: schema refs, validators and serializers built with per-process object ids; plus FAVICON_PATH, another Path) link no tests or 1 test. They do count toward the changed-value limit that switches to the full suite.
- **Caused by the commit:** the real changes reduce to a few root causes, each fanning out to many values:
  1. a slot added to a class whose instances are module constants (05ca128c02: `Attribute` gains `values`, `SpanName` gains `prefix`). One class edit changes 86 registry constants, each linking about 2,100 tests;
  2. edited description strings stored inside such constants (287e8ba3b2: 66 values from about 25 text edits in one commit);
  3. docstring and comment text copied into values (8e17729ff3, a comments-only commit): pytest's fixture definitions carry `__doc__`, and an OpenTelemetry instrument carries its description. These link every test through autouse telemetry fixtures, so the whole suite was selected for an edit that changes no behaviour;
  4. one changed lambda shared by 24 dataclasses (e1a4e03635: `default_factory=lambda: datetime.now(UTC)`);
  5. a changed import binding plus a removed module (d0836ddedc: `copytree`, 27 tests).

**sqlglot, test_execute_tpcds** (38% of test time).
- **Why ValueRTS selects it:** ValueRTS selects it in 50 of 52 pairs; testmon in 26-27. In every pair where ValueRTS selects it and testmon does not, ValueRTS's reason is the always rule: the test runs its queries in a process pool, and the recorder cannot see worker code.
- **What testmon's data shows:** testmon never recorded the test running a changed line. It records only the parent process, which just parses the queries.
- **Only 2 of the 25 pairs** link the test to the change through the map itself:
  - a6698b765b: the edited function `build_formatted_time`, whose nested closure holds the edit. testmon shows the closure body was not run in the parent process;
  - 5fc93a9eab: changed function-registry tables, when a new function class was added.

## 1. datasette: import-time values reported as changed

Pairs: 5 of the 49 first-run pairs (maps of the superseded run) whose scenario S reported more than 80 changed values. Per pair, Proviso's selection was re-run on a tree at the parent with the commit's source changes, and the changed values taken from its reason (`import_state_changed`).

**No-change baseline.** The same parent was also checked out at a second path and snapshotted, then compared with Proviso's base snapshot of the parent exactly as selection compares the changed tree. A value that differs there differs without any code change.

| Pair | Commit | Changed values | Also differ with no change | Real | Real causes (greedy cover) | Tests linked by no-change values | ... by them only | Tests linked by real values | Proviso selected / universe |
|---|---|---|---|---|---|---|---|---|---|
| 05ca128c02 | Add a plugin telemetry kit: public registry API, linked_root | 176 | 84 | 92 | 5 | 2168 | 100 | 2135 | 2246 / 2796 |
| 287e8ba3b2 | Simplified telemetry descriptions in telemetry_registry.py | 150 | 84 | 66 | 25 | 2169 | 100 | 2157 | 2269 / 2824 |
| 8e17729ff3 | Simplify code comments added since 1.0a40 (#2957) | 91 | 84 | 7 | 6 | 2178 | 0 | 2841 | 2841 / 2836 |
| d0836ddedc | Remove shutil.copytree backport | 86 | 84 | 2 | 2 | 2186 | 2186 | 27 | 2225 / 2844 |
| e1a4e03635 | Require Python 3.11, remove SQLite authorizer workaround | 112 | 84 | 28 | 2 | 2186 | 1989 | 216 | 2217 / 2844 |

The no-change values are the same 84 in every pair (identical sets): 2 module value, 82 class attribute. Grouped by the leaf that differs:

| Values | What differs (both versions walked with importstate's fingerprint rules) | Tests linked |
|---|---|---|
| 25 | object ids inside <the value> ['ref'] | 0 (max) |
| 25 | <the value> : pydantic_core._pydantic_core.SchemaSerializer:SchemaSerializ -> pydantic_core._pydantic_core.SchemaSerializer:SchemaSerializ | 0 (max) |
| 25 | <the value> : pydantic_core._pydantic_core.SchemaValidator:SchemaValidator -> pydantic_core._pydantic_core.SchemaValidator:SchemaValidator | 0 (max) |
| 7 | object ids inside pydantic._internal._decorators.Decorator slot:cls_ref | 0 (max) |
| 1 | tree location inside pathlib.PosixPath slot:_tail_cached[#] | 2168 (max) |
| 1 | no leaf difference found by the walker: datasette.app:FAVICON_PATH | |

No-change values linking the most tests: `datasette.app:app_root` (module value, 2168 tests, fingerprint 1d11cdcaff253968~9ffec6c42fbda4e9 -> 825bba666088300b~29ab39e26c60a8bf); `datasette.app:FAVICON_PATH` (module value, 1 tests, fingerprint 85f15d16d9324d06~8b69224682e28af8 -> 85f15d16d9324d06~167bd11af7be790f); `datasette.views.table_create_alter:AddColumnArgs.__pydantic_core_schema__` (class attribute, 0 tests, fingerprint 1e22b6150a8788c1~38662d0cdc5da752 -> 18da072a1b6bd61c~c2ea3122ab416bba).

### Per-pair real causes

**05ca128c02** Add a plugin telemetry kit: public registry API, linked_root_span_kwargs, test helpers, do - changed functions 4, module-level edits in datasette/database.py, datasette/telemetry.py, datasette/telemetry_registry.py; 92 real values, 5 causes:

- 80 value(s): datasette.telemetry_registry.Attribute: added slot:values (up to 2122 tests per value)
  - diff: `+    __slots__ = ("description", "optional", "values")`
  - diff: `+    def __new__(cls, name, description, optional=False, values=None):`
- 6 value(s): datasette.telemetry_registry.SpanName: added slot:prefix (up to 2118 tests per value)
  - diff: `+    __slots__ = ("attributes", "description", "dynamic", "kind", "prefix")`
  - diff: `+        prefix=False,`
- 2 value(s): <the value>: removed  (up to 1803 tests per value)
  - diff: `+        # an open value set. Declaring one does two things: the conformance`
  - diff: `+        # helpers assert every emitted value is a member, and it marks the`
- 2 value(s): <the value>: added [#] (up to 0 tests per value)
  - diff: `+        # an open value set. Declaring one does two things: the conformance`
  - diff: `+        # helpers assert every emitted value is a member, and it marks the`
- 2 value(s): <the value>: added  (up to 0 tests per value)
  - diff: `+        # an open value set. Declaring one does two things: the conformance`
  - diff: `+        # helpers assert every emitted value is a member, and it marks the`
- real values linking the most tests: `datasette.telemetry_registry:DB_NAMESPACE` (module value, 2122); `datasette.telemetry_registry:DB_QUERY` (module value, 2118); `datasette.telemetry_registry:CALLBACK` (module value, 2113); `datasette.telemetry_registry:DB_OPERATION_NAME` (module value, 2113)

**287e8ba3b2** Simplified telemetry descriptions in telemetry_registry.py - changed functions 0, module-level edits in datasette/telemetry_registry.py; 66 real values, 25 causes:

- 9 value(s): datasette.telemetry_registry.Attribute slot:description: "Set when the request failed: the exception class name if on -> 'The exception class name for a failed  (up to 2073 tests per value)
  - diff: `-    "The HTTP method, clamped to the nine methods RFC 9110 and RFC 5789 "`
  - diff: `+    "The HTTP request method. Methods outside the nine defined by RFC 9110 "`
- 4 value(s): datasette.telemetry_registry.Attribute slot:description: 'The qualified name of the Python callable passed to ``execu -> 'The qualified name of the Python calla (up to 2129 tests per value)
  - diff: `-    "Omitted when no route matched - a 404 - which is also when the span name "`
  - diff: `-    "Set when the request failed: the exception class name if one escaped the "`
- 3 value(s): datasette.telemetry_registry.MetricName slot:description: 'Open SQLite connections currently tracked for closing.' -> 'Open SQLite connections managed by Datase (up to 2044 tests per value)
  - diff: `-    "pattern Datasette routes with - for example "`
  - diff: `-    "recorded, on this or any other span: Datasette puts user-supplied SQL in "`
- 3 value(s): datasette.telemetry_registry.MetricName slot:description: 'Queries cancelled for exceeding :ref:`setting_sql_time_limi -> 'Queries cancelled for exceeding :ref: (up to 2044 tests per value)
  - diff: `-    "True if the query was cancelled for exceeding the time limit. The span "`
  - diff: `-    "Queries cancelled for exceeding :ref:`setting_sql_time_limit_ms`. Worth "`
- 3 value(s): datasette.telemetry_registry.MetricName slot:description: 'Read queries submitted to the pool and not yet complete. Su -> 'Read queries submitted to the pool an (up to 2044 tests per value)
  - diff: `-    "reads, which are the queries that time limit applies to.",`
  - diff: `-    "triggers for each database touched for the first time), saved queries, "`
- 3 value(s): datasette.telemetry_registry.MetricName slot:description: 'Maximum concurrent read queries - the :ref:`setting_num_sql -> 'Maximum concurrent read queries, conf (up to 2044 tests per value)
  - diff: `-    "The status of the response, read from the ASGI ``http.response.start`` "`
  - diff: `-    "reads, which are the queries that time limit applies to.",`
- real values linking the most tests: `datasette.database:DB_QUERY` (module value, 2129); `datasette.telemetry_registry:DB_QUERY` (module value, 2129); `datasette.database:CALLBACK` (module value, 2122); `datasette.database:DB_OPERATION_NAME` (module value, 2122)

**8e17729ff3** Simplify code comments added since 1.0a40 (#2957) - changed functions 0, module-level edits in datasette/app.py, datasette/database.py, datasette/telemetry.py, datasette/telemetry_registry.py, datasette/telemetry_testing.py; 7 real values, 6 causes:

- 2 value(s): opentelemetry.metrics._internal.instrument._ProxyCounter _description: 'Queries cancelled for exceeding sql_time_limit_ms. Not deri -> 'Queries cancelled for ex (up to 2841 tests per value)
  - diff: `+        # Stop reporting metrics before closing databases`
  - diff: `-        # sql_time_limit_ms is saying "this may not finish, and that is an`
- 1 value(s): _pytest.fixtures.FixtureFunctionDefinition __doc__: '\n    Session-scoped, autouse: install the metric reader on -> 'Install the metric reader once per test ses (up to 2841 tests per value)
  - diff: `-# (_DatasetteClientContext) and reader (in_client()) both live here.`
  - diff: `+        # Last, so metric callbacks never see a partially initialized instance`
- 1 value(s): _pytest.fixtures.FixtureFunctionDefinition __doc__: '\n    Function-scoped metrics collector. Drains delta state -> 'A `MetricsCollector`, drained before the te (up to 2841 tests per value)
  - diff: `-        # `datasette serve` calls invoke_startup() before uvicorn starts, so`
  - diff: `-        # Stop reporting gauges before tearing anything down, so a collection`
- 1 value(s): _pytest.fixtures.FixtureFunctionDefinition __doc__: "\n    Session-scoped, autouse: install the span exporter ex -> 'Install the span exporter once per test ses (up to 2841 tests per value)
  - diff: `-# _in_datasette_client itself lives in telemetry.py so the request span`
  - diff: `-        # `datasette serve` calls invoke_startup() before uvicorn starts, so`
- 1 value(s): _pytest.fixtures.FixtureFunctionDefinition __doc__: "\n    Autouse, function-scoped: drain the span exporter and -> 'Clear recorded spans and drain collected me (up to 2841 tests per value)
  - diff: `-# _in_datasette_client itself lives in telemetry.py so the request span`
  - diff: `-        # on the CLI path every span its children create - the register_*`
- 1 value(s): _pytest.fixtures.FixtureFunctionDefinition __doc__: '\n    Function-scoped access to the finished-spans exporter -> '\n    The in-memory span exporter, cleared  (up to 105 tests per value)
  - diff: `-# _in_datasette_client itself lives in telemetry.py so the request span`
  - diff: `-        # `datasette serve` calls invoke_startup() before uvicorn starts, so`
- real values linking the most tests: `datasette.telemetry:meter` (module value, 2841); `datasette.telemetry_testing:otel_meter_provider` (module value, 2841); `datasette.telemetry_testing:otel_metrics` (module value, 2841); `datasette.telemetry_testing:otel_provider` (module value, 2841)

**d0836ddedc** Remove shutil.copytree backport - changed functions 2, module-level edits in datasette/utils/__init__.py, datasette/utils/shutil_backport.py; 2 real values, 2 causes:

- 1 value(s): <the value> : datasette.utils.shutil_backport.copytree -> shutil.copytree (up to 27 tests per value)
  - diff: `+from shutil import copytree`
  - diff: `-from .shutil_backport import copytree`
- 1 value(s): <the value>: removed  (up to 0 tests per value)
- real values linking the most tests: `datasette.utils:copytree` (import binding, 27); `datasette.utils:shutil_backport` (module value, 0)

**e1a4e03635** Require Python 3.11, remove SQLite authorizer workaround - changed functions 6, module-level edits in datasette/events.py, datasette/utils/sql_analysis.py; 28 real values, 2 causes:

- 24 value(s): code of datasette.events.Event.<lambda> (up to 1 tests per value)
  - diff: `-        init=False, default_factory=lambda: datetime.now(timezone.utc)`
  - diff: `+    created: datetime = field(init=False, default_factory=lambda: datetime.now(UTC))`
- 4 value(s): <the value>: removed  (up to 110 tests per value)
- real values linking the most tests: `datasette.events:timezone` (import binding, 110); `datasette.utils.sql_analysis:_allow_authorizer_action` (module value, 106); `datasette.utils.sql_analysis:_disable_authorizer` (module value, 106); `datasette.utils.sql_analysis:sys` (import binding, 106)

## 2. sqlglot: the 15 slowest tests

Ranking and shares from `results/b1/sqlglot/time_concentration.md` (each test's own duration in the plain run at the parent, summed over the 52 ok pairs). Per pair: B = selected by both ValueRTS and testmon, V = ValueRTS only, T = testmon only, . = neither; columns in rank order.

| # | Test | Share of test time |
|---|---|---|
| 1 | `tests/test_executor.py::TestExecutor::test_execute_tpcds` | 38.2% |
| 2 | `tests/test_parser.py::TestParser::test_max_nodes` | 17.0% |
| 3 | `tests/test_executor.py::TestExecutor::test_execute_tpch` | 6.1% |
| 4 | `tests/test_executor.py::TestExecutor::test_optimized_tpch` | 5.1% |
| 5 | `tests/test_optimizer.py::TestOptimizer::test_scope` | 2.9% |
| 6 | `tests/test_optimizer.py::TestOptimizer::test_annotate_funcs` | 2.6% |
| 7 | `tests/test_optimizer.py::TestOptimizer::test_canonicalize` | 2.5% |
| 8 | `tests/test_optimizer.py::TestOptimizer::test_qualify_columns` | 2.1% |
| 9 | `tests/test_optimizer.py::TestOptimizer::test_tpcds` | 2.0% |
| 10 | `tests/test_optimizer.py::TestOptimizer::test_simplify` | 1.0% |
| 11 | `tests/test_serde.py::TestSerde::test_recursion` | 0.9% |
| 12 | `tests/test_optimizer.py::TestOptimizer::test_merge_subqueries` | 0.9% |
| 13 | `tests/test_optimizer.py::TestOptimizer::test_deep_ast_type_annotation` | 0.9% |
| 14 | `tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake` | 0.7% |
| 15 | `tests/test_serde.py::TestSerde::test_serde` | 0.7% |

Tests 2, 4 and 8 (test_max_nodes, test_optimized_tpch, test_qualify_columns) fail at the parent in all 52 pairs in this environment, so they are outside every tool's universe (failing tests are excluded); together they are about 24% of the summed test time.

| Pair | S: 1..15 | F: 1..15 |
|---|---|---|
| 7f1cf60c88 | `B.B.TTB.TTTTTBB` | `B.B.TTB.TTTTTBB` |
| f2b81bfb2d | `V.V.VBB..B..BB.` | `V.V.VBB..B..BB.` |
| 022bb41fc5 | `B.V..TV..B.B.B.` | `B.V..TV..B.B.B.` |
| aa64321744 | `B.B.BTB.TTTTTTT` | `B.B.BTB.TTTTTTT` |
| b7e515399a | `V.V...V........` | `V.V.BBB.BB.BB..` |
| 6aeb6a0ab7 | `V.V..BB..V...B.` | `B.B..BB..V...B.` |
| 3096a591d6 | `V.V...V..B.....` | `V.V...V..B.....` |
| f8606fe8f9 | `V.V..BB......B.` | `V.V..BB......B.` |
| f5dd70bff7 | `B.V.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| e1e0d2e52f | `B.B.BBB.VBBBBBB` | `B.B.BBB.VBBBBBB` |
| 818483464b | `V.V..BV..V.B.B.` | `V.V..BV..V.B.B.` |
| af9915fa4c | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 48beaa64b8 | `V.V...V........` | `V.V...V........` |
| 30958d6152 | `V.V.B.B........` | `V.V.BBB.BB.BB..` |
| 6de29fdce7 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 5b7b413451 | `V.V.B.B........` | `V.V.B.B........` |
| d5d436bc32 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| e3ed74860f | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| fc8178edd3 | `V.V...V......BB` | `V.V...V......BB` |
| ee7567c86d | `B.B.BBB..B.TBBT` | `B.B.BBB..B.TBBT` |
| 971d004474 | `V.V.BBB..B..BB.` | `V.V.BBB..B..BB.` |
| 50d7ce4a98 | `V.V...V......B.` | `V.V...V......B.` |
| 51587ffdec | `V.V...V........` | `V.V...V........` |
| c7957e8c86 | `V.V...V........` | `V.V...V........` |
| 74d8bec7dd | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| a980f01713 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 47b94d424a | `B.B.BBB.TTTTTBB` | `B.B.BBB.TTTTTBB` |
| 7fb054f17f | `V.V..BV..B...B.` | `V.V..BV..B...B.` |
| f337c70ee4 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| a7fcf9e07f | `V.V..BB......B.` | `V.V..BB......B.` |
| 5e6887adc8 | `V.V..BB......B.` | `V.V..BB......B.` |
| fc4964bbe8 | `B.B.TTB.TTTTTBB` | `B.B.TTB.TTTTTBB` |
| 8a713b6e49 | `...............` | `...............` |
| a6698b765b | `V.V.VBV..V.V.B.` | `V.V.VBV..V.V.B.` |
| 0ceaf1319e | `V.V..BV..B...B.` | `V.V..BV..B...B.` |
| bffcdefc16 | `B.B.BBB.VBBBBBB` | `B.B.BBB.VBBBBBB` |
| b65592b458 | `B.B.BBB.TBBBBBB` | `B.B.BBB.TBBBBBB` |
| b12b50fc06 | `V.V.B.B..T...T.` | `V.V.B.B..T...T.` |
| 5fc93a9eab | `V.V.BBB.VBVVVBV` | `V.V.BBB.VBVVVBV` |
| 1d2a99b9cc | `B.B.TTB.TTTTTBB` | `B.B.TTB.TTTTTBB` |
| 268ad021b8 | `B.B.TTB.TTTTTTB` | `B.B.TTB.TTTTTBB` |
| 5fe5606b90 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 13463de608 | `V.V..BV..B...B.` | `V.V..BV..B...B.` |
| 06fdfb4d20 | `T.T.TTT.TTTTTTT` | `T.T.TTT.TTTTTTT` |
| 5cc5ef046e | `V.V...V......B.` | `V.V...V......B.` |
| db3931c8ba | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| fdc0339b21 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 49d6ed4366 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| 15a77f1d89 | `B.B.BBB.BBBBBBB` | `B.B.BBB.BBBBBBB` |
| c7778cf56d | `V.V.BBV.VV.V..B` | `V.V.BBV.VV.V..B` |
| 5d997d94d8 | `B.B.BBB.BBTBTBB` | `B.B.BBB.BBTBTBB` |
| cb5d8da1ba | `V.V...V.VV.V...` | `V.V...V.VV.V.B.` |

### test_execute_tpcds selected by ValueRTS but not by testmon: 25 pairs (49 pair-scenarios)

- **Why ValueRTS selected it:** in all 49 cases the map marks the test *always* run (49/49). The test runs its queries in a `ProcessPoolExecutor` (`_mp_execute` in tests/test_executor.py), and the recorder marks any test that starts a process as always selected, because it cannot see the code the workers run. test_execute_tpch and test_canonicalize (test_optimizer's spawn pool) are the other always-run tests in the map.
- **Beyond the always rule:** in 2 case(s) the test also reaches a changed function in the parent process, and in 2 through changed import-time values. In the other 45 cases nothing in the test's own record or its fixtures reaches the change.

  - a6698b765b S (fix: drop wrong Dialect cast in build_formatted_time [CLAUDE): sqlglot/dialects/dialect.py:1640 build_formatted_time via own call
  - a6698b765b F (fix: drop wrong Dialect cast in build_formatted_time [CLAUDE): sqlglot/dialects/dialect.py:1640 build_formatted_time via own call
  - 5fc93a9eab S (fix(snowflake): support for SPLIT_TO_TABLE (#8488)): sqlglot.expressions:ALL_FUNCTIONS (module value); sqlglot.expressions:EXPR_CLASSES (module value); sqlglot.expressions:FUNCTION_BY_NAME (module value); sqlglot.parser:Parser.FUNCTIONS (class attribute)
  - 5fc93a9eab F (fix(snowflake): support for SPLIT_TO_TABLE (#8488)): sqlglot.expressions:ALL_FUNCTIONS (module value); sqlglot.expressions:EXPR_CLASSES (module value); sqlglot.expressions:FUNCTION_BY_NAME (module value); sqlglot.parser:Parser.FUNCTIONS (class attribute)

- **testmon's data about the changed lines.** For each changed source file in these cases, testmon's stored fingerprint for the test (parent process only) was checked against testmon's blocks of the old file that contain a changed line:
  - file not in the test's testmon record: 68 file-cases;
  - file recorded, but no block holding a changed line among the blocks the test ran: 18 (testmon's fingerprint for the file still matches the new code);
  - a block holding a changed line was run by the test: 0.
  - So by testmon's data the test never executed the changed lines in the parent process. Its parent side only parses the queries; execution happens in the workers, which testmon (coverage without subprocess tracking) does not record either. Where the workers run changed code, testmon's skip is unsafe; ValueRTS's always rule is safe but costs 27 s (38% of the suite's test time) on each of these pairs.
