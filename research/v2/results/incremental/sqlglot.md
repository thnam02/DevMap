# Incremental recording check: sqlglot

- Steps: 20; full re-recordings (selection ran the whole suite, or no clean map): 3
- First full recording: 153.72 s; fresh recordings at check points: median 160.18 s
- Incremental update: median 22.69 s, max 166.97 s; test files re-recorded: median 2; selection: median 3.32 s; base snapshot adopted at 13 of 20 steps
- Map comparisons: 20; tests whose fresh record has something the incremental one lacks: 50; tests only in the fresh map: 0; global record missing: 0
- Noise baseline (two fresh recordings of one commit): 0 tests differ, 0 with something only one of them records
- Selection at the next commit: 19 checks; tests selected only with the fresh map: 0

## v2.3 (record from scratch at every commit) vs v2.4 (incremental), same commits

| | v2.3 | v2.4 |
|---|---|---|
| Per-commit cost: recording + selection, median | 174.6 s | 25.4 s |
| Total over 19 commits | 3249 s | 1023 s |
| Selection alone, median | 17.5 s | 2.6 s |
| Commits with identical selected tests | 19 of 19 | |
| Tests only v2.3 selects (lost by v2.4) | 0 | |
| Tests only v2.4 selects (extra cost) | 0 | |
  - step 15 (6aeb6a0ab7): [{"test": "tests/dialects/test_clickhouse.py::TestClickhouse::test_clickhouse", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/dialect.py", 1286], ["sqlglot/dialects/dialect.py", 1712], ["sqlglot/dialects/dialect.py", 1745]]}}, {"test": "tests/dialects/test_databricks.py::TestDatabricks::test_databricks", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/databricks.py", 1], ["sqlglot/dialects/databricks.py", 15], ["sqlglot/dialects/databricks.py", 30]], "classes": ["sqlglot/dialects/tsql.py:TSQL.Tokenizer"]}}]
  - step 16 (b7e515399a): [{"test": "tests/dialects/test_clickhouse.py::TestClickhouse::test_clickhouse", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/dialect.py", 1286], ["sqlglot/dialects/dialect.py", 1712], ["sqlglot/dialects/dialect.py", 1745]]}}, {"test": "tests/dialects/test_databricks.py::TestDatabricks::test_databricks", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/databricks.py", 1], ["sqlglot/dialects/databricks.py", 15], ["sqlglot/dialects/databricks.py", 30]], "classes": ["sqlglot/dialects/tsql.py:TSQL.Tokenizer"]}}]
  - step 17 (aa64321744): [{"test": "tests/dialects/test_athena.py::TestAthena::test_qualify", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/athena.py", 1], ["sqlglot/dialects/athena.py", 13], ["sqlglot/dialects/athena.py", 53]], "classes": ["sqlglot/dialects/dialect.py:JSONPathTokenizer", "sqlglot/dialects/dialect.py:Tokenizer", "sqlglot/dialects/mysql.py:MySQL.Tokenizer"]}}, {"test": "tests/dialects/test_clickhouse.py::TestClickhouse::test_clickhouse", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/dialect.py", 1312], ["sqlglot/dialects/dialect.py", 1738], ["sqlglot/dialects/dialect
  - step 18 (022bb41fc5): [{"test": "tests/dialects/test_athena.py::TestAthena::test_qualify", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/athena.py", 1], ["sqlglot/dialects/athena.py", 13], ["sqlglot/dialects/athena.py", 53]], "classes": ["sqlglot/dialects/dialect.py:JSONPathTokenizer", "sqlglot/dialects/dialect.py:Tokenizer", "sqlglot/dialects/mysql.py:MySQL.Tokenizer"]}}, {"test": "tests/dialects/test_databricks.py::TestDatabricks::test_databricks", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/dialect.py", 2096], ["sqlglot/dialects/tsql.py", 1], ["sqlglot/dialects/tsql.py", 14]
  - step 19 (f2b81bfb2d): [{"test": "tests/dialects/test_athena.py::TestAthena::test_qualify", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/athena.py", 1], ["sqlglot/dialects/athena.py", 13], ["sqlglot/dialects/athena.py", 53]], "classes": ["sqlglot/dialects/dialect.py:JSONPathTokenizer", "sqlglot/dialects/dialect.py:Tokenizer", "sqlglot/dialects/mysql.py:MySQL.Tokenizer"]}}, {"test": "tests/dialects/test_databricks.py::TestDatabricks::test_databricks", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/dialect.py", 2096], ["sqlglot/dialects/tsql.py", 1], ["sqlglot/dialects/tsql.py", 14]
  - step 20 (7f1cf60c88): [{"test": "tests/dialects/test_athena.py::TestAthena::test_ddl", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/athena.py", 1], ["sqlglot/dialects/athena.py", 13], ["sqlglot/dialects/athena.py", 53]], "classes": ["sqlglot/dialects/dialect.py:JSONPathTokenizer", "sqlglot/dialects/mysql.py:MySQL.Tokenizer", "sqlglot/jsonpath.py:JSONPathTokenizer"]}}, {"test": "tests/dialects/test_athena.py::TestAthena::test_qualify", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/athena.py", 1], ["sqlglot/dialects/athena.py", 13], ["sqlglot/dialects/athena.py", 53]], "classes": 
