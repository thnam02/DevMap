"""STEP 4 estimate: hours for 50 B1 pairs per project at the 80% cap, one project at a time (--workers 1).
Model from the calibration rows (sqlglot, sphinx): a pair's wall time = A + B * suite, where suite = the plain run of the
project's whole suite at the parent (base_s). B is fitted per component (base run, Proviso recording, testmon recording,
NameRTS init, TDAD index, scenarios S and F) as seconds per suite-second; A = the rest. Other projects' suite times come
from the env check (results/env_check/P.json run_s: the same single-process run).
  python estimate.py [CALIB_DIR ...]"""
import datetime as dt
import glob
import json
import os
import statistics
import sys

R = os.path.expanduser("~/proviso-dev/research/v2/results")
calib_dirs = sys.argv[1:] or [f"{R}/b1/sqlglot", f"{R}/b1/sphinx"]
rows = [json.loads(l) for d in calib_dirs for f in glob.glob(f"{d}/rows.w*.jsonl") for l in open(f) if l.strip()]
rows = [r for r in rows if r.get("status") == "ok"]
parts = ["base_s", "record_s", "testmon_record_s", "namerts_init_s", "tdad_index_s"]
print(f"calibration pairs: {len(rows)}")
print(f"{'pair':12s} {'secs':>7s} {'base':>6s} {'record':>6s} {'testmon':>7s} {'nr_init':>7s} {'tdad':>6s} {'S_run':>6s} {'F_run':>6s} {'rest':>6s}")
ratios, rests = [], []
for r in rows:
    s_run = (r.get("S") or {}).get("run_s") or 0
    f_run = (r.get("F") or {}).get("run_s") or 0
    comp = sum(r.get(k) or 0 for k in parts) + s_run + f_run
    rest = r["secs"] - comp
    print(f"{r['id'][:10]:12s} {r['secs']:7.0f} " + " ".join(f"{(r.get(k) or 0):6.0f}" for k in parts[:2]) +
          f" {(r.get('testmon_record_s') or 0):7.0f} {(r.get('namerts_init_s') or 0):7.0f} {(r.get('tdad_index_s') or 0):6.0f}"
          f" {s_run:6.0f} {f_run:6.0f} {rest:6.0f}")
    ratios.append((r["secs"] - 0) / max(1.0, r["base_s"]))
    rests.append(rest)
# fit secs = A + B * base_s by least squares over the calibration pairs
xs = [r["base_s"] for r in rows]
ys = [r["secs"] for r in rows]
mx, my = statistics.mean(xs), statistics.mean(ys)
sxx = sum((x - mx) ** 2 for x in xs)
B = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx > 1e-9 else my / mx
A = my - B * mx
# the components scale with the suite; a robust per-suite-second factor from the component sums
comp_ratio = statistics.median([(r["secs"] - statistics.median(rests)) / max(1.0, r["base_s"]) for r in rows])
A2 = max(0.0, statistics.median(rests))
print(f"\nfit secs = {A:.0f} + {B:.2f} * suite   |   component model: secs = {A2:.0f} + {comp_ratio:.2f} * suite")
order = ["sqlglot", "pygments", "datasette", "loguru", "pvlib", "pylint", "seaborn", "sphinx", "xarray", "dask",
         "sqlalchemy", "sympy"]
done_pairs = {}
for p in order:
    done_pairs[p] = sum(1 for f in glob.glob(f"{R}/b1/{p}/rows.w*.jsonl") for l in open(f)
                        if l.strip() and json.loads(l).get("status") == "ok")
# B1's base run vs the env check's run of the same suite (the env checks ran several projects at once): scale factor
measured = {}
for d in calib_dirs:
    p = os.path.basename(d.rstrip("/"))
    rs = [r for r in rows if os.path.exists(f"{d}/rows.w0.jsonl") and r["id"] in open(f"{d}/rows.w0.jsonl").read()]
    if rs:
        env_s = json.load(open(f"{R}/env_check/{p}.json"))["run_s"]
        measured[p] = (statistics.median(r["base_s"] for r in rs) / env_s, statistics.median(r["secs"] for r in rs))
scale = statistics.median(v[0] for v in measured.values()) if measured else 1.0
print("base_s / env-check run_s:", {p: round(v[0], 2) for p, v in measured.items()}, "-> scale", round(scale, 2))
print(f"\n{'project':11s} {'suite_s':>8s} {'pair_s':>7s} {'50 pairs h':>10s}")
total = 0.0
for p in order:
    env = json.load(open(f"{R}/env_check/{p}.json"))
    suite = (env.get("run_s") or 0) * scale
    pair = measured[p][1] if p in measured else A2 + comp_ratio * suite
    h = 50 * pair / 3600
    total += h
    print(f"{p:11s} {suite:8.0f} {pair:7.0f} {h:10.1f}")
now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
deadline = dt.datetime(2026, 12, 13, 23, 59)
avail = (deadline - now).total_seconds() / 3600
print(f"\nTOTAL {total:.0f} h = {total / 24:.1f} days, one project at a time, --workers 1, 80% cap")
print(f"from {now:%Y-%m-%d %H:%M} UTC: finish ~{(now + dt.timedelta(hours=total)):%Y-%m-%d %H:%M} UTC; "
      f"hours until 13 Dec 2026 end: {avail:.0f} -> {'fits' if total <= avail else 'DOES NOT fit'} "
      f"(margin {avail - total:+.0f} h)")
print("not included: history projects' candidates that do not build (one base run each), re-runs of failing tests "
      "beyond 3, timeouts, machine sleep/restarts")
