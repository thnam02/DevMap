# B1b: reversed SWE-bench fixes

## mwaskom__seaborn: 16 bugs (3 skipped, 0 errors); FAIL_TO_PASS reproduced in 16

| Tool | Bugs | Bugs with a missed failure | Failing tests missed | Median % tests | Median % time |
|---|---|---|---|---|---|
| ekstap | 16 | 0/16 | 0/25 | 96.4 | 99.2 |
| namerts | 16 | 0/16 | 0/25 | 12.4 | 6.4 |
| proviso | 16 | 0/16 | 0/25 | 5.8 | 3.9 |
| run_all | 16 | 0/16 | 0/25 | 100.0 | 100.0 |
| tdad | 16 | 14/16 | 22/25 | 2.7 | 0.0 |
| testmon | 15 | 0/15 | 0/23 | 8.0 | 4.9 |
| traditional | 16 | 0/16 | 0/25 | 6.8 | 4.6 |

## pallets__flask: 8 bugs (0 skipped, 0 errors); FAIL_TO_PASS reproduced in 4

| Tool | Bugs | Bugs with a missed failure | Failing tests missed | Median % tests | Median % time |
|---|---|---|---|---|---|
| ekstap | 8 | 0/4 | 0/5 | 100.0 | 100.0 |
| namerts | 8 | 0/4 | 0/5 | 13.1 | 6.1 |
| proviso | 8 | 0/4 | 0/5 | 6.7 | 75.4 |
| run_all | 8 | 0/4 | 0/5 | 100.0 | 100.0 |
| tdad | 8 | 2/4 | 2/5 | 22.3 | 8.1 |
| testmon | 8 | 0/4 | 0/5 | 12.8 | 5.7 |
| traditional | 8 | 0/4 | 0/5 | 6.7 | 75.4 |

## pydata__xarray: 39 bugs (1 skipped, 0 errors); FAIL_TO_PASS reproduced in 35

| Tool | Bugs | Bugs with a missed failure | Failing tests missed | Median % tests | Median % time |
|---|---|---|---|---|---|
| ekstap | 39 | 0/38 | 0/1262 | 100.0 | 100.0 |
| namerts | 39 | 26/38 | 1087/1262 | 0.0 | 0.0 |
| proviso | 39 | 0/38 | 0/1262 | 11.1 | 17.5 |
| run_all | 39 | 0/38 | 0/1262 | 100.0 | 100.0 |
| tdad | 39 | 30/38 | 1210/1262 | 1.0 | 0.8 |
| testmon | 39 | 3/38 | 7/1262 | 13.7 | 37.6 |
| traditional | 39 | 0/38 | 0/1262 | 100.0 | 100.0 |

## Environment check: one dependencies-only hash per SWE environment

`env_deps.hash`: the environment's packages without the project under test (whose own editable install changes per instance, and with it `env.hash`).

7 of 7 environments with rows have a single dependencies-only hash.

