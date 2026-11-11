"""dc_eval: a task's `python` (a prepared environment, e.g. SWE-bench's) is what the run venv inherits, and the run's
own copy of the project comes first on sys.path (not the environment's editable install of another tree)."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval import run as R  # noqa: E402
from dc_eval import tasks as T  # noqa: E402
from dc_eval.grade import install_test_env  # noqa: E402


class BasePython(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def test_run_venv_inherits_the_prepared_environment(self):
        d = self.d
        for name, where in (("repo", "run copy"), ("other", "other tree")):
            os.makedirs(os.path.join(d, name, "toypkg"))
            open(os.path.join(d, name, "toypkg", "__init__.py"), "w").write(f"WHERE = {where!r}\n")
        open(os.path.join(d, "repo", "pyproject.toml"), "w").write('[project]\nname = "toypkg"\nversion = "0"\n')
        base = os.path.join(d, "base")
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", base], check=True)
        site = glob.glob(os.path.join(base, "lib", "python3*", "site-packages"))[0]
        # the prepared environment: its own pytest (and what pytest imports) and an editable install of another tree
        import pytest
        src = os.path.dirname(os.path.dirname(pytest.__file__))
        for m in ("pytest", "_pytest", "pluggy", "iniconfig", "packaging", "pygments", "py.py"):
            if os.path.exists(os.path.join(src, m)):
                os.symlink(os.path.join(src, m), os.path.join(site, m))
        open(os.path.join(site, "zz_editable_other.pth"), "w").write(os.path.join(d, "other") + "\n")

        task = T.Task.from_dict({"id": "toy-1", "repo": "x", "commit": "y", "prompt": "p",
                                 "setup": "python -m pip install -e .", "python": os.path.join(base, "bin", "python")})
        self.assertTrue(task.python.endswith("bin/python"))
        venv = R.create_run_venv(os.path.join(d, "slot"), task.python)
        env = R.venv_env(venv)
        env["DC_EVAL_OFFLINE"] = "1"
        py = R.venv_python(venv)
        install_test_env(py, os.path.join(d, "repo"), env=env)
        R.run_setup(os.path.join(d, "repo"), task.setup, env=env)
        out = subprocess.run([py, "-c", "import toypkg, pytest; print(toypkg.WHERE)"], capture_output=True,
                             text=True, env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "run copy")

    def test_missing_interpreter_is_an_error(self):
        with self.assertRaises(RuntimeError):
            R.create_run_venv(os.path.join(self.d, "slot"), "/nonexistent/bin/python")


if __name__ == "__main__":
    unittest.main()
