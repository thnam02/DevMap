"""dc_eval's grading check imports the project's package: by its import name, not its distribution name."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval.grade import detect_import_name  # noqa: E402


class ImportName(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def make(self, files):
        for rel, text in files.items():
            p = os.path.join(self.d, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(text)

    def test_flask(self):  # pallets/flask: [project] name = "Flask", src/flask
        self.make({"pyproject.toml": '[project]\nname = "Flask"\n', "src/flask/__init__.py": ""})
        self.assertEqual(detect_import_name(self.d), "flask")

    def test_sphinx(self):  # sphinx-doc/sphinx: name = "Sphinx", sphinx/ beside tests/ and doc/
        self.make({"pyproject.toml": '[project]\nname = "Sphinx"\n', "sphinx/__init__.py": "",
                   "tests/__init__.py": "", "doc/conf.py": ""})
        self.assertEqual(detect_import_name(self.d), "sphinx")

    def test_pytest_src_layout_with_two_packages(self):
        self.make({"setup.cfg": "[metadata]\nname = pytest\n", "src/pytest/__init__.py": "",
                   "src/_pytest/__init__.py": ""})
        self.assertEqual(detect_import_name(self.d), "pytest")

    def test_sphinx_setup_py(self):  # sphinx 4.x: setup(name='Sphinx'), packages sphinx/, tests/, utils/
        self.make({"setup.py": "setup(\n    name='Sphinx',\n)\n", "sphinx/__init__.py": "",
                   "tests/__init__.py": "", "utils/__init__.py": ""})
        self.assertEqual(detect_import_name(self.d), "sphinx")

    def test_xarray_setup_cfg(self):
        self.make({"setup.cfg": "[metadata]\nname = xarray\n", "xarray/__init__.py": "", "asv_bench/x.py": ""})
        self.assertEqual(detect_import_name(self.d), "xarray")

    def test_distribution_unlike_package(self):  # scikit-learn -> sklearn
        self.make({"pyproject.toml": '[project]\nname = "scikit-learn"\n', "sklearn/__init__.py": ""})
        self.assertEqual(detect_import_name(self.d), "sklearn")

    def test_unknown_is_none(self):
        self.make({"pyproject.toml": '[project]\nname = "thing"\n', "a/__init__.py": "", "b/__init__.py": ""})
        self.assertIsNone(detect_import_name(self.d))


if __name__ == "__main__":
    unittest.main()
