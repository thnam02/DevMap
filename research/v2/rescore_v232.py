"""Offline re-score of finished B1 pairs and B1b instances with the Proviso in this checkout (selection only, from the
saved maps; no test run, no install, no environment change), to compare Proviso versions (v2.3.1 -> v2.3.2).

  python research/v2/rescore_v232.py select TAG b1 PROJECT     # $PROVISO_WORK/PROJECT/rescore/TAG/<id12>.json
  python research/v2/rescore_v232.py select TAG b1b            # $PROVISO_WORK/swe/rescore/TAG/<instance>.json
  python research/v2/rescore_v232.py compare A B [PROJECT ...] # results/b1/RESCORE_<B>.md (b1b included)
  python research/v2/rescore_v232.py write-rows B [PROJECT ...] [--b1b]   # tools["proviso-<B>"] added to the rows

Per B1 pair, scenarios S and F as b1.py builds them (b1.apply_source / b1.apply_full on a tree at the parent), and per
B1b instance the reversal on the fixed version (rebuilt like b1b.fixed_tree, without installing it; the commit must
match the map's). Selections are kept as test lists (None = the full suite). compare: identical selections per pair,
and missed failures for each version against the row's confirmed failures (b1.score's rule: the selection within the
pair's universe, plus the tests of edited test files in F). Run select with each checkout's own interpreter setup
(the B1 runner's for that project; B1b: the SWE environments)."""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1  # noqa: E402
import pipeline as PL  # noqa: E402
import rts as SEL  # noqa: E402
from dc_engine import impact as I  # noqa: E402

MAX_LOAD = float(os.environ.get("RESCORE_MAX_LOAD", "10"))
# the live result rows (another checkout's research/v2/results, e.g. the main one when running from a verification
# checkout, whose own results folder is a stale committed copy)
RESULTS = os.environ.get("RESCORE_RESULTS")
if RESULTS:
    b1.OUT = os.path.join(RESULTS, "b1")


def _b1b():
    B = _b1b()
    if RESULTS:
        B.OUT = os.path.join(RESULTS, "b1b")
    return B


def wait_load():
    while os.getloadavg()[0] > MAX_LOAD:
        time.sleep(60)


def _sel(tree, cov, universe):
    t = time.time()
    sel, why = I.selection(tree, cov, PL.PY)
    return {"sel": None if sel is None else sorted(set(sel) & universe), "n_raw": None if sel is None else len(sel),
            "reason": why.get("reason"), "import_state_n": why.get("import_state_n"),
            "changed_functions": len(why.get("changed_functions", [])), "secs": round(time.time() - t, 1)}


def select_b1(tag, name):
    b1.use(name)
    out = os.path.join(PL.WORK, "rescore", tag)
    os.makedirs(out, exist_ok=True)
    rows = sorted((r for r in b1.rows(name).values() if r.get("status") == "ok"), key=lambda r: r.get("rank", 0))
    for k, r in enumerate(rows):
        f = os.path.join(out, f"{r['id'][:12]}.json")
        if os.path.exists(f):
            continue
        wait_load()
        p, c = r["parent"], r["id"]
        d = os.path.join(PL.WORK, "b1", c[:12])
        cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
        res = {"id": c, "tag": tag, "proviso": __import__("dc_engine.importstate", fromlist=["x"]).__file__}
        if not cov or not base or (cov.get("__base__") or {}).get("commit") != p:
            res["error"] = "no usable saved map/base outcomes at P"
        else:
            universe = PL.universe_of(cov, PL.failing(base))
            res["universe"] = len(universe)
            tree = PL.make_tree(f"rs-{tag}", p)
            b1.use_targets(tree)
            for sc in ("S", "F"):
                if sc not in r or r[sc].get("timeout"):
                    continue
                b1.to_parent(tree, p)
                try:
                    if sc == "S":
                        b1.apply_source(tree, p, c)
                        edited = []
                    else:
                        changed = b1.apply_full(tree, p, c)
                        edited = [f2 for _, f2 in b1._changed(tree, p, c) if I._is_test_path(f2) and f2.endswith(".py")]
                    res[sc] = {**_sel(tree, cov, universe), "edited_test_files": edited}
                except Exception as e:  # noqa: BLE001
                    res[sc] = {"error": repr(e)[:300]}
            b1.to_parent(tree, p)
        PL.jdump(res, f)
        print(time.strftime("%H:%M:%S"), name, tag, f"[{k + 1}/{len(rows)}] {c[:10]}",
              {sc: (res[sc].get("n_raw"), res[sc].get("secs")) for sc in ("S", "F") if sc in res} or res.get("error"),
              flush=True)


