"""Impact of the import-time values that differ with no code change (sphinx, xarray, dask, sqlalchemy), with the frozen
Proviso (src/ unchanged; selection and snapshots only; one map recorded where none was saved).

  python research/v2/nochange_impact.py map PROJECT       # a map at one parent: saved if any, else recorded
  python research/v2/nochange_impact.py analyse PROJECT   # per value, and the selection for a no-op change
  python research/v2/nochange_impact.py write             # results/b1/NOCHANGE_IMPACT.md

The no-op change: a comment line added at the top of the package's __init__.py. Proviso treats an edit outside any
function as module-level code, so it compares the import-time snapshot of the tree with the base snapshot of the
parent; nothing behaves differently, so every value it reports differs without a change. Per value: the tests it links
(impact._selection's reader rule, as in v24_diagnosis.Links) and their share of the map's test time; whether the base
snapshot's 9 samples marked it unstable; its fingerprints; and 4 extra snapshots of the parent (2 s apart, other heap
shifts) to see whether, and how, it varies between processes."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
import v24_diagnosis as V  # noqa: E402
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as IS  # noqa: E402

SAVED = {"sqlalchemy": "record_speed_maps/sqlalchemy-diag-again.json"}   # full maps from the freeze-check diagnosis
NOOP = "# proviso no-op edit (NOCHANGE_IMPACT): a comment, so nothing behaves differently\n"


def work(name):
    d = os.path.join(PL.BASE_WORK, name, "nochange_impact")
    os.makedirs(d, exist_ok=True)
    return d


def build_map(name):
    b1.use(name)
    meta_p = os.path.join(work(name), "meta.json")
    if name in SAVED:
        path = os.path.join(PL.BASE_WORK, SAVED[name])
        cov = PL.jload(path)
        meta = {"map": path, "source": "saved (freeze-check diagnosis map)", "parent": cov["__base__"]["commit"]}
    else:
        nc = PL.jload(os.path.join(PL.WORK, "v24", "nochange-v2.3.2.json"))
        short = nc["pairs"][0]["parent"]
        tree = PL.make_tree("ni", short)
        parent = PL.git(tree, "rev-parse", "HEAD").strip()
        b1.use_targets(tree)
        out = os.path.join(work(name), "covmap.json")
        t = time.time()
        PL.covmap(tree, out, int(os.environ.get("NI_WORKERS", "4")))
        meta = {"map": out, "source": f"recorded fresh ({round(time.time() - t)} s, Proviso {b1.proviso_version()})",
                "parent": parent}
    PL.jdump(meta, meta_p)
    print(name, meta, flush=True)


def analyse(name):
    b1.use(name)
    meta = PL.jload(os.path.join(work(name), "meta.json"))
    cov = PL.jload(meta["map"])
    p = meta["parent"]
    tree = PL.make_tree("ni", p)
    files = I._snapshot_files(cov)
    tests = I.tests_of(cov)
    universe = {n for n, v in tests.items() if v.get("ok", True)}
    times = {n: (tests[n].get("time") or 0) for n in universe}
    total_t = sum(times.values()) or 1e-9
    with tempfile.TemporaryDirectory() as tmp:
        base = IS.base_snapshot(tree, files, PL.PY, os.path.join(tmp, "b.json"), rev=p)
    unstable = set(base.get("unstable", []))
    # the no-op edit
    pkg = PL.CFG["pkg"].rstrip("/")
    init = os.path.join(pkg, "__init__.py")
    path = os.path.join(tree, init)
    src = open(path).read()
    open(path, "w").write(NOOP + src)
    try:
        sel, why = I.selection(tree, cov, PL.PY)
        cur = IS.snapshot(tree, files, PL.PY)
        keys = why.get("import_state_changed", [])
        links = V.Links(tree, cov)
        dep = I._DepView(cov)
        always = {n for n in universe if dep.always(n)}
        vals, tsets = {}, {}
        for k in keys:
            kind, ts, nread = links.tests(k)
            ts &= universe
            tsets[k] = ts
            vals[k] = {"kind": kind, "tests": len(ts), "tests_pct": round(100 * len(ts) / max(1, len(universe)), 2),
                       "time_pct": round(100 * sum(times[n] for n in ts) / total_t, 2),
                       "tests_beyond_always": len(ts - always), "readers": nread,
                       "unstable": k in unstable, "base": base["state"].get(k), "cur": (cur or {}).get("state", {}).get(k)}
        noise_tests = set().union(*tsets.values()) if tsets else set()
    finally:
        open(path, "w").write(src)
    # extra samples of the parent: an export, 2 s apart and with other heap shifts, to see how each value varies
    samples = []
    arch = subprocess.run(["git", "-C", tree, "archive", p, *sorted({f.split("/", 1)[0] for f in files})],
                          capture_output=True)
    exp = tempfile.mkdtemp(prefix="ni-export-")
    try:
        subprocess.run(["tar", "-x", "-C", exp], input=arch.stdout, capture_output=True)
        for pad in (0, 0, 5003, 20011):
            time.sleep(2)
            s = IS.snapshot(exp, files, PL.PY, heap_pad=pad)
            samples.append({k: (s or {}).get("state", {}).get(k) for k in keys})
    finally:
        shutil.rmtree(exp, ignore_errors=True)
    for k in keys:
        fps = [s.get(k) for s in samples]
        vals[k]["extra_samples_distinct"] = len(set(fps))
        vals[k]["extra_samples_unordered_distinct"] = len({(f or "").split("~")[-1] for f in fps})
        vals[k]["base_vs_cur_unordered_equal"] = (vals[k]["base"] or "").split("~")[-1] == (vals[k]["cur"] or "").split("~")[-1]
    selset = universe if sel is None else set(sel) & universe
    res = {"project": name, "parent": p, "map": meta, "universe": len(universe), "always": len(always),
           "always_time_pct": round(100 * sum(times[n] for n in always) / total_t, 2),
           "edit": init, "full": sel is None, "reason": why.get("reason"), "values": vals,
           "selected": len(selset), "selected_pct": round(100 * len(selset) / max(1, len(universe)), 2),
           "selected_time_pct": round(100 * sum(times[n] for n in selset) / total_t, 2),
           "noise_tests": len(noise_tests), "noise_tests_pct": round(100 * len(noise_tests) / max(1, len(universe)), 2),
           "noise_time_pct": round(100 * sum(times[n] for n in noise_tests) / total_t, 2),
           "base_samples": base.get("unstable_samples"), "unstable_total": len(unstable)}
    PL.jdump(res, os.path.join(work(name), "result.json"))
    print(json.dumps({k: res[k] for k in ("project", "universe", "selected", "selected_pct", "selected_time_pct",
                                          "noise_tests", "always", "reason")}), flush=True)
    for k, v in vals.items():
        print("  ", k, {x: v[x] for x in ("kind", "tests", "time_pct", "unstable", "extra_samples_distinct",
                                          "extra_samples_unordered_distinct", "base_vs_cur_unordered_equal")}, flush=True)


# --------------------------------------------------------------------------------------------- report

PURPOSE = ("v2.3's own unit test `test_value_differing_between_imports_still_counts_when_code_changes` "
           "(tests/test_importstate_noise.py): a value that differs on every import, such as a registry keyed by "
           "`id()` or the process id, cannot be compared; Proviso keeps reporting it rather than ignoring it, because "
           "ignoring such values hid real changes to SQLAlchemy registries. Sampling marks it unstable, and unstable "
           "values are compared without order, which forgives a different order but not different contents.")


def classify(name, k, v, universe):
    few = v["tests"] <= max(5, universe // 100) and v["time_pct"] < 1.0
    if few:
        return "a", f"links {v['tests']} tests ({v['time_pct']}% of test time): harmless"
    if name == "sqlalchemy" and re.search(r"event\.registry|_sa_instrumented|_NO_STATE_SYMBOLS", k):
        return "c", "an id-keyed registry or marker that differs in every process; reported on purpose (see below)"
    if v["unstable"]:
        return "b", ("the 9 base samples saw it vary and marked it unstable, but its contents (not only its order) "
                     "differ between processes, and unstable values are compared without order only")
    if v["extra_samples_distinct"] > 1:
        return "b", ("varies between processes but the 9 base samples did not: they are taken at nearly the same "
                     "moment (in parallel, a few seconds in total), and this value changes with time or with "
                     "something constant within those seconds")
    return "b", ("differs between the base snapshot and the working tree but not between the base samples: it "
                 "depends on where or when the snapshot runs (export folder vs working tree, or later time)")


def write():
    L = ["# No-change values: impact on selection (sphinx, xarray, dask, sqlalchemy)", "",
         "Frozen Proviso (v2.3.2; src/ unchanged), selection and snapshots only. Per project one map at one parent "
         "(sqlalchemy: a saved full map from the freeze-check diagnosis; the others recorded fresh). The no-op change "
         "is a comment line added at the top of the package's `__init__.py`: Proviso treats it as module-level code "
         "and compares the import-time snapshot, so everything it reports differs without a behavioural change. "
         "`research/v2/nochange_impact.py`.", "",
         "## Effect: selection for a no-op import-time change", "",
         "| Project | Map | Tests | Always selected | Selected | % tests | % test time | Tests linked by the no-change "
         "values | % of tests | % of test time |", "|---|---|---|---|---|---|---|---|---|---|"]
    res = {}
    for name in ("sphinx", "xarray", "dask", "sqlalchemy"):
        r = PL.jload(os.path.join(PL.BASE_WORK, name, "nochange_impact", "result.json"))
        if not r:
            L.append(f"| {name} | (not analysed yet) | | | | | | | | |")
            continue
        res[name] = r
        L.append(f"| {name} | {r['map']['source'].split(' (')[0]} at {r['parent'][:10]} | {r['universe']} | "
                 f"{r['always']} ({r['always_time_pct']}% time) | {r['selected']}{' (full: ' + str(r['reason']) + ')' if r['full'] else ''} | "
                 f"{r['selected_pct']} | {r['selected_time_pct']} | {r['noise_tests']} | {r['noise_tests_pct']} | "
                 f"{r['noise_time_pct']} |")
    L += ["", "Always-selected tests run for any change; the rest of the selection comes from the no-change values.", "",
          "## Per value", "",
          "Unstable: marked by the base snapshot's 9 samples (3 export locations, heap shifts). Extra samples: 4 more "
          "snapshots of an export of the parent, 2 s apart and with other heap shifts (distinct fingerprints, and "
          "distinct when order is ignored). Class: (a) links few tests, harmless; (b) varies between processes and "
          "should have been caught as unstable; (c) reported on purpose.", "",
          "| Project | Value | Kind | Tests linked | % test time | Unstable (9 samples) | Extra samples: distinct / "
          "ignoring order | Base vs tree equal ignoring order | Class | Why |", "|---|---|---|---|---|---|---|---|---|---|"]
    counts = {}
    for name, r in res.items():
        for k, v in sorted(r["values"].items(), key=lambda kv: -kv[1]["tests"]):
            c, why = classify(name, k, v, r["universe"])
            counts[(name, c)] = counts.get((name, c), 0) + 1
            L.append(f"| {name} | `{k}` | {v['kind']} | {v['tests']} | {v['time_pct']} | {'yes' if v['unstable'] else 'no'} | "
                     f"{v['extra_samples_distinct']} / {v['extra_samples_unordered_distinct']} | "
                     f"{'yes' if v['base_vs_cur_unordered_equal'] else 'no'} | {c} | {why} |")
    L += ["", "Counts per class: " + "; ".join(f"{n} {c}: {k}" for (n, c), k in sorted(counts.items())) + ".", "",
          "### Why a value marked unstable is still reported", "",
          "importstate compares an unstable value by its order-free fingerprint (the part after `~`). That forgives "
          "values whose order follows memory addresses, but a value whose contents differ (a random token, a thread "
          "id, the time of import, an id-keyed registry) still differs and is reported. The column 'Base vs tree equal "
          "ignoring order' shows this per value.", "",
          "### (c) Reported on purpose", "", PURPOSE, ""]
    open(os.path.join(b1.OUT, "NOCHANGE_IMPACT.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    a = sys.argv[1:]
    if a[0] == "map":
        build_map(a[1])
    elif a[0] == "analyse":
        analyse(a[1])
    elif a[0] == "write":
        write()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
