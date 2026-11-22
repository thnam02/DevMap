# Incremental recording check: sqlglot

- Steps: 20; full re-recordings (selection ran the whole suite, or no clean map): 3
- First full recording: 145.32 s; fresh recordings at check points: median 148.78 s
- Incremental update: median 21.63 s, max 171.54 s; test files re-recorded: median 2; selection: median 3.39 s; base snapshot adopted at 13 of 20 steps
- Map comparisons: 20; tests whose fresh record has something the incremental one lacks: 0; tests only in the fresh map: 0; global record missing: 0
- Noise baseline (two fresh recordings of one commit): 0 tests differ, 0 with something only one of them records
- Selection at the next commit: 19 checks; tests selected only with the fresh map: 0

## v2.3 (record from scratch at every commit) vs v2.4 (incremental), same commits

| | v2.3 | v2.4 |
|---|---|---|
| Per-commit cost: recording + selection, median | 163.3 s | 24.3 s |
| Total over 19 commits | 3057 s | 1021 s |
| Selection alone, median | 15.5 s | 2.9 s |
| Commits with identical selected tests | 19 of 19 | |
| Tests only v2.3 selects (lost by v2.4) | 0 | |
| Tests only v2.4 selects (extra cost) | 0 | |
