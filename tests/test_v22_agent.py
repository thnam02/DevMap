"""(v2.2) Agent behaviour the benchmarks do not exercise: the agent commits its edits (the change is measured from
the commit the map was recorded at, not HEAD), and edits files that are not Python (data the code or tests read:
the full suite runs)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_engine import impact as I  # noqa: E402
from dc_engine import record as REC  # noqa: E402

CORE = '''import json, os

def limit():
    return json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))["limit"]

def double(x):
    return 2 * x

def triple(x):
    return 3 * x
'''
TESTS = '''from pkg.core import limit, double, triple
def test_limit():
    assert limit() == 5
def test_double():
    assert double(2) == 4
def test_triple():
    assert triple(2) == 6
'''


class AgentBehaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        r = cls.root
        for p, c in {"pkg/__init__.py": "", "pkg/core.py": CORE, "pkg/settings.json": '{"limit": 5}\n',
                     "pkg/templates/page.html": "<p/>\n", "tests/test_core.py": TESTS,
                     "tests/data/expected.yaml": "x: 1\n"}.items():
            os.makedirs(os.path.dirname(os.path.join(r, p)), exist_ok=True)
            open(os.path.join(r, p), "w").write(c)
        cls.git("init", "-q")
        cls.git("add", "-A")
        cls.git("commit", "-qm", "base")
        cls.git("tag", "BASE")
        os.makedirs(os.path.join(r, ".dc-engine"))
        cls.cov = REC.record(r, "pkg", os.path.join(r, ".dc-engine", "covmap.json"), sys.executable, ["tests"], 1, "",
                             ["-p", "no:randomly"], {**os.environ, "PYTHONPATH": r})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    @classmethod
    def git(cls, *a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=cls.root, check=True,
                              capture_output=True, text=True).stdout

    def tearDown(self):
        self.git("checkout", "-qf", "BASE")
        self.git("clean", "-qfd", "-e", ".dc-engine")

    def edit(self, path, old, new):
        p = os.path.join(self.root, path)
        text = open(p).read()
        self.assertIn(old, text)
        open(p, "w").write(text.replace(old, new, 1))

    def sel(self):
        sel, why = I.selection(self.root, self.cov, sys.executable)
        return (None if sel is None else sorted(t.rsplit("::", 1)[-1] for t in sel)), why

    def test_map_records_its_commit(self):
        self.assertEqual(self.cov["__base__"]["commit"], self.git("rev-parse", "BASE").strip())

    def test_committed_edit_still_selects(self):
        self.edit("pkg/core.py", "2 * x", "3 * x")
        self.assertEqual(self.sel()[0], ["test_double"])
        self.git("commit", "-qam", "agent commit")
        self.assertEqual(self.sel()[0], ["test_double"])
        self.edit("pkg/core.py", "def triple(x):\n    return 3 * x", "def triple(x):\n    return 4 * x")  # uncommitted
        self.assertEqual(self.sel()[0], ["test_double", "test_triple"])

    def test_commit_then_revert_selects_nothing(self):
        self.edit("pkg/core.py", "2 * x", "3 * x")
        self.git("commit", "-qam", "c1")
        self.edit("pkg/core.py", "3 * x\n\ndef triple", "2 * x\n\ndef triple")
        self.git("commit", "-qam", "revert")
        self.assertEqual(self.sel()[0], [])

    def test_report_names_committed_edits(self):
        self.edit("pkg/core.py", "2 * x", "3 * x")
        self.git("commit", "-qam", "c1")
        sel, why = I.selection(self.root, self.cov, sys.executable)
        self.assertTrue(any("double" in line for line in I.impact_report(self.root, self.cov, why, sel)))

    def test_map_from_outside_the_history_runs_the_full_suite(self):
        self.git("checkout", "-q", "--orphan", "elsewhere")
        self.edit("pkg/core.py", "2 * x", "5 * x")   # other code: not the same tree under another commit
        self.git("commit", "-qam", "unrelated root")
        sel, why = self.sel()
        self.assertIsNone(sel)
        self.assertIn("not in the current history", why["reason"])

    def test_same_code_under_a_new_commit_is_the_base(self):
        self.git("checkout", "-q", "-b", "amended")
        self.git("commit", "-q", "--amend", "-m", "same code, new commit")
        self.edit("pkg/core.py", "2 * x", "3 * x")
        self.assertEqual(self.sel()[0], ["test_double"])
        self.git("checkout", "-qf", "BASE")
        self.git("branch", "-qD", "amended")

    def test_data_files_run_the_full_suite(self):
        for path, content in (("pkg/settings.json", '{"limit": 6}\n'), ("pkg/templates/page.html", "<b/>\n"),
                              ("tests/data/expected.yaml", "x: 2\n"), ("pkg/new_table.csv", "a,b\n")):
            with self.subTest(path):
                open(os.path.join(self.root, path), "w").write(content)
                sel, why = self.sel()
                self.assertIsNone(sel)
                self.assertIn(path, why["reason"])
                self.tearDown()

    def test_committed_data_file_runs_the_full_suite(self):
        open(os.path.join(self.root, "pkg/settings.json"), "w").write('{"limit": 6}\n')
        self.git("commit", "-qam", "data")
        self.assertIsNone(self.sel()[0])

    def test_leftovers_and_stubs_are_not_data(self):
        for name in ("pkg/core.py.bak", "pkg/core.pyi", "pkg/__pycache__/core.cpython-313.pyc", "pkg/.notes"):
            os.makedirs(os.path.dirname(os.path.join(self.root, name)), exist_ok=True)
            open(os.path.join(self.root, name), "w").write("x")
        self.assertEqual(self.sel()[0], [])

    def test_data_switch_off_restores_v21(self):
        open(os.path.join(self.root, "pkg/settings.json"), "w").write('{"limit": 6}\n')
        old = os.environ.get("PROVISO_OFF")
        os.environ["PROVISO_OFF"] = "data"
        try:
            self.assertEqual(self.sel()[0], [])
        finally:
            if old is None:
                os.environ.pop("PROVISO_OFF")
            else:
                os.environ["PROVISO_OFF"] = old


if __name__ == "__main__":
    unittest.main()
