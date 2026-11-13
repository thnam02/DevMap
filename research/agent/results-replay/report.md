# dc-eval report

## dc-engine versions

Runs grouped by dc-engine commit:

| commit | dirty | path | runs |
|---|---|---|---:|
| 1b55c692ade9 | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 20 |
| 3daf84345989 | e3b0c44298fc | /Users/agentrun/DevMap/src/dc_engine | 20 |

**Warning:** this comparison mixes dc-engine versions (commits: 1b55c692ade97de6a33b15fc9dcc452ca3ef9d45, 3daf84345989bec34cc8761ee000897752ee653f). Do not treat arm differences as an ablation of one engine.

## Per-arm summary

| arm | runs | resolved | hidden checks | requests | tokens | tokens/request | time | read calls | dc-engine calls | contracts created | contract retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 8 | 60% | 17.150 | 5758036 | 15591.885 | 1890.4 | 1 | 0 | 0 | 0 |
| impact-noreport | 20 | 7 | 56% | 17.550 | 3622914 | 12332.020 | 2756.3 | 7 | 0 | 0 | 0 |

## Tool result sizes

Size of the result text returned to the agent for each completed tool call (chars, ~tokens = chars/4). MCP calls are grouped by dc-engine tool name. Totals are summed over the runs below (including contaminated).

### baseline

