# Root causes of Proviso v2.3's 10 missed changes (main benchmark, 650 changes)

Method: the planted bug was reapplied at the base commit, or the real commit read at its parent. A sys.monitoring tracer
(research/v2/trace_changed.py and its plugin; scratchpad wa/trace_at.py) checked whether each missed test runs the
edited function at the base:
- run alone;
- run within its class or file, as Proviso records it (one process per test file).

The import-time snapshot was taken with dc_engine.importstate. "Traditional" = PROVISO_MODE=traditional (every test
that executes changed code; any import-time change selects the whole suite), read from
results/<repo>/ablate-traditional.w*.jsonl.

Datasette's dependencies cannot be installed here (pydantic-core is compiled, PyPI is blocked). Its 3 cases are
inferred from the code at the base commit, not reproduced.

| # | Change | Missed / failing | Cause | Category | Evidence | Traditional catches? |
|---|---|---|---|---|---|---|
| 1 | sympy class:mul.py:31 (`NC_Marker.is_Mul` False→True) | 1/1 (test_exponential::test_as_numer_denom) | The snapshot sees the change (`sympy.core.mul:NC_Marker.is_Mul`). But class-attribute readers count only in tests that "use" the class, and the recorder adds a class to a test only when one of its methods runs on it. `NC_Marker` has no methods and is never instantiated: `Mul.flatten` appends the class itself as a marker and reads `o.is_Mul` on it. So no test uses it, and nothing is selected. | Pure-data class (no method ever runs) | Reproduced: snapshot diff here; impact.py readers_cls + covplugin `_classes_of` only on method calls | Yes (whole suite) |
| 2 | sympy class:mul.py:35 (`NC_Marker.is_commutative`) | 1/1 (same test) | Same as #1 | Pure-data class | Same | Yes |
| 3 | sympy function:mul.py:827 (`Mul.as_two_terms` flip) | 1/143 (test_hyper::test_eval_nseries) | Run alone, the test reaches `as_two_terms`. After the file's earlier tests it does not, because sympy's expression cache already holds the result. | Result cached inside a test file (sympy cache) | Reproduced: alone → hit; whole file (cache on) → not hit. No-cache whole-file run did not finish here. | No (recording-based too) |
| 4 | sqlalchemy compiler.py:1741 (`SQLCompiler._process_positional`) | 2/2007 (test_insert_exec::TableInsertTest::test_uppercase_direct_params; test_returning::InsertReturningTest::test_no_ipk_on_returning) | Run alone, the test compiles and reaches the function. Within its class, an earlier test (test_direct_params) has compiled the same statement, and the later test reuses SQLAlchemy's compiled-statement cache. | Result cached inside a test file (compiled cache) | Reproduced for test_uppercase_direct_params (alone → hit; class → not hit). test_no_ipk_on_returning not traced; same mechanism likely. | No |
| 5 | sqlalchemy elements.py:5098 (`NamedColumn._tq_key_label`, `@HasMemoized.memoized_attribute`) | 3/11 (test_resultset::KeyTargetingTest) | The value is memoized on the column objects of class-scoped tables, so only the first test that computes it runs the code. | Result cached inside a test file (memoized attribute) | Reproduced: test_keyed_accessor_single_labeled alone → hit; whole class → only one test hits | No |
| 6 | sqlalchemy compiler.py:4034 (`SQLCompiler.visit_bindparam`) | 9/40 (test_type_expressions::*RoundTripTest::test_targeting_*) | Same mechanism as #4: the statements were compiled by earlier tests of the class and come from the compiled cache. | Result cached inside a test file (compiled cache) | Reproduced: test_targeting_by_string alone → hit; class/file → only test_targeting_apply_labels hits | No |
| 7 | pygments real d24e272894 (Python lexer token table: Text→Whitespace) | 1/12 (test_irc_formatter::test_linecount_output) | The test module lexes at import (`newlinetokensource = list(PythonLexer().get_tokens(...))`, module level of the test file), during collection. The test itself only runs `IRCFormatter.format`. The snapshot reports `PythonLexer.tokens` changed, but its readers ran during collection, which is kept apart from tests. | Value computed in a test module at collection | Read from the test source and covplugin (`__global__` = code outside any test's set-up, call and tear-down) | Yes |
| 8 | datasette function:views/database.py:732 (`QueryView`: `stored_query_write` False→True) | 2/60 (test_api::test_plugins_json, test_cli::test_plugins_cli) | Neither test can reach `QueryView`: they read `/-/plugins.json` or run the `plugins` CLI command, which list the global plugin manager. The ground truth runs the whole suite in one process (pipeline.run_tests), so they likely fail on state left by earlier tests that do run `QueryView` (global `pm` / session-scoped `ds_client`). Which test pollutes is not pinned down. | Shared state between tests (test-order dependence) | Inferred (code reading). Not reproduced. | No |
| 9 | datasette function:utils/internal_db.py:161 (`_internal_schema_exists` returns True early) | 192/1892 (test_cors, test_permissions_cascade, test_auth_create_token, schema endpoints, ...) | The schema check runs once per Datasette instance, lazily: `TestClient._request` calls `ds.invoke_startup()` on the first request (utils/testing.py:151), which runs `_refresh_schemas` → `init_internal_db` → `_internal_schema_exists`. With session-scoped `app_client*` fixtures, only the first test of a file that requests through a client runs it. Later tests reuse the started instance, so they are not linked. Fixture set-up is credited to every user, but this code runs inside the first test's call, not in set-up. | Result cached in a shared fixture object (lazy start-up in the first test) | Inferred from code (testing.py:151, app.py invoke_startup / _refresh_schemas, internal_db_created flag). Not reproduced. | No |
| 10 | datasette real 1538832830 (adds `TableCountView` import to `datasette/app.py`) | 1/1 (test_docs::test_view_classes_are_documented) | The test reflects over the module (`[v for v in dir(app) if v.endswith("View")]`). The commit adds a new import binding to `datasette.app`. The snapshot treats names the base did not have as unread ("no existing code reads them"), but `dir(app)` reads every name. | Reflection over a module's names | Read: test_docs.py:92-96 and the app.py diff. Matches the known note in v2_changes.md. | Yes |

## Summary by category
- **Result cached inside a test file, or in a shared fixture object** (sympy cache, SQLAlchemy compiled cache,
  memoized attribute, Datasette lazy start-up): #3, #4, #5, #6, #9. That is 5 changes; #9 is inferred.
- **Import-time state reached in ways the linking does not see**: #1 and #2 (pure-data marker class with no methods),
  #7 (value read during collection by the test module), #10 (reflection over module names). That is 4 changes, all
  caught by the traditional variant.
- **Shared state between tests / test-order dependence**: #8 (inferred).

## Traditional variant vs Proviso
Traditional misses #3–#6, #8 and #9: 6 changes, matching the "traditional misses 6" ablation.

So the 4 changes Proviso misses and traditional catches are exactly the import-time cases #1, #2, #7 and #10. Each is
a specific gap in linking changed import-time values to tests: classes without methods, collection-time readers, and
reflection. None comes from the recording itself.

The other 6 are recording limits that any approach recording execution shares: caching within a test file, lazy
shared state, and test order.

## Open
- #8: the polluting test is not identified. Needs datasette's environment (PC): run test_api.py and test_cli.py
  together with and without the bug, then bisect the tests that run before them.
- #9: confirm by recording on the PC. Check that the 192 missed tests' first-request test is the only one credited
  with `_internal_schema_exists`.
- #4: test_no_ipk_on_returning not traced individually.
- #3: the no-cache whole-file run did not finish here. The cache explanation rests on alone-vs-file, plus the same
  mechanism in sympy-22402 (SWE-bench).
