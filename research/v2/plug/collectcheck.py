"""pytest plugin for env_check.py: per test file, how many tests collect, and every file whose collection fails or is
skipped as a whole (a module-level importorskip), with pytest's message. Output path in COLLECTCHECK_OUT."""
import json
import os

_problems = {}


def pytest_collectreport(report):
    if (report.failed or report.skipped) and report.nodeid and "::" not in report.nodeid:
        _problems[report.nodeid] = {"outcome": report.outcome, "message": str(report.longrepr)[-1500:]}


def pytest_collection_finish(session):
    items = {}
    for it in session.items:
        f = it.nodeid.split("::", 1)[0]
        items[f] = items.get(f, 0) + 1
    json.dump({"items": items, "problems": _problems}, open(os.environ["COLLECTCHECK_OUT"], "w"))
