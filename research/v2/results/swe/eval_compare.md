# Proviso and NameRTS on the same real agent regressions (SWE-bench)

Cases where the regression reproduced here and both tools ran. Time share: test time of the selection over the whole suite (Proviso's per-test times; NameRTS selects whole files).

| repository | instances | regressions | Proviso missed | NameRTS missed | Proviso time (mean) | NameRTS time (mean) | NameRTS errors | map / init time (median s) |
|---|---|---|---|---|---|---|---|---|
| sympy__sympy | 0 | 0 | | | | | 1 | |
| sphinx-doc__sphinx | 8 | 20 | 3 | 1 | 70.1% | 65.4% | 0 | 30 / 71 |
| pydata__xarray | 13 | 30 | 0 | 0 | 41.5% | 63.1% | 1 | 64 / 166 |
| pytest-dev__pytest | 0 | 0 | | | | | 10 | |
| pylint-dev__pylint | 11 | 26 | 0 | 0 | 81.6% | 53.2% | 0 | 41 / 53 |
| mwaskom__seaborn | 12 | 28 | 1 | 0 | 9.1% | 30.3% | 1 | 36 / 132 |
| pallets__flask | 3 | 3 | 1 | 1 | 67.7% | 9.9% | 0 | 2 / 17 |
| **all** | 47 | 107 | 5 | 2 | 48.8% | 51.0% | 13 | 37 / 90 |
