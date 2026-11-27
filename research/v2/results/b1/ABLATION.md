# RQ2 ablation in B1: how the rows are produced

B1 itself runs without `B1_ABLATE` (decision of 2026-11-27: no inline ablation). Every pair's map stays on disk
(`$PROVISO_WORK/<project>/b1/<pair>/covmap.json`, with `base_outcomes.json`). The ablation is added afterwards,
selection only, by `research/v2/b1_ablate_rows.py`, as a low-priority job that runs only while B1b has yielded the CPU
(its pause file exists) and the 1-minute load is under 8.

## Variants (one per row of the paper's RQ2 table), each selected once

| Tool in the rows | What is off | How |
|---|---|---|
| `proviso-snapshot` | the import-time snapshot | `PROVISO_OFF=snapshot` |
| `proviso-files` | file records (data files read, directories listed) | `PROVISO_OFF=files` |
| `proviso-nameindex` | the name index: callers and bindings together | `PROVISO_OFF=callers,bindings` |
| `proviso-fallbacks` | the fallbacks: config, data, syntax, new files together | `PROVISO_OFF=config,data,syntax,newfiles` |
| `proviso-nofixattr` | fixture attribution (emulated, below) | the map transformed, no switch |

Per pair, scenarios S and F are rebuilt on a separate tree from the saved map at P; each variant is selected once
(one `impact.selection` call; its time is `selection_s`) and scored with `b1.score` against the row's confirmed failures
and the same affected-tests references B1 uses. As a check, Proviso itself is selected once more and compared with the
row's own selection (`ablation_offline.check_proviso`): on the two test pairs (sqlglot 7f1cf60c88, f2b81bfb2d) it was
reproduced exactly in S and F. Cost: about 20-50 s per sqlglot pair.

## nofixattr: "without fixture attribution", emulated from the map

The recorder (src/dc_engine/covplugin.py) records the code a fixture runs while pytest sets it up per **fixture
instance**, in `__fixtures__`, keyed `baseid::argname@<scope node>[param]`; every test lists in `fx` the keys of all the
instances in its closure (pytest's fixture graph), so a class-, module- or session-scoped fixture's code reaches every
test that used it. A recorder without fixture attribution credits that code only to the test that was running when
the fixture was set up: the first test that used the instance. Each test file is recorded in its own process and the
map keeps the tests in execution order, so this is emulated from the saved map, with no new recording:

- a fixture instance shared by several tests (class, module or session scope) stays in `fx` only of the **first test
  in its file** that lists it; the same for the `<session>` record (session-level code outside tests and fixtures):
  first user per file;
- function-scoped instances (scope node = the test itself) are per test already: unchanged;
- the package-import records (`<import>@<module>`: code run when a package module is first imported during a test)
  and the setup/teardown records (`<setup/teardown>@<class or file>`) are left as they are.

### Limits of the emulation

1. **Session-scoped records are unions over files.** A session fixture is set up once per file (one process per file),
   but the map merges its records from all files into one key. The first user in each file gets the union, where a real
   recorder would give it only that file's run. This over-attributes (more tests selected), never under-attributes.
2. **Fixture teardown is not in the fixture's record.** Finalizer code is recorded under the test's
   `<setup/teardown>@...` record (kept as is); a real recorder would credit a broader-scoped fixture's teardown to the
   last test that used it. The map cannot tell which code was the fixture's teardown.
3. **Package-import records are kept for every test that lists them**, as recorded; a real recorder would credit a
   lazily imported module's import-time code to the first test that imported it.
4. **Order within a file is the recorded execution order** (no `-p randomly`); in a different order the first user,
   and so the variant's selection, could differ.
5. The `fixtures` switch of `PROVISO_OFF` is **not** this row: in v2.3.1 it is a recording-time switch that only drops
   `fx` keys whose fixture record is empty. A faithful "without fixture attribution" recording would need a recorder
   change in `src/`, which is frozen; the emulation is the only route.