Total returned chars: **322562** (~80641 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 318554 | 79639 |
| Monitor | 1576 | 394 |
| Read | 1449 | 363 |
| Edit | 507 | 127 |
| bash | 476 | 119 |

### impact-noreport

Total returned chars: **377196** (~94299 tokens).

| tool | chars | ~tokens |
|---|---:|---:|
| Bash | 368197 | 92050 |
| Read | 3127 | 782 |
| Edit | 2469 | 618 |
| Monitor | 2106 | 527 |
| bash | 595 | 149 |
| Grep | 471 | 118 |
| Write | 231 | 58 |

### Layer: largest dc-engine responses

No dc-engine tool results on the layer arm.

## Model requests

A request is a distinct `model_call_id` when the stream has one, otherwise an assistant event. tokens/request = run tokens / requests.

| task | arm | rep | requests | tokens | tokens/request |
|---|---|---:|---:|---:|---:|
| mwaskom__seaborn-2813__c0 | baseline | 1 | 14 | 228053 | 16289.500 |
| mwaskom__seaborn-2813__c0 | impact-noreport | 1 | 10 | 131292 | 13129.200 |
| mwaskom__seaborn-2846__c0 | baseline | 1 | 8 | 112115 | 14014.375 |
| mwaskom__seaborn-2846__c0 | impact-noreport | 1 | 14 | 187120 | 13365.714 |
| mwaskom__seaborn-2846__c1 | impact-noreport | 1 | 8 | 108342 | 13542.750 |
| mwaskom__seaborn-2846__c1 | baseline | 1 | 8 | 113337 | 14167.125 |
| mwaskom__seaborn-2848__c0 | baseline | 1 | 21 | 307959 | 14664.714 |
| mwaskom__seaborn-2848__c0 | impact-noreport | 1 | 14 | 161694 | 11549.571 |
| pydata__xarray-4759__c0 | baseline | 1 | 38 | 675621 | 17779.500 |
| pydata__xarray-4759__c0 | impact-noreport | 1 | 43 | 41919 | 974.860 |
| pydata__xarray-4759__c1 | baseline | 1 | 50 | 961908 | 19238.160 |
| pydata__xarray-4759__c1 | impact-noreport | 1 | 40 | 42241 | 1056.025 |
| pydata__xarray-4759__c2 | baseline | 1 | 40 | 683185 | 17079.625 |
| pydata__xarray-4759__c2 | impact-noreport | 1 | 36 | 613176 | 17032.667 |
| pydata__xarray-4759__c3 | baseline | 1 | 40 | 816359 | 20408.975 |
| pydata__xarray-4759__c3 | impact-noreport | 1 | 36 | 202066 | 5612.944 |
| pylint-dev__pylint-4339__c1 | baseline | 1 | 8 | 105969 | 13246.125 |
| pylint-dev__pylint-4339__c1 | impact-noreport | 1 | 9 | 123797 | 13755.222 |
| pylint-dev__pylint-4339__c2 | impact-noreport | 1 | 10 | 115936 | 11593.600 |
| pylint-dev__pylint-4339__c2 | baseline | 1 | 11 | 162450 | 14768.182 |
| pylint-dev__pylint-4339__c3 | impact-noreport | 1 | 22 | 264251 | 12011.409 |
| pylint-dev__pylint-4339__c3 | baseline | 1 | 10 | 164268 | 16426.800 |
| pylint-dev__pylint-4492__c1 | baseline | 1 | 20 | 309552 | 15477.600 |
| pylint-dev__pylint-4492__c1 | impact-noreport | 1 | 9 | 143454 | 15939.333 |
| pytest-dev__pytest-11148__c0 | impact-noreport | 1 | 16 | 249105 | 15569.062 |
| pytest-dev__pytest-11148__c0 | baseline | 1 | 7 | 107753 | 15393.286 |
| pytest-dev__pytest-11148__c2 | impact-noreport | 1 | 14 | 232265 | 16590.357 |
| pytest-dev__pytest-11148__c2 | baseline | 1 | 11 | 157685 | 14335 |
| pytest-dev__pytest-11148__c3 | baseline | 1 | 12 | 181570 | 15130.833 |
| pytest-dev__pytest-11148__c3 | impact-noreport | 1 | 13 | 165954 | 12765.692 |
| pytest-dev__pytest-11148__c4 | impact-noreport | 1 | 30 | 460593 | 15353.100 |
| pytest-dev__pytest-11148__c4 | baseline | 1 | 12 | 176754 | 14729.500 |
| sphinx-doc__sphinx-10021__c0 | baseline | 1 | 10 | 146614 | 14661.400 |
| sphinx-doc__sphinx-10021__c0 | impact-noreport | 1 | 7 | 94030 | 13432.857 |
| sphinx-doc__sphinx-10021__c1 | impact-noreport | 1 | 6 | 93535 | 15589.167 |
| sphinx-doc__sphinx-10021__c1 | baseline | 1 | 10 | 174415 | 17441.500 |
| sphinx-doc__sphinx-10137__c1 | impact-noreport | 1 | 8 | 101931 | 12741.375 |
| sphinx-doc__sphinx-10137__c1 | baseline | 1 | 6 | 81777 | 13629.500 |
| sphinx-doc__sphinx-10207__c1 | baseline | 1 | 7 | 90692 | 12956 |
| sphinx-doc__sphinx-10207__c1 | impact-noreport | 1 | 6 | 90213 | 15035.500 |

| arm | mean requests | mean tokens | mean tokens/request |
|---|---:|---:|---:|
| baseline | 17.150 | 287901.800 | 15591.885 |
| impact-noreport | 17.550 | 181145.700 | 12332.020 |

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
| mwaskom__seaborn-2813__c0 | 1 | — | 0 | — | 228053 | — | $0.0757 | — | 131.944 | — |
| mwaskom__seaborn-2846__c0 | 0 | — | 0 | — | 112115 | — | $0.0555 | — | 45.205 | — |
| mwaskom__seaborn-2846__c1 | 0 | — | 0 | — | 113337 | — | $0.0555 | — | 51.882 | — |
| mwaskom__seaborn-2848__c0 | 0 | — | 0 | — | 307959 | — | $0.1088 | — | 66.258 | — |
| pydata__xarray-4759__c0 | 0 | — | 0 | — | 675621 | — | $0.1974 | — | 110.997 | — |
| pydata__xarray-4759__c1 | 0 | — | 0 | — | 961908 | — | $0.2677 | — | 363.317 | — |
| pydata__xarray-4759__c2 | 1 | — | 0 | — | 683185 | — | $0.2046 | — | 344.102 | — |
| pydata__xarray-4759__c3 | 0 | — | 0 | — | 816359 | — | $0.2492 | — | 480.699 | — |
| pylint-dev__pylint-4339__c1 | 1 | — | 1 | — | 105969 | — | $0.0510 | — | 14.601 | — |
| pylint-dev__pylint-4339__c2 | 1 | — | 1 | — | 162450 | — | $0.0645 | — | 22.687 | — |
| pylint-dev__pylint-4339__c3 | 1 | — | 1 | — | 164268 | — | $0.0623 | — | 17.863 | — |
| pylint-dev__pylint-4492__c1 | 0 | — | 0 | — | 309552 | — | $0.1317 | — | 78.119 | — |
| pytest-dev__pytest-11148__c0 | 1 | — | 0 | — | 107753 | — | $0.0491 | — | 18.676 | — |
| pytest-dev__pytest-11148__c2 | 1 | — | 0 | — | 157685 | — | $0.0643 | — | 26.780 | — |
| pytest-dev__pytest-11148__c3 | 0 | — | 73 | — | 181570 | — | $0.0660 | — | 19.745 | — |
| pytest-dev__pytest-11148__c4 | 1 | — | 0 | — | 176754 | — | $0.0612 | — | 23.229 | — |
| sphinx-doc__sphinx-10021__c0 | 0 | — | 0 | — | 146614 | — | $0.0625 | — | 20.786 | — |
| sphinx-doc__sphinx-10021__c1 | 0 | — | 0 | — | 174415 | — | $0.0723 | — | 23.828 | — |
| sphinx-doc__sphinx-10137__c1 | 0 | — | 0 | — | 81777 | — | $0.0381 | — | 12.719 | — |
| sphinx-doc__sphinx-10207__c1 | 0 | — | 0 | — | 90692 | — | $0.0494 | — | 16.966 | — |

## Paired difference (impact-noreport − baseline) with 95% bootstrap CI

Resamples: 10000 with `random.choices`, seed 0. Each observation is one task (median/rate over its reps). Negative cost or tokens means the impact-noreport arm was cheaper/smaller.

| metric | n | mean(L−B) | 95% CI low | 95% CI high |
|---|---:|---:|---:|---:|
| resolved rate | 20 | -0.0500 | -0.3000 | 0.2000 |
| hidden checks passed | 20 | -0.0412 | -0.2579 | 0.1833 |
| regressions | 20 | -0.1000 | -0.2500 | 0.0000 |
| tokens (all-in, incl. cache) | 20 | -106756.1000 | -240526.0500 | 5123.9500 |
| requests | 20 | 0.4000 | -2.5500 | 3.5500 |
| tokens/request | 20 | -3259.8646 | -6063.3626 | -937.6748 |
| cost (USD) | 20 | 0.0072 | -0.0068 | 0.0224 |
| wall time (s) | 20 | 43.2927 | -19.8128 | 118.9999 |
| read chars | 20 | 83.9000 | -165.0500 | 370.2500 |
| read calls | 20 | 0.3000 | -0.0500 | 0.7500 |
| dc-engine calls | 20 | 0.0000 | 0.0000 | 0.0000 |
| contracts created | 20 | 0.0000 | 0.0000 | 0.0000 |
| contract retries | 20 | 0.0000 | 0.0000 | 0.0000 |
| turns | 20 | -3.0500 | -7.3500 | 0.6500 |
