# B1: real consecutive history

## datasette

Pairs: 52 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['83a6ccb73a54c1cd'].

### Scenario S (behaviour change): 52 pairs, 6 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 0/6 | 0/33 | 47/48 | 0.0 | 100.0 | 100.0 | 1.9 | 0 |
| namerts | 52 | 0/6 | 0/33 | 21/48 | 323.0 | 62.5 | 77.7 | 58.6 | 0 |
| proviso | 52 | 0/6 | 0/33 | 45/48 | 567.5 | 28.8 | 63.7 | 48.7 | 5 |
| run_all | 52 | 0/6 | 0/33 | 48/48 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 4/6 | 31/33 | 8/48 | 2483.5 | 1.9 | 1.2 | 94.2 | 0 |
| testmon | 52 | 1/6 | 1/33 | 46/48 | 4.0 | 92.6 | 93.7 | 5.4 | 0 |
| traditional | 52 | 0/6 | 0/33 | 48/48 | 0.0 | 100.0 | 100.0 | 24.5 | 34 |

### Scenario F (full commit): 52 pairs, 0 break a test; flaky failures dropped 1, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 0/0 | 0/0 | 48/48 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| namerts | 52 | 0/0 | 0/0 | 22/48 | 338.0 | 62.5 | 77.7 | 58.3 | 0 |
| proviso | 52 | 0/0 | 0/0 | 46/48 | 0.5 | 46.5 | 76.7 | 45.8 | 5 |
| run_all | 52 | 0/0 | 0/0 | 48/48 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 0/0 | 0/0 | 10/48 | 2380.0 | 3.2 | 3.0 | 92.9 | 0 |
| testmon | 52 | 0/0 | 0/0 | 46/48 | 4.0 | 94.4 | 95.0 | 5.2 | 0 |
| traditional | 52 | 0/0 | 0/0 | 48/48 | 0.0 | 100.0 | 100.0 | 22.7 | 34 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 118.8 | 77.5 | 5.9 / 1.3 | 47.2 | 123.2 | 1.7 |

## loguru

Pairs: 50 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['07ac6be4b356a695'].

### Scenario S (behaviour change): 50 pairs, 5 break a test; flaky failures dropped 23, flaky at parent 3

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 50 | 0/5 | 0/29 | 48/49 | 0.0 | 98.2 | 95.3 | 26.7 | 0 |
| namerts | 50 | 1/5 | 17/29 | 38/49 | 92.5 | 19.2 | 14.3 | 59.7 | 0 |
| proviso | 50 | 0/5 | 0/29 | 38/49 | 513.0 | 12.2 | 30.0 | 62.2 | 9 |
| proviso-fallbacks | 50 | 1/5 | 17/29 | 38/49 | 1231.5 | 10.6 | 27.0 | 67.6 | 6 |
| proviso-files | 50 | 0/5 | 0/29 | 38/49 | 513.0 | 12.2 | 30.0 | 62.5 | 9 |
| proviso-nameindex | 50 | 0/5 | 0/29 | 38/49 | 441.5 | 12.2 | 30.0 | 61.2 | 9 |
| proviso-nofixattr | 50 | 0/5 | 0/29 | 38/49 | 513.0 | 12.2 | 30.0 | 62.2 | 9 |
| proviso-snapshot | 50 | 0/5 | 0/29 | 43/49 | 163.0 | 59.5 | 81.1 | 46.4 | 9 |
| proviso-v2.3.2 | 50 | 0/5 | 0/29 | 49/49 | n/a | 12.2 | 30.0 | 62.2 | 9 |
| run_all | 50 | 0/5 | 0/29 | 49/49 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 50 | 3/5 | 26/29 | 15/49 | 1493.0 | 1.5 | 0.0 | 94.0 | 0 |
| testmon | 50 | 0/5 | 0/29 | 46/49 | 260.0 | 62.5 | 81.5 | 42.1 | 0 |
| traditional | 50 | 0/5 | 0/29 | 49/49 | 0.0 | 100.0 | 100.0 | 23.0 | 37 |

