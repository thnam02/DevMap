# Proviso (v2.3) and NameRTS on the same real agent regressions (SWE-bench)

Cases where the regression reproduced here and both tools ran. Time share: test time of the selection over the whole suite (Proviso's per-test times; NameRTS selects whole files). Missed: a case with a broken test not selected; undetected: no broken test selected.

## core sample (development of v2.1)

| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso undetected | NameRTS undetected | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | map / init time (median s) |
|---|---|---|---|---|---|---|---|---|---|---|
| sympy__sympy | 0 | 0 | | | | | | | 1 | |
| sphinx-doc__sphinx | 8 | 20 | 3 | 1 | 0 | 1 | 67.3% | 65.4% | 0 | 27 / 71 |
| pydata__xarray | 13 | 30 | 0 | 0 | 0 | 0 | 41.7% | 63.1% | 1 | 66 / 166 |
| pytest-dev__pytest | 0 | 0 | | | | | | | 10 | |
| pylint-dev__pylint | 11 | 26 | 0 | 0 | 0 | 0 | 81.5% | 53.2% | 0 | 41 / 53 |
| mwaskom__seaborn | 12 | 28 | 0 | 0 | 0 | 0 | 9.4% | 30.3% | 1 | 34 / 132 |
| pallets__flask | 3 | 3 | 0 | 1 | 0 | 1 | 66.5% | 9.9% | 0 | 1 / 17 |
| **all** | 47 | 107 | 3 | 2 | 0 | 2 | 48.4% | 51.0% | 13 | 38 / 90 |

## held-out instances

| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso undetected | NameRTS undetected | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | map / init time (median s) |
|---|---|---|---|---|---|---|---|---|---|---|
| sphinx-doc__sphinx | 24 | 62 | 3 | 3 | 0 | 3 | 58.0% | 63.5% | 0 | 25 / 70 |
| pydata__xarray | 19 | 51 | 0 | 1 | 0 | 1 | 41.9% | 69.9% | 0 | 70 / 190 |
| pylint-dev__pylint | 1 | 1 | 0 | 0 | 0 | 0 | 99.0% | 94.8% | 0 | 39 / 52 |
| **all** | 44 | 114 | 3 | 4 | 0 | 4 | 51.2% | 66.7% | 0 | 33 / 84 |

