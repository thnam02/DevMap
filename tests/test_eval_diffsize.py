"""dc_eval's diff size counts the lines of new files too (pilot: pylint-5610's fix was one new 89-line file and
counted 0)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval.grade import working_tree_stats  # noqa: E402


class DiffSize(unittest.TestCase):
    def test_new_file_lines_count(self):
        d = tempfile.mkdtemp()
        try:
            open(os.path.join(d, "a.py"), "w").write("x = 1\n")
            for c in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "b"]):
                subprocess.run(["git", *c], cwd=d, check=True)
            open(os.path.join(d, "a.py"), "w").write("x = 2\n")                 # 1 added + 1 removed
            open(os.path.join(d, "new.py"), "w").write("a = 1\nb = 2\nc = 3")   # 3 new lines, no final newline
            open(os.path.join(d, "blob.bin"), "wb").write(b"\0\1\2\n")           # binary: not counted
            s = working_tree_stats(d)
            self.assertEqual(s["diff_size"], 5)
            self.assertIn("new.py", s["changed_files"])
        finally:
            shutil.rmtree(d, True)


if __name__ == "__main__":
    unittest.main()
