"""The check when the agent finishes (agent study arms gate-proviso and gate-full): a Claude Code Stop hook that runs
the tests the change can affect (or the whole suite) anywhere in the project and sends new failures back to the agent,
at most twice; silent when nothing new fails or nothing changed."""
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

from dc_engine import impact as I  # noqa: E402
from dc_engine import record as REC  # noqa: E402
from dc_engine.proviso import summarize_log  # noqa: E402

FILES = {
    "pkg/__init__.py": "",
    "pkg/colors.py": "def get(name):\n    return {'red': '#f00'}[name]\n",
    "pkg/shapes.py": "def area(w, h):\n    return w * h\n",
    "tests/test_colors.py": "from pkg import colors\n\ndef test_red():\n    assert colors.get('red') == '#f00'\n",
    "tests/test_plot.py": "from pkg import colors\n\ndef test_plot_red():\n    assert colors.get('red').startswith('#')\n",
    "tests/test_shapes.py": "from pkg import shapes\n\ndef test_area():\n    assert shapes.area(2, 3) == 6\n",
}


class Gate(unittest.TestCase):
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
        open(os.path.join(r, ".dc-engine", ".gitignore"), "w").write("*\n")
        REC.record(r, "pkg", os.path.join(r, ".dc-engine", "covmap.json"), sys.executable, ["tests"], 1, "",
                   ["-p", "no:randomly"], {**os.environ, "PYTHONPATH": r})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    @classmethod
    def git(cls, *a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=cls.root, check=True,
                              capture_output=True, text=True).stdout

    def setUp(self):
        for f in ("proviso_state.json", "proviso.log"):
            p = os.path.join(self.root, ".dc-engine", f)
            if os.path.exists(p):
                os.remove(p)

    def tearDown(self):
        self.git("checkout", "-qf", "BASE")
        self.git("clean", "-qfd", "-e", ".dc-engine")

    def gate(self, mode):
        cfg = {"gate": mode, "python": sys.executable, "report": False}
        json.dump(cfg, open(os.path.join(self.root, ".dc-engine", "proviso.json"), "w"))
        return I.gate({"hook_event_name": "Stop"}, self.root, cfg)

    def break_colors(self):
        open(os.path.join(self.root, "pkg", "colors.py"), "w").write("def get(name):\n    return {'red': 'red'}[name]\n")

    def test_breakage_outside_what_the_agent_tested_is_sent_back(self):
        self.break_colors()
        for mode in ("proviso", "full"):
            self.setUp()
            out = self.gate(mode)
            self.assertEqual(out.get("decision"), "block", mode)
            self.assertIn("test_plot_red", out["reason"])
            self.assertIn("test_red", out["reason"])

    def test_proviso_runs_only_the_affected_tests(self):
        self.break_colors()
        self.gate("proviso")
        s = summarize_log(self.root)
        self.assertEqual((s["proviso_gate_runs"], s["proviso_gate_blocks"]), (1, 1))
        log = [json.loads(l) for l in open(os.path.join(self.root, ".dc-engine", "proviso.log"))]
        runs = [e for e in log if e.get("event") == "impact_run"]
        self.assertEqual(runs[-1]["ran"], 2)  # the two colour tests, not test_area

    def test_nothing_new_fails_is_silent(self):
        open(os.path.join(self.root, "pkg", "shapes.py"), "w").write("def area(w, h):\n    return h * w\n")
        self.assertEqual(self.gate("proviso"), {})
        self.assertEqual(self.gate("full"), {})

    def test_no_change_is_silent(self):
        self.assertEqual(self.gate("proviso"), {})

    def test_at_most_two_blocks(self):
        self.break_colors()
        self.assertEqual(self.gate("proviso").get("decision"), "block")
        self.assertEqual(self.gate("proviso").get("decision"), "block")
        self.assertEqual(self.gate("proviso"), {})  # the agent may finish now

    def run_hook(self, event):
        """The command exactly as dc_eval installs it for Claude Code, a Stop payload on stdin."""
        from dc_eval.arms import hook_command
        src = os.path.join(os.path.dirname(HERE), "src")
        cmd = hook_command(f"hook {event}", sys.executable)
        return subprocess.run(cmd, shell=True, cwd=self.root, input=json.dumps(
            {"hook_event_name": "Stop", "cwd": self.root, "stop_hook_active": False}), capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": src})

    def test_the_installed_hook_command_end_to_end(self):
        """The first pilot's check never ran: the CLI rejected the event (exit 2), which Claude Code turns into a block."""
        cfg = {"gate": "proviso", "python": sys.executable, "report": False}
        json.dump(cfg, open(os.path.join(self.root, ".dc-engine", "proviso.json"), "w"))
        r = self.run_hook("proviso-gate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {})  # nothing changed: silent
        self.break_colors()
        r = self.run_hook("proviso-gate")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block", out)
        self.assertIn("test_plot_red", out["reason"])

    def test_every_event_dc_eval_installs_is_known(self):
        import re
        from dc_engine.hooks import HOOK_EVENTS
        src = open(os.path.join(os.path.dirname(HERE), "src", "dc_eval", "arms.py")).read()
        events = set(re.findall(r'"hook ([a-z0-9-]+)', src))
        events = {e for e in events if not e.endswith("-")} | {f"proviso-brief-{i}" for i in range(1, 6)}
        self.assertTrue(events)
        self.assertEqual(events - HOOK_EVENTS, set())

    def test_an_unknown_event_never_blocks(self):
        r = self.run_hook("proviso-no-such-event")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), {})


if __name__ == "__main__":
    unittest.main()
