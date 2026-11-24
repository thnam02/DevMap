# Running B1, B1b and the checks on the PC

Use Proviso v2.3.1 (tag `proviso-v2.3.1` once the record_speed_check passes on sympy, sqlalchemy and datasette), with
no local edits under `src/`. Every row records the Proviso commit (`proviso.commit`, `proviso.src_dirty`) and an
environment hash (`env.hash`); all rows of one project must share both.

## 1. Environment check, per project, before anything else

```
python research/v2/env_check.py PROJECT            # exit 1 if any test file fails to collect
python research/v2/env_check.py PROJECT --skips    # also: tests skipped at run time, by reason
```

Install whatever the "missing" list names, then run it again until it reports 0 files failing to collect. In the
cloud container sqlglot was missing pytz and duckdb (3 test files) and pygments was missing wcag_contrast_ratio
(1 file).

## 2. Calibration (a day): 5 pairs on a fast and a slow project

```
PROVISO_WORKERS=6 python research/v2/b1.py sqlglot 5
PROVISO_WORKERS=6 python research/v2/b1.py sphinx 5     # NameRTS's pairs; needs NAMERTS_HOME
python research/v2/b1.py report
python research/v2/overhead.py
```

Each row has `secs` (wall time of the pair). Hours per pair × pairs planned gives the time for the Must list.

## 3. B1 (one run per project; resumable, rows in results/b1/<project>/)

```
PROVISO_WORKERS=6 python research/v2/b1.py PROJECT 50 [--workers 2]
```

- `--workers` runs pairs in parallel (each with its own trees). Map recording uses PROVISO_WORKERS cores divided by
  B1_PAIR_WORKERS if you set it.
- B1_ABLATE=all adds Proviso with each selection part off (RQ4) on the same maps.
- B1_FULL=0 skips the full-commit scenario (only the source-only scenario S).
- Dry runs: B1_OUT=research/v2/results_smoke/b1 (kept out of git).

## 4. B1b (after swe_probe.py has built the environments)

```
python research/v2/b1b.py --list 500                   # the sample
python research/v2/b1b.py 500 --workers 3              # instances sharing an environment run one after another
python research/v2/b1b.py report
```

## 5. Run-to-run variation (a 10% sample per project)

```
python research/v2/seed_check.py PROJECT --sample 0.1
```

Container results: sqlglot 0 of 1,104 tests differ across hash seeds 0, 1, 2. pygments: 78 of 5,342 differ, all
`test_random_input` (random inputs, not the seed).
