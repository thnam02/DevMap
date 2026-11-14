# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 87f8ac63846d | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 20 |
| e2552e8e6da3 | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 40 |

**Warning:** this comparison mixes dc-engine versions (commits: 87f8ac63846dfc9e2a2f2a02c7e4080b84579c16, e2552e8e6da386bd0f43caafeb82169eefa099c3). Do not treat arm differences as an ablation of one engine.

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 6 | 45% | 50.550 | 13721930 | 13976.336 | 3813.6 | 23 | 0 | 0 | 0 |
| gate-full | 20 | 7 | 50% | 57.300 | 19438241 | 15550.561 | 6981.1 | 2 | 0 | 0 | 0 |
| gate-proviso | 20 | 7 | 52% | 52.900 | 18485719 | 15848.480 | 5179.8 | 7 | 0 | 0 | 0 |

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

Total returned chars: **608172** (~152043 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 595620 | 148905 |
| Edit | 11248 | 2812 |
| Read | 781 | 196 |
| bash | 238 | 60 |
| Write | 226 | 57 |
| Grep | 59 | 15 |

### gate-proviso

Total returned chars: **568452** (~142113 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 530441 | 132611 |
| Read | 25168 | 6292 |
| Edit | 11490 | 2873 |
| Monitor | 1005 | 252 |
| Write | 229 | 58 |
| bash | 119 | 30 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 55 | 1045680.000 | 19012.364 |
| mwaskom__seaborn-2813__c0 | gate-proviso | 1 | 50 | 831370 | 16627.400 |
| mwaskom__seaborn-2813__c0 | gate-full | 1 | 46 | 602246 | 13092.304 |
| mwaskom__seaborn-2846__c0 | gate-proviso | 1 | 36 | 567891 | 15774.750 |
| mwaskom__seaborn-2846__c0 | gate-full | 1 | 55 | 728838 | 13251.600 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 74 | 1361397.000 | 18397.257 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 51 | 723561 | 14187.471 |
| mwaskom__seaborn-2846__c1 | gate-full | 1 | 53 | 808662 | 15257.774 |
| mwaskom__seaborn-2846__c1 | gate-proviso | 1 | 45 | 886236 | 19694.133 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 55 | 765637 | 13920.673 |
| mwaskom__seaborn-2848__c0 | gate-proviso | 1 | 73 | 1045581.000 | 14323.027 |
| mwaskom__seaborn-2848__c0 | gate-full | 1 | 59 | 830998 | 14084.712 |
| pydata__xarray-4759__c0 | baseline | 1 | 141 | 89166 | 632.383 |
| pydata__xarray-4759__c0 | gate-proviso | 1 | 144 | 3999347.000 | 27773.243 |
| pydata__xarray-4759__c0 | gate-full | 1 | 133 | 3102907.000 | 23330.128 |
| pydata__xarray-4759__c1 | gate-full | 1 | 41 | 549056 | 13391.610 |
| pydata__xarray-4759__c1 | baseline | 1 | 35 | 444291 | 12694.029 |
| pydata__xarray-4759__c1 | gate-proviso | 1 | 54 | 775396 | 14359.185 |
| pydata__xarray-4759__c2 | gate-full | 1 | 99 | 1694397.000 | 17115.121 |
| pydata__xarray-4759__c2 | baseline | 1 | 40 | 562639 | 14065.975 |
| pydata__xarray-4759__c2 | gate-proviso | 1 | 78 | 1132638.000 | 14521 |
| pydata__xarray-4759__c3 | gate-proviso | 1 | 100 | 2071728.000 | 20717.280 |
| pydata__xarray-4759__c3 | baseline | 1 | 85 | 2015104.000 | 23707.106 |
| pydata__xarray-4759__c3 | gate-full | 1 | 111 | 2518321.000 | 22687.577 |
| pylint-dev__pylint-4339__c1 | gate-proviso | 1 | 24 | 365252 | 15218.833 |
| pylint-dev__pylint-4339__c1 | gate-full | 1 | 23 | 255488 | 11108.174 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 34 | 394139 | 11592.324 |
| pylint-dev__pylint-4339__c2 | gate-full | 1 | 35 | 630722 | 18020.629 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 29 | 356891 | 12306.586 |
| pylint-dev__pylint-4339__c2 | gate-proviso | 1 | 36 | 494832 | 13745.333 |
| pylint-dev__pylint-4339__c3 | gate-proviso | 1 | 40 | 659654 | 16491.350 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 53 | 891853 | 16827.415 |
| pylint-dev__pylint-4339__c3 | gate-full | 1 | 43 | 485256 | 11285.023 |
| pylint-dev__pylint-4492__c1 | gate-full | 1 | 57 | 1103930.000 | 19367.193 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 71 | 1081578.000 | 15233.493 |
| pylint-dev__pylint-4492__c1 | gate-proviso | 1 | 74 | 1381800.000 | 18672.973 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 28 | 280113 | 10004.036 |
| pytest-dev__pytest-11148__c0 | gate-full | 1 | 59 | 807208 | 13681.492 |
| pytest-dev__pytest-11148__c0 | gate-proviso | 1 | 51 | 973585 | 19089.902 |
| pytest-dev__pytest-11148__c2 | gate-proviso | 1 | 51 | 765984 | 15019.294 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 53 | 747183 | 14097.792 |
| pytest-dev__pytest-11148__c2 | gate-full | 1 | 52 | 874193 | 16811.404 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 29 | 303981 | 10482.103 |
| pytest-dev__pytest-11148__c3 | gate-proviso | 1 | 62 | 776231 | 12519.855 |
| pytest-dev__pytest-11148__c3 | gate-full | 1 | 61 | 1188997.000 | 19491.754 |
| pytest-dev__pytest-11148__c4 | gate-proviso | 1 | 31 | 333621 | 10761.968 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 38 | 539679 | 14202.079 |
| pytest-dev__pytest-11148__c4 | gate-full | 1 | 63 | 842954 | 13380.222 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 50 | 775618 | 15512.360 |
| sphinx-doc__sphinx-10021__c0 | gate-full | 1 | 19 | 226871 | 11940.579 |
| sphinx-doc__sphinx-10021__c0 | gate-proviso | 1 | 22 | 265111 | 12050.500 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 31 | 339435 | 10949.516 |
| sphinx-doc__sphinx-10021__c1 | gate-proviso | 1 | 40 | 537214 | 13430.350 |
| sphinx-doc__sphinx-10021__c1 | gate-full | 1 | 76 | 1358380.000 | 17873.421 |
| sphinx-doc__sphinx-10137__c1 | gate-full | 1 | 16 | 184279 | 11517.438 |
| sphinx-doc__sphinx-10137__c1 | gate-proviso | 1 | 22 | 236373 | 10744.227 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 20 | 244614 | 12230.700 |
| sphinx-doc__sphinx-10207__c1 | gate-proviso | 1 | 25 | 385875 | 15435 |
| sphinx-doc__sphinx-10207__c1 | gate-full | 1 | 45 | 644538 | 14323.067 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 39 | 759371 | 19471.051 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 50.550 | 686096.500 | 13976.336 |
| gate-full | 57.300 | 971912.050 | 15550.561 |
| gate-proviso | 52.900 | 924285.950 | 15848.480 |

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
| resolved rate | 20 | 0.0500 | 0.0000 | 0.1500 |
| hidden checks passed | 20 | 0.0553 | -0.0171 | 0.1434 |
| regressions | 20 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 285815.5500 | -18237.3000 | 657723.4500 |
| requests | 20 | 6.7500 | -2.6000 | 16.6500 |
| tokens/request | 20 | 1574.2254 | -943.8964 | 4558.4349 |
| cost (USD) | 20 | 0.0016 | -0.0030 | 0.0062 |
| wall time (s) | 20 | 158.3778 | 77.5814 | 253.3359 |
| read chars | 20 | -1670.2500 | -3729.4500 | -155.5000 |
| read calls | 20 | -1.0500 | -2.1500 | -0.1500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 4.5000 | -1.6000 | 11.8000 |

## Paired difference (gate-proviso − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-proviso arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | 0.0500 | -0.1000 | 0.2000 |
| hidden checks passed | 20 | 0.0711 | -0.0750 | 0.2382 |
| regressions | 20 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 238189.4500 | -78521.0000 | 687487.9000 |
| requests | 20 | 2.3500 | -5.8500 | 10.5000 |
| tokens/request | 20 | 1872.1446 | -549.5540 | 5099.8886 |
| cost (USD) | 20 | 0.0027 | -0.0018 | 0.0080 |
| wall time (s) | 20 | 68.3112 | -15.1907 | 145.5310 |
| read chars | 20 | -450.9000 | -2869.7000 | 1700.5500 |
| read calls | 20 | -0.8000 | -2.0000 | 0.1500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 3.5000 | -2.2500 | 10.9000 |
