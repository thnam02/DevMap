# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 87f8ac63846d | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 60 |

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 9 | 64% | 17.450 | 5702464 | 15479.244 | 1841.7 | 0 | 0 | 0 | 0 |
| gate-full | 20 | 7 | 55% | 24.150 | 10502477 | 21075.361 | 1565.5 | 1 | 0 | 0 | 0 |
| gate-proviso | 20 | 7 | 56% | 29.350 | 13043465 | 21160.954 | 2700.9 | 0 | 0 | 0 | 0 |

## Tool result sizes

Size of the result text returned to the agent for each completed tool call (chars, ~tokens = chars/4). MCP calls are grouped by dc-engine tool name. Totals are summed over the runs below (including contaminated).

### baseline

Total returned chars: **317904** (~79476 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 317131 | 79283 |
| bash | 476 | 119 |
| Edit | 297 | 75 |

### gate-full

Total returned chars: **287815** (~71954 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 285322 | 71331 |
| Read | 1100 | 275 |
| bash | 714 | 179 |
| Edit | 459 | 115 |
| Write | 220 | 55 |

### gate-proviso

Total returned chars: **343022** (~85756 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 340474 | 85119 |
| Edit | 1730 | 433 |
| bash | 595 | 149 |
| Write | 223 | 56 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 15 | 207675 | 13845 |
| mwaskom__seaborn-2813__c0 | gate-proviso | 1 | 19 | 344052 | 18108 |
| mwaskom__seaborn-2813__c0 | gate-full | 1 | 17 | 322241 | 18955.353 |
| mwaskom__seaborn-2846__c0 | gate-proviso | 1 | 17 | 379126 | 22301.529 |
| mwaskom__seaborn-2846__c0 | gate-full | 1 | 17 | 344466 | 20262.706 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 16 | 212218 | 13263.625 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 9 | 135903 | 15100.333 |
| mwaskom__seaborn-2846__c1 | gate-full | 1 | 19 | 386765 | 20356.053 |
| mwaskom__seaborn-2846__c1 | gate-proviso | 1 | 19 | 366444 | 19286.526 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 19 | 275961 | 14524.263 |
| mwaskom__seaborn-2848__c0 | gate-proviso | 1 | 30 | 580893 | 19363.100 |
| mwaskom__seaborn-2848__c0 | gate-full | 1 | 31 | 593221 | 19136.161 |
| pydata__xarray-4759__c0 | baseline | 1 | 38 | 594295 | 15639.342 |
| pydata__xarray-4759__c0 | gate-proviso | 1 | 67 | 1609550.000 | 24023.134 |
| pydata__xarray-4759__c0 | gate-full | 1 | 61 | 1496181.000 | 24527.557 |
| pydata__xarray-4759__c1 | gate-full | 1 | 53 | 1222503.000 | 23066.094 |
| pydata__xarray-4759__c1 | baseline | 1 | 46 | 878980 | 19108.261 |
| pydata__xarray-4759__c1 | gate-proviso | 1 | 61 | 1373701.000 | 22519.689 |
| pydata__xarray-4759__c2 | gate-full | 1 | 24 | 473458 | 19727.417 |
| pydata__xarray-4759__c2 | baseline | 1 | 35 | 608196 | 17377.029 |
| pydata__xarray-4759__c2 | gate-proviso | 1 | 81 | 2144886.000 | 26480.074 |
| pydata__xarray-4759__c3 | gate-proviso | 1 | 58 | 1425504.000 | 24577.655 |
| pydata__xarray-4759__c3 | baseline | 1 | 40 | 791137 | 19778.425 |
| pydata__xarray-4759__c3 | gate-full | 1 | 43 | 1138390.000 | 26474.186 |
| pylint-dev__pylint-4339__c1 | gate-proviso | 1 | 16 | 321791 | 20111.938 |
| pylint-dev__pylint-4339__c1 | gate-full | 1 | 16 | 320525 | 20032.812 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 12 | 188172 | 15681 |
| pylint-dev__pylint-4339__c2 | gate-full | 1 | 15 | 303807 | 20253.800 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 8 | 115034 | 14379.250 |
| pylint-dev__pylint-4339__c2 | gate-proviso | 1 | 18 | 362936 | 20163.111 |
| pylint-dev__pylint-4339__c3 | gate-proviso | 1 | 22 | 482518 | 21932.636 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 8 | 116834 | 14604.250 |
| pylint-dev__pylint-4339__c3 | gate-full | 1 | 18 | 377174 | 20954.111 |
| pylint-dev__pylint-4492__c1 | gate-full | 1 | 26 | 568985 | 21884.038 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 22 | 379799 | 17263.591 |
| pylint-dev__pylint-4492__c1 | gate-proviso | 1 | 34 | 704301 | 20714.735 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 10 | 138430 | 13843 |
| pytest-dev__pytest-11148__c0 | gate-full | 1 | 20 | 371517 | 18575.850 |
| pytest-dev__pytest-11148__c0 | gate-proviso | 1 | 15 | 313481 | 20898.733 |
| pytest-dev__pytest-11148__c2 | gate-proviso | 1 | 17 | 353793 | 20811.353 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 7 | 112355 | 16050.714 |
| pytest-dev__pytest-11148__c2 | gate-full | 1 | 17 | 360136 | 21184.471 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 10 | 157953 | 15795.300 |
| pytest-dev__pytest-11148__c3 | gate-proviso | 1 | 22 | 431343 | 19606.500 |
| pytest-dev__pytest-11148__c3 | gate-full | 1 | 19 | 383641 | 20191.632 |
| pytest-dev__pytest-11148__c4 | gate-proviso | 1 | 17 | 355317 | 20901 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 10 | 138646 | 13864.600 |
| pytest-dev__pytest-11148__c4 | gate-full | 1 | 18 | 348406 | 19355.889 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 10 | 173764 | 17376.400 |
| sphinx-doc__sphinx-10021__c0 | gate-full | 1 | 18 | 390111 | 21672.833 |
| sphinx-doc__sphinx-10021__c0 | gate-proviso | 1 | 18 | 389172 | 21620.667 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 19 | 264758 | 13934.632 |
| sphinx-doc__sphinx-10021__c1 | gate-proviso | 1 | 24 | 443633 | 18484.708 |
| sphinx-doc__sphinx-10021__c1 | gate-full | 1 | 19 | 437742 | 23039.053 |
| sphinx-doc__sphinx-10137__c1 | gate-full | 1 | 18 | 347432 | 19301.778 |
| sphinx-doc__sphinx-10137__c1 | gate-proviso | 1 | 16 | 314274 | 19642.125 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 8 | 122103 | 15262.875 |
| sphinx-doc__sphinx-10207__c1 | gate-proviso | 1 | 16 | 346750 | 21671.875 |
| sphinx-doc__sphinx-10207__c1 | gate-full | 1 | 14 | 315776 | 22555.429 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 7 | 90251 | 12893 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 17.450 | 285123.200 | 15479.244 |
| gate-full | 24.150 | 525123.850 | 21075.361 |
| gate-proviso | 29.350 | 652173.250 | 21160.954 |

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
| mwaskom__seaborn-2813__c0 | 1 | — | 0 | — | 207675 | — | $0.0831 | — | 118.819 | — |
| mwaskom__seaborn-2846__c0 | 1 | — | 0 | — | 212218 | — | $0.0805 | — | 88.633 | — |
| mwaskom__seaborn-2846__c1 | 1 | — | 0 | — | 135903 | — | $0.0603 | — | 39.114 | — |
| mwaskom__seaborn-2848__c0 | 1 | — | 0 | — | 275961 | — | $0.1015 | — | 119.371 | — |
| pydata__xarray-4759__c0 | 0 | — | 0 | — | 594295 | — | $0.1922 | — | 179.266 | — |
| pydata__xarray-4759__c1 | 0 | — | 0 | — | 878980 | — | $0.2652 | — | 305.267 | — |
| pydata__xarray-4759__c2 | 0 | — | 0 | — | 608196 | — | $0.1900 | — | 179.241 | — |
| pydata__xarray-4759__c3 | 0 | — | 0 | — | 791137 | — | $0.3246 | — | 487.566 | — |
| pylint-dev__pylint-4339__c1 | 1 | — | 1 | — | 188172 | — | $0.0702 | — | 22.510 | — |
| pylint-dev__pylint-4339__c2 | 1 | — | 1 | — | 115034 | — | $0.0590 | — | 18.365 | — |
| pylint-dev__pylint-4339__c3 | 0 | — | 0 | — | 116834 | — | $0.0606 | — | 23.131 | — |
| pylint-dev__pylint-4492__c1 | 0 | — | 0 | — | 379799 | — | $0.1262 | — | 60.431 | — |
| pytest-dev__pytest-11148__c0 | 1 | — | 0 | — | 138430 | — | $0.0599 | — | 26.731 | — |
| pytest-dev__pytest-11148__c2 | 1 | — | 0 | — | 112355 | — | $0.0543 | — | 21.354 | — |
| pytest-dev__pytest-11148__c3 | 0 | — | 73 | — | 157953 | — | $0.0600 | — | 22.532 | — |
| pytest-dev__pytest-11148__c4 | 1 | — | 0 | — | 138646 | — | $0.0587 | — | 23.546 | — |
| sphinx-doc__sphinx-10021__c0 | 0 | — | 0 | — | 173764 | — | $0.0728 | — | 26.729 | — |
| sphinx-doc__sphinx-10021__c1 | 0 | — | 0 | — | 264758 | — | $0.0954 | — | 44.859 | — |
| sphinx-doc__sphinx-10137__c1 | 0 | — | 0 | — | 122103 | — | $0.0426 | — | 18.672 | — |
| sphinx-doc__sphinx-10207__c1 | 0 | — | 0 | — | 90251 | — | $0.0486 | — | 15.584 | — |

## Paired difference (gate-full − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-full arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | -0.1000 | -0.2500 | 0.0000 |
| hidden checks passed | 20 | -0.0851 | -0.2096 | 0.0079 |
| regressions | 20 | -0.0500 | -0.1500 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 240000.6500 | 168387.9000 | 326754.4000 |
| requests | 20 | 6.7000 | 3.8500 | 9.4000 |
| tokens/request | 20 | 5596.1166 | 4828.0715 | 6429.0563 |
| cost (USD) | 20 | 0.0503 | 0.0332 | 0.0684 |
| wall time (s) | 20 | -13.8121 | -56.3170 | 15.6543 |
| read chars | 20 | 55.0000 | 0.0000 | 165.0000 |
| read calls | 20 | 0.0500 | 0.0000 | 0.1500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 8.5000 | 6.8000 | 10.2500 |

## Paired difference (gate-proviso − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-proviso arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | -0.1000 | -0.2500 | 0.0000 |
| hidden checks passed | 20 | -0.0727 | -0.1917 | 0.0071 |
| regressions | 20 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 367050.0500 | 241644.7000 | 531271.7500 |
| requests | 20 | 11.9000 | 8.2000 | 16.6500 |
| tokens/request | 20 | 5681.7100 | 4882.9022 | 6545.8873 |
| cost (USD) | 20 | 0.0790 | 0.0561 | 0.1100 |
| wall time (s) | 20 | 42.9577 | 7.9115 | 87.4462 |
| read chars | 20 | 0.0000 | 0.0000 | 0.0000 |
| read calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 11.3000 | 9.0500 | 14.1000 |
