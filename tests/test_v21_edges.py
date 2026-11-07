"""Edge cases of v2.1/v2.2: changed functions found by name, the docstring filter with repeated names, and pytest
configuration changes (nested files, renames, pytest 9 formats, sections, a project inside a larger repository)."""
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

BASE = "class A:\n    def f(self):\n        return 1\n\n    def g(self):\n        return 2\n"
PROP = ('class A:\n    @property\n    def x(self):\n        """old"""\n        return 1\n'
        '    @x.setter\n    def x(self, v):\n        pass\n')
IFELSE = "import sys\nif sys:\n    def f():\n        return 1\nelse:\n    def f():\n        return 2\n"


def by_name(old, new):
    return sorted(ln for _, ln in I._changed_by_name("m.py", old, new))


class ByName(unittest.TestCase):
    def test_cases(self):
        cases = [
            ("unchanged", BASE, BASE, []),
            ("moved down", BASE, "\n\n" + BASE, []),
            ("body edit", BASE, BASE.replace("return 1", "return 3"), [2]),
            ("appended after the blank line", BASE,
             BASE.replace("        return 1\n\n", "        return 1\n\n        x = 1\n\n"), [2]),
            ("redefinition appended", BASE, BASE + "\n    def f(self):\n        return 9\n", [2]),
            ("deleted or renamed: left to the line mapping", BASE, BASE.replace("def f(", "def h("), []),
            ("syntax error in the new version", BASE, BASE + "def (:\n", []),
            ("decorator change", "@a\ndef f():\n    return 1\n", "@b\ndef f():\n    return 1\n", [1]),
            ("async def", "async def f():\n    return 1\n", "async def f():\n    return 2\n", [1]),
            ("property setter", PROP, PROP.replace("pass", "self.v = v"), [6]),
            ("second if/else branch", IFELSE, IFELSE.replace("return 2", "return 3"), [6]),
            ("CRLF only", BASE, BASE.replace("\n", "\r\n"), []),
            ("trailing whitespace only", BASE, BASE.replace("return 1", "return 1   "), []),
            ("nested function: the outer one", "def f():\n    def g():\n        return 1\n    return g\n",
             "def f():\n    def g():\n        return 2\n    return g\n", [1]),
            ("new file", "", BASE, []),
        ]
        for name, old, new, want in cases:
            with self.subTest(name):
                self.assertEqual(by_name(old, new), want)


class DocFilter(unittest.TestCase):
    def filt(self, old, new, lines):
        r = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, r, True)
        os.makedirs(os.path.join(r, "pkg"))
        open(os.path.join(r, "pkg", "m.py"), "w").write(old)
        subprocess.run("git init -q && git add . && git -c user.email=a@b -c user.name=a commit -qm b", shell=True,
                       cwd=r, check=True)
        open(os.path.join(r, "pkg", "m.py"), "w").write(new)
        doc, fmt = I._docstring_only_edits(r, {("pkg/m.py", ln) for ln in lines})
        return sorted(ln for _, ln in doc), sorted(ln for _, ln in fmt)

    def test_property_getter_docstring_only_is_still_filtered(self):
        self.assertEqual(self.filt(PROP, PROP.replace('"""old"""', '"""new"""'), [2]), ([2], []))

    def test_property_setter_real_edit_is_not_filtered(self):
        self.assertEqual(self.filt(PROP, PROP.replace("pass", "self.v = v"), [6]), ([], []))

    def test_redefinition_is_never_filtered(self):
        old = "class A:\n    def f(self):\n        return 1\n"
        self.assertEqual(self.filt(old, old + "    def f(self):\n        return 2\n", [2]), ([], []))

    def test_second_branch_edit_is_not_filtered_and_its_comment_is(self):
        self.assertEqual(self.filt(IFELSE, IFELSE.replace("return 2", "return 3"), [6]), ([], []))
        self.assertEqual(self.filt(IFELSE, IFELSE.replace("return 2", "return 2  # c"), [6]), ([], [6]))


