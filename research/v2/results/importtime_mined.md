# All scanned commits (250 per project) that edit import-time code

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| datasette | 250 | 141 (56.4%) | 105 (42.0%) | 78 (31.2%) | 109 (43.6%) | 0 (0.0%) | 0 |
| pygments | 250 | 223 (89.2%) | 213 (85.2%) | 207 (82.8%) | 19 (7.6%) | 8 (3.2%) | 0 |
| sqlalchemy | 250 | 166 (66.4%) | 116 (46.4%) | 102 (40.8%) | 83 (33.2%) | 1 (0.4%) | 0 |
| sqlglot | 250 | 176 (70.4%) | 149 (59.6%) | 143 (57.2%) | 71 (28.4%) | 3 (1.2%) | 0 |
| sympy | 250 | 103 (41.2%) | 53 (21.2%) | 22 (8.8%) | 72 (28.8%) | 4 (1.6%) | 118 |
| all | 1250 | 809 (64.7%) | 636 (50.9%) | 552 (44.2%) | 354 (28.3%) | 16 (1.3%) | 118 |

Changed code lines by kind: body 33,284, statement 7,838, import 1,210, header 4,808, docstring 2,173, unparsable 3,462

Commits that break a test:

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| datasette | 4 | 4 (100.0%) | 3 (75.0%) | 3 (75.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| pygments | 34 | 31 (91.2%) | 31 (91.2%) | 30 (88.2%) | 3 (8.8%) | 0 (0.0%) | 0 |
| sqlalchemy | 10 | 9 (90.0%) | 7 (70.0%) | 6 (60.0%) | 1 (10.0%) | 0 (0.0%) | 0 |
| sqlglot | 32 | 25 (78.1%) | 23 (71.9%) | 23 (71.9%) | 7 (21.9%) | 0 (0.0%) | 0 |
| sympy | 1 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) | 0 (0.0%) | 0 |
| all | 81 | 69 (85.2%) | 64 (79.0%) | 62 (76.5%) | 12 (14.8%) | 0 (0.0%) | 0 |

Changed code lines by kind: body 4,883, statement 770, import 77, header 254, docstring 122, unparsable 0

Commits that break no test:

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| datasette | 34 | 20 (58.8%) | 16 (47.1%) | 11 (32.4%) | 14 (41.2%) | 0 (0.0%) | 0 |
| pygments | 214 | 191 (89.3%) | 182 (85.0%) | 177 (82.7%) | 15 (7.0%) | 8 (3.7%) | 0 |
| sqlalchemy | 97 | 58 (59.8%) | 39 (40.2%) | 33 (34.0%) | 39 (40.2%) | 0 (0.0%) | 0 |
| sqlglot | 218 | 151 (69.3%) | 126 (57.8%) | 120 (55.0%) | 64 (29.4%) | 3 (1.4%) | 0 |
| sympy | 21 | 7 (33.3%) | 4 (19.0%) | 3 (14.3%) | 14 (66.7%) | 0 (0.0%) | 0 |
| all | 584 | 427 (73.1%) | 367 (62.8%) | 344 (58.9%) | 146 (25.0%) | 11 (1.9%) | 0 |

Changed code lines by kind: body 8,928, statement 4,885, import 321, header 1,279, docstring 790, unparsable 0

Commits not run (suite does not run at the parent here):

| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) | Import-time statements (values) | Function bodies only | No non-test Python code | With an unparsable file |
|---|---|---|---|---|---|---|---|
| datasette | 212 | 117 (55.2%) | 86 (40.6%) | 64 (30.2%) | 95 (44.8%) | 0 (0.0%) | 0 |
| pygments | 2 | 1 (50.0%) | 0 (0.0%) | 0 (0.0%) | 1 (50.0%) | 0 (0.0%) | 0 |
| sqlalchemy | 143 | 99 (69.2%) | 70 (49.0%) | 63 (44.1%) | 43 (30.1%) | 1 (0.7%) | 0 |
| sympy | 228 | 96 (42.1%) | 49 (21.5%) | 19 (8.3%) | 57 (25.0%) | 4 (1.8%) | 118 |
| all | 585 | 313 (53.5%) | 205 (35.0%) | 146 (25.0%) | 196 (33.5%) | 5 (0.9%) | 118 |

Changed code lines by kind: body 19,473, statement 2,183, import 812, header 3,275, docstring 1,261, unparsable 3,462
