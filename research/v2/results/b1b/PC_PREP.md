# B1b / B3 preparation on the PC (2026-11-27, no B1b or B3 runs)

- SWE-bench metadata (princeton-nlp/SWE-bench, test split) for the 8 repositories: 936 instances, all with patches,
  in `$PROVISO_WORK/swe/instances.jsonl`; `results/swe/instances.jsonl` regenerated identical. Fetched with a separate
  tools venv (`datasets`), so the evaluation venvs are unchanged.
- `swe_probe.py` (Python 3.12, uv, packages no newer than each version's cut-off): 289 candidate instances,
  **46 environments, 44 ok, 2 failed: pylint 2.15 and 2.17** (uv cannot resolve setuptools for pylint's
  build-system.requires under the cut-off and the setuptools>=68 build constraint). Same 44 ok environments and the
  same per-repository table as the cloud container's probe (kept in `results/swe/container_probe/`).
- `b1b.py --list 500`: **437 instances** (all with a working environment, a patch and FAIL_TO_PASS tests; fewer than
  500 exist): sphinx 117, xarray 109, sympy 85, pytest 51, pylint 44, seaborn 21, flask 10, requests 0.
  List: `sample_list.txt`.
- Disk: envs 791 MB, repos 680 MB, trees 130 MB, uv cache 1.2 GB (~2.8 GB in all).
- Run alongside B1 in the same capped slice (app.slice: CPUQuota=1200%, MemoryMax=24G) at Nice=15, CPUWeight=10;
  a watchdog would have frozen it if memory passed 20 GB or B1's pairs slowed by more than 20%: it never fired
  (B1 pair time ratio 1.05-1.07, slice memory peak ~8 GB, load5 peak 10.5 of 12). Took 28 min.
