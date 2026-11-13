# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 3daf84345989 | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 40 |

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 6 | 53% | 51.850 | 14352921 | 14527.980 | 3188.5 | 8 | 0 | 0 | 0 |
| impact-noreport | 20 | 7 | 49% | 56.800 | 19179510 | 15739.043 | 3216.9 | 20 | 0 | 0 | 0 |

## Tool result sizes

Size of the result text returned to the agent for each completed tool call (chars, ~tokens = chars/4). MCP calls are grouped by dc-engine tool name. Totals are summed over the runs below (including contaminated).

### baseline

Total returned chars: **586430** (~146608 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 561020 | 140255 |
| Edit | 11495 | 2874 |
| Read | 8403 | 2101 |
| Grep | 3760 | 940 |
| Write | 673 | 169 |
| ScheduleWakeup | 466 | 117 |
| Monitor | 375 | 94 |
| bash | 238 | 60 |

### impact-noreport

Total returned chars: **701496** (~175374 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 640326 | 160082 |
| Read | 28802 | 7201 |
| Grep | 16086 | 4022 |
| Edit | 15511 | 3878 |
| Write | 454 | 114 |
| Glob | 317 | 80 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 53 | 813649 | 15351.868 |
| mwaskom__seaborn-2813__c0 | impact-noreport | 1 | 64 | 836766 | 13074.469 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 36 | 635269 | 17646.361 |
| mwaskom__seaborn-2846__c0 | impact-noreport | 1 | 38 | 539078 | 14186.263 |
| mwaskom__seaborn-2846__c1 | impact-noreport | 1 | 50 | 654130 | 13082.600 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 48 | 1012397.000 | 21091.604 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 59 | 937740 | 15893.898 |
| mwaskom__seaborn-2848__c0 | impact-noreport | 1 | 37 | 410319 | 11089.703 |
| pydata__xarray-4759__c0 | baseline | 1 | 77 | 1438275.000 | 18678.896 |
| pydata__xarray-4759__c0 | impact-noreport | 1 | 78 | 1543221.000 | 19784.885 |
| pydata__xarray-4759__c1 | baseline | 1 | 49 | 686442 | 14009.020 |
| pydata__xarray-4759__c1 | impact-noreport | 1 | 59 | 853707 | 14469.610 |
| pydata__xarray-4759__c2 | baseline | 1 | 79 | 1391014.000 | 17607.772 |
| pydata__xarray-4759__c2 | impact-noreport | 1 | 82 | 1488376.000 | 18150.927 |
| pydata__xarray-4759__c3 | baseline | 1 | 136 | 193637 | 1423.801 |
| pydata__xarray-4759__c3 | impact-noreport | 1 | 116 | 2559214.000 | 22062.190 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 34 | 340514 | 10015.118 |
| pylint-dev__pylint-4339__c1 | impact-noreport | 1 | 28 | 367492 | 13124.714 |
| pylint-dev__pylint-4339__c2 | impact-noreport | 1 | 69 | 1223168.000 | 17727.072 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 32 | 471869 | 14745.906 |
| pylint-dev__pylint-4339__c3 | impact-noreport | 1 | 65 | 1238904.000 | 19060.062 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 43 | 532384 | 12381.023 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 63 | 1014806.000 | 16108.032 |
| pylint-dev__pylint-4492__c1 | impact-noreport | 1 | 87 | 1664393.000 | 19130.954 |
| pytest-dev__pytest-11148__c0 | impact-noreport | 1 | 29 | 309271 | 10664.517 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 66 | 993478 | 15052.697 |
| pytest-dev__pytest-11148__c2 | impact-noreport | 1 | 67 | 1279138.000 | 19091.612 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 53 | 922177 | 17399.566 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 14 | 194074 | 13862.429 |
| pytest-dev__pytest-11148__c3 | impact-noreport | 1 | 20 | 288105 | 14405.250 |
| pytest-dev__pytest-11148__c4 | impact-noreport | 1 | 101 | 1756307.000 | 17389.178 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 28 | 331351 | 11833.964 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 49 | 820093 | 16736.592 |
| sphinx-doc__sphinx-10021__c0 | impact-noreport | 1 | 53 | 863522 | 16292.868 |
| sphinx-doc__sphinx-10021__c1 | impact-noreport | 1 | 41 | 564944 | 13779.122 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 48 | 732979 | 15270.396 |
| sphinx-doc__sphinx-10137__c1 | impact-noreport | 1 | 25 | 279327 | 11173.080 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 35 | 449449 | 12841.400 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 35 | 441324 | 12609.257 |
| sphinx-doc__sphinx-10207__c1 | impact-noreport | 1 | 27 | 460128 | 17041.778 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 51.850 | 717646.050 | 14527.980 |
| impact-noreport | 56.800 | 958975.500 | 15739.043 |

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
| mwaskom__seaborn-2813__c0 | 0 | — | 0 | — | 813649 | — | $0.0186 | — | 364.043 | — |
| mwaskom__seaborn-2846__c0 | 1 | — | 0 | — | 635269 | — | $0.0147 | — | 108.761 | — |
| mwaskom__seaborn-2846__c1 | 0 | — | 0 | — | 1012397.000 | — | $0.0225 | — | 158.143 | — |
| mwaskom__seaborn-2848__c0 | 0 | — | 0 | — | 937740 | — | $0.0198 | — | 218.908 | — |
| pydata__xarray-4759__c0 | 0 | — | 0 | — | 1438275.000 | — | $0.0295 | — | 226.886 | — |
| pydata__xarray-4759__c1 | 0 | — | 0 | — | 686442 | — | $0.0164 | — | 126.012 | — |
| pydata__xarray-4759__c2 | 0 | — | 0 | — | 1391014.000 | — | $0.0313 | — | 247.801 | — |
| pydata__xarray-4759__c3 | 0 | — | 0 | — | 193637 | — | $0.0754 | — | 630.270 | — |
| pylint-dev__pylint-4339__c1 | 1 | — | 1 | — | 340514 | — | $0.0083 | — | 44.834 | — |
| pylint-dev__pylint-4339__c2 | 1 | — | 0 | — | 471869 | — | $0.0125 | — | 71.534 | — |
| pylint-dev__pylint-4339__c3 | 0 | — | 0 | — | 532384 | — | $0.0152 | — | 93.206 | — |
| pylint-dev__pylint-4492__c1 | 0 | — | 0 | — | 1014806.000 | — | $0.0276 | — | 155.624 | — |
| pytest-dev__pytest-11148__c0 | 1 | — | 0 | — | 993478 | — | $0.0263 | — | 222.744 | — |
| pytest-dev__pytest-11148__c2 | 1 | — | 0 | — | 922177 | — | $0.0216 | — | 142.244 | — |
| pytest-dev__pytest-11148__c3 | 0 | — | 73 | — | 194074 | — | $0.0085 | — | 44.381 | — |
| pytest-dev__pytest-11148__c4 | 0 | — | 0 | — | 331351 | — | $0.0113 | — | 67.004 | — |
| sphinx-doc__sphinx-10021__c0 | 0 | — | 0 | — | 820093 | — | $0.0191 | — | 78.766 | — |
| sphinx-doc__sphinx-10021__c1 | 0 | — | 0 | — | 732979 | — | $0.0180 | — | 79.078 | — |
| sphinx-doc__sphinx-10137__c1 | 1 | — | 0 | — | 449449 | — | $0.0097 | — | 46.124 | — |
| sphinx-doc__sphinx-10207__c1 | 0 | — | 0 | — | 441324 | — | $0.0130 | — | 62.108 | — |

## Paired difference (impact-noreport − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the impact-noreport arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | 0.0500 | -0.1500 | 0.2500 |
| hidden checks passed | 20 | -0.0333 | -0.2009 | 0.1114 |
| regressions | 20 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 241329.4500 | -26825.0000 | 558052.0500 |
| requests | 20 | 4.9500 | -4.4500 | 15.5000 |
| tokens/request | 20 | 1211.0626 | -1105.1314 | 3924.2644 |
| cost (USD) | 20 | 0.0009 | -0.0037 | 0.0052 |
| wall time (s) | 20 | 1.4208 | -62.7182 | 62.8854 |
| read chars | 20 | 1019.9500 | -202.9000 | 2489.4500 |
| read calls | 20 | 0.6000 | -0.2500 | 1.7000 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 4.4000 | -1.1500 | 11.3000 |
