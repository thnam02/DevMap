"""dc_eval grading of SWE-bench-style tasks: hidden tests come from test_patch alone (never from a later commit of
the source clone), and a regrade sees the run copy as the agent left it."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval.grade import grade_repo  # noqa: E402
from dc_eval.tasks import Task  # noqa: E402

PATCH = """diff --git a/tests/test_mod.py b/tests/test_mod.py
--- a/tests/test_mod.py
+++ b/tests/test_mod.py
@@ -3,0 +4,4 @@ def test_old():
+
+
+def test_new():
+    assert mod.f() == 2
"""


def git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


class TestPatchOnly(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        src = self.src = os.path.join(self.d, "src")
        os.makedirs(os.path.join(src, "tests"))
        open(os.path.join(src, "mod.py"), "w").write("def f():\n    return 1\n")
        open(os.path.join(src, "tests", "test_mod.py"), "w").write("import mod\n\ndef test_old():\n    assert mod.f()\n")
        git(src, "init", "-q")
        git(src, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
        git(src, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
        self.base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=src, capture_output=True, text=True).stdout.strip()
        # later, unrelated upstream history: its test file must not be used for grading
        open(os.path.join(src, "tests", "test_mod.py"), "w").write("def test_unrelated():\n    assert True\n")
        git(src, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "later")
        self.repo = os.path.join(self.d, "run", "repo")
        subprocess.run(["git", "clone", "-q", src, self.repo], check=True)
        git(self.repo, "checkout", "-q", self.base)
        open(os.path.join(self.repo, "mod.py"), "w").write("def f():\n    return 2\n")  # the agent's fix
        self.task = Task.from_dict({"id": "toy-1", "repo": src, "commit": self.base, "prompt": "p",
                                    "hidden_tests": ["tests/test_mod.py::test_new"], "test_patch": PATCH,
                                    "regression_tests": ["tests/test_mod.py::test_old"], "test_patch_only": True})

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def grade(self):
        return grade_repo(self.task, self.repo, python=sys.executable, src_repo=self.src,
                          run_dir=os.path.join(self.d, "run"))

    def test_hidden_tests_from_the_patch(self):
        g = self.grade()
        self.assertTrue(g["resolved"], g)
        self.assertEqual(g["regressions"], 0)
        self.assertEqual(g["changed_files"], ["mod.py"])

    def test_regrade_sees_the_agents_copy(self):
        first = self.grade()
        again = self.grade()
        self.assertTrue(again["resolved"], again)
        for k in ("changed_files", "diff_size", "modified_tests"):
            self.assertEqual(again[k], first[k], k)
        self.assertEqual(again["agent_modified_hidden_test_files"], [])

    def test_ids_cut_at_a_space_and_unknown_ids(self):
        """SWE-bench cuts some parametrized ids at a space; pytest then runs nothing (exit 4) unless the grader runs
        the files and matches the cut ids. An id that exists nowhere fails alone, not the whole selection."""
        open(os.path.join(self.repo, "tests", "test_par.py"), "w").write(
            "import pytest\n\n@pytest.mark.parametrize('u', ['days since 2000', 'hours since 2000'])\n"
            "def test_p(u):\n    assert u\n")
        self.task.regression_tests = ["tests/test_mod.py::test_old", "tests/test_par.py::test_p[days",
                                      "tests/test_par.py::test_p[hours", "tests/test_mod.py::test_gone"]
        g = self.grade()
        self.assertTrue(g["resolved"], g)
        self.assertEqual(g["regression_failed"], ["tests/test_mod.py::test_gone"], g["regression"])
        self.assertEqual((g["hidden_checks_passed"], g["hidden_checks_total"]), (1, 1))

    def test_without_the_flag_the_later_commit_is_used(self):  # the old behaviour, kept for mined tasks
        self.task.test_patch_only = False
        g = self.grade()
        self.assertFalse(g["resolved"])


if __name__ == "__main__":
    unittest.main()
