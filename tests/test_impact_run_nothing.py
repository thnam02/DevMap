"""Proviso's runner never answers "no new failures" when pytest ran nothing (replay check: a broken pytest, a path
that does not exist), and names a session-level failure instead of printing an empty test id."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_engine import impact as I  # noqa: E402


class RunNothing(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "tests"))
        os.makedirs(os.path.join(self.d, I.STATE_DIR))
        open(os.path.join(self.d, "tests", "test_a.py"), "w").write("def test_a():\n    assert True\n")
        subprocess.run(["git", "init", "-q", self.d], check=True)

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def run_(self, targets):
        return I.run_selected(self.d, sys.executable, targets)

    def test_normal(self):
        out = self.run_(["tests"])
        self.assertIn("No new failures", out)

    def test_missing_path(self):
        out = self.run_(["nonexistent_dir"])
        self.assertIn("did not run", out)
        self.assertNotIn("No new failures", out)

    def test_broken_conftest(self):
        open(os.path.join(self.d, "conftest.py"), "w").write("raise ImportError('broken by the change')\n")
        out = self.run_(["tests"])
        self.assertNotIn("No new failures", out)
        self.assertIn("broken by the change", out)

    def test_long_selection_without_argfile(self):
        """Over 200 node ids: pytest gets the test files and the outcome plugin keeps only the selected ids (pytest
        before 8.2 reads "@file" as a path and runs nothing)."""
        open(os.path.join(self.d, "tests", "test_p.py"), "w").write(
            "import pytest\n@pytest.mark.parametrize('i', range(300))\ndef test_p(i):\n    assert i != 299\n")
        ids = [f"tests/test_p.py::test_p[{i}]" for i in range(250)] + ["tests/test_a.py::test_a"]
        res, out = I._pytest(self.d, sys.executable, ids, "impact-args.txt")
        self.assertEqual(len(res), 251, out[-500:])
        self.assertTrue(all(res.values()))
        self.assertNotIn("tests/test_p.py::test_p[299]", res)


if __name__ == "__main__":
    unittest.main()
