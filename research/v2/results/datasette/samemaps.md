# datasette: current Proviso (snapshot format 16) vs v1, both on the v1 dependency maps

| change set | changes | v1 misses | current misses | new misses (v1 caught) | v1 time share | current time share |
|---|---|---|---|---|---|---|
| planted | 95 | 2 | 30 | 28 | 71.6% | 18.0% |
|  new miss: class:datasette/views/special.py:209 | | | | 1 tests, e.g. tests/test_telemetry_registry.py::test_every_registered_metric_attribute_is_emitted | | |
|  new miss: module:datasette/views/table_create_alter.py:366 | | | | 12 tests, e.g. tests/test_allowed_many.py::test_database_page_precomputes_action_permissions | | |
|  new miss: module:datasette/utils/sql_analysis.py:89 | | | | 1 tests, e.g. tests/test_queries.py::test_execute_write_schema_operations_use_schema_permissions[create-index] | | |
|  new miss: module:datasette/utils/sql_analysis.py:81 | | | | 42 tests, e.g. tests/test_api_write.py::test_execute_write_form_parameter_called_sql | | |
|  new miss: module:datasette/views/table_create_alter.py:361 | | | | 12 tests, e.g. tests/test_allowed_many.py::test_database_page_precomputes_action_permissions | | |
|  new miss: module:datasette/views/table_create_alter.py:360 | | | | 2838 tests, e.g. tests/test_actions_sql.py::test_allowed_resources_global_allow | | |
|  new miss: class:datasette/views/base.py:79 | | | | 2 tests, e.g. tests/test_html.py::test_alternate_url_json[/-/plugins-http://localhost/-/plugins.json] | | |
|  new miss: class:datasette/resources.py:28 | | | | 63 tests, e.g. tests/test_fts_permissions.py::test_derived_permissions_allow_one_hop_but_deny_nested_sources[anonymous-fts4] | | |
|  new miss: module:datasette/utils/sql_analysis.py:90 | | | | 4 tests, e.g. tests/test_queries.py::test_execute_write_create_table_as_select_requires_view_table_on_source | | |
|  new miss: module:datasette/utils/sql_analysis.py:95 | | | | 1 tests, e.g. tests/test_queries.py::test_execute_write_schema_operations_use_schema_permissions[drop-index] | | |
|  new miss: module:datasette/views/execute_write.py:30 | | | | 2 tests, e.g. tests/test_queries.py::test_execute_write_create_table_template_is_filtered_by_permission | | |
|  new miss: module:datasette/app.py:396 | | | | 6 tests, e.g. tests/test_template_context.py::test_template_context_matches_documented_contract[database-/fixtures] | | |
|  new miss: module:datasette/views/table_create_alter.py:44 | | | | 2 tests, e.g. tests/test_table_html.py::test_database_create_table_data_includes_custom_column_types | | |
|  new miss: class:datasette/views/table_extras.py:1016 | | | | 2 tests, e.g. tests/test_table_api.py::test_html_only_extras_are_not_advertised | | |
|  new miss: module:datasette/utils/sql_analysis.py:84 | | | | 7 tests, e.g. tests/test_queries.py::test_execute_write_create_table_template_is_filtered_by_permission | | |
|  new miss: module:datasette/views/table_create_alter.py:370 | | | | 2838 tests, e.g. tests/test_actions_sql.py::test_allowed_resources_global_allow | | |
|  new miss: module:datasette/app.py:386 | | | | 6 tests, e.g. tests/test_template_context.py::test_template_context_matches_documented_contract[database-/fixtures] | | |
|  new miss: module:datasette/views/table_create_alter.py:357 | | | | 12 tests, e.g. tests/test_allowed_many.py::test_database_page_precomputes_action_permissions | | |
|  new miss: module:datasette/utils/sql_analysis.py:96 | | | | 1 tests, e.g. tests/test_queries.py::test_execute_write_schema_operations_use_schema_permissions[drop-table] | | |
|  new miss: module:datasette/utils/sql_analysis.py:83 | | | | 19 tests, e.g. tests/test_api_write.py::test_execute_write_form_parameter_called_sql | | |
|  new miss: class:datasette/views/table_extras.py:618 | | | | 3 tests, e.g. tests/test_error_shape.py::test_html_only_extra_via_json_is_400 | | |
|  new miss: class:datasette/views/special.py:727 | | | | 1 tests, e.g. tests/test_html.py::test_no_alternate_url_json[/-/allow-debug] | | |
|  new miss: class:datasette/views/table_extras.py:420 | | | | 2 tests, e.g. tests/test_table_api.py::test_html_only_extras_are_not_advertised | | |
|  new miss: module:datasette/views/table_create_alter.py:356 | | | | 12 tests, e.g. tests/test_allowed_many.py::test_database_page_precomputes_action_permissions | | |
|  new miss: module:datasette/app.py:398 | | | | 6 tests, e.g. tests/test_template_context.py::test_template_context_matches_documented_contract[database-/fixtures] | | |
|  new miss: module:datasette/utils/sqlite.py:32 | | | | 1 tests, e.g. tests/test_html.py::test_homepage | | |
|  new miss: module:datasette/views/table_create_alter.py:371 | | | | 12 tests, e.g. tests/test_allowed_many.py::test_database_page_precomputes_action_permissions | | |
|  new miss: module:datasette/views/execute_write.py:32 | | | | 3 tests, e.g. tests/test_queries.py::test_execute_write_create_table_template_is_filtered_by_permission | | |
| real | 24 | 2 | 3 | 1 | 69.7% | 53.1% |
|  new miss: 9bce2eec7c | | | | 1 tests, e.g. tests/test_telemetry_registry.py::test_registry_matches_the_expected_names | | |
