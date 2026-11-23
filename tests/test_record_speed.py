"""(v2.3.1) Recording speed-ups must not change the map: shared byte-code, longest files first, and the fast path for
package methods in the recorder."""
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

from dc_engine import record as REC  # noqa: E402

FILES = {
    "pkg/__init__.py": "",
    "pkg/shapes.py": "class Base:\n    def area(self):\n        return self.size() * 2\n\n    @classmethod\n"
                     "    def make(cls):\n        return cls()\n\n\nclass Sq(Base):\n    def size(self):\n        return 2\n\n\n"
                     "class Ci(Base):\n    def size(self):\n        return 3\n",
    "pkg/lazy.py": "from pkg.shapes import Sq\n\n\ndef table():\n    return {'sq': Sq().area()}\n",
    "tests/test_shapes.py": "import pytest\nfrom pkg.shapes import Ci, Sq\n\n\n@pytest.fixture(scope='class')\ndef ci():\n"
                            "    return Ci.make()\n\n\nclass TestBoth:\n    def test_both(self, ci):\n"
                            "        assert Sq().area() + ci.area() == 10\n\n    def test_ci_again(self, ci):\n"
                            "        assert ci.area() == 6\n\n\ndef test_one():\n    assert Sq.make().area() == 4\n",
    "tests/test_lazy.py": "def test_lazy():\n    from pkg.lazy import table\n    assert table() == {'sq': 4}\n\n\n"
                          "def test_after():\n    from pkg.lazy import table\n    assert table()['sq'] == 4\n",
    "tests/test_slow.py": "import time\n\n\ndef test_slow():\n    time.sleep(0.5)\n",
}


def strip(m):
    """The map without what legitimately differs between two recordings: the measured test times."""
    return {k: ({kk: vv for kk, vv in v.items() if kk != "time"} if not k.startswith("__") else v)
            for k, v in m.items()}


class RecordSpeedTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="proviso-recspeed-")
        for p, s in FILES.items():
            full = os.path.join(self.root, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w").write(s)
        g = ["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(g + ["init", "-q"], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "base"], check=True)
        self.pycache = REC.PYCACHE

    def tearDown(self):
        REC.PYCACHE = self.pycache
        shutil.rmtree(self.root, ignore_errors=True)

    def rec(self, name):
        return REC.record(self.root, "pkg", os.path.join(self.root, name), sys.executable, workers=2)

    def test_classes_of_every_type_a_method_runs_on(self):
        m = self.rec(".m.json")
        both = m["tests/test_shapes.py::TestBoth::test_both"]["classes"]
        # one method, two types in one target: both types' classes (Ci's object comes from the fixture)
        self.assertEqual(sorted(both), ["pkg/shapes.py:Base", "pkg/shapes.py:Ci", "pkg/shapes.py:Sq"])
        fx = [r for k, r in m["__fixtures__"].items() if "::ci@" in k]
        self.assertEqual(len(fx), 1)
        self.assertEqual(sorted(fx[0]["classes"]), ["pkg/shapes.py:Base", "pkg/shapes.py:Ci"])  # cls of make()
        again = m["tests/test_shapes.py::TestBoth::test_ci_again"]["classes"]
        self.assertEqual(sorted(again), ["pkg/shapes.py:Base", "pkg/shapes.py:Ci"])  # a new target sees Ci again
        one = m["tests/test_shapes.py::test_one"]["classes"]
        self.assertEqual(sorted(one), ["pkg/shapes.py:Base", "pkg/shapes.py:Sq"])
        # the first test to import pkg.lazy is charged with its import, the next one only with what it runs
        self.assertIn(["pkg/lazy.py", 1], m["tests/test_lazy.py::test_lazy"]["funcs"])
        self.assertNotIn(["pkg/lazy.py", 1], m["tests/test_lazy.py::test_after"]["funcs"])

    def test_shared_bytecode_and_scheduling_leave_the_map_unchanged(self):
        REC.PYCACHE = False
        plain = self.rec(".plain.json")
        REC.PYCACHE = True
        first = self.rec(".first.json")       # no recorded file times yet: collection order
        times = json.load(open(os.path.join(self.root, REC.TIMES)))
        self.assertEqual(sorted(times), sorted(plain["__collected__"]))
        self.assertGreater(times["tests/test_slow.py"], 0.5)
        second = self.rec(".second.json")     # longest file first now
        for m in (first, second):
            self.assertEqual(strip(m), strip(plain))
            self.assertEqual(list(m), list(plain))      # same key order: parts are merged in collection order
        # byte-code went to a temporary directory outside the tree, which is gone
        caches = [d for d, _, _ in os.walk(self.root) if d.endswith("__pycache__")]
        self.assertEqual(caches, [])

    def test_partial_recordings_do_not_overwrite_file_times(self):
        self.rec(".full.json")
        before = json.load(open(os.path.join(self.root, REC.TIMES)))
        REC.record(self.root, "pkg", os.path.join(self.root, ".part.json"), sys.executable,
                   ["tests/test_shapes.py"], workers=1,
                   nodes={"tests/test_shapes.py": ["tests/test_shapes.py::test_one"]})
        self.assertEqual(json.load(open(os.path.join(self.root, REC.TIMES))), before)


if __name__ == "__main__":
    unittest.main()
