"""pytest plugin for NameRTS's runs in the SWE-bench evaluation (loaded by nrts-bin/pytest when
NRTS_PYTEST_ARGS="-p nrts_reap"; swe_eval_namerts.py sets it). Two jobs, neither changes what NameRTS records for
the files it runs:

1. End each finished worker process of `--dist=isolation`. NameRTS's isolation scheduler (its copy of pytest-xdist)
   starts a fresh worker for every test file; a finished worker's execnet gateway (the
   `python -c "import sys;exec(eval(sys.stdin.readline()))"` process) was only terminated with all the others when
   the whole run ended, so with hundreds of test files (sympy) they piled up until memory ran out.

2. NRTS_FILE_TIMEOUT=<seconds>: the same per-file limit Proviso's recorder has (PROVISO_RECORD_FILE_TIMEOUT). When a
   test file's tests have run that long, the running test is interrupted and the file's remaining tests are skipped;
   the file is written to NRTS_TIMEOUT_DIR, and swe_eval_namerts.py then treats its tests as always selected (as
   Proviso does with its own timed-out files). The worker is not killed: a crashed worker's file would be re-queued
   by the scheduler and run again."""
from __future__ import annotations

import ctypes
import os
import signal
import threading
import time

import pytest

LIMIT = float(os.environ.get("NRTS_FILE_TIMEOUT") or 0)
OUT_DIR = os.environ.get("NRTS_TIMEOUT_DIR", "")


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


# ---- per-file time limit (worker side only) ----

class FileTimeLimit(BaseException):
    """Raised into a test still running when its file's time limit passes (BaseException: `except Exception` in the
    test cannot swallow it; pytest reports the test as failed)."""


_st = {"deadline": None, "files": set(), "tid": None, "main": False, "in_call": False, "expired": False}


def _watch():
    while True:
        time.sleep(1)
        if not _st["expired"] and time.time() > _st["deadline"]:
            _st["expired"] = True
            if OUT_DIR:
                try:
                    os.makedirs(OUT_DIR, exist_ok=True)
                    with open(os.path.join(OUT_DIR, f"{os.getpid()}.txt"), "w") as fh:
                        fh.write("\n".join(sorted(_st["files"])) + "\n")
                except OSError:
                    pass
        if _st["expired"] and _st["in_call"] and _st["tid"] is not None:
            if _st["main"]:
                os.kill(os.getpid(), signal.SIGUSR2)   # also interrupts a blocking call (sleep, wait)
            else:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(_st["tid"]),
                                                           ctypes.py_object(FileTimeLimit))
            time.sleep(4)


def _on_signal(signum, frame):
    if _st["expired"] and _st["in_call"]:
        raise FileTimeLimit()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    if not LIMIT or not hasattr(item.config, "workerinput"):
        return None
    _st["files"].add(item.nodeid.split("::", 1)[0])
    if _st["deadline"] is None:
        _st["deadline"] = time.time() + LIMIT
        _st["tid"] = threading.get_ident()
        _st["main"] = threading.current_thread() is threading.main_thread()
        if _st["main"]:
            try:
                signal.signal(signal.SIGUSR2, _on_signal)
            except (ValueError, OSError):
                _st["main"] = False
        threading.Thread(target=_watch, daemon=True).start()
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if _st["expired"] and hasattr(item.config, "workerinput"):
        pytest.skip(f"test file over its time limit ({LIMIT:.0f} s)")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    _st["in_call"] = True
    try:
        yield
    finally:
        _st["in_call"] = False
