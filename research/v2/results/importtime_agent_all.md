# SWE-bench agent regressions that edit import-time code

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| mwaskom/seaborn | 72 | 29 (40.3%) | 20 (27.8%) | 12 (16.7%) | 40 (55.6%) | 0 (0.0%) | 5 |
| pallets/flask | 54 | 14 (25.9%) | 7 (13.0%) | 5 (9.3%) | 38 (70.4%) | 0 (0.0%) | 4 |
| psf/requests | 437 | 151 (34.6%) | 132 (30.2%) | 80 (18.3%) | 277 (63.4%) | 0 (0.0%) | 22 |
| pydata/xarray | 673 | 324 (48.1%) | 232 (34.5%) | 193 (28.7%) | 329 (48.9%) | 0 (0.0%) | 43 |
| pylint-dev/pylint | 352 | 205 (58.2%) | 147 (41.8%) | 86 (24.4%) | 137 (38.9%) | 4 (1.1%) | 18 |
| pytest-dev/pytest | 692 | 322 (46.5%) | 226 (32.7%) | 158 (22.8%) | 359 (51.9%) | 2 (0.3%) | 23 |
| sphinx-doc/sphinx | 1367 | 879 (64.3%) | 742 (54.3%) | 680 (49.7%) | 453 (33.1%) | 9 (0.7%) | 83 |
| sympy/sympy | 2338 | 1286 (55.0%) | 948 (40.5%) | 747 (32.0%) | 966 (41.3%) | 0 (0.0%) | 179 |
| all | 5985 | 3210 (53.6%) | 2454 (41.0%) | 1961 (32.8%) | 2599 (43.4%) | 15 (0.3%) | 377 |

Changed code lines by kind: body 333,332, statement 114,140, import 11,132, header 27,934, docstring 10,458, unparsable 50,598

Patches that did not apply to the base commit: 629
