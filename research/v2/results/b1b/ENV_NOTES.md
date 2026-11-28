# B1b environments: fixes and groups not runnable on Python 3.12 (2026-11-28)

Proviso needs Python 3.12 (sys.monitoring), so every SWE environment is a Python 3.12 one (swe_probe.py). Before B1b
reached them, `research/v2/b1b_preflight.py` collected the suite of one not-yet-run instance per environment (fixed
version on PYTHONPATH, no install). Candidate fixes were tested without touching an environment: pinned packages in a
scratch folder on PYTHONPATH, or a throwaway copy of the environment with the tree installed. Environments were changed
only while B1b was stopped between instances.

## Fixed (a test dependency was missing or too new)

| Environment | Symptom | Installed | After (collected tests, one instance) | Rows |
|---|---|---|---|---|
| pylint 2.13 | `No module named 'toml'` (older commits of the group import it); 7 of 8 instances skipped | toml 0.10.2 | 1,383-1,682 per instance (7 checked) | the group's 8 rows superseded and re-run (one dependencies hash) |
| pylint 2.10 | `No module named 'appdirs'` in tests/conftest.py | appdirs 1.4.4 | 1,693 | none yet (installed before the group ran) |
| sphinx 3.5 | `cannot import name 'environmentfilter' from 'jinja2'` (removed in Jinja2 3.1) | jinja2 3.0.3 | 1,624 | none yet |
| sphinx 4.0 | same | jinja2 3.0.3 | 1,528 | none yet |

## Not runnable on Python 3.12 (their own code; no dependency fixes it): B1b skips them

| Environment | Instances in the sample | Verified cause |
|---|---|---|
| sphinx 4.1 | 19 | `from types import Union` in sphinx's own code fails on Python 3.12 (unchanged with jinja2 3.0.3, markupsafe 2.0.1, docutils 0.17.1) |
| pytest 6.3 | 8 | its assertion rewriter fails on Python 3.12's AST (`TypeError: required field "lineno" missing from alias`), with the tree installed |
| pytest 7.0, 7.1, 7.4 | 11 + 5 + 6 | the assertion rewriter uses `ast.Str`, deprecated in 3.12; the project's own warnings-as-errors setting makes the conftest import fail |
| pytest 7.2 | 15 | the same (after `py` is added, which it also lacks) |

B1b records these as skipped ("the suite produced no outcomes at the fixed version"); the cause per environment is the
one above. pytest 8.0 collects (3,471 tests, with the tree installed, as B1b runs it).

## Collect, with a few test files failing to import (kept as they are)

pylint 2.11 (`py._path`), pylint 2.14 (`git`, `py._path`), pylint 3.0 (`git`, `pytest_benchmark`), sphinx 4.2 and 4.3
(`_testcapi`): 1,583-2,095 tests collect; the files that fail to import are excluded at the fixed version like any
collection error.
