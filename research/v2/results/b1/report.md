# B1: real consecutive history

## pygments

Pairs: 52 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['7c1d39129f10abf7'].

### Scenario S (behaviour change): 52 pairs, 8 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 7/8 | 8/9 | 43/51 | 5301.5 | 0.0 | 0.0 | 99.8 | 0 |
| namerts | 52 | 7/8 | 8/9 | 43/51 | 5305.0 | 0.0 | 0.0 | 100.0 | 0 |
| proviso | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 91.5 | 0 |
| run_all | 52 | 0/8 | 0/9 | 51/51 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 8/8 | 9/9 | 42/51 | 5144.5 | 3.2 | 0.4 | 99.8 | 0 |
| testmon | 52 | 4/8 | 4/9 | 49/51 | 5249.5 | 1.1 | 4.7 | 96.5 | 0 |
| traditional | 52 | 0/8 | 0/9 | 51/51 | 0.0 | 100.0 | 100.0 | 10.3 | 46 |

### Scenario F (full commit): 52 pairs, 2 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 1/2 | 1/2 | 43/51 | 5301.0 | 0.0 | 0.0 | 99.8 | 0 |
| namerts | 52 | 1/2 | 1/2 | 43/51 | 5305.0 | 0.0 | 0.0 | 100.0 | 0 |
| proviso | 52 | 0/2 | 0/2 | 50/51 | 5273.5 | 0.5 | 2.2 | 83.7 | 5 |
| run_all | 52 | 0/2 | 0/2 | 51/51 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 2/2 | 2/2 | 44/51 | 5144.5 | 3.2 | 0.4 | 99.8 | 0 |
| testmon | 52 | 2/2 | 2/2 | 49/51 | 5249.5 | 1.1 | 4.7 | 96.5 | 0 |
| traditional | 52 | 0/2 | 0/2 | 51/51 | 0.0 | 100.0 | 100.0 | 10.3 | 46 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 19.5 | 260.7 | 7.8 / 1.5 | 78.6 | 20.5 | 0.7 |

## sqlglot

Pairs: 52 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['7c1d39129f10abf7'].

### Scenario S (behaviour change): 52 pairs, 15 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| namerts | 52 | 2/15 | 2/21 | 13/52 | 129.0 | 84.5 | 97.7 | 61.0 | 0 |
| proviso | 52 | 0/15 | 0/21 | 49/52 | 800.5 | 12.3 | 74.5 | 46.5 | 10 |
| run_all | 52 | 0/15 | 0/21 | 52/52 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 13/15 | 17/21 | 6/52 | 1249.0 | 3.8 | 1.4 | 97.0 | 0 |
| testmon | 52 | 1/15 | 1/21 | 37/52 | 92.5 | 25.5 | 45.4 | 45.3 | 0 |
| traditional | 52 | 0/15 | 0/21 | 52/52 | 0.0 | 100.0 | 100.0 | 13.3 | 44 |

### Scenario F (full commit): 52 pairs, 0 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| namerts | 52 | 0/0 | 0/0 | 14/52 | 129.0 | 84.5 | 97.7 | 60.4 | 0 |
| proviso | 52 | 0/0 | 0/0 | 49/52 | 800.5 | 16.4 | 78.2 | 46.4 | 10 |
| run_all | 52 | 0/0 | 0/0 | 52/52 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 0/0 | 0/0 | 10/52 | 1196.5 | 7.5 | 2.6 | 94.7 | 0 |
| testmon | 52 | 0/0 | 0/0 | 37/52 | 92.5 | 26.3 | 70.5 | 45.1 | 0 |
| traditional | 52 | 0/0 | 0/0 | 52/52 | 0.0 | 100.0 | 100.0 | 13.3 | 44 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 74.6 | 114.1 | 6.0 / 1.5 | 161.1 | 87.2 | 2.4 |

