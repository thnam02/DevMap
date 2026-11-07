"""The import-time snapshot must not report changes that come from how a tree is installed rather than from the code:
a version module generated at install time (setuptools-scm's _version.py), the logging registry state that a
missing version module leaves behind (a warning logged during import), and the process environment (os.environ).
Real changes must still be reported."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_engine import importstate as S  # noqa: E402

INIT = '''import logging
logger = logging.getLogger("pkg")
try:
    from pkg._version import __version__
except ImportError:
    logger.warning("version unknown")
    __version__ = "0"
'''
CORE = '''import logging
from os import environ
logger = logging.getLogger("pkg")
TABLE = {"a": 1, "b": 2}
'''


def _git(cwd, *a):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=cwd, check=True, capture_output=True)


class ImportStateNoise(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "pkg"))
        open(os.path.join(self.root, "pkg", "__init__.py"), "w").write(INIT)
        open(os.path.join(self.root, "pkg", "core.py"), "w").write(CORE)
        _git(self.root, "init", "-q")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "base")
        self.files = ["pkg/__init__.py", "pkg/core.py"]
        self.base = S.base_snapshot(self.root, self.files, sys.executable, os.path.join(self.root, "base.json"))
        self.assertIsNotNone(self.base)

    def changed(self):
        d = S.diff(self.base, S.snapshot(self.root, self.files, sys.executable), set())
        return set(d if isinstance(d, (set, list)) else d.get("changed", d))

    def test_generated_version_module_is_not_a_change(self):
        open(os.path.join(self.root, "pkg", "_version.py"), "w").write('__version__ = "1.2.3"\n')
        self.assertEqual(self.changed(), set())

    def test_unchanged_code_reports_nothing(self):
        # the process environment differs between any two imports: never a change by itself
        self.assertEqual(self.changed(), set())

    def test_value_differing_between_imports_still_counts_when_code_changes(self):
        # a value that differs on every import (here keyed by the process id, like SQLAlchemy's id-keyed registries)
        # cannot be compared; it must stay reported when its code changes, not be ignored: ignoring such values hid
        # real changes to SQLAlchemy registries
        reg = os.path.join(self.root, "pkg", "reg.py")
        open(reg, "w").write("import os\nREG = {os.getpid(): [1, 2]}\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "registry")
        files = self.files + ["pkg/reg.py"]
        base = S.base_snapshot(self.root, files, sys.executable, os.path.join(self.root, "base2.json"))
        open(reg, "w").write("import os\nREG = {os.getpid(): [1, 3]}\n")
        d = S.diff(base, S.snapshot(self.root, files, sys.executable), set())
        self.assertIn("pkg.reg:REG", d["changed"])

    def test_paths_of_the_tree_itself_are_not_a_change(self):
        # the base snapshot is taken from an export in a temporary folder and the current one from the working tree;
        # values holding the package's own location (loguru keeps its file path inside `logger`) must compare equal
        p = os.path.join(self.root, "pkg", "paths.py")
        open(p, "w").write("import os\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
                           "class Holder:\n    def __init__(self):\n        self.file = __file__\n"
                           "HOLDER = Holder()\nDATA = {'dir': HERE, 'files': [os.path.join(HERE, 'x.csv')]}\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "paths")
        files = self.files + ["pkg/paths.py"]
        base = S.base_snapshot(self.root, files, sys.executable, os.path.join(self.root, "base3.json"))
        self.assertEqual(S.diff(base, S.snapshot(self.root, files, sys.executable), set())["changed"], [])

    def test_value_too_large_to_fingerprint_counts_as_changed(self):
        # pylint's test helpers build a whole linter at import; fingerprinting it took minutes and timed out the
        # snapshot (then every test ran). Over a budget a value is unknown: reported as changed, the rest compared.
        p = os.path.join(self.root, "pkg", "big.py")
        open(p, "w").write("BIG = [[i, str(i)] for i in range(5000)]\nSMALL = 1\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "big")
        files = self.files + ["pkg/big.py"]
        old = os.environ.get("DC_VALUE_BUDGET")
        os.environ["DC_VALUE_BUDGET"] = "100"
        try:
            base = S.base_snapshot(self.root, files, sys.executable, os.path.join(self.root, "base4.json"))
            changed = S.diff(base, S.snapshot(self.root, files, sys.executable), set())["changed"]
        finally:
            if old is None:
                os.environ.pop("DC_VALUE_BUDGET")
            else:
                os.environ["DC_VALUE_BUDGET"] = old
        self.assertIn("pkg.big:BIG", changed)
        self.assertNotIn("pkg.big:SMALL", changed)

    def test_import_only_pass_lists_functions_run_at_import(self):
        p = os.path.join(self.root, "pkg", "init_time.py")
        open(p, "w").write("def build():\n    return {1: 2}\n\nTABLE = build()\n\ndef later():\n    return 3\n")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "init")
        funcs = S.import_funcs_of(self.root, self.files + ["pkg/init_time.py"], sys.executable,
                                  os.path.join(self.root, "imp.json"))
        self.assertIn(["pkg/init_time.py", 1], funcs)
        self.assertNotIn(["pkg/init_time.py", 6], funcs)

    def test_settings_inside_a_wrapper_count(self):
        # pvlib: parse_psm3 = deprecated(since="0.12.1")(read_psm3); functools.wraps gives the wrapper the wrapped
        # function's name, so the fingerprint saw "the same function" and missed the changed setting
        p = os.path.join(self.root, "pkg", "wrap.py")
        src = ("import functools\n\n\ndef deprecated(since):\n    def deco(f):\n        @functools.wraps(f)\n"
               "        def w(*a):\n            print('deprecated since', since)\n            return f(*a)\n        return w\n"
               "    return deco\n\n\n"
               "def read():\n    return 1\n\n\nparse = deprecated(since='0.12')(read)\n")
        open(p, "w").write(src)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "wrap")
        files = self.files + ["pkg/wrap.py"]
        base = S.base_snapshot(self.root, files, sys.executable, os.path.join(self.root, "base5.json"))
        self.assertEqual(S.diff(base, S.snapshot(self.root, files, sys.executable), set())["changed"], [])
        open(p, "w").write(src.replace("'0.12'", "'0.13'"))
        self.assertIn("pkg.wrap:parse", S.diff(base, S.snapshot(self.root, files, sys.executable), set())["changed"])

    def test_real_table_change_is_reported(self):
        open(os.path.join(self.root, "pkg", "core.py"), "w").write(CORE.replace('"b": 2', '"b": 3'))
        self.assertIn("pkg.core:TABLE", self.changed())

    def test_logger_level_change_is_reported(self):
        open(os.path.join(self.root, "pkg", "core.py"), "w").write(CORE + "logger.setLevel(logging.ERROR)\n")
        self.assertIn("pkg.core:logger", self.changed())


if __name__ == "__main__":
    unittest.main()


ORDERED = '''class A: pass
class B: pass
class C: pass
class D: pass
class E: pass
class F: pass
# order follows the classes' memory addresses (a set of classes), like sympy's multipledispatch orderings
BY_ADDRESS = tuple({A, B, C, D, E, F})
PRIORITY = ["low", "mid", "high"]
'''


class OrderNoise(unittest.TestCase):
    """(v2.2) Values whose order follows memory addresses are compared without order once seen to vary; a reorder of
    a value whose order is fixed is still a change."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "pkg"))
        open(os.path.join(self.root, "pkg", "__init__.py"), "w").write("")
        open(os.path.join(self.root, "pkg", "order.py"), "w").write(ORDERED)
        _git(self.root, "init", "-q")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "base")
        self.files = ["pkg/__init__.py", "pkg/order.py"]
        self.base = S.base_snapshot(self.root, self.files, sys.executable, os.path.join(self.root, "base.json"))

    def changed(self):
        return set(S.diff(self.base, S.snapshot(self.root, self.files, sys.executable), set())["changed"])

    def test_address_ordered_value_is_marked_unstable(self):
        self.assertIn("pkg.order:BY_ADDRESS", self.base["unstable"])
        for _ in range(3):
            self.assertNotIn("pkg.order:BY_ADDRESS", self.changed())

    def test_reordering_a_fixed_list_is_a_change(self):
        self.assertNotIn("pkg.order:PRIORITY", self.base["unstable"])
        open(os.path.join(self.root, "pkg", "order.py"), "w").write(
            ORDERED.replace('["low", "mid", "high"]', '["high", "mid", "low"]'))
        self.assertIn("pkg.order:PRIORITY", self.changed())
