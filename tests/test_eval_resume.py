"""--resume: a run whose agent never reached the model (pilot: a mistyped API key, $0, authentication_failed) is run
again; an agent error after real work is kept, so its cost is not paid twice."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from dc_eval.run import agent_finished  # noqa: E402


class Resume(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def slot(self, **metrics):
        json.dump(metrics, open(os.path.join(self.d, "metrics.json"), "w"))
        open(os.path.join(self.d, "stream.jsonl"), "w").write('{"type": "result"}\n')
        return self.d

    def test_invalid_key_is_rerun(self):
        self.assertFalse(agent_finished(self.slot(status="agent_error", cost_usd=0.0, model_requests=0)))

    def test_agent_error_after_work_is_kept(self):
        self.assertTrue(agent_finished(self.slot(status="agent_error", cost_usd=0.31, model_requests=9)))

    def test_ok_and_grading_error_are_kept(self):
        self.assertTrue(agent_finished(self.slot(status="ok", cost_usd=0.05)))
        self.assertTrue(agent_finished(self.slot(status="grading_error", cost_usd=0.05)))


if __name__ == "__main__":
    unittest.main()
