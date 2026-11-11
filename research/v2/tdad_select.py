"""TDAD (Alonso, Yovine, Braberman 2026; github.com/pepealonso95/TDAD @ 73d1234) as a baseline selector, run through
its own Python API, unmodified, with its default NetworkX backend and "balanced" strategy:
  index(tree)                    build_graph + link_tests on the base tree (TDAD keeps its graph in TREE/.tdad/)
  select(tree, files, cap)       get_impacted_tests(tree, db, changed files, strategy="balanced", max_tests=cap)
TDAD's default cap is 50 tests; select(..., cap=None) gives the uncapped selection (to separate the cap's effect).
select(..., keep=f) applies the cap only to the tests the evaluation measures (keep(base) is true): TDAD ranks every test
of the repository, and on SQLAlchemy its top 50 for a change in lib/sqlalchemy/sql/ fall in test/dialect and
test/aaa_profiling, outside the benchmark's test folders (test/base, test/sql), so a plain cap left nothing to score. With
keep, the result is TDAD's own ranking and tiers (high/medium/low by score, sorted by score) cut at 50 among the measured
tests: what TDAD selects when only those folders exist.
Its test ids ("test::FILE::Class.method:LINE") are mapped to pytest node ids (FILE::Class::method, all parameters)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

TDAD_SRC = os.environ.get("TDAD_SRC", os.path.expanduser("~/proviso-work/v2/TDAD/tdad/src"))
_ID = re.compile(r"^test::(?P<file>[^:]+\.py)::(?P<name>.+?)(?::\d+)?$")


def _api():
    if TDAD_SRC not in sys.path:
        sys.path.insert(0, TDAD_SRC)
    from tdad.core.config import get_settings, get_db
    from tdad.indexer.graph_builder import build_graph
    from tdad.indexer.test_linker import link_tests
    from tdad.analyzer.impact import get_impacted_tests
    return get_settings, get_db, build_graph, link_tests, get_impacted_tests


def index(tree: str) -> None:
    get_settings, get_db, build_graph, link_tests, _ = _api()
    repo = Path(tree).resolve()
    if (repo / ".tdad" / "graph.pkl").exists():
        return
    with get_db(get_settings(), repo_path=repo) as db:
        build_graph(repo, db, force=True)
        link_tests(repo, db)


def select(tree: str, files: list[str], cap: int | None = 50, keep=None) -> set[str]:
    """Pytest node-id bases (FILE::Class::method) of the tests TDAD selects for the changed files (in TDAD's order;
    with keep, the cap counts only the tests keep accepts)."""
    get_settings, get_db, _, _, get_impacted_tests = _api()
    repo = Path(tree).resolve()
    with get_db(get_settings(), repo_path=repo) as db:
        tests = get_impacted_tests(repo, db, files, strategy="balanced",
                                   max_tests=10 ** 9 if (keep or not cap) else cap)
    return bases(tests, cap, keep)


def bases(tests: list[dict], cap: int | None = 50, keep=None) -> set[str]:
    """TDAD's result list (best first) as pytest node-id bases; with keep, cut at cap among the accepted tests."""
    out, order = set(), []
    for t in tests:
        m = _ID.match(t.get("test_id", ""))
        if m:
            base = f"{m.group('file')}::{m.group('name').replace('.', '::')}"
        elif t.get("test_file") and t.get("test_name"):
            base = f"{t['test_file']}::{t['test_name'].replace('.', '::')}"
        else:
            continue
        if keep is not None and not keep(base):
            continue
        if base not in out:
            out.add(base)
            order.append(base)
        if cap and keep is not None and len(order) >= cap:
            break
    return out


# SQLAlchemy's per-backend test classes are renamed when collected: DocTest becomes DocTest_sqlite+pysqlite_3_53_1
# (name_dialect+driver_version), while TDAD names the class as written in the source
_BACKEND = re.compile(r"_[A-Za-z0-9]+\+[A-Za-z0-9]+(?:_[0-9_]+)?$")


def base_of(node: str) -> str:
    """A pytest node id as TDAD names it: parameters dropped, per-backend class suffixes removed."""
    parts = node.split("[", 1)[0].split("::")
    return "::".join([parts[0]] + [_BACKEND.sub("", p) for p in parts[1:]])


def expand(bases: set[str], universe: set[str]) -> set[str]:
    """All node ids of the universe whose base (parameters and backend suffixes dropped) TDAD selected."""
    return {n for n in universe if base_of(n) in bases}


def measured(universe: set[str]):
    """keep() for select(): the tests the evaluation measures."""
    known = {base_of(n) for n in universe}
    return known.__contains__
