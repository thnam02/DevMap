"""dc_eval run copies: history up to the task's commit only (later commits, such as the upstream fix, out of reach),
with objects borrowed from one base-only store, so a run stores only its working tree."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval.run import _fresh_copy  # noqa: E402


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, capture_output=True,
                          text=True)


class Copy(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src = os.path.join(self.d, "src")
        os.makedirs(self.src)
        git(self.src, "init", "-q")
        open(os.path.join(self.src, "a.py"), "w").write("x = 1\n")
        git(self.src, "add", ".")
        git(self.src, "commit", "-qm", "base")
        self.base = git(self.src, "rev-parse", "HEAD").stdout.strip()
        open(os.path.join(self.src, "a.py"), "w").write("x = 2  # the fix\n")
        git(self.src, "commit", "-qam", "fix")
        self.fix = git(self.src, "rev-parse", "HEAD").stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def test_copy(self):
        for n in (1, 2):
            dest = os.path.join(self.d, "runs", str(n), "repo")
            _fresh_copy(self.src, self.base, dest)
            self.assertEqual(open(os.path.join(dest, "a.py")).read(), "x = 1\n")
            self.assertEqual(git(dest, "rev-parse", "HEAD").stdout.strip(), self.base)
            self.assertNotEqual(git(dest, "cat-file", "-e", self.fix).returncode, 0)  # the fix is out of reach
            self.assertNotIn(self.fix, git(dest, "log", "--all", "--format=%H").stdout)
            open(os.path.join(dest, "a.py"), "w").write("x = 3\n")
            self.assertIn("x = 3", git(dest, "diff").stdout)
        stores = [n for n in os.listdir(self.d) if ".base-" in n]
        self.assertEqual(len(stores), 1, stores)


if __name__ == "__main__":
    unittest.main()
