# Classic safety measure, main benchmark (650 changes; 181 without a classic row)

## Reference: every test that executes changed code (import-time code: every test)

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 469 | 197 | 303,616 of 1,192,383 (25.5%) | 175 changes | 8 of 283 |
| testmon | 459 | 353 | 419,255 of 1,182,467 (35.5%) | 308 changes | 46 of 273 |
| tdad | 378 | 378 | 1,130,187 of 1,158,181 (97.6%) | 378 changes | 229 of 236 |

proviso, exec reference, changes that break tests (283): classically unsafe and missed a failure 2; classically unsafe, no failure missed 85; classically safe but missed a failure 6; both fine 190

## Reference: every test that ran a modified function (NameRTS's SafeR)

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 469 | 1 | 37 of 61,869 (0.1%) | 1 changes | 8 of 283 |
| testmon | 459 | 52 | 1,633 of 61,869 (2.6%) | 35 changes | 46 of 273 |
| tdad | 378 | 144 | 57,467 of 59,672 (96.3%) | 144 changes | 229 of 236 |

proviso, func reference, changes that break tests (283): classically unsafe and missed a failure 0; classically unsafe, no failure missed 0; classically safe but missed a failure 8; both fine 275

Changes whose exec reference is the whole suite (code run at import, or a full-suite rule): 301

### sqlglot

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 95 | 58 | 53,626 of 78,295 (68.5%) | 58 changes | 0 of 59 |
| testmon | 95 | 95 | 59,683 of 78,295 (76.2%) | 88 changes | 5 of 59 |
| tdad | 95 | 95 | 76,113 of 78,295 (97.2%) | 95 changes | 56 of 59 |

### sympy

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 91 | 45 | 10,514 of 34,202 (30.7%) | 23 changes | 3 of 47 |
| testmon | 83 | 61 | 18,774 of 29,554 (63.5%) | 33 changes | 6 of 39 |

### sqlalchemy

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 94 | 0 | 0 of 579,121 (0.0%) | 0 changes | 3 of 61 |
| testmon | 94 | 11 | 5,471 of 579,121 (0.9%) | 1 changes | 6 of 61 |
| tdad | 94 | 94 | 576,972 of 579,121 (99.6%) | 94 changes | 61 of 61 |

### pygments

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 94 | 40 | 212,117 of 329,841 (64.3%) | 40 changes | 0 of 56 |
| testmon | 94 | 94 | 320,435 of 329,841 (97.1%) | 94 changes | 26 of 56 |
| tdad | 94 | 94 | 309,581 of 329,841 (93.9%) | 94 changes | 56 of 56 |

### datasette

| Selector | Changes scored | Changes skipping a test that runs changed code (classically unsafe) | Such tests skipped (of all such tests) | Test files skipped (NameRTS-style) | Changes with a missed failure |
|---|---|---|---|---|---|
| proviso | 95 | 54 | 27,359 of 170,924 (16.0%) | 54 changes | 2 of 60 |
| testmon | 93 | 92 | 14,892 of 165,656 (9.0%) | 92 changes | 3 of 58 |
| tdad | 95 | 95 | 167,521 of 170,924 (98.0%) | 95 changes | 56 of 60 |