def _fixed_commit(tree_dir, src, x):
    """b1b.fixed_tree without the install: base commit + test patch + reference fix, committed with the same identity
    and dates (so the commit is the one the map was recorded at)."""
    B = _b1b()
    if not os.path.isdir(os.path.join(tree_dir, ".git")):
        os.makedirs(os.path.dirname(tree_dir), exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", src, tree_dir], check=True)
    B.git(tree_dir, "fetch", "-q", src, x["base_commit"], check=False)
    B.git(tree_dir, "checkout", "-q", "-f", x["base_commit"])
    B.git(tree_dir, "clean", "-q", "-fdx", "-e", ".dc-engine")
    for what in ("test_patch", "patch"):
        if x.get(what):
            B.git(tree_dir, "apply", "-", inp=x[what] if x[what].endswith("\n") else x[what] + "\n")
    B.git(tree_dir, "add", "-A")
    when = B.git(tree_dir, "log", "-1", "--format=%cI", x["base_commit"]).strip()
    env0 = dict(os.environ)
    os.environ.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    try:
        B.git(tree_dir, "commit", "-q", "--allow-empty", "-m", f"{x['instance_id']}: fixed version with its tests")
    finally:
        os.environ.clear()
        os.environ.update(env0)
    return B.git(tree_dir, "rev-parse", "HEAD").strip()


def select_b1b(tag, only=None):
    B = _b1b()
    import swe_probe as P
    meta, envs = P.load_instances(), B.envs_ok()
    outdir = os.path.join(P.WORK, "rescore", tag)
    os.makedirs(outdir, exist_ok=True)
    rows = [r for r in B.rows().values() if r.get("status") == "ok" and "tools" in (r.get("R") or {})]
    for k, r in enumerate(sorted(rows, key=lambda r: r["id"])):
        f = os.path.join(outdir, f"{r['id']}.json")
        if os.path.exists(f) or (only and r["id"] not in only):
            continue
        wait_load()
        x = meta[r["id"]]
        repo = r["repo"]
        B.configure(repo, envs[(repo, r["version"])])
        d = os.path.join(PL.WORK, "b1b", r["id"])
        cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
        res = {"id": r["id"], "tag": tag}
        try:
            tree = os.path.join(PL.WORK, "trees", f"rs-{tag}")
            fc = _fixed_commit(tree, P.repo_clone(repo), x)
            if not cov or not base or (cov.get("__base__") or {}).get("commit") != fc:
                raise RuntimeError(f"fixed commit {fc[:10]} is not the map's "
                                   f"{((cov or {}).get('__base__') or {}).get('commit', '?')[:10]}")
            universe = PL.universe_of(cov, PL.failing(base))
            res["universe"] = len(universe)
            B.reverse(tree, fc, B.source_part(x["patch"]))
            res["R"] = _sel(tree, cov, universe)
            b1.to_parent(tree, fc)
        except Exception as e:  # noqa: BLE001
            res["error"] = repr(e)[:300]
        PL.jdump(res, f)
        print(time.strftime("%H:%M:%S"), "b1b", tag, f"[{k + 1}/{len(rows)}] {r['id']}",
              (res.get("R") or {}).get("n_raw"), (res.get("R") or {}).get("secs"), res.get("error", ""), flush=True)


# ------------------------------------------------------------------------------------------- compare / write

def _universe(d):
    cov, base = PL.jload(os.path.join(d, "covmap.json")), PL.jload(os.path.join(d, "base_outcomes.json"))
    return set(PL.universe_of(cov, PL.failing(base))), {k: tt for k, (ok_, tt) in base.items()}


def _scored(selrec, universe, plain, truth, edited_files):
    s = set(universe) if selrec["sel"] is None else set(selrec["sel"])
    ed = {n for n in universe if n.split("::", 1)[0] in set(edited_files)}
    sc = b1.score({"x": s}, {}, universe, plain, set(truth), {}, sorted(edited_files))["x"]
    return sc, s | ed


def items(a, b, projects, with_b1b=True):
    """Yield (kind, project, row, scenario, recA, recB, workdir) for every item both tags scored."""
    for name in projects:
        b1.use(name)
        for r in b1.rows(name).values():
            if r.get("status") != "ok":
                continue
            fa = PL.jload(os.path.join(PL.WORK, "rescore", a, f"{r['id'][:12]}.json")) or {}
            fb = PL.jload(os.path.join(PL.WORK, "rescore", b, f"{r['id'][:12]}.json")) or {}
            for sc in ("S", "F"):
                if sc in fa and sc in fb:
                    yield "b1", name, r, sc, fa, fb, os.path.join(PL.WORK, "b1", r["id"][:12])
    if with_b1b:
        B = _b1b()
        import swe_probe as P
        for r in B.rows().values():
            fa = PL.jload(os.path.join(P.WORK, "rescore", a, f"{r['id']}.json")) or {}
            fb = PL.jload(os.path.join(P.WORK, "rescore", b, f"{r['id']}.json")) or {}
            if "R" in fa and "R" in fb:
                yield "b1b", r["repo"], r, "R", fa, fb, os.path.join(PL.BASE_WORK, f"b1b-{r['repo']}", "b1b", r["id"])


def compare(a, b, projects):
    stats, gains, diffs, sanity = {}, [], [], []
    for kind, proj, r, sc, fa, fb, d in items(a, b, projects):
        A, Bv = fa[sc], fb[sc]
        st = stats.setdefault((kind, proj), {"items": 0, "identical": 0, "errors": 0, "gained_missed": 0,
                                             "lost_missed": 0, "sel_a": 0, "sel_b": 0})
        st["items"] += 1
        if "error" in A or "error" in Bv:
            st["errors"] += 1
            continue
        universe, plain = _universe(d)
        truth = r[sc].get("failing", [])
        ed = A.get("edited_test_files", [])
        sa, seta = _scored(A, universe, plain, truth, ed)
        sb, setb = _scored(Bv, universe, plain, truth, ed)
        st["sel_a"] += len(seta)
        st["sel_b"] += len(setb)
        row_n = ((r[sc].get("tools") or {}).get("proviso") or {}).get("selected")
        if row_n is not None and row_n != sa["selected"]:
            sanity.append((proj, r["id"][:10], sc, row_n, sa["selected"]))
        if A["sel"] == Bv["sel"]:
            st["identical"] += 1
        else:
            diffs.append((kind, proj, r["id"][:10], sc, sa["selected"], sb["selected"], A.get("import_state_n"),
                          Bv.get("import_state_n"), A.get("reason"), Bv.get("reason")))
        ga, gb = set(sa["missed"]), set(sb["missed"])
        if gb - ga:
            st["gained_missed"] += 1
            gains.append((kind, proj, r["id"][:10], sc, sorted(gb - ga)[:5]))
        if ga - gb:
            st["lost_missed"] += 1
    L = [f"# Offline re-score: Proviso {a} vs {b}", "",
         "Selection only, from each item's saved map (no test run). Missed failures against the row's confirmed "
         "failures, scored as b1.py does. `research/v2/rescore_v232.py`.", "",
         "| Set | Project | Items (pair x scenario) | Identical selections | Errors | Items gaining a missed failure | "
         f"Items losing one | Tests selected, {a} | Tests selected, {b} |", "|---|---|---|---|---|---|---|---|---|"]
    for (kind, proj), st in sorted(stats.items()):
        L.append(f"| {kind} | {proj} | {st['items']} | {st['identical']} | {st['errors']} | {st['gained_missed']} | "
                 f"{st['lost_missed']} | {st['sel_a']} | {st['sel_b']} |")
    L += ["", f"Sanity ({a} recomputed = the row's recorded size): {len(sanity)} mismatches"
          + (f": {sanity[:10]}" if sanity else ""), "",
          f"Items whose selection differs ({len(diffs)}):", ""]
    for x in diffs[:60]:
        L.append(f"- {x[0]} {x[1]} {x[2]} {x[3]}: selected {x[4]} -> {x[5]}; changed values {x[6]} -> {x[7]}"
                 + (f"; reason {x[8]!r} -> {x[9]!r}" if x[8] or x[9] else ""))
    L += ["", f"Items gaining a missed failure ({len(gains)}):" + ("" if gains else " none"), ""]
    for x in gains:
        L.append(f"- {x[0]} {x[1]} {x[2]} {x[3]}: {x[4]}")
    out = os.path.join(b1.OUT, f"RESCORE_{b}.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    return stats, gains, diffs, sanity


def write_rows(b, projects, with_b1b):
    """Add tools['proviso-<b>'] (scored like tools['proviso'], which stays the recorded version) to each row."""
    key = f"proviso-{b}"
    for name in projects:
        b1.use(name)
        for path in sorted(glob.glob(os.path.join(b1.res(), "rows.w*.jsonl"))):
            rows = [json.loads(l) for l in open(path) if l.strip()]
            n = 0
            for r in rows:
                fb = PL.jload(os.path.join(PL.WORK, "rescore", b, f"{r['id'][:12]}.json")) or {}
                for sc in ("S", "F"):
                    if r.get("status") != "ok" or sc not in r or sc not in fb or "tools" not in r[sc]:
                        continue
                    if "error" in fb[sc]:
                        r[sc]["tools"][key] = {"error": fb[sc]["error"]}
                    else:
                        universe, plain = _universe(os.path.join(PL.WORK, "b1", r["id"][:12]))
                        s, _ = _scored(fb[sc], universe, plain, r[sc].get("failing", []),
                                       fb[sc].get("edited_test_files", []))
                        r[sc]["tools"][key] = {**s, "full": fb[sc]["sel"] is None, "reason": fb[sc].get("reason"),
                                               "import_state_changed": fb[sc].get("import_state_n"),
                                               "offline": "selection from the saved map (rescore_v232.py)"}
                    n += 1
            if n:
                tmp = path + ".tmp"
                open(tmp, "w").writelines(json.dumps(r) + "\n" for r in rows)
                os.replace(tmp, path)
            print(name, os.path.basename(path), n, "items", flush=True)
    if with_b1b:
        B = _b1b()
        import swe_probe as P
        for path in sorted(glob.glob(os.path.join(B.OUT, "rows.w*.jsonl"))):
            rows = [json.loads(l) for l in open(path) if l.strip()]
            n = 0
            for r in rows:
                fb = PL.jload(os.path.join(P.WORK, "rescore", b, f"{r['id']}.json")) or {}
                if r.get("status") != "ok" or "R" not in fb or "tools" not in (r.get("R") or {}):
                    continue
                if "error" in fb["R"]:
                    r["R"]["tools"][key] = {"error": fb["R"]["error"]}
                else:
                    universe, plain = _universe(os.path.join(PL.BASE_WORK, f"b1b-{r['repo']}", "b1b", r["id"]))
                    s, _ = _scored(fb["R"], universe, plain, r["R"].get("failing", []), [])
                    r["R"]["tools"][key] = {**s, "full": fb["R"]["sel"] is None, "reason": fb["R"].get("reason"),
                                            "import_state_changed": fb["R"].get("import_state_n"),
                                            "offline": "selection from the saved map (rescore_v232.py)"}
                n += 1
            if n:
                tmp = path + ".tmp"
                open(tmp, "w").writelines(json.dumps(r) + "\n" for r in rows)
                os.replace(tmp, path)
            print("b1b", os.path.basename(path), n, "items", flush=True)


def main():
    a = sys.argv[1:]
    if a[0] == "select" and a[2] == "b1":
        select_b1(a[1], a[3])
    elif a[0] == "select" and a[2] == "b1b":
        select_b1b(a[1], set(a[3:]) or None)
    elif a[0] == "compare":
        compare(a[1], a[2], a[3:] or ["sqlglot", "pygments", "loguru"])
    elif a[0] == "write-rows":
        rest = [x for x in a[2:] if not x.startswith("--")]
        write_rows(a[1], rest or ["sqlglot", "pygments", "loguru"], "--b1b" in a)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
