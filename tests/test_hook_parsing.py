"""Which agent commands Proviso rewrites, and with which targets (replay check with Haiku: words of a git command,
unexpanded $VARS and globs, redirection files were taken for test targets)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import shutil
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_engine.impact import _broad_targets, rewrite  # noqa: E402


class Targets(unittest.TestCase):
    def test_plain_runs(self):
        self.assertEqual(_broad_targets("pytest"), [])
        self.assertEqual(_broad_targets("python -m pytest tests/test_a.py -q"), ["tests/test_a.py"])
        self.assertEqual(_broad_targets("/venv/bin/pytest testing"), ["testing"])
        self.assertEqual(_broad_targets("timeout 600 python3 -m pytest xarray/tests -x"), ["xarray/tests"])

    def test_a_path_containing_pytest_is_not_pytest(self):
        self.assertIsNone(_broad_targets("git -C /work/pytest diff --stat"))
        self.assertIsNone(_broad_targets("cd src/_pytest"))
        self.assertIsNone(_broad_targets("cat src/_pytest/pathlib.py"))

    def test_redirections_end_the_targets(self):
        self.assertEqual(_broad_targets("pytest tests/test_a.py > /tmp/out.txt"), ["tests/test_a.py"])
        self.assertEqual(_broad_targets("pytest tests 2>&1"), ["tests"])
        self.assertEqual(_broad_targets("pytest tests 2> err.log"), ["tests"])

    def test_shell_patterns_are_left_alone(self):
        self.assertIsNone(_broad_targets("pytest $S"))
        self.assertIsNone(_broad_targets("pytest tests/test_ext_autodoc*.py"))
        self.assertIsNone(_broad_targets("pytest ~/x/tests"))

    def test_filters_and_ids_stay_narrow(self):
        self.assertIsNone(_broad_targets("pytest tests -k foo"))
        self.assertIsNone(_broad_targets("pytest tests/test_a.py::test_x"))

    def test_rewrite_keeps_other_segments(self):
        new = rewrite("git diff --stat && pytest tests | tail -5", "/py", "/tpy")
        self.assertTrue(new.startswith("git diff --stat && "))
        self.assertIn("dc_engine.impact run --python /tpy -- tests", new)
        self.assertIsNone(rewrite("git -C /w/pytest diff; git -C /w/pytest status", "/py", "/tpy"))


class StepAside(unittest.TestCase):
    """A target outside the project or missing here: pytest runs the agent's targets as written."""

    def test_missing_target(self):
        d = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-q", d], check=True)
            r = subprocess.run([sys.executable, "-m", "dc_engine.impact", "run", "--python", sys.executable, "--",
                                "no_such_dir"], cwd=d, capture_output=True, text=True,
                               env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(HERE), "src")})
            out = r.stdout + r.stderr
            self.assertNotIn("No new failures", out)
            self.assertIn("no_such_dir", out)  # pytest's own "file or directory not found"
            self.assertNotEqual(r.returncode, 0)
        finally:
            shutil.rmtree(d, True)


if __name__ == "__main__":
    unittest.main()
