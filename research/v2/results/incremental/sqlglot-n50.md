# Incremental recording check: sqlglot-n50

- Steps: 50; full re-recordings (selection ran the whole suite, or no clean map): 10
- First full recording: 128.49 s; fresh recordings at check points: median 127.77 s
- Incremental update: median 19.91 s, max 133.87 s; test files re-recorded: median 2; selection: median 1.88 s; base snapshot adopted at 31 of 50 steps
- Map comparisons: 50; tests whose fresh record has something the incremental one lacks: 1; tests only in the fresh map: 0; global record missing: 0
- Noise baseline (two fresh recordings of one commit): 0 tests differ, 0 with something only one of them records
- Selection at the next commit: 49 checks; tests selected only with the fresh map: 0

## v2.3 (record from scratch at every commit) vs v2.4 (incremental), same commits

| | v2.3 | v2.4 |
|---|---|---|
| Per-commit cost: recording + selection, median | 137.3 s | 21.8 s |
| Total over 49 commits | 6737 s | 2847 s |
| Selection alone, median | 13.1 s | 1.9 s |
| Commits with identical selected tests | 48 of 49 | |
| Tests only v2.3 selects (lost by v2.4) | 0 | |
| Tests only v2.4 selects (extra cost) | 1 | |
  - step 16 (0ceaf1319e): [{"test": "tests/dialects/test_databricks.py::TestDatabricks::test_databricks", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/dialects/databricks.py", 1], ["sqlglot/dialects/databricks.py", 15], ["sqlglot/dialects/databricks.py", 30]], "classes": ["sqlglot/dialects/tsql.py:TSQL.Tokenizer"]}}, {"test": "tests/dialects/test_dialect.py::TestDialect::test_nested_ctes", "missing_in_a": {}, "extra_in_a": {"funcs": [["sqlglot/optimizer/qualify_columns.py", 1], ["sqlglot/optimizer/resolver.py", 1], ["sqlglot/optimizer/resolver.py", 17]]}}]
