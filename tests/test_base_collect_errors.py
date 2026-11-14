"""A test module that cannot be imported at the base (an optional dependency missing, say) is a base failure: without
it in base_failures.json, every finish check reported it as a NEW failure and sent the agent back (the first
finish-check runs: xarray-4759 blocked twice in nearly every run). The agent study's asset builder now records failing
collectors at the base."""
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
sys.path.insert(0, os.path.join(ROOT, "research", "agent"))

from dc_engine import impact as I  # noqa: E402
from dc_engine import record as REC  # noqa: E402
import swe_tasks as S  # noqa: E402

FILES = {
    "pkg/__init__.py": "",
    "pkg/colors.py": "def get(name):\n    return {'red': '#f00'}[name]\n",
    "tests/test_colors.py": "from pkg import colors\n\ndef test_red():\n    assert colors.get('red') == '#f00'\n",
    # fails to import at the base, before any change
    "tests/test_optional.py": "import not_installed_dependency_xyz\n\ndef test_x():\n    pass\n",
}


class BaseCollectErrors(unittest.TestCase):
    def setUp(self):
        self.root = r = tempfile.mkdtemp()
        for p, c in FILES.items():
            os.makedirs(os.path.dirname(os.path.join(r, p)), exist_ok=True)
            open(os.path.join(r, p), "w").write(c)
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.git("tag", "BASE")
        self.dc = os.path.join(r, ".dc-engine")
        os.makedirs(self.dc)
        open(os.path.join(self.dc, ".gitignore"), "w").write("*\n")
        self.env = S.record_env(r, sys.executable)
        self.cov = REC.record(r, "pkg", os.path.join(self.dc, "covmap.json"), sys.executable, ["tests"], 1, "",
                              ["-p", "no:randomly"], self.env)

    def tearDown(self):
        shutil.rmtree(self.root, True)

    def git(self, *a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout

    def check(self) -> str:
        """The finish check over the whole suite, after an edit that breaks nothing."""
        with open(os.path.join(self.root, "pkg", "colors.py"), "a") as fh:
            fh.write("\n# a comment\n")
        return I.run_selected(self.root, sys.executable, [], None, force_full=True)

    def test_map_has_no_trace_of_the_module(self):
        self.assertFalse([n for n in self.cov if n.startswith("tests/test_optional.py")])

    def test_collection_errors_found(self):
        self.assertEqual(S.base_collection_errors(self.root, sys.executable, ["tests"], self.env),
                         ["tests/test_optional.py"])

    def test_old_assets_report_a_false_new_failure(self):
        # the assets as built before: map failures only
        json.dump([], open(os.path.join(self.dc, "base_failures.json"), "w"))
        self.assertIn("NEW failures", self.check())

    def test_fixed_assets_report_it_as_failing_before(self):
        errs = S.base_collection_errors(self.root, sys.executable, ["tests"], self.env)
        out = S.write_base_failures(self.dc, json.load(open(os.path.join(self.dc, "covmap.json"))), errs)
        self.assertEqual(out, ["tests/test_optional.py"])
        self.assertEqual(json.load(open(os.path.join(self.dc, "base_collection_errors.json"))), errs)
        text = self.check()
        self.assertNotIn("NEW failures", text)

    def test_a_module_the_change_breaks_is_still_new(self):
        errs = S.base_collection_errors(self.root, sys.executable, ["tests"], self.env)
        S.write_base_failures(self.dc, json.load(open(os.path.join(self.dc, "covmap.json"))), errs)
        open(os.path.join(self.root, "pkg", "colors.py"), "w").write("def get(name:\n")  # syntax error
        text = I.run_selected(self.root, sys.executable, [], None, force_full=True)
        self.assertIn("NEW failures", text)
        self.assertIn("tests/test_colors.py", text)

    def test_proviso_check_too(self):
        errs = S.base_collection_errors(self.root, sys.executable, ["tests"], self.env)
        S.write_base_failures(self.dc, json.load(open(os.path.join(self.dc, "covmap.json"))), errs)
        with open(os.path.join(self.root, "pkg", "colors.py"), "a") as fh:
            fh.write("\n# a comment\n")
        self.assertNotIn("NEW failures", I.run_selected(self.root, sys.executable, [], None))


if __name__ == "__main__":
    unittest.main()
