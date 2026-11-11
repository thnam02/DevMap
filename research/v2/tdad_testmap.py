"""TDAD as its paper evaluates it, on the main benchmark's planted bugs.

TDAD (Alonso, Yovine, Braberman 2026; github.com/pepealonso95/TDAD @ 73d1234) gives the agent a static test map, not a
ranked list: "Stage 2 exports impacted tests as a static test map. The agent uses grep on the test map to find tests to
verify" (paper.tex, Fig. 1); SKILL.md: for each changed file, grep .tdad/test_map.txt, collect the test files listed,
run them (`python -m pytest <test_files>`); if a changed file has no entry, fall back to finding tests by convention
(src/foo/bar.py -> tests/test_bar.py or tests/foo/test_bar.py) and by searching the tests for imports of the module.

Here, unmodified TDAD code:
  index    what `tdad index` does: build_graph, link_tests, export_test_map (NetworkX backend, the default)
  lookup   each changed file's entry in .tdad/test_map.txt; with no entry, SKILL.md step 4's two fallbacks
  select   every test of the evaluation universe in those test files (pytest runs whole files)
Scored on the planted bugs (one base commit per repository, so one index), against the same universe, failing tests
and base test times as the other selectors. Rows: results/<repo>/tdad_map.jsonl. sympy is left out: TDAD's indexing
ran out of memory there (over 23 GB). Real commits need a tree and test times per commit, which live on the PC.

  python3 research/v2/tdad_testmap.py sqlglot pygments datasette sqlalchemy   (TDAD_SRC: TDAD's src directory)"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline as PL  # noqa: E402
import tdad_select as T  # noqa: E402

TREES = os.environ.get("TDAD_TREES", os.path.join(os.path.expanduser("~"), "tdad-trees"))


def tree_at(repo: str, url: str, commit: str) -> str:
    d = os.path.join(TREES, repo)
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(d, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        subprocess.run(["git", "remote", "add", "origin", url], cwd=d, check=True)
    have = subprocess.run(["git", "cat-file", "-e", commit], cwd=d, capture_output=True).returncode == 0
    if not have:
        subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", commit], cwd=d, check=True)
    subprocess.run(["git", "checkout", "-q", "-f", commit], cwd=d, check=True)
    subprocess.run(["git", "clean", "-q", "-fdx", "-e", ".tdad"], cwd=d, check=True)
    return d


def index(tree: str) -> dict[str, list[str]]:
    """`tdad index`, then the test map it exports."""
    path = Path(tree) / ".tdad" / "test_map.txt"
    if not path.exists():
        get_settings, get_db, build_graph, link_tests, _ = T._api()
        from tdad.analyzer.impact import export_test_map
        with get_db(get_settings(), repo_path=Path(tree)) as db:
            build_graph(Path(tree), db, force=True)
            link_tests(Path(tree), db)
            export_test_map(db, Path(tree))
        # the graph is only needed to export the map; TDAD rewrites it on every close (1.1 GB on SQLAlchemy)
        g = Path(tree) / ".tdad" / "graph.pkl"
        if g.exists():
            g.unlink()
    out = {}
    for line in path.read_text().splitlines():
        if ": " in line and not line.startswith("#"):
            src, tests = line.split(": ", 1)
            out[src] = tests.split()
    return out


def fallback(tree: str, changed: str, test_dirs: list[str]) -> list[str]:
    """SKILL.md step 4: tests named after the module, and test files importing it."""
    stem = Path(changed).stem
    parent = Path(changed).parent.name
    found = set()
    for td in test_dirs:
        for cand in (f"{td}/test_{stem}.py", f"{td}/{parent}/test_{stem}.py"):
            if os.path.exists(os.path.join(tree, cand)):
                found.add(cand)
        r = subprocess.run(["grep", "-rlE", f"from.*{re.escape(stem)} import|import.*{re.escape(stem)}", td,
                            "--include=*.py"], cwd=tree, capture_output=True, text=True)
        found |= {l.strip() for l in r.stdout.splitlines() if l.strip()}
    return sorted(found)


def run(repo: str):
    PL.use(repo)
    cfg = PL.CFG
    tree = tree_at(repo, cfg["url"], cfg["commit"])
    tmap = index(tree)
    base = json.load(open(os.path.join(PL.RES, "base_outcomes.json")))
    universe = {n for n in base if "::" in n and PL.ok_filter(PL.failing(base))(n)}
    plain = {n: t for n, (ok, t) in base.items()}
    tot = sum(plain.get(n, 0) for n in universe) or 1e-9
    truth = PL.merged("truth")
    test_dirs = [cfg.get("test_dirs") or "tests"] if isinstance(cfg.get("test_dirs"), str) else (cfg.get("test_dirs") or ["tests"])
    out_path = os.path.join(PL.RES, "tdad_map.jsonl")
    rows = []
    for rid, row in PL.merged("select").items():
        b = truth.get(rid)
        if not b:
            continue
        changed = b["file"]
        files, how = tmap.get(changed, []), "map"
        if not files:
            files, how = fallback(tree, changed, test_dirs), "fallback"
        fset = set(files)
        sel = {n for n in universe if n.split("::", 1)[0] in fset}
        fails = PL.truth_failing(b, universe)
        rows.append({"id": rid, "changed": changed, "how": how, "test_files": files, "selected": len(sel),
                     "missed": sorted(set(fails) - sel), "time_share": round(sum(plain.get(n, 0) for n in sel) / tot, 4)})
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return rows, len(universe), len(tmap)


def score(repo: str) -> dict:
    """Changes with a missed failure and mean time share, filtered exactly like the gate report (PL._confirmed)."""
    PL.use(repo)
    tm = {}
    for line in open(os.path.join(PL.RES, "tdad_map.jsonl")):
        r = json.loads(line)
        tm[r["id"]] = {"selected": r["selected"], "missed": r["missed"], "time_share": r["time_share"]}
    rows = [{**r, "selectors": {**r["selectors"], "tdad_map": tm[r["id"]]}} for r in PL.merged("select").values()
            if r["id"] in tm]
    rows = PL._confirmed(rows, "select")
    res = {}
    for k in ("proviso", "namerts", "tdad", "tdad_map"):
        have = [r for r in rows if k in r["selectors"] and "error" not in r["selectors"][k]]
        res[k] = {"changes": len(have), "missed": sum(1 for r in have if r["truth"] and r["selectors"][k]["missed"]),
                  "tests_missed": sum(len(r["selectors"][k]["missed"]) for r in have if r["truth"]),
                  "time": round(100 * sum(r["selectors"][k]["time_share"] for r in have) / max(1, len(have)), 1)}
    return res


if __name__ == "__main__":
    for repo in sys.argv[1:]:
        rows, nu, nmap = run(repo)
        fb = sum(r["how"] == "fallback" for r in rows)
        print(f"{repo}: test map {nmap} source files; universe {nu}; {len(rows)} planted bugs ({fb} by fallback)", flush=True)
        print(f"  {score(repo)}", flush=True)
