# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 31eade093008 | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 48 |

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 24 | 11 | 46% | 12.417 | 4169340 | 14206.169 | 684.0 | 82 | 0 | 0 | 0 |
| impact-noreport | 24 | 13 | 54% | 11.833 | 3930032 | 14436.143 | 665.4 | 81 | 0 | 0 | 0 |

## Tool result sizes

Size of the result text returned to the agent for each completed tool call (chars, ~tokens = chars/4). MCP calls are grouped by dc-engine tool name. Totals are summed over the runs below (including contaminated).

### baseline

Total returned chars: **206273** (~51569 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Read | 88882 | 22221 |
| Bash | 68520 | 17130 |
| Grep | 45383 | 11346 |
| Edit | 3488 | 872 |

### impact-noreport

Total returned chars: **229945** (~57487 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Read | 98986 | 24747 |
| Bash | 80431 | 20108 |
| Grep | 46198 | 11550 |
| Edit | 4212 | 1053 |
| Write | 118 | 30 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2848 | baseline | 1 | 12 | 164303 | 13691.917 |
| mwaskom__seaborn-2848 | impact-noreport | 1 | 15 | 199572 | 13304.800 |
| mwaskom__seaborn-2848 | baseline | 2 | 14 | 212954 | 15211 |
| mwaskom__seaborn-2848 | impact-noreport | 2 | 12 | 167434 | 13952.833 |
| mwaskom__seaborn-2996 | impact-noreport | 1 | 7 | 114087 | 16298.143 |
| mwaskom__seaborn-2996 | baseline | 1 | 11 | 140778 | 12798 |
| mwaskom__seaborn-2996 | baseline | 2 | 13 | 189595 | 14584.231 |
| mwaskom__seaborn-2996 | impact-noreport | 2 | 7 | 113576 | 16225.143 |
| pallets__flask-5014 | baseline | 1 | 4 | 75606 | 18901.500 |
| pallets__flask-5014 | impact-noreport | 1 | 10 | 158765 | 15876.500 |
| pallets__flask-5014 | baseline | 2 | 4 | 75949 | 18987.250 |
| pallets__flask-5014 | impact-noreport | 2 | 4 | 76112 | 19028 |
| pallets__flask-5063 | baseline | 1 | 12 | 194447 | 16203.917 |
| pallets__flask-5063 | impact-noreport | 1 | 5 | 82355 | 16471 |
| pallets__flask-5063 | baseline | 2 | 7 | 102468 | 14638.286 |
| pallets__flask-5063 | impact-noreport | 2 | 6 | 101233 | 16872.167 |
| pydata__xarray-6598 | baseline | 1 | 7 | 107086 | 15298 |
| pydata__xarray-6598 | impact-noreport | 1 | 6 | 106713 | 17785.500 |
| pydata__xarray-6598 | impact-noreport | 2 | 5 | 84888 | 16977.600 |
| pydata__xarray-6598 | baseline | 2 | 6 | 107056 | 17842.667 |
| pydata__xarray-6889 | impact-noreport | 1 | 20 | 285883 | 14294.150 |
| pydata__xarray-6889 | baseline | 1 | 27 | 429189 | 15895.889 |
| pydata__xarray-6889 | baseline | 2 | 21 | 310454 | 14783.524 |
| pydata__xarray-6889 | impact-noreport | 2 | 15 | 211060 | 14070.667 |
| pylint-dev__pylint-4398 | impact-noreport | 1 | 18 | 197347 | 10963.722 |
| pylint-dev__pylint-4398 | baseline | 1 | 21 | 208821 | 9943.857 |
| pylint-dev__pylint-4398 | impact-noreport | 2 | 18 | 200501 | 11138.944 |
| pylint-dev__pylint-4398 | baseline | 2 | 16 | 213369 | 13335.562 |
| pylint-dev__pylint-6386 | baseline | 1 | 15 | 182634 | 12175.600 |
| pylint-dev__pylint-6386 | impact-noreport | 1 | 17 | 213897 | 12582.176 |
| pylint-dev__pylint-6386 | impact-noreport | 2 | 14 | 184484 | 13177.429 |
| pylint-dev__pylint-6386 | baseline | 2 | 17 | 193289 | 11369.941 |
| pytest-dev__pytest-11160 | baseline | 1 | 5 | 63089 | 12617.800 |
| pytest-dev__pytest-11160 | impact-noreport | 1 | 5 | 63764 | 12752.800 |
| pytest-dev__pytest-11160 | impact-noreport | 2 | 13 | 152692 | 11745.538 |
| pytest-dev__pytest-11160 | baseline | 2 | 7 | 85814 | 12259.143 |
| pytest-dev__pytest-11178 | impact-noreport | 1 | 16 | 191855 | 11990.938 |
| pytest-dev__pytest-11178 | baseline | 1 | 10 | 132367 | 13236.700 |
| pytest-dev__pytest-11178 | baseline | 2 | 8 | 85439 | 10679.875 |
| pytest-dev__pytest-11178 | impact-noreport | 2 | 13 | 157593 | 12122.538 |
| sphinx-doc__sphinx-9459 | baseline | 1 | 23 | 346168 | 15050.783 |
| sphinx-doc__sphinx-9459 | impact-noreport | 1 | 23 | 361931 | 15736.130 |
| sphinx-doc__sphinx-9459 | impact-noreport | 2 | 19 | 276369 | 14545.737 |
| sphinx-doc__sphinx-9459 | baseline | 2 | 24 | 364753 | 15198.042 |
| sphinx-doc__sphinx-9829 | baseline | 1 | 7 | 102082 | 14583.143 |
| sphinx-doc__sphinx-9829 | impact-noreport | 1 | 9 | 126163 | 14018.111 |
| sphinx-doc__sphinx-9829 | baseline | 2 | 7 | 81630 | 11661.429 |
| sphinx-doc__sphinx-9829 | impact-noreport | 2 | 7 | 101758 | 14536.857 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 12.417 | 173722.500 | 14206.169 |
| impact-noreport | 11.833 | 163751.333 | 14436.143 |

## Tool surface (static)

Exact text dc-engine exposes: server instructions plus each tool's name, description, and input schema. ~tokens = chars/4.

Before (full): **8246** chars (~2062 tokens, 20 tools). After (slim): **3543** chars (~886 tokens, 5 tools).

### full

instructions: 594 chars (~149 tokens, 84 words)

| tool | chars | ~tokens |
|---|---:|---:|
| (instructions) | 594 | 149 |
| dc_start | 401 | 101 |
| dc_get_symbol | 236 | 59 |
| dc_replace_symbol | 479 | 120 |
| dc_contract | 1553 | 389 |
| dc_find | 270 | 68 |
| dc_repo_map | 242 | 61 |
| dc_find_symbol | 242 | 61 |
| dc_get_slice | 643 | 161 |
| dc_find_references | 242 | 61 |
| dc_file_outline | 155 | 39 |
| dc_insert_symbol | 361 | 91 |
| dc_index_status | 115 | 29 |
| dc_create_contract | 1053 | 264 |
| dc_check_contract | 232 | 58 |
| dc_get_contract | 161 | 41 |
| dc_list_contracts | 92 | 23 |
| dc_close_contract | 271 | 68 |
| dc_amend_contract | 408 | 102 |
| dc_list_checkpoints | 166 | 42 |
| dc_restore_checkpoint | 290 | 73 |
| TOTAL | 8246 | 2062 |

```
Call dc_start(task) FIRST. Output is the exact current source of shown
symbols; do not re-read those files unless something was omitted.

Then dc_contract(action=create) before any Python edit. Edit with
dc_replace_symbol; its result includes contract status. dc_find looks up
symbols or (mode=references) call sites. dc_get_symbol loads one symbol;
include_body=true for source.

Fix every ✗. Amend or close via dc_contract. Hooks deny Python edits without
an active contract. Do not stop while the score is below 1.0. Names:
pkg.mod.Class.method or a unique suffix; @L<line> picks duplicates.
```

#### dc_start

```
dc_start
First call on a task. One response: repo size, compressed map,
slices for hint_symbols or best-matching names/docs, a contract
template, and a complete JSON example. On a small repo, skip
exploration and read files directly.
{"type":"object","properties":{"task":{"type":"string"},"hint_symbols":{"type":"array","items":{"type":"string"}},"max_tokens":{"type":"integer"}},"required":["task"]}
```

#### dc_get_symbol

```
dc_get_symbol
One symbol's signature, docstring, what it calls, who calls it, and
(with include_body=true) its exact source.
{"type":"object","properties":{"name":{"type":"string"},"include_body":{"type":"boolean"}},"required":["name"]}
```

#### dc_replace_symbol

```
dc_replace_symbol
Replace one function/method/class with `new_code` (its complete new
definition, decorators included; indentation is fixed automatically).
Rejected without changes if the file would not parse. Reports only
lint/type errors the edit introduced and callers a signature change
may break. Result includes contract status.
{"type":"object","properties":{"name":{"type":"string"},"new_code":{"type":"string"},"check":{"type":"boolean"}},"required":["name","new_code"]}
```

#### dc_contract

```
dc_contract
Create, amend, check, or close a delta contract. action is create | amend | check | close. create needs task, targets, must_change (must_preserve optional). amend, check, and close need contract_id; amend takes add_targets / add_must_change / add_must_preserve. Declare a delta contract before editing. `must_change` / `must_preserve` are JSON objects: {id, setup?, call, expect_old?, expect_new?}. Expect values are JSON objects: {"returns": "<repr>"} for a normalised return value, or {"raises": "ValueError"} for an exception class name. must_change probes require expect_new. Probe setup auto-imports each target (`from pkg.mod import func` or `from pkg.mod import Class` for a method). Returns the contract id, one line per probe, and the validation verdict. Full probe code is echoed only when validation fails. ✗ with a corrected example if a target does not resolve or expect_old does not match the baseline. A complete JSON example is in the dc_start response.
{"type":"object","properties":{"action":{"type":"string"},"task":{"type":"string"},"targets":{"type":"array","items":{"type":"string"}},"must_change":{"type":"array","items":{"type":"object"}},"must_preserve":{"type":"array","items":{"type":"object"}},"pytest_ids":{"type":"array","items":{"type":"string"}},"contract_id":{"type":"string"},"add_targets":{"type":"array","items":{"type":"string"}},"add_must_change":{"type":"array","items":{"type":"object"}},"add_must_preserve":{"type":"array","items":{"type":"object"}},"reason":{"type":"string"}},"required":["action"]}
```

#### dc_find

```
dc_find
Find symbols by (partial) name, or with mode=references every
resolved call site of a symbol (plus name-matched unresolved sites).
{"type":"object","properties":{"query":{"type":"string"},"mode":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}
```

#### dc_repo_map

```
dc_repo_map
Outline of the repo: files with class/function signatures and line
numbers, compressed to fit max_tokens. Use path_prefix to zoom in.
{"type":"object","properties":{"path_prefix":{"type":"string"},"max_tokens":{"type":"integer"}}}
```

#### dc_find_symbol

```
dc_find_symbol
Find functions, methods and classes by (partial) name. Returns
qualified names, locations, signatures and one-line docs.
{"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}
```

#### dc_get_slice

```
dc_get_slice
Context for changing `targets`: their source, plus signatures of
their callees and callers up to `depth` hops, class context, and calls
whose target could not be resolved statically. Bodies are included
only for the targets unless include_test_bodies=true. include_tests=true
adds test functions that call the targets (name-matched). Fits max_tokens.
{"type":"object","properties":{"targets":{"type":"array","items":{"type":"string"}},"depth":{"type":"integer"},"max_tokens":{"type":"integer"},"include_bodies":{"type":"boolean"},"include_tests":{"type":"boolean"},"include_test_bodies":{"type":"boolean"}},"required":["targets"]}
```

#### dc_find_references

```
dc_find_references
Every resolved call site of a symbol, plus possible call sites
where the receiver's type is unknown (matched by name).
{"type":"object","properties":{"name":{"type":"string"},"limit":{"type":"integer"}},"required":["name"]}
```

#### dc_file_outline

```
dc_file_outline
Signatures and line ranges of everything defined in one file.
{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
```

#### dc_insert_symbol

```
dc_insert_symbol
Add new definitions: after=<symbol> inserts right after it at the
same indentation (e.g. a new method after an existing one);
path=<file> appends at the end of a file (created if missing).
{"type":"object","properties":{"code":{"type":"string"},"after":{"type":"string"},"path":{"type":"string"},"check":{"type":"boolean"}},"required":["code"]}
```

#### dc_index_status

```
dc_index_status
Index size, call-graph coverage and which checkers are available.
{"type":"object","properties":{}}
```

#### dc_create_contract

```
dc_create_contract
Declare a delta contract before editing. `must_change` / `must_preserve` are JSON objects: {id, setup?, call, expect_old?, expect_new?}. Expect values are JSON objects: {"returns": "<repr>"} for a normalised return value, or {"raises": "ValueError"} for an exception class name. must_change probes require expect_new. Probe setup auto-imports each target (`from pkg.mod import func` or `from pkg.mod import Class` for a method). Returns the contract id, one line per probe, and the validation verdict. Full probe code is echoed only when validation fails. ✗ with a corrected example if a target does not resolve or expect_old does not match the baseline. A complete JSON example is in the dc_start response.
{"type":"object","properties":{"task":{"type":"string"},"targets":{"type":"array","items":{"type":"string"}},"must_change":{"type":"array","items":{"type":"object"}},"must_preserve":{"type":"array","items":{"type":"object"}},"pytest_ids":{"type":"array","items":{"type":"string"}}},"required":["task","targets","must_change"]}
```

#### dc_check_contract

```
dc_check_contract
Compare baseline vs the working tree for one contract. Compact
✓/✗ report and a score (satisfied / scorable). Fix every ✗.
{"type":"object","properties":{"contract_id":{"type":"string"}},"required":["contract_id"]}
```

#### dc_get_contract

```
dc_get_contract
Show a saved contract: task, targets, probes, status.
{"type":"object","properties":{"contract_id":{"type":"string"}},"required":["contract_id"]}
```

#### dc_list_contracts

```
dc_list_contracts
List saved contracts (id, status, task).
{"type":"object","properties":{}}
```

#### dc_close_contract

```
dc_close_contract
Mark a contract closed. If the score is below 1.0, `reason` is
required. The contract JSON is kept; only the baseline tree is removed.
{"type":"object","properties":{"contract_id":{"type":"string"},"reason":{"type":"string"}},"required":["contract_id"]}
```

#### dc_amend_contract

```
dc_amend_contract
Add targets or probes to an open contract. New probes are validated
against the frozen baseline, same as at creation.
{"type":"object","properties":{"contract_id":{"type":"string"},"add_targets":{"type":"array","items":{"type":"string"}},"add_must_change":{"type":"array","items":{"type":"object"}},"add_must_preserve":{"type":"array","items":{"type":"object"}}},"required":["contract_id"]}
```

#### dc_list_checkpoints

```
dc_list_checkpoints
List score checkpoints for a contract (n, score, ref).
{"type":"object","properties":{"contract_id":{"type":"string"}},"required":["contract_id"]}
```

#### dc_restore_checkpoint

```
dc_restore_checkpoint
Roll the working tree back to checkpoint n. Only files that differ
are overwritten; untracked files the checkpoint doesn't know about
are left alone.
{"type":"object","properties":{"contract_id":{"type":"string"},"n":{"type":"integer"}},"required":["contract_id","n"]}
```

### slim

instructions: 594 chars (~149 tokens, 84 words)

| tool | chars | ~tokens |
|---|---:|---:|
| (instructions) | 594 | 149 |
| dc_start | 401 | 101 |
| dc_get_symbol | 236 | 59 |
| dc_replace_symbol | 479 | 120 |
| dc_contract | 1553 | 389 |
| dc_find | 270 | 68 |
| TOTAL | 3543 | 886 |

```
Call dc_start(task) FIRST. Output is the exact current source of shown
symbols; do not re-read those files unless something was omitted.

Then dc_contract(action=create) before any Python edit. Edit with
dc_replace_symbol; its result includes contract status. dc_find looks up
symbols or (mode=references) call sites. dc_get_symbol loads one symbol;
include_body=true for source.

Fix every ✗. Amend or close via dc_contract. Hooks deny Python edits without
an active contract. Do not stop while the score is below 1.0. Names:
pkg.mod.Class.method or a unique suffix; @L<line> picks duplicates.
```

#### dc_start

```
dc_start
First call on a task. One response: repo size, compressed map,
slices for hint_symbols or best-matching names/docs, a contract
template, and a complete JSON example. On a small repo, skip
exploration and read files directly.
{"type":"object","properties":{"task":{"type":"string"},"hint_symbols":{"type":"array","items":{"type":"string"}},"max_tokens":{"type":"integer"}},"required":["task"]}
```

#### dc_get_symbol

```
dc_get_symbol
One symbol's signature, docstring, what it calls, who calls it, and
(with include_body=true) its exact source.
{"type":"object","properties":{"name":{"type":"string"},"include_body":{"type":"boolean"}},"required":["name"]}
```

#### dc_replace_symbol

```
dc_replace_symbol
Replace one function/method/class with `new_code` (its complete new
definition, decorators included; indentation is fixed automatically).
Rejected without changes if the file would not parse. Reports only
lint/type errors the edit introduced and callers a signature change
may break. Result includes contract status.
{"type":"object","properties":{"name":{"type":"string"},"new_code":{"type":"string"},"check":{"type":"boolean"}},"required":["name","new_code"]}
```

#### dc_contract

```
dc_contract
Create, amend, check, or close a delta contract. action is create | amend | check | close. create needs task, targets, must_change (must_preserve optional). amend, check, and close need contract_id; amend takes add_targets / add_must_change / add_must_preserve. Declare a delta contract before editing. `must_change` / `must_preserve` are JSON objects: {id, setup?, call, expect_old?, expect_new?}. Expect values are JSON objects: {"returns": "<repr>"} for a normalised return value, or {"raises": "ValueError"} for an exception class name. must_change probes require expect_new. Probe setup auto-imports each target (`from pkg.mod import func` or `from pkg.mod import Class` for a method). Returns the contract id, one line per probe, and the validation verdict. Full probe code is echoed only when validation fails. ✗ with a corrected example if a target does not resolve or expect_old does not match the baseline. A complete JSON example is in the dc_start response.
{"type":"object","properties":{"action":{"type":"string"},"task":{"type":"string"},"targets":{"type":"array","items":{"type":"string"}},"must_change":{"type":"array","items":{"type":"object"}},"must_preserve":{"type":"array","items":{"type":"object"}},"pytest_ids":{"type":"array","items":{"type":"string"}},"contract_id":{"type":"string"},"add_targets":{"type":"array","items":{"type":"string"}},"add_must_change":{"type":"array","items":{"type":"object"}},"add_must_preserve":{"type":"array","items":{"type":"object"}},"reason":{"type":"string"}},"required":["action"]}
```

#### dc_find

```
dc_find
Find symbols by (partial) name, or with mode=references every
resolved call site of a symbol (plus name-matched unresolved sites).
{"type":"object","properties":{"query":{"type":"string"},"mode":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}
```

### contracts

instructions: 367 chars (~92 tokens, 54 words)

| tool | chars | ~tokens |
|---|---:|---:|
| (instructions) | 367 | 92 |
| dc_contract | 1885 | 472 |
| dc_replace_symbol | 479 | 120 |
| TOTAL | 2735 | 684 |

```
Call dc_contract(action=create) before any Python edit. Use Read and Grep
for context.

Edit with dc_replace_symbol; its result includes contract status. Fix every
✗. Amend or close via dc_contract. Hooks deny Python edits without an
active contract. Do not stop while the score is below 1.0. Names:
pkg.mod.Class.method or a unique suffix; @L<line> picks duplicates.
```

#### dc_contract

```
dc_contract
Create, amend, check, or close a delta contract. action is create | amend | check | close. create needs task, targets, must_change (must_preserve optional). amend, check, and close need contract_id; amend takes add_targets / add_must_change / add_must_preserve. Declare a delta contract before editing. `must_change` / `must_preserve` are JSON objects: {id, setup?, call, expect_old?, expect_new?}. Expect values are JSON objects: {"returns": "<repr>"} for a normalised return value, or {"raises": "ValueError"} for an exception class name. must_change probes require expect_new. Probe setup auto-imports each target (`from pkg.mod import func` or `from pkg.mod import Class` for a method). Returns the contract id, one line per probe, and the validation verdict. Full probe code is echoed only when validation fails. ✗ with a corrected example if a target does not resolve or expect_old does not match the baseline. Example: {"action":"create","task":"reject zero charges","targets":["shop.billing.validate_amount"],"must_change":[{"id":"zero","setup":"from decimal import Decimal","call":"validate_amount(Decimal('0'))","expect_old":{"returns":"None"},"expect_new":{"raises":"ValueError"}}],"must_preserve":[{"id":"pos","setup":"from decimal import Decimal","call":"validate_amount(Decimal('5'))"}]}
{"type":"object","properties":{"action":{"type":"string"},"task":{"type":"string"},"targets":{"type":"array","items":{"type":"string"}},"must_change":{"type":"array","items":{"type":"object"}},"must_preserve":{"type":"array","items":{"type":"object"}},"pytest_ids":{"type":"array","items":{"type":"string"}},"contract_id":{"type":"string"},"add_targets":{"type":"array","items":{"type":"string"}},"add_must_change":{"type":"array","items":{"type":"object"}},"add_must_preserve":{"type":"array","items":{"type":"object"}},"reason":{"type":"string"}},"required":["action"]}
```

#### dc_replace_symbol

```
dc_replace_symbol
Replace one function/method/class with `new_code` (its complete new
definition, decorators included; indentation is fixed automatically).
Rejected without changes if the file would not parse. Reports only
lint/type errors the edit introduced and callers a signature change
may break. Result includes contract status.
{"type":"object","properties":{"name":{"type":"string"},"new_code":{"type":"string"},"check":{"type":"boolean"}},"required":["name","new_code"]}
```

Resolved rate is the fraction of runs where every hidden test passed. Other per-task numbers below are **medians over repetitions** (resolved rate per task is the mean of 0/1 over reps).

## Paired per-task (median over reps)

| task | resolved B | resolved L | regr B | regr L | tokens B | tokens L | cost B | cost L | time B | time L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mwaskom__seaborn-2848 | 0 | — | 0 | — | 188628.500 | — | $0.0769 | — | 52.008 | — |
| mwaskom__seaborn-2996 | 1 | — | 0 | — | 165186.500 | — | $0.0782 | — | 35.723 | — |
| pallets__flask-5014 | 0 | — | 57 | — | 75777.500 | — | $0.0292 | — | 7.567 | — |
| pallets__flask-5063 | 0 | — | 53 | — | 148457.500 | — | $0.0593 | — | 20.549 | — |
| pydata__xarray-6598 | 1 | — | 417 | — | 107071 | — | $0.0442 | — | 13.090 | — |
| pydata__xarray-6889 | 1 | — | 0 | — | 369821.500 | — | $0.1263 | — | 48.142 | — |
| pylint-dev__pylint-4398 | 0 | — | 62 | — | 211095 | — | $0.0949 | — | 38.000 | — |
| pylint-dev__pylint-6386 | 0.500 | — | 0 | — | 187961.500 | — | $0.0795 | — | 26.538 | — |
| pytest-dev__pytest-11160 | 0 | — | 47 | — | 74451.500 | — | $0.0414 | — | 13.106 | — |
| pytest-dev__pytest-11178 | 1 | — | 0 | — | 108903 | — | $0.0595 | — | 21.368 | — |
| sphinx-doc__sphinx-9459 | 0 | — | 0 | — | 355460.500 | — | $0.1213 | — | 50.642 | — |
| sphinx-doc__sphinx-9829 | 1 | — | 12 | — | 91856 | — | $0.0449 | — | 15.284 | — |

## Paired difference (impact-noreport − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the impact-noreport arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 12 | 0.0833 | 0.0000 | 0.2500 |
| hidden checks passed | 12 | 0.0833 | 0.0000 | 0.2500 |
| regressions | 12 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 12 | -9971.1667 | -39187.1250 | 17135.2083 |
| requests | 12 | -0.5833 | -2.5000 | 1.3333 |
| tokens/request | 12 | 229.9738 | -389.6102 | 880.0044 |
| cost (USD) | 12 | -0.0005 | -0.0076 | 0.0065 |
| wall time (s) | 12 | -0.7752 | -5.2157 | 3.4540 |
| read chars | 12 | 421.0000 | -656.4167 | 2017.9583 |
| read calls | 12 | -0.0417 | -0.8333 | 0.6667 |
| dc-engine calls | 12 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 12 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 12 | 0.0000 | 0.0000 | 0.0000 |
| turns | 12 | -0.5833 | -1.8750 | 0.7500 |