class PytestConfig(unittest.TestCase):
    BASE = {"pkg/__init__.py": "", "setup.cfg": "[metadata]\nname = p\n", "pyproject.toml": "[project]\nname = 'p'\n",
            "tox.ini": "[tox]\nenvlist = py\n"}

    def repo(self, files, sub=""):
        r = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, r, True)
        for p, c in files.items():
            self.write(r, p, c)
        subprocess.run("git init -q && git add -A && git -c user.email=a@b -c user.name=a commit -qm b", shell=True,
                       cwd=r, check=True)
        return r, os.path.join(r, sub) if sub else r

    @staticmethod
    def write(top, p, c):
        os.makedirs(os.path.dirname(os.path.join(top, p)) or top, exist_ok=True)
        open(os.path.join(top, p), "w").write(c)

    def change(self, files, act, sub=""):
        top, root = self.repo(files, sub)
        act(top)
        return I._pytest_config_change(root)

    def test_cases(self):
        B = self.BASE
        w = lambda p, c: (lambda t: self.write(t, p, c))  # noqa: E731
        rm = lambda p: (lambda t: os.remove(os.path.join(t, p)))  # noqa: E731
        cases = [
            ("nothing", B, lambda t: None, None),
            ("new pytest.ini", B, w("pytest.ini", "[pytest]\naddopts = -x\n"), "pytest.ini"),
            ("new pytest.toml (pytest 9)", B, w("pytest.toml", "[pytest]\n"), "pytest.toml"),
            ("nested tests/pytest.ini", B, w("tests/pytest.ini", "[pytest]\n"), "tests/pytest.ini"),
            ("pytest.ini deleted", {**B, "pytest.ini": "[pytest]\n"}, rm("pytest.ini"), "pytest.ini"),
            ("setup.cfg metadata", B, w("setup.cfg", "[metadata]\nname = q\n"), None),
            ("setup.cfg [tool:pytest]", B, w("setup.cfg", "[metadata]\nname = p\n[tool:pytest]\naddopts = -x\n"),
             "setup.cfg"),
            ("setup.cfg deleted, no pytest section", B, rm("setup.cfg"), None),
            ("setup.cfg deleted, pytest section", {**B, "setup.cfg": "[tool:pytest]\naddopts = -x\n"},
             rm("setup.cfg"), "setup.cfg"),
            ("tox.ini [tox]", B, w("tox.ini", "[tox]\nenvlist = py3\n"), None),
            ("tox.ini [pytest]", B, w("tox.ini", "[tox]\nenvlist = py\n[pytest]\naddopts = -x\n"), "tox.ini"),
            ("pyproject [project]", B, w("pyproject.toml", "[project]\nname = 'q'\n"), None),
            ("pyproject ini_options", B,
             w("pyproject.toml", "[project]\nname = 'p'\n[tool.pytest.ini_options]\naddopts = '-x'\n"),
             "pyproject.toml"),
            ("pyproject native [tool.pytest]", B,
             w("pyproject.toml", "[project]\nname = 'p'\n[tool.pytest]\naddopts = ['-x']\n"), "pyproject.toml"),
            ("pyproject other tool", B,
             w("pyproject.toml", "[project]\nname = 'p'\n[tool.black]\nline-length = 99\n"), None),
            ("pyproject unparsable", B, w("pyproject.toml", "[project\nname = \n"), "pyproject.toml"),
        ]
        for name, files, act, want in cases:
            with self.subTest(name):
                self.assertEqual(self.change(files, act), want)

    def test_rename(self):
        files = {**self.BASE, "pytest.ini": "[pytest]\n"}
        self.assertEqual(self.change(files, lambda t: subprocess.run(["git", "mv", "pytest.ini", ".pytest.ini"],
                                                                      cwd=t, check=True)), ".pytest.ini")

    def test_project_inside_a_larger_repository(self):
        files = {"sub/pkg/__init__.py": "", "other/x": ""}
        self.assertEqual(self.change(files, lambda t: self.write(t, "sub/pytest.ini", "[pytest]\n"), "sub"),
                         "pytest.ini")
        self.assertIsNone(self.change(files, lambda t: self.write(t, "other/pytest.ini", "[pytest]\n"), "sub"))


if __name__ == "__main__":
    unittest.main()
