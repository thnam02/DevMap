"""pytest plugin for NameRTS's runs: end each finished worker process of `--dist=isolation`.

NameRTS's isolation scheduler (its copy of pytest-xdist) starts a fresh worker for every test file and sends it
`shutdown` once its file is assigned; the worker then finishes its pytest session, but its execnet gateway (the
`python -c "import sys;exec(eval(sys.stdin.readline()))"` process) is only terminated with all the others when the
whole run ends. With hundreds of test files (sympy) the finished workers pile up until memory runs out. This plugin
exits a worker's gateway as soon as the controller sees the worker finish. It changes no test, no outcome and nothing
NameRTS records (a worker has sent everything by the time it reports it finished), only when the idle process ends.

Loaded by nrts-bin/pytest when NRTS_PYTEST_ARGS="-p nrts_reap" (swe_eval_namerts.py sets it)."""
from __future__ import annotations

import threading

import pytest


@pytest.hookimpl(optionalhook=True, trylast=True)
def pytest_testnodedown(node, error):
    gw = getattr(node, "gateway", None)
    if gw is None:
        return
    try:
        gw.exit()   # sends GATEWAY_TERMINATE: the idle process exits
    except Exception:  # noqa: BLE001
        return
    io = getattr(gw, "_io", None)
    wait = getattr(io, "wait", None)
    if callable(wait):   # reap it, so no zombie is left behind
        threading.Thread(target=wait, daemon=True).start()
