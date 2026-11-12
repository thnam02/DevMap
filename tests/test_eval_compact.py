"""DC_EVAL_COMPACT=1: a graded run keeps only final.diff, logs and metrics; regrading rebuilds its copy from the base
commit and final.diff and grades it the same."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval import run as R  # noqa: E402
from dc_eval.grade import grade_repo  # noqa: E402
from dc_eval.tasks import Task  # noqa: E402

PATCH = """diff --git a/tests/test_mod.py b/tests/test_mod.py
--- a/tests/test_mod.py
+++ b/tests/test_mod.py
@@ -3,0 +4,4 @@ def test_old():
+
+
+def test_new():
+    assert toymod.f() == 2
"""


def git(cwd, *a):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, capture_output=True)


class Compact(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        src = self.src = os.path.join(self.d, "src")
        os.makedirs(os.path.join(src, "toymod"))
        os.makedirs(os.path.join(src, "tests"))
        open(os.path.join(src, "pyproject.toml"), "w").write('[project]\nname = "toymod"\nversion = "0"\n')
        open(os.path.join(src, "toymod", "__init__.py"), "w").write("def f():\n    return 1\n")
        open(os.path.join(src, "tests", "test_mod.py"), "w").write("import toymod\n\ndef test_old():\n    assert toymod.f()\n")
        git(src, "init", "-q")
        git(src, "add", ".")
        git(src, "commit", "-qm", "base")
        self.base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=src, capture_output=True, text=True).stdout.strip()
        self.task = Task.from_dict({"id": "toy-1", "repo": src, "commit": self.base, "prompt": "p",
                                    "hidden_tests": ["tests/test_mod.py::test_new"], "test_patch": PATCH,
                                    "regression_tests": ["tests/test_mod.py::test_old"], "test_patch_only": True,
                                    "setup": "python -m pip install -e .", "python": sys.executable})
        self.slot = os.path.join(self.d, "runs", "toy-1", "baseline", "1")
        self.repo = os.path.join(self.slot, "repo")
        R._fresh_copy(src, self.base, self.repo)
        venv = R.create_run_venv(self.slot, self.task.python)
        env = R.venv_env(venv)
        env["DC_EVAL_OFFLINE"] = "1"
        R.install_test_env(R.venv_python(venv), self.repo, env=env)
        R.run_setup(self.repo, self.task.setup, env=env)
        # the agent's work: a fix, a new helper file, a binary file
        open(os.path.join(self.repo, "toymod", "__init__.py"), "w").write("def f():\n    return 2\n")
        open(os.path.join(self.repo, "notes.txt"), "w").write("tried things\n")
        open(os.path.join(self.repo, "blob.bin"), "wb").write(bytes(range(256)))

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def test_compact_and_regrade(self):
        R.save_final_diff(self.repo, self.slot)
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, capture_output=True,
                                        text=True).stdout.count("??"), 2)  # the copy's index is untouched
        first = grade_repo(self.task, self.repo, python=R.venv_python(os.path.join(self.slot, "venv")),
                           src_repo=self.src, run_dir=self.slot)
        json.dump({"task": "toy-1", "arm": "baseline", "rep": 1, "status": "ok"},
                  open(os.path.join(self.slot, "metrics.json"), "w"))
        with mock.patch.dict(os.environ, {"DC_EVAL_COMPACT": "1"}):
            R.compact_slot(self.slot)
            self.assertFalse(os.path.exists(self.repo))
            row = R.regrade_slot(self.task, self.slot, src_repo=self.src)
        self.assertTrue(first["resolved"])
        self.assertEqual(row["status"], "ok", row.get("grading_error"))
        self.assertTrue(row["resolved"])
        self.assertEqual(row["diff_size"], first["diff_size"])
        self.assertEqual(row["regressions"], 0)
        self.assertFalse(os.path.exists(self.repo))  # compacted again


if __name__ == "__main__":
    unittest.main()
