"""Incremental recording (v2.4): after a change, the map brought up to date from the old one must describe the new
commit as a fresh recording does, while re-recording only the test files that can have changed."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from dc_engine import impact as I  # noqa: E402
from dc_engine import incremental as INC  # noqa: E402
from dc_engine import record as REC  # noqa: E402

BASE = {
    "pkg/__init__.py": "",
    "pkg/a.py": "def f(x):\n    return x + 1\n\n\ndef g(x):\n    return x * 2\n",
    "pkg/b.py": "import functools\n\n\n@functools.lru_cache\ndef h(x):\n    return x - 1\n",
    "tests/test_a.py": "from pkg.a import f\n\n\ndef test_f():\n    assert f(1) == 2\n",
    "tests/test_b.py": "from pkg.b import h\n\n\ndef test_h():\n    assert h(1) == 0\n",
    "tests/test_gone.py": "from pkg.a import g\n\n\ndef test_g():\n    assert g(2) == 4\n",
}


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def write(root, files):
    for p, s in files.items():
        full = os.path.join(root, p)
        if s is None:
            os.remove(full)
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write(s)


class LineMapTest(unittest.TestCase):
    def test_lines_move_with_an_insertion_and_edited_lines_do_not(self):
        m = INC.line_map("a\nb\nc\nd\n", "x\ny\na\nb\nC\nd\n")
        self.assertEqual(m[1], 3)
        self.assertEqual(m[2], 4)
        self.assertNotIn(3, m)
        self.assertEqual(m[4], 6)

    def test_move_reports_an_unmovable_key(self):
        maps = {"p.py": {1: 3}}
        self.assertEqual(INC._move([["p.py", 1], ["q.py", 7]], maps, {"p.py"}), ([["p.py", 3], ["q.py", 7]], True))
        self.assertEqual(INC._move([["p.py", 2]], maps, {"p.py"})[1], False)


class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="proviso-incr-")
        write(self.root, BASE)
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
        self.map0 = REC.record(self.root, "pkg", os.path.join(self.root, ".map0.json"), sys.executable, workers=2)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def commit(self, files):
        write(self.root, files)
        git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "change")

    def test_matches_a_fresh_recording_and_keeps_unaffected_files(self):
        # an edit above f moves it down 4 lines; g changes; a test file is deleted, another added
        self.commit({"pkg/a.py": "# helper\ndef k():\n    return 0\n\n\n" + BASE["pkg/a.py"].replace("x * 2", "x * 3"),
                     "tests/test_gone.py": None,
                     "tests/test_new.py": "from pkg.a import k\n\n\ndef test_k():\n    assert k() == 0\n"})
        selected, _ = I.selection(self.root, self.map0, sys.executable)
        self.assertIsNotNone(selected)
        new = INC.update(self.map0, self.root, "pkg", os.path.join(self.root, ".map1.json"), selected, sys.executable,
                         workers=2)
        fresh = REC.record(self.root, "pkg", os.path.join(self.root, ".fresh.json"), sys.executable, workers=2)
        d = INC.compare(new, fresh)
        self.assertEqual((d["only_in_a"], d["only_in_b"], d["differ"], d["global_missing_in_a"]), (0, 0, 0, 0), d)
        inc = new["__incremental__"]
        self.assertIsNone(inc["full"])
        self.assertIn("tests/test_new.py::test_k", new)
        self.assertNotIn("tests/test_gone.py::test_g", new)
        # test_a and test_b ran nothing that changed: kept, with f's key moved from line 1 to line 6
        self.assertEqual(inc["rerecorded_files"], 1, inc)
        self.assertIn(["pkg/a.py", 6], new["tests/test_a.py::test_f"]["funcs"])
        self.assertEqual(new["__base__"]["commit"], git(self.root, "rev-parse", "HEAD").strip())

    def test_an_edited_first_line_re_records_its_tests(self):
        # h's decorator line (its recorded first line) is edited: test_b cannot keep its record
        self.commit({"pkg/b.py": BASE["pkg/b.py"].replace("@functools.lru_cache", "@functools.lru_cache(maxsize=8)")})
        selected, _ = I.selection(self.root, self.map0, sys.executable)
        new = INC.update(self.map0, self.root, "pkg", os.path.join(self.root, ".map1.json"), selected or [],
                         sys.executable, workers=2)
        fresh = REC.record(self.root, "pkg", os.path.join(self.root, ".fresh.json"), sys.executable, workers=2)
        self.assertEqual(INC.compare(new, fresh)["differ"], 0)
        self.assertIn("tests/test_b.py::test_h", new)
        self.assertEqual(new["__incremental__"]["rerecorded_files"], 1, new["__incremental__"])
        self.assertEqual(new["__incremental__"]["kept_tests"], 2)

    def test_whole_suite_selection_records_everything(self):
        self.commit({"pkg/a.py": BASE["pkg/a.py"] + "\n"})
        new = INC.update(self.map0, self.root, "pkg", os.path.join(self.root, ".map1.json"), None, sys.executable,
                         workers=2)
        self.assertEqual(new["__incremental__"]["full"], "selection ran the whole suite")


if __name__ == "__main__":
    unittest.main()
