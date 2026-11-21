# SWE-bench agent regressions that edit import-time code

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| mwaskom/seaborn | 27 | 12 (44.4%) | 7 (25.9%) | 5 (18.5%) | 15 (55.6%) | 0 (0.0%) | 1 |
| pallets/flask | 9 | 5 (55.6%) | 3 (33.3%) | 2 (22.2%) | 3 (33.3%) | 0 (0.0%) | 3 |
| pydata/xarray | 84 | 48 (57.1%) | 42 (50.0%) | 34 (40.5%) | 33 (39.3%) | 0 (0.0%) | 6 |
| pylint-dev/pylint | 30 | 22 (73.3%) | 12 (40.0%) | 9 (30.0%) | 8 (26.7%) | 0 (0.0%) | 0 |
| pytest-dev/pytest | 10 | 4 (40.0%) | 2 (20.0%) | 0 (0.0%) | 5 (50.0%) | 1 (10.0%) | 0 |
| sphinx-doc/sphinx | 110 | 63 (57.3%) | 55 (50.0%) | 47 (42.7%) | 45 (40.9%) | 1 (0.9%) | 2 |
| sympy/sympy | 123 | 69 (56.1%) | 55 (44.7%) | 42 (34.1%) | 52 (42.3%) | 0 (0.0%) | 5 |
| all | 393 | 223 (56.7%) | 176 (44.8%) | 139 (35.4%) | 161 (41.0%) | 2 (0.5%) | 17 |

Changed code lines by kind: body 30,663, statement 2,258, import 776, header 3,167, docstring 864, unparsable 1,863

Only the reproduced regressions:

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| mwaskom/seaborn | 26 | 11 (42.3%) | 6 (23.1%) | 4 (15.4%) | 15 (57.7%) | 0 (0.0%) | 0 |
| pallets/flask | 3 | 1 (33.3%) | 0 (0.0%) | 0 (0.0%) | 2 (66.7%) | 0 (0.0%) | 0 |
| pydata/xarray | 73 | 39 (53.4%) | 33 (45.2%) | 26 (35.6%) | 33 (45.2%) | 0 (0.0%) | 2 |
| pylint-dev/pylint | 26 | 18 (69.2%) | 10 (38.5%) | 8 (30.8%) | 8 (30.8%) | 0 (0.0%) | 0 |
| pytest-dev/pytest | 7 | 2 (28.6%) | 1 (14.3%) | 0 (0.0%) | 4 (57.1%) | 1 (14.3%) | 0 |
| sphinx-doc/sphinx | 69 | 36 (52.2%) | 30 (43.5%) | 24 (34.8%) | 32 (46.4%) | 0 (0.0%) | 1 |
| sympy/sympy | 98 | 49 (50.0%) | 37 (37.8%) | 30 (30.6%) | 49 (50.0%) | 0 (0.0%) | 0 |
| all | 302 | 156 (51.7%) | 117 (38.7%) | 92 (30.5%) | 143 (47.4%) | 1 (0.3%) | 3 |

Changed code lines by kind: body 12,828, statement 1,490, import 330, header 688, docstring 294, unparsable 119

Patches that did not apply to the base commit: 36
