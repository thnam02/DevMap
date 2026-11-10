# Full-suite ground truth: every test the agent patch breaks (Proviso v2.3, NameRTS)

Cases with at least one test that passes twice at base and fails twice after the patch. Missed: a broken test outside the tool's selection. Undetected: every broken test outside it. NameRTS columns count only cases where NameRTS ran.

## held-out instances

| repository | cases | with broken tests | broken tests | beyond SWE-bench's | Proviso missed | Proviso undetected | NameRTS ran | NameRTS missed | NameRTS undetected |
|---|---|---|---|---|---|---|---|---|---|
| pydata__xarray | 59 | 58 | 102745 | 100468 | 1 | 0 | 58 | 7 | 5 |
| pylint-dev__pylint | 1 | 1 | 536 | 522 | 0 | 0 | 1 | 1 | 0 |
| sphinx-doc__sphinx | 99 | 68 | 12822 | 12122 | 11 | 0 | 68 | 16 | 3 |
| **all** | 159 | 127 | 116103 | 113112 | 12 | 0 | 127 | 24 | 8 |

Proviso's selection differs from its eval row in 0 case(s).

