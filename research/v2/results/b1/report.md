# B1: real consecutive history

## sqlglot

Pairs: 5 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['7c1d39129f10abf7'].

### Scenario S (behaviour change): 5 pairs, 3 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| namerts | 5 | 0/3 | 0/3 | 2/5 | 659 | 35.7 | 67.2 | 79.6 | 0 |
| proviso | 5 | 0/3 | 0/3 | 5/5 | 1128 | 12.1 | 70.9 | 64.4 | 0 |
| run_all | 5 | 0/3 | 0/3 | 5/5 | 0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 5 | 3/3 | 3/3 | 1/5 | 1271 | 3.8 | 1.4 | 96.7 | 0 |
| testmon | 5 | 0/3 | 0/3 | 5/5 | 81 | 17.7 | 66.2 | 45.1 | 0 |
| traditional | 5 | 0/3 | 0/3 | 5/5 | 0 | 100.0 | 100.0 | 18.9 | 4 |

### Scenario F (full commit): 5 pairs, 0 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| namerts | 5 | 0/0 | 0/0 | 2/5 | 641 | 35.7 | 86.2 | 78.9 | 0 |
| proviso | 5 | 0/0 | 0/0 | 5/5 | 1107 | 12.1 | 75.4 | 64.4 | 0 |
| run_all | 5 | 0/0 | 0/0 | 5/5 | 0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 5 | 0/0 | 0/0 | 1/5 | 1220 | 7.6 | 19.8 | 95.3 | 0 |
| testmon | 5 | 0/0 | 0/0 | 5/5 | 81 | 18.3 | 66.3 | 44.7 | 0 |
| traditional | 5 | 0/0 | 0/0 | 5/5 | 0 | 100.0 | 100.0 | 18.9 | 4 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 51.8 | 74.0 | 6.6 / 1.3 | 127.5 | 68.2 | 1.9 |

