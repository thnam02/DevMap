# Proviso (v2.2) and NameRTS on the same real agent regressions (SWE-bench)

Cases where the regression reproduced here and both tools ran. Time share: test time of the selection over the whole suite (Proviso's per-test times; NameRTS selects whole files). Missed: a case with a broken test not selected; undetected: no broken test selected.

## core sample (development of v2.1)

| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso undetected | NameRTS undetected | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | map / init time (median s) |
|---|---|---|---|---|---|---|---|---|---|---|
| sympy__sympy | 0 | 0 | | | | | | | 1 | |
| sphinx-doc__sphinx | 8 | 20 | 3 | 1 | 0 | 1 | 70.7% | 65.4% | 0 | 30 / 71 |
| pydata__xarray | 13 | 30 | 0 | 0 | 0 | 0 | 44.0% | 63.1% | 1 | 64 / 166 |
| pytest-dev__pytest | 0 | 0 | | | | | | | 10 | |
| pylint-dev__pylint | 11 | 26 | 0 | 0 | 0 | 0 | 81.9% | 53.2% | 0 | 41 / 53 |
| mwaskom__seaborn | 12 | 28 | 0 | 0 | 0 | 0 | 9.4% | 30.3% | 1 | 36 / 132 |
| pallets__flask | 3 | 3 | 0 | 1 | 0 | 1 | 72.1% | 9.9% | 0 | 2 / 17 |
| **all** | 47 | 107 | 3 | 2 | 0 | 2 | 50.0% | 51.0% | 13 | 37 / 90 |

## held-out instances

| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso undetected | NameRTS undetected | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | map / init time (median s) |
|---|---|---|---|---|---|---|---|---|---|---|
| sphinx-doc__sphinx | 24 | 62 | 3 | 3 | 0 | 3 | 60.8% | 63.5% | 0 | 23 / 70 |
| pydata__xarray | 19 | 51 | 1 | 1 | 0 | 1 | 40.0% | 69.9% | 0 | 64 / 190 |
| pylint-dev__pylint | 1 | 1 | 0 | 0 | 0 | 0 | 99.0% | 94.8% | 0 | 38 / 52 |
| **all** | 44 | 114 | 4 | 4 | 0 | 4 | 51.8% | 66.7% | 0 | 31 / 84 |

