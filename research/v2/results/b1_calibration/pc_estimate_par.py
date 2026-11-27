"""New B1 estimate with 3 pairs in parallel (--workers 3, B1_PAIR_WORKERS=3), from the first parallel round on sqlglot:
per-project serial hours (estimate.txt, calibrated) x (parallel pair secs / serial pair secs) / 3, minus pairs done."""
import datetime as dt
import glob
import json
import os
import statistics

R = os.path.expanduser("~/proviso-dev/research/v2/results")
serial_h = {"sqlglot": 6.6, "pygments": 1.4, "datasette": 12.1, "loguru": 6.1, "pvlib": 3.6, "pylint": 8.9,
            "seaborn": 21.9, "sphinx": 7.8, "xarray": 48.4, "dask": 68.2, "sqlalchemy": 86.0, "sympy": 82.3}
rows = [json.loads(l) for f in glob.glob(f"{R}/b1/sqlglot/rows.w*.jsonl") for l in open(f) if l.strip()]
serial = [r["secs"] for r in rows if r.get("status") == "ok" and r.get("rank", 99) < 5]
par = [r["secs"] for r in rows if r.get("status") == "ok" and r.get("rank", -1) >= 5]
slow = statistics.median(par) / statistics.median(serial)
W = 3
eff = slow / W
print(f"sqlglot serial pairs (B1, --workers 1): {len(serial)}, median {statistics.median(serial):.0f} s")
print(f"sqlglot parallel pairs (--workers 3): {len(par)}, median {statistics.median(par):.0f} s, "
      f"{', '.join(f'{x:.0f}' for x in sorted(par))}")
print(f"slowdown per pair {slow:.2f}x; wall time per pair = {eff:.3f} x serial ({1 / eff:.2f}x throughput)")
total = 0.0
print(f"\n{'project':11s} {'serial h':>9s} {'done':>5s} {'left h (3 par)':>15s}")
for p, h in serial_h.items():
    done = sum(1 for f in glob.glob(f"{R}/b1/{p}/rows.w*.jsonl") for l in open(f)
               if l.strip() and json.loads(l).get("status") == "ok")
    left = h * eff * max(0, 50 - done) / 50
    total += left
    print(f"{p:11s} {h:9.1f} {done:5d} {left:15.1f}")
now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
deadline = dt.datetime(2026, 12, 13, 23, 59)
print(f"\nTOTAL left {total:.0f} h = {total / 24:.1f} days -> finish ~{(now + dt.timedelta(hours=total)):%Y-%m-%d %H:%M} UTC; "
      f"margin to 13 Dec end: {((deadline - now).total_seconds() / 3600) - total:+.0f} h")
print("assumes the big projects slow down per pair like sqlglot (1.3x); their suites are single-process, so 3 at a "
      "time fit in 12 CPUs, but memory is unmeasured for them yet (drop to 2 pairs on a memory kill: ~+50% time)")