### Scenario F (full commit): 50 pairs, 4 break a test; flaky failures dropped 19, flaky at parent 4

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 50 | 2/4 | 31/33 | 48/49 | 0.0 | 98.2 | 95.5 | 10.9 | 0 |
| namerts | 50 | 2/4 | 31/33 | 38/49 | 120.5 | 26.2 | 42.6 | 56.8 | 0 |
| proviso | 50 | 0/4 | 0/33 | 39/49 | 424.5 | 15.3 | 43.0 | 55.5 | 9 |
| proviso-fallbacks | 50 | 0/4 | 0/33 | 39/49 | 697.0 | 14.6 | 32.5 | 58.9 | 6 |
| proviso-files | 50 | 0/4 | 0/33 | 39/49 | 0.0 | 15.8 | 45.3 | 52.4 | 13 |
| proviso-nameindex | 50 | 0/4 | 0/33 | 39/49 | 349.0 | 15.5 | 44.1 | 54.6 | 9 |
| proviso-nofixattr | 50 | 0/4 | 0/33 | 39/49 | 424.5 | 15.3 | 43.0 | 55.5 | 9 |
| proviso-snapshot | 50 | 0/4 | 0/33 | 44/49 | 53.5 | 67.8 | 92.6 | 40.3 | 9 |
| proviso-v2.3.2 | 50 | 0/4 | 0/33 | 49/49 | n/a | 15.3 | 43.0 | 55.5 | 9 |
| run_all | 50 | 0/4 | 0/33 | 49/49 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 50 | 4/4 | 33/33 | 15/49 | 1396.0 | 5.1 | 0.4 | 89.9 | 0 |
| testmon | 50 | 0/4 | 0/33 | 46/49 | 74.0 | 70.8 | 86.0 | 30.3 | 0 |
| traditional | 50 | 0/4 | 0/33 | 49/49 | 0.0 | 100.0 | 100.0 | 19.1 | 37 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 78.1 | 32.2 | 0.6 / 0.2 | 88.8 | 70.3 | 0.2 |

## pygments

Pairs: 52 ok, 0 skipped (do not build here), 0 errors. Environment hashes: ['7c1d39129f10abf7'].

### Scenario S (behaviour change): 52 pairs, 8 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 7/8 | 8/9 | 43/51 | 5301.5 | 0.0 | 0.0 | 99.8 | 0 |
| namerts | 52 | 7/8 | 8/9 | 43/51 | 5305.0 | 0.0 | 0.0 | 100.0 | 0 |
| proviso | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 91.5 | 0 |
| proviso-fallbacks | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 89.6 | 1 |
| proviso-files | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 91.5 | 0 |
| proviso-nameindex | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 91.2 | 0 |
| proviso-nofixattr | 52 | 0/8 | 0/9 | 50/51 | 5281.0 | 0.3 | 1.9 | 91.5 | 0 |
| proviso-snapshot | 52 | 0/8 | 0/9 | 51/51 | 5222.5 | 1.1 | 3.8 | 89.6 | 1 |
| proviso-v2.3.2 | 52 | 0/8 | 0/9 | 51/51 | n/a | 0.3 | 1.9 | 91.5 | 0 |
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
| proviso-fallbacks | 52 | 0/2 | 0/2 | 50/51 | 5281.0 | 0.4 | 1.9 | 89.6 | 1 |
| proviso-files | 52 | 0/2 | 0/2 | 50/51 | 0.0 | 58.2 | 82.7 | 47.7 | 25 |
| proviso-nameindex | 52 | 0/2 | 0/2 | 50/51 | 5273.5 | 0.5 | 2.2 | 83.4 | 5 |
| proviso-nofixattr | 52 | 0/2 | 0/2 | 50/51 | 5273.5 | 0.5 | 2.2 | 83.7 | 5 |
| proviso-snapshot | 52 | 0/2 | 0/2 | 51/51 | 5142.0 | 2.0 | 4.1 | 80.1 | 6 |
| proviso-v2.3.2 | 52 | 0/2 | 0/2 | 51/51 | n/a | 0.5 | 2.2 | 83.7 | 5 |
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
| ekstap | 52 | 0/15 | 0/21 | 50/52 | 0.0 | 100.0 | 100.0 | 3.8 | 0 |
| namerts | 52 | 2/15 | 2/21 | 13/52 | 129.0 | 84.5 | 97.7 | 61.0 | 0 |
| proviso | 52 | 0/15 | 0/21 | 49/52 | 800.5 | 12.3 | 74.5 | 46.5 | 10 |
| proviso-fallbacks | 52 | 0/15 | 0/21 | 49/52 | 800.5 | 12.3 | 74.5 | 46.5 | 10 |
| proviso-files | 52 | 0/15 | 0/21 | 49/52 | 800.5 | 12.3 | 74.5 | 46.5 | 10 |
| proviso-nameindex | 52 | 0/15 | 0/21 | 49/52 | 768.5 | 12.3 | 74.5 | 45.8 | 10 |
| proviso-nofixattr | 52 | 0/15 | 0/21 | 49/52 | 800.5 | 12.3 | 74.5 | 46.5 | 10 |
| proviso-snapshot | 52 | 0/15 | 0/21 | 50/52 | 85.0 | 26.0 | 84.8 | 36.1 | 10 |
| proviso-v2.3.2 | 52 | 0/15 | 0/21 | 52/52 | n/a | 12.3 | 74.5 | 46.5 | 10 |
| run_all | 52 | 0/15 | 0/21 | 52/52 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 13/15 | 17/21 | 6/52 | 1249.0 | 3.8 | 1.4 | 97.0 | 0 |
| testmon | 52 | 1/15 | 1/21 | 37/52 | 92.5 | 25.5 | 45.4 | 45.3 | 0 |
| traditional | 52 | 0/15 | 0/21 | 52/52 | 0.0 | 100.0 | 100.0 | 13.3 | 44 |

