"""(v2.5) Worker processes are recorded: a test that uses a process pool gets the functions its workers ran, and is
no longer always selected; whatever cannot be accounted for keeps the always rule."""
from __future__ import annotations

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
    "pkg/work.py": "TABLE = {'a': 1}\n\n\ndef square(x):\n    return helper(x) * x\n\n\ndef helper(x):\n    return x\n\n\n"
                   "def cube(x):\n    return x * x * x\n\n\ndef local(x):\n    return x + 1\n\n\n"
                   "def nap(x):\n    import time\n    time.sleep(x)\n    return x\n",
    "pkg/lazy.py": "def late(x):\n    return -x\n",
    "pkg/tasks.py": "def via_lazy(x):\n    from pkg.lazy import late\n    return late(x)\n",
    "tests/test_fork.py":
        "import multiprocessing as mp\nfrom pkg import work\n\n\n"
        "def test_fork_pool():\n    with mp.get_context('fork').Pool(2) as pool:\n"
        "        assert pool.map(work.square, [1, 2, 3]) == [1, 4, 9]\n\n\n"
        "def test_plain():\n    assert work.local(1) == 2\n",
    "tests/test_spawn.py":
        "from concurrent.futures import ProcessPoolExecutor\nfrom multiprocessing import get_context\n"
        "from pkg import work, tasks\n\n\n"
        "def test_spawn_pool():\n    with ProcessPoolExecutor(2, mp_context=get_context('spawn')) as pool:\n"
        "        assert [f.result() for f in [pool.submit(work.cube, 2), pool.submit(tasks.via_lazy, 3)]] == [8, -3]\n\n\n"
        "def test_after_spawn():\n    assert work.local(2) == 3\n",
    "tests/test_leak.py":
        "import multiprocessing as mp\nimport pytest\nfrom pkg import work\n\nPROCS = []\n\n\n"
        "def test_leaks_a_worker():\n    p = mp.get_context('fork').Process(target=work.nap, args=(8,))\n"
        "    p.start()\n    PROCS.append(p)\n\n\n"
        "def test_after_leak():\n    assert work.local(3) == 4\n\n\n"
        "def test_cleanup():\n    for p in PROCS:\n        p.terminate()\n        p.join()\n",
    "tests/test_forkserver.py":
        "import multiprocessing as mp\nfrom pkg import work\n\n\n"
        "def test_forkserver():\n    with mp.get_context('forkserver').Pool(1) as pool:\n"
        "        assert pool.map(work.cube, [2]) == [8]\n",
    "tests/test_fixture_pool.py":
        "import multiprocessing as mp\nimport pytest\nfrom pkg import work\n\n\n"
        "@pytest.fixture(scope='module')\ndef results():\n    with mp.get_context('fork').Pool(1) as pool:\n"
        "        return pool.map(work.square, [4])\n\n\n"
        "def test_uses_results(results):\n    assert results == [16]\n\n\n"
        "def test_uses_results_too(results):\n    assert results[0] == 16\n",
}


def line_of(root, rel, name):
    for i, ln in enumerate(open(os.path.join(root, rel)), 1):
        if ln.startswith(f"def {name}("):
            return i
    raise KeyError(name)


class WorkerRecordingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="proviso-mprec-")
        for p, s in FILES.items():
            full = os.path.join(cls.root, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w").write(s)
        g = ["git", "-C", cls.root, "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(g + ["init", "-q"], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "base"], check=True)
        cls.map = REC.record(cls.root, "pkg", os.path.join(cls.root, "on.json"), sys.executable, workers=2)
        old = os.environ.get("PROVISO_OFF")
        os.environ["PROVISO_OFF"] = "mprecord"
        try:
            cls.off = REC.record(cls.root, "pkg", os.path.join(cls.root, "off.json"), sys.executable, workers=2)
        finally:
            if old is None:
                os.environ.pop("PROVISO_OFF")
            else:
                os.environ["PROVISO_OFF"] = old

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def funcs(self, m, test):
        return {tuple(f) for f in m[test]["funcs"]}

    def key(self, rel, name):
        return (rel, line_of(self.root, rel, name))

    def test_fork_pool_is_recorded(self):
        t = "tests/test_fork.py::test_fork_pool"
        self.assertFalse(self.map[t]["always"])
        self.assertLessEqual({self.key("pkg/work.py", "square"), self.key("pkg/work.py", "helper")}, self.funcs(self.map, t))
        self.assertNotIn(self.key("pkg/work.py", "cube"), self.funcs(self.map, t))

    def test_spawn_pool_is_recorded(self):
        t = "tests/test_spawn.py::test_spawn_pool"
        self.assertFalse(self.map[t]["always"])
        got = self.funcs(self.map, t)
        self.assertIn(self.key("pkg/work.py", "cube"), got)
        self.assertIn(self.key("pkg/tasks.py", "via_lazy"), got)
        self.assertIn(self.key("pkg/lazy.py", "late"), got)          # a module only the worker imported
        self.assertNotIn(self.key("pkg/work.py", "square"), got)

    def test_other_tests_unchanged(self):
        for t in ("tests/test_fork.py::test_plain", "tests/test_spawn.py::test_after_spawn"):
            self.assertEqual(self.map[t]["funcs"], self.off[t]["funcs"])
            self.assertFalse(self.map[t]["always"])

    def test_old_behaviour_with_switch(self):
        for t in ("tests/test_fork.py::test_fork_pool", "tests/test_spawn.py::test_spawn_pool"):
            self.assertTrue(self.off[t]["always"])
        self.assertNotIn(self.key("pkg/work.py", "square"), self.funcs(self.off, "tests/test_fork.py::test_fork_pool"))

    def test_leaked_worker_keeps_always(self):
        self.assertTrue(self.map["tests/test_leak.py::test_leaks_a_worker"]["always"])
        self.assertTrue(self.map["tests/test_leak.py::test_after_leak"]["always"])    # may use the worker unseen

    def test_forkserver_keeps_always(self):
        self.assertTrue(self.map["tests/test_forkserver.py::test_forkserver"]["always"])

    def test_pool_in_a_fixture_reaches_every_user(self):
        sq = self.key("pkg/work.py", "square")
        for t in ("tests/test_fixture_pool.py::test_uses_results", "tests/test_fixture_pool.py::test_uses_results_too"):
            keys = self.map[t]["fx"]
            got = {tuple(f) for k in keys for f in (self.map["__fixtures__"].get(k) or {}).get("funcs", [])}
            self.assertIn(sq, got)
            self.assertFalse(self.map[t]["always"])
            self.assertFalse(any((self.map["__fixtures__"].get(k) or {}).get("always") for k in keys))


if __name__ == "__main__":
    unittest.main()
