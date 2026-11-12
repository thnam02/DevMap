"""Claude Code reports the shell's current directory as the hook's cwd; after `cd pkg/sub` the hook must still find
the project at the repository top (pilot run pylint-4970 impact-noreport 1: a broad pytest went unrewritten)."""
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

from dc_engine import hooks  # noqa: E402


class HookRoot(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", self.d], check=True)
        os.makedirs(os.path.join(self.d, ".dc-engine"))
        os.makedirs(os.path.join(self.d, "pkg", "sub"))
        os.makedirs(os.path.join(self.d, "tests"))
        open(os.path.join(self.d, ".dc-engine", "covmap.json"), "w").write("{}")
        json.dump({"impact": True}, open(os.path.join(self.d, ".dc-engine", "proviso.json"), "w"))

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def pretool(self, cwd, command):
        return hooks.handle("proviso-pretool", {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})

    def test_from_a_subdirectory(self):
        sub = os.path.join(self.d, "pkg", "sub")
        out = self.pretool(sub, "cd ../.. && python -m pytest tests/test_a.py")
        new = out["hookSpecificOutput"]["updatedInput"]["command"]
        self.assertIn("dc_engine.impact run", new)
        self.assertTrue(new.startswith("cd ../.. && "))
        self.assertFalse(os.path.exists(os.path.join(sub, ".dc-engine")))  # no state written into the subdirectory

    def test_at_the_top(self):
        out = self.pretool(self.d, "python -m pytest tests/test_a.py")
        self.assertIn("dc_engine.impact run", out["hookSpecificOutput"]["updatedInput"]["command"])

    def test_root_resolution(self):
        self.assertEqual(hooks._project_root(os.path.join(self.d, "pkg", "sub")), os.path.abspath(self.d))
        outside = tempfile.mkdtemp()
        try:
            self.assertEqual(hooks._project_root(outside), os.path.abspath(outside))
        finally:
            shutil.rmtree(outside, True)


if __name__ == "__main__":
    unittest.main()