### Scenario F (full commit): 52 pairs, 0 break a test; flaky failures dropped 0, flaky at parent 0

| Tool | Pairs | Breaking pairs with a missed failure | Failing tests missed | SafeR (func, files) | Skipped exec tests (median) | Median % tests | Median % time | Mean TestR | Full suite |
|---|---|---|---|---|---|---|---|---|---|
| ekstap | 52 | 0/0 | 0/0 | 50/52 | 0.0 | 100.0 | 100.0 | 3.8 | 0 |
| namerts | 52 | 0/0 | 0/0 | 14/52 | 129.0 | 84.5 | 97.7 | 60.4 | 0 |
| proviso | 52 | 0/0 | 0/0 | 49/52 | 800.5 | 16.4 | 78.2 | 46.4 | 10 |
| proviso-fallbacks | 52 | 0/0 | 0/0 | 49/52 | 800.5 | 16.4 | 78.2 | 46.4 | 10 |
| proviso-files | 52 | 0/0 | 0/0 | 49/52 | 122.5 | 24.8 | 81.5 | 38.3 | 17 |
| proviso-nameindex | 52 | 0/0 | 0/0 | 49/52 | 768.5 | 16.4 | 78.2 | 45.7 | 10 |
| proviso-nofixattr | 52 | 0/0 | 0/0 | 49/52 | 800.5 | 16.4 | 78.2 | 46.4 | 10 |
| proviso-snapshot | 52 | 0/0 | 0/0 | 50/52 | 85.0 | 26.8 | 84.8 | 36.0 | 10 |
| proviso-v2.3.2 | 52 | 0/0 | 0/0 | 52/52 | n/a | 16.4 | 78.2 | 46.4 | 10 |
| run_all | 52 | 0/0 | 0/0 | 52/52 | 0.0 | 100.0 | 100.0 | 0.0 | 0 |
| tdad | 52 | 0/0 | 0/0 | 10/52 | 1196.5 | 7.5 | 2.6 | 94.7 | 0 |
| testmon | 52 | 0/0 | 0/0 | 37/52 | 92.5 | 26.3 | 70.5 | 45.1 | 0 |
| traditional | 52 | 0/0 | 0/0 | 52/52 | 0.0 | 100.0 | 100.0 | 13.3 | 44 |

### Overhead (seconds, median over ok pairs)

| Plain suite at P | Proviso recording | Proviso selection (cold / warm) | testmon recording | NameRTS init | TDAD index |
|---|---|---|---|---|---|
| 74.6 | 114.1 | 6.0 / 1.5 | 161.1 | 87.2 | 2.4 |

