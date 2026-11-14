# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 87f8ac63846d | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 20 |
| 30898c15ce1d | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 40 |

**Warning:** this comparison mixes dc-engine versions (commits: 30898c15ce1d4971a00ff6c92dd4ceef9f5d064d, 87f8ac63846dfc9e2a2f2a02c7e4080b84579c16). Do not treat arm differences as an ablation of one engine.

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 9 | 64% | 17.450 | 5702464 | 15479.244 | 1841.7 | 0 | 0 | 0 | 0 |
| gate-full | 20 | 5 | 49% | 18.400 | 6810637 | 16817.424 | 4904.9 | 0 | 0 | 0 | 0 |
| gate-proviso | 20 | 7 | 56% | 19 | 6951391 | 16220.201 | 3691.3 | 0 | 0 | 0 | 0 |

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

Total returned chars: **317077** (~79270 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 316228 | 79057 |
| bash | 476 | 119 |
| Write | 220 | 55 |
| Edit | 153 | 39 |

### gate-proviso

Total returned chars: **331321** (~82831 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 330588 | 82647 |
| Edit | 495 | 124 |
| bash | 238 | 60 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 15 | 207675 | 13845 |
| mwaskom__seaborn-2813__c0 | gate-proviso | 1 | 8 | 130549 | 16318.625 |
| mwaskom__seaborn-2813__c0 | gate-full | 1 | 8 | 106568 | 13321 |
| mwaskom__seaborn-2846__c0 | gate-proviso | 1 | 6 | 87130 | 14521.667 |
| mwaskom__seaborn-2846__c0 | gate-full | 1 | 8 | 109366 | 13670.750 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 16 | 212218 | 13263.625 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 9 | 135903 | 15100.333 |
| mwaskom__seaborn-2846__c1 | gate-full | 1 | 8 | 116351 | 14543.875 |
| mwaskom__seaborn-2846__c1 | gate-proviso | 1 | 8 | 116182 | 14522.750 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 19 | 275961 | 14524.263 |
| mwaskom__seaborn-2848__c0 | gate-proviso | 1 | 17 | 221022 | 13001.294 |
| mwaskom__seaborn-2848__c0 | gate-full | 1 | 11 | 155615 | 14146.818 |
| pydata__xarray-4759__c0 | baseline | 1 | 38 | 594295 | 15639.342 |
| pydata__xarray-4759__c0 | gate-proviso | 1 | 55 | 1073113.000 | 19511.145 |
| pydata__xarray-4759__c0 | gate-full | 1 | 39 | 760880 | 19509.744 |
| pydata__xarray-4759__c1 | gate-full | 1 | 43 | 875007 | 20349 |
| pydata__xarray-4759__c1 | baseline | 1 | 46 | 878980 | 19108.261 |
| pydata__xarray-4759__c1 | gate-proviso | 1 | 45 | 989627 | 21991.711 |
| pydata__xarray-4759__c2 | gate-full | 1 | 35 | 735562 | 21016.057 |
| pydata__xarray-4759__c2 | baseline | 1 | 35 | 608196 | 17377.029 |
| pydata__xarray-4759__c2 | gate-proviso | 1 | 35 | 632903 | 18082.943 |
| pydata__xarray-4759__c3 | gate-proviso | 1 | 59 | 1369586.000 | 23213.322 |
| pydata__xarray-4759__c3 | baseline | 1 | 40 | 791137 | 19778.425 |
| pydata__xarray-4759__c3 | gate-full | 1 | 48 | 1111784.000 | 23162.167 |
| pylint-dev__pylint-4339__c1 | gate-proviso | 1 | 20 | 390052 | 19502.600 |
| pylint-dev__pylint-4339__c1 | gate-full | 1 | 21 | 379459 | 18069.476 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 12 | 188172 | 15681 |
| pylint-dev__pylint-4339__c2 | gate-full | 1 | 22 | 403943 | 18361.045 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 8 | 115034 | 14379.250 |
| pylint-dev__pylint-4339__c2 | gate-proviso | 1 | 10 | 142505 | 14250.500 |
| pylint-dev__pylint-4339__c3 | gate-proviso | 1 | 18 | 342658 | 19036.556 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 8 | 116834 | 14604.250 |
| pylint-dev__pylint-4339__c3 | gate-full | 1 | 19 | 414860 | 21834.737 |
| pylint-dev__pylint-4492__c1 | gate-full | 1 | 26 | 414566 | 15944.846 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 22 | 379799 | 17263.591 |
| pylint-dev__pylint-4492__c1 | gate-proviso | 1 | 24 | 346849 | 14452.042 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 10 | 138430 | 13843 |
| pytest-dev__pytest-11148__c0 | gate-full | 1 | 10 | 153450 | 15345 |
| pytest-dev__pytest-11148__c0 | gate-proviso | 1 | 9 | 130170 | 14463.333 |
| pytest-dev__pytest-11148__c2 | gate-proviso | 1 | 10 | 133302 | 13330.200 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 7 | 112355 | 16050.714 |
| pytest-dev__pytest-11148__c2 | gate-full | 1 | 8 | 134658 | 16832.250 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 10 | 157953 | 15795.300 |
| pytest-dev__pytest-11148__c3 | gate-proviso | 1 | 15 | 244378 | 16291.867 |
| pytest-dev__pytest-11148__c3 | gate-full | 1 | 17 | 264916 | 15583.294 |
| pytest-dev__pytest-11148__c4 | gate-proviso | 1 | 9 | 134491 | 14943.444 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 10 | 138646 | 13864.600 |
| pytest-dev__pytest-11148__c4 | gate-full | 1 | 10 | 134176 | 13417.600 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 10 | 173764 | 17376.400 |
| sphinx-doc__sphinx-10021__c0 | gate-full | 1 | 12 | 177014 | 14751.167 |
| sphinx-doc__sphinx-10021__c0 | gate-proviso | 1 | 8 | 119952 | 14994 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 19 | 264758 | 13934.632 |
| sphinx-doc__sphinx-10021__c1 | gate-proviso | 1 | 10 | 172234 | 17223.400 |
| sphinx-doc__sphinx-10021__c1 | gate-full | 1 | 10 | 172743 | 17274.300 |
| sphinx-doc__sphinx-10137__c1 | gate-full | 1 | 7 | 100988 | 14426.857 |
| sphinx-doc__sphinx-10137__c1 | gate-proviso | 1 | 5 | 60107 | 12021.400 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 8 | 122103 | 15262.875 |
| sphinx-doc__sphinx-10207__c1 | gate-proviso | 1 | 9 | 114581 | 12731.222 |
| sphinx-doc__sphinx-10207__c1 | gate-full | 1 | 6 | 88731 | 14788.500 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 7 | 90251 | 12893 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 17.450 | 285123.200 | 15479.244 |
| gate-full | 18.400 | 340531.850 | 16817.424 |
| gate-proviso | 19 | 347569.550 | 16220.201 |

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
| resolved rate | 20 | -0.2000 | -0.4000 | -0.0500 |
| hidden checks passed | 20 | -0.1439 | -0.2930 | -0.0237 |
| regressions | 20 | -0.0500 | -0.1500 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 55408.6500 | -973.7000 | 115491.3000 |
| requests | 20 | 0.9500 | -1.7500 | 3.7000 |
| tokens/request | 20 | 1338.1797 | 348.9457 | 2383.0093 |
| cost (USD) | 20 | 0.0140 | -0.0021 | 0.0308 |
| wall time (s) | 20 | 153.1576 | 95.1947 | 218.1904 |
| read chars | 20 | 0.0000 | 0.0000 | 0.0000 |
| read calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 1.3000 | -0.3000 | 2.9500 |

## Paired difference (gate-proviso − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the gate-proviso arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | -0.1000 | -0.3500 | 0.1500 |
| hidden checks passed | 20 | -0.0741 | -0.2246 | 0.0842 |
| regressions | 20 | 0.0000 | 0.0000 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | 62446.3500 | -7907.8500 | 147396.0500 |
| requests | 20 | 1.5500 | -1.5000 | 4.8500 |
| tokens/request | 20 | 740.9566 | -341.2130 | 1793.6204 |
| cost (USD) | 20 | 0.0164 | 0.0018 | 0.0319 |
| wall time (s) | 20 | 92.4780 | 24.4844 | 181.6295 |
| read chars | 20 | 0.0000 | 0.0000 | 0.0000 |
| read calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | 1.1500 | -0.6000 | 3.1000 |
