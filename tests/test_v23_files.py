"""(v2.3) Per-test file records: the recorder notes the project files each test opens for reading and the directories
it lists (Python audit events); a changed data file selects the tests that read it instead of the whole suite."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_engine import impact as I  # noqa: E402
from dc_engine import record as REC  # noqa: E402

FILES = {
    "pkg/__init__.py": "",
    "pkg/core.py": (
        "import json, os\n"
        "HERE = os.path.dirname(__file__)\n"
        "with open(os.path.join(HERE, 'defaults.json')) as fh:\n"     # read at import: every test depends on it
        "    DEFAULTS = json.load(fh)\n\n"
        "def load(name):\n"
        "    return open(os.path.join(HERE, 'data', name)).read()\n\n"
        "def names():\n"
        "    return sorted(os.listdir(os.path.join(HERE, 'data')))\n\n"
        "def write_report(path):\n"
        "    with open(path, 'w') as fh:\n"
        "        fh.write('report')\n"),
    "pkg/defaults.json": '{"x": 1}\n',
    "pkg/data/a.txt": "alpha\n",
    "pkg/data/b.txt": "beta\n",
    "tests/conftest.py": (
        "import os, pytest\n"
        "SETTINGS = open(os.path.join(os.path.dirname(__file__), 'golden', 'settings.ini')).read()\n"
        "@pytest.fixture(scope='session')\n"
        "def expected():\n"
        "    return open(os.path.join(os.path.dirname(__file__), 'golden', 'expected.txt')).read()\n"),
    "tests/golden/expected.txt": "alpha\n",
    "tests/golden/unused.txt": "nobody reads this\n",
    "tests/test_files.py": (
        "import os\n"
        "from pkg.core import load, names, write_report, DEFAULTS\n"
        "def test_a(expected):\n"
        "    assert load('a.txt') == expected\n"
        "def test_b():\n"
        "    assert load('b.txt') == 'beta\\n'\n"
        "def test_names():\n"
        "    assert names() == ['a.txt', 'b.txt']\n"
        "def test_writes_only():\n"
        "    p = os.path.join(os.path.dirname(__file__), 'out.log')\n"
        "    write_report(p)\n"
        "    os.remove(p)\n"
        "def test_defaults():\n"
        "    assert DEFAULTS == {'x': 1}\n"
        "def test_glob():\n"
        "    import glob\n"
        "    assert glob.glob(os.path.join(os.path.dirname(__file__), 'golden', 'cases', '*.case'))\n"
        "def test_os_open():\n"
        "    fd = os.open(os.path.join(os.path.dirname(__file__), 'golden', 'raw.bin'), os.O_RDONLY)\n"
        "    os.close(fd)\n"),
    "tests/golden/raw.bin": "raw\n",
    "tests/inputs/sample.py": "x = 1\n",
    "tests/inputs/other.py": "y = 2\n",
    "tests/params/one.yaml": "1\n",
    "tests/test_params.py": (
        "import os, pytest\n"
        "D = os.path.join(os.path.dirname(__file__), 'params')\n"
        "CASES = sorted(os.listdir(D))\n"
        "@pytest.mark.parametrize('name', CASES)\n"
        "def test_case(name):\n"
        "    assert open(os.path.join(D, name)).read()\n"
        "def test_source_read():\n"
        "    src = open(os.path.join(os.path.dirname(__file__), 'inputs', 'sample.py')).read()\n"
        "    assert compile(src, 'sample.py', 'exec')\n"),
    "tests/golden/settings.ini": "[x]\n",
    "tests/golden/cases/one.case": "1\n",
}


class FileRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = r = tempfile.mkdtemp()
        for p, c in FILES.items():
            os.makedirs(os.path.dirname(os.path.join(r, p)), exist_ok=True)
            open(os.path.join(r, p), "w").write(c)
        cls.git("init", "-q")
        cls.git("add", "-A")
        cls.git("commit", "-qm", "base")
        cls.git("tag", "BASE")
        os.makedirs(os.path.join(r, ".dc-engine"))
        cls.cov = REC.record(r, "pkg", os.path.join(r, ".dc-engine", "covmap.json"), sys.executable, ["tests"], 1, "",
                             ["-p", "no:randomly"], {**os.environ, "PYTHONPATH": r})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    @classmethod
    def git(cls, *a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=cls.root, check=True,
                              capture_output=True, text=True).stdout

    def tearDown(self):
        self.git("checkout", "-qf", "BASE")
        self.git("clean", "-qfd", "-e", ".dc-engine")

    def write(self, path, content):
        os.makedirs(os.path.dirname(os.path.join(self.root, path)), exist_ok=True)
        open(os.path.join(self.root, path), "w").write(content)

    def sel(self):
        sel, why = I.selection(self.root, self.cov, sys.executable)
        return (None if sel is None else sorted(t.rsplit("::", 1)[-1] for t in sel)), why

    # the records
    def test_map_holds_file_records(self):
        g = self.cov["__global__"]
        self.assertTrue(g["file_records"])
        self.assertIn("pkg/defaults.json", g["files"])
        own = self.cov["tests/test_files.py::test_b"]
        self.assertEqual(own.get("files"), ["pkg/data/b.txt"])
        self.assertIn("pkg/data", self.cov["tests/test_files.py::test_names"].get("dirs", []))

    def test_writes_are_not_reads(self):
        self.assertNotIn("files", self.cov["tests/test_files.py::test_writes_only"])

    def test_fixture_reads_reach_the_tests_that_use_it(self):
        fx = self.cov["__fixtures__"]
        self.assertTrue(any("tests/golden/expected.txt" in r.get("files", []) for r in fx.values()))

    # the selections
    def test_file_read_by_one_test(self):
        self.write("pkg/data/b.txt", "BETA\n")
        self.assertEqual(self.sel()[0], ["test_b"])

    def test_file_read_in_a_session_fixture(self):
        self.write("tests/golden/expected.txt", "ALPHA\n")
        self.assertEqual(self.sel()[0], ["test_a"])

    def test_file_read_with_os_open(self):
        self.write("tests/golden/raw.bin", "RAW\n")
        self.assertEqual(self.sel()[0], ["test_os_open"])

    def test_new_file_in_a_listed_directory(self):
        self.write("pkg/data/c.txt", "gamma\n")
        self.assertEqual(self.sel()[0], ["test_names"])

    def test_deleted_file_in_a_listed_directory(self):
        os.remove(os.path.join(self.root, "pkg/data/a.txt"))
        self.assertEqual(self.sel()[0], ["test_a", "test_names"])

    def test_new_file_matched_by_a_glob(self):
        self.write("tests/golden/cases/two.case", "2\n")
        self.assertEqual(self.sel()[0], ["test_glob"])

    def test_file_read_while_conftest_imports_runs_the_full_suite(self):
        # conftest code and collection hooks may decide which tests exist
        self.write("tests/golden/settings.ini", "[y]\n")
        sel, why = self.sel()
        self.assertIsNone(sel)
        self.assertIn("collects", why["reason"])

    def test_parameter_file_added_runs_the_whole_test_file(self):
        # the new case has no test id yet: the test module that listed the directory runs whole
        self.write("tests/params/two.yaml", "2\n")
        sel, why = I.selection(self.root, self.cov, sys.executable)
        self.assertEqual(sel, ["tests/test_params.py"])

    def test_parameter_file_edited_selects_its_case(self):
        # collection only listed the directory: an edit keeps the cases, and only the case that reads the file runs
        self.write("tests/params/one.yaml", "one\n")
        sel, why = I.selection(self.root, self.cov, sys.executable)
        self.assertEqual(sel, ["tests/test_params.py::test_case[one.yaml]"])

    def test_python_file_read_as_data(self):
        self.write("tests/inputs/sample.py", "x = 2\n")
        self.assertIn("test_source_read", self.sel()[0])

    def test_python_file_nobody_reads(self):
        self.write("tests/inputs/other.py", "y = 3\n")
        self.assertNotIn("test_source_read", self.sel()[0] or [])

    def test_file_read_at_import_runs_the_full_suite(self):
        self.write("pkg/defaults.json", '{"x": 2}\n')
        sel, why = self.sel()
        self.assertIsNone(sel)
        self.assertIn("imported", why["reason"])

    def test_test_data_nobody_reads_selects_nothing(self):
        self.write("tests/golden/unused.txt", "changed\n")
        self.assertEqual(self.sel()[0], [])

    def test_untracked_leftovers_select_nothing(self):
        self.write("tests/test-server.lock", "1234\n")
        self.write("pkg/core.py.backup", "x\n")
        self.write("notes/scratch.md", "x\n")
        self.assertEqual(self.sel()[0], [])

    def test_unread_tracked_package_file_runs_the_full_suite(self):
        self.write("pkg/README.txt", "docs\n")
        self.git("add", "pkg/README.txt")
        self.git("commit", "-qm", "add package file")
        sel, why = self.sel()
        self.assertIsNone(sel)
        self.assertIn("no recorded test read", why["reason"])

    def test_data_edit_plus_code_edit(self):
        self.write("pkg/data/b.txt", "BETA\n")
        p = os.path.join(self.root, "pkg/core.py")
        src = open(p).read()
        open(p, "w").write(src.replace("fh.write('report')", "fh.write('REPORT!')"))
        self.assertEqual(self.sel()[0], ["test_b", "test_writes_only"])

    def test_switch_off_restores_v221(self):
        self.write("pkg/data/b.txt", "BETA\n")
        old = os.environ.get("PROVISO_OFF")
        os.environ["PROVISO_OFF"] = "files"
        try:
            sel, why = self.sel()
            self.assertIsNone(sel)
            self.assertIn("not tracked per test", why["reason"])
        finally:
            if old is None:
                os.environ.pop("PROVISO_OFF")
            else:
                os.environ["PROVISO_OFF"] = old

    def test_map_without_file_records_keeps_v22_behaviour(self):
        old_map = {k: v for k, v in self.cov.items()}
        old_map["__global__"] = {"funcs": self.cov["__global__"]["funcs"]}
        self.write("pkg/data/b.txt", "BETA\n")
        sel, why = I.selection(self.root, old_map, sys.executable)
        self.assertIsNone(sel)


if __name__ == "__main__":
    unittest.main()
