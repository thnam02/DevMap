# Offline re-score: Proviso v2.3.1 vs v2.3.2

Selection only, from each item's saved map (no test run). Missed failures against the row's confirmed failures, scored as b1.py does. `research/v2/rescore_v232.py`.

| Set | Project | Items (pair x scenario) | Identical selections | Errors | Items gaining a missed failure | Items losing one | Tests selected, v2.3.1 | Tests selected, v2.3.2 |
|---|---|---|---|---|---|---|---|---|
| b1 | loguru | 100 | 100 | 0 | 0 | 0 | 53870 | 53870 |
| b1 | pygments | 104 | 104 | 0 | 0 | 0 | 59246 | 59246 |
| b1 | sqlglot | 104 | 104 | 0 | 0 | 0 | 52237 | 52237 |
| b1b | mwaskom__seaborn | 17 | 17 | 0 | 0 | 0 | 3051 | 3051 |
| b1b | pallets__flask | 10 | 10 | 0 | 0 | 0 | 574 | 574 |
| b1b | pydata__xarray | 54 | 54 | 0 | 0 | 0 | 101810 | 101810 |

Sanity (v2.3.1 recomputed = the row's recorded size): 0 mismatches

Items whose selection differs (0):


Items gaining a missed failure (0): none

