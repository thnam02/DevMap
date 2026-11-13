# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 87f8ac63846d | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 60 |

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 6 | 45% | 50.550 | 13721930 | 13976.336 | 3813.6 | 23 | 0 | 0 | 0 |
| gate-full | 20 | 6 | 47% | 79.350 | 34208637 | 20808.428 | 4512.7 | 27 | 0 | 0 | 0 |
| gate-proviso | 20 | 4 | 45% | 78.200 | 29257059 | 20604.929 | 4338.6 | 15 | 0 | 0 | 0 |

## Tool result sizes

Size of the result text returned to the agent for each completed tool call (chars, ~tokens = chars/4). MCP calls are grouped by dc-engine tool name. Totals are summed over the runs below (including contaminated).

### baseline

Total returned chars: **571893** (~142974 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 513322 | 128331 |
| Read | 34186 | 8547 |
| Edit | 10195 | 2549 |
| Grep | 8510 | 2128 |
| Monitor | 5561 | 1391 |
| bash | 119 | 30 |

### gate-full

Total returned chars: **643886** (~160972 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 582378 | 145595 |
| Read | 26955 | 6739 |
| Grep | 19178 | 4795 |
| Edit | 14923 | 3731 |
| Write | 452 | 113 |

### gate-proviso

Total returned chars: **637849** (~159463 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 600760 | 150190 |
| Read | 17179 | 4295 |
| Edit | 12444 | 3111 |
| Grep | 4507 | 1127 |
| Monitor | 2353 | 589 |
| TaskStop | 373 | 94 |
| ScheduleWakeup | 233 | 59 |
| ToolSearch | 0 | 0 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 55 | 1045680.000 | 19012.364 |
| mwaskom__seaborn-2813__c0 | gate-proviso | 1 | 51 | 964271 | 18907.275 |
| mwaskom__seaborn-2813__c0 | gate-full | 1 | 72 | 1392832.000 | 19344.889 |
| mwaskom__seaborn-2846__c0 | gate-proviso | 1 | 57 | 994697 | 17450.825 |
| mwaskom__seaborn-2846__c0 | gate-full | 1 | 62 | 1360985.000 | 21951.371 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 74 | 1361397.000 | 18397.257 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 51 | 723561 | 14187.471 |
| mwaskom__seaborn-2846__c1 | gate-full | 1 | 77 | 1731642.000 | 22488.857 |
| mwaskom__seaborn-2846__c1 | gate-proviso | 1 | 56 | 1336428.000 | 23864.786 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 55 | 765637 | 13920.673 |
| mwaskom__seaborn-2848__c0 | gate-proviso | 1 | 111 | 2097741.000 | 18898.568 |
| mwaskom__seaborn-2848__c0 | gate-full | 1 | 63 | 1051503.000 | 16690.524 |
| pydata__xarray-4759__c0 | baseline | 1 | 141 | 89166 | 632.383 |
| pydata__xarray-4759__c0 | gate-proviso | 1 | 97 | 2872203.000 | 29610.340 |
| pydata__xarray-4759__c0 | gate-full | 1 | 137 | 3288856.000 | 24006.248 |
| pydata__xarray-4759__c1 | gate-full | 1 | 75 | 1515837.000 | 20211.160 |
| pydata__xarray-4759__c1 | baseline | 1 | 35 | 444291 | 12694.029 |
| pydata__xarray-4759__c1 | gate-proviso | 1 | 282 | 1383129.000 | 4904.713 |
| pydata__xarray-4759__c2 | gate-full | 1 | 147 | 3626620.000 | 24670.884 |
| pydata__xarray-4759__c2 | baseline | 1 | 40 | 562639 | 14065.975 |
| pydata__xarray-4759__c2 | gate-proviso | 1 | 70 | 1680220.000 | 24003.143 |
| pydata__xarray-4759__c3 | gate-proviso | 1 | 72 | 1908305.000 | 26504.236 |
| pydata__xarray-4759__c3 | baseline | 1 | 85 | 2015104.000 | 23707.106 |
| pydata__xarray-4759__c3 | gate-full | 1 | 115 | 2951079.000 | 25661.557 |
| pylint-dev__pylint-4339__c1 | gate-proviso | 1 | 42 | 696559 | 16584.738 |
| pylint-dev__pylint-4339__c1 | gate-full | 1 | 55 | 1023383.000 | 18606.964 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 34 | 394139 | 11592.324 |
| pylint-dev__pylint-4339__c2 | gate-full | 1 | 61 | 1053786.000 | 17275.180 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 29 | 356891 | 12306.586 |
| pylint-dev__pylint-4339__c2 | gate-proviso | 1 | 72 | 1860124.000 | 25835.056 |
| pylint-dev__pylint-4339__c3 | gate-proviso | 1 | 57 | 1076802.000 | 18891.263 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 53 | 891853 | 16827.415 |
| pylint-dev__pylint-4339__c3 | gate-full | 1 | 63 | 1089328.000 | 17290.921 |
| pylint-dev__pylint-4492__c1 | gate-full | 1 | 89 | 2273178.000 | 25541.326 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 71 | 1081578.000 | 15233.493 |
| pylint-dev__pylint-4492__c1 | gate-proviso | 1 | 76 | 1515104.000 | 19935.579 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 28 | 280113 | 10004.036 |
| pytest-dev__pytest-11148__c0 | gate-full | 1 | 74 | 1530304.000 | 20679.784 |
| pytest-dev__pytest-11148__c0 | gate-proviso | 1 | 49 | 716964 | 14631.918 |
| pytest-dev__pytest-11148__c2 | gate-proviso | 1 | 79 | 1922574.000 | 24336.380 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 53 | 747183 | 14097.792 |
| pytest-dev__pytest-11148__c2 | gate-full | 1 | 79 | 1600928.000 | 20264.911 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 29 | 303981 | 10482.103 |
| pytest-dev__pytest-11148__c3 | gate-proviso | 1 | 89 | 1623844.000 | 18245.438 |
| pytest-dev__pytest-11148__c3 | gate-full | 1 | 68 | 1480780.000 | 21776.176 |
| pytest-dev__pytest-11148__c4 | gate-proviso | 1 | 73 | 1415596.000 | 19391.726 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 38 | 539679 | 14202.079 |
| pytest-dev__pytest-11148__c4 | gate-full | 1 | 99 | 2459190.000 | 24840.303 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 50 | 775618 | 15512.360 |
| sphinx-doc__sphinx-10021__c0 | gate-full | 1 | 67 | 1222240.000 | 18242.388 |
| sphinx-doc__sphinx-10021__c0 | gate-proviso | 1 | 55 | 1290533.000 | 23464.236 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 31 | 339435 | 10949.516 |
| sphinx-doc__sphinx-10021__c1 | gate-proviso | 1 | 65 | 1320551.000 | 20316.169 |
| sphinx-doc__sphinx-10021__c1 | gate-full | 1 | 76 | 1618957.000 | 21302.066 |
| sphinx-doc__sphinx-10137__c1 | gate-full | 1 | 43 | 701269 | 16308.581 |
| sphinx-doc__sphinx-10137__c1 | gate-proviso | 1 | 49 | 1095195.000 | 22350.918 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 20 | 244614 | 12230.700 |
| sphinx-doc__sphinx-10207__c1 | gate-proviso | 1 | 62 | 1486219.000 | 23971.274 |
| sphinx-doc__sphinx-10207__c1 | gate-full | 1 | 65 | 1235940.000 | 19014.462 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 39 | 759371 | 19471.051 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 50.550 | 686096.500 | 13976.336 |
| gate-full | 79.350 | 1710431.850 | 20808.428 |
| gate-proviso | 78.200 | 1462852.950 | 20604.929 |

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
| mwaskom__seaborn-2813__c0 | 1 | — | 0 | — | 1045680.000 | — | $0.0241 | — | 250.772 | — |
| mwaskom__seaborn-2846__c0 | 1 | — | 0 | — | 1361397.000 | — | $0.0286 | — | 579.073 | — |
| mwaskom__seaborn-2846__c1 | 1 | — | 0 | — | 723561 | — | $0.0207 | — | 291.572 | — |
| mwaskom__seaborn-2848__c0 | 0 | — | 0 | — | 765637 | — | $0.0186 | — | 341.072 | — |
| pydata__xarray-4759__c0 | 0 | — | 0 | — | 89166 | — | $0.0784 | — | 722.460 | — |
| pydata__xarray-4759__c1 | 0 | — | 0 | — | 444291 | — | $0.0141 | — | 113.178 | — |
| pydata__xarray-4759__c2 | 0 | — | 0 | — | 562639 | — | $0.0141 | — | 117.354 | — |
| pydata__xarray-4759__c3 | 0 | — | 0 | — | 2015104.000 | — | $0.0454 | — | 499.675 | — |
| pylint-dev__pylint-4339__c1 | 1 | — | 1 | — | 394139 | — | $0.0097 | — | 60.404 | — |
| pylint-dev__pylint-4339__c2 | 0 | — | 0 | — | 356891 | — | $0.0103 | — | 51.937 | — |
| pylint-dev__pylint-4339__c3 | 0 | — | 0 | — | 891853 | — | $0.0198 | — | 112.919 | — |
| pylint-dev__pylint-4492__c1 | 0 | — | 0 | — | 1081578.000 | — | $0.0277 | — | 143.361 | — |
| pytest-dev__pytest-11148__c0 | 1 | — | 0 | — | 280113 | — | $0.0082 | — | 44.652 | — |
| pytest-dev__pytest-11148__c2 | 0 | — | 0 | — | 747183 | — | $0.0198 | — | 98.303 | — |
| pytest-dev__pytest-11148__c3 | 0 | — | 0 | — | 303981 | — | $0.0121 | — | 64.505 | — |
| pytest-dev__pytest-11148__c4 | 0 | — | 0 | — | 539679 | — | $0.0145 | — | 87.141 | — |
| sphinx-doc__sphinx-10021__c0 | 0 | — | 0 | — | 775618 | — | $0.0183 | — | 81.797 | — |
| sphinx-doc__sphinx-10021__c1 | 0 | — | 0 | — | 339435 | — | $0.0104 | — | 50.953 | — |
| sphinx-doc__sphinx-10137__c1 | 1 | — | 0 | — | 244614 | — | $0.0068 | — | 27.845 | — |
| sphinx-doc__sphinx-10207__c1 | 0 | — | 0 | — | 759371 | — | $0.0175 | — | 74.602 | — |

## Paired difference (gate-full − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-full arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | 0.0000 | -0.1500 | 0.1500 |
| hidden checks passed | 20 | 0.0263 | -0.1237 | 0.1763 |
| regressions | 20 | 3.6500 | 0.0000 | 10.9500 |
| tokens (all-in, incl. cache) | 20 | 1024335.3500 | 688976.5500 | 1408688.0000 |
| requests | 20 | 28.8000 | 18.8500 | 40.4000 |
| tokens/request | 20 | 6832.0920 | 4619.8974 | 9298.8453 |
| cost (USD) | 20 | 0.0119 | 0.0066 | 0.0180 |
| wall time (s) | 20 | 34.9564 | -33.4504 | 89.7000 |
| read chars | 20 | -361.5500 | -2187.2500 | 1520.8000 |
| read calls | 20 | 0.2000 | -1.1000 | 1.3500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 19.9000 | 14.3000 | 26.3500 |

## Paired difference (gate-proviso − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-proviso arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | -0.1000 | -0.2500 | 0.0000 |
| hidden checks passed | 20 | 0.0031 | -0.0886 | 0.0947 |
| regressions | 20 | 3.6500 | 0.0000 | 10.9500 |
| tokens (all-in, incl. cache) | 20 | 776756.4500 | 494553.3000 | 1080766.3000 |
| requests | 20 | 27.6500 | 7.9000 | 55.7000 |
| tokens/request | 20 | 6628.5934 | 3795.7634 | 9821.8971 |
| cost (USD) | 20 | 0.0447 | 0.0032 | 0.1229 |
| wall time (s) | 20 | 26.2517 | -56.2747 | 114.1146 |
| read chars | 20 | -850.3500 | -3192.0500 | 1181.6000 |
| read calls | 20 | -0.4000 | -1.7000 | 0.6500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 15.3500 | 9.7500 | 21.4500 |
