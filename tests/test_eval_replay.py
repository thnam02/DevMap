"""dc_eval for replay tasks: the starting patch is applied (uncommitted) to the run's copy, tasks can share an
assets folder, and the total spend cap counts each run once."""
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

from dc_eval.run import apply_start_patch, spent_usd  # noqa: E402
from dc_eval.tasks import Task  # noqa: E402

PATCH = """diff --git a/mod.py b/mod.py
--- a/mod.py
+++ b/mod.py
@@ -1,2 +1,2 @@
 def f():
-    return 1
+    return 3
"""


class Replay(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        open(os.path.join(self.d, "mod.py"), "w").write("def f():\n    return 1\n")
        for c in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "b"]):
            subprocess.run(["git", *c], cwd=self.d, check=True)

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def test_start_patch_applied_uncommitted(self):
        apply_start_patch(self.d, PATCH)
        self.assertIn("return 3", open(os.path.join(self.d, "mod.py")).read())
        diff = subprocess.run(["git", "diff", "--stat"], cwd=self.d, capture_output=True, text=True).stdout
        self.assertIn("mod.py", diff)

    def test_start_patch_that_does_not_apply(self):
        with self.assertRaises(RuntimeError):
            apply_start_patch(self.d, PATCH.replace("return 1", "return 9"))

    def test_task_fields(self):
        t = Task.from_dict({"id": "x__c0", "repo": "r", "commit": "c", "prompt": "p", "start_patch": PATCH,
                            "assets": "x"})
        self.assertEqual((t.assets, t.start_patch), ("x", PATCH))

    def test_spent_counts_each_run_once(self):
        p = os.path.join(self.d, "results.jsonl")
        with open(p, "w") as fh:
            for row in ({"task": "a", "arm": "b", "rep": 1, "cost_usd": 0.5},
                        {"task": "a", "arm": "b", "rep": 1, "cost_usd": 0.5},   # regraded: same run
                        {"task": "a", "arm": "i", "rep": 1, "cost_usd": 0.25}):
                fh.write(json.dumps(row) + "\n")
        self.assertAlmostEqual(spent_usd(p), 0.75)


if __name__ == "__main__":
    unittest.main()
