"""(v2.3.1) Fork server for recording: one interpreter imports pytest once, then forks a child per test file, which runs
`pytest.main(args)` exactly as `python -m pytest args` would, with the recorder (-p dc_engine.covplugin) imported in the
child. The children skip interpreter start-up and pytest's own import; everything the recorder sees still happens in
the child: the recorder is loaded after pytest in a normal run too, so importing pytest earlier changes nothing it
records. The project's own code is never imported in the server.

Protocol (record.py): started with the recording environment and cwd = the tree, as `python -m dc_engine.forkrec`;
reads {"workers": N, "timeout": seconds or 0, "jobs": [{"id": i, "args": [...], "env": {...}}, ...]} as JSON on
stdin, runs the jobs in the order given (at most N at a time), and prints one JSON line per finished job:
{"id": i, "rc": exit status or null, "timeout": bool, "seconds": wall time}.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time


def _child(args: list[str], env: dict) -> None:
    try:
        fd = os.open(os.devnull, os.O_RDWR)
        for k in (0, 1, 2):
            os.dup2(fd, k)
        os.environ.clear()
        os.environ.update(env)
        # a fresh interpreter seeds its random generator itself; forked children would all share the server's state
        if "random" in sys.modules:
            sys.modules["random"].seed()
        import pytest
        sys.argv = [os.path.join(os.path.dirname(pytest.__file__), "__main__.py"), *args]   # as `python -m pytest`
        rc = pytest.main(args)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(int(rc) if isinstance(rc, int) else 0)
    except BaseException:  # noqa: BLE001
        os._exit(70)


def main() -> None:
    req = json.load(sys.stdin)
    out = sys.stdout
    workers, timeout = max(1, int(req.get("workers") or 1)), float(req.get("timeout") or 0)
    import pytest  # noqa: F401  (the only thing preloaded)
    queue = list(req["jobs"])
    running: dict = {}   # pid -> (id, start)
    while queue or running:
        while queue and len(running) < workers:
            job = queue.pop(0)
            out.flush()
            pid = os.fork()
            if pid == 0:
                _child(job["args"], job["env"])
            running[pid] = (job["id"], time.time())
        pid, status = os.waitpid(-1, os.WNOHANG)
        if pid == 0:
            if timeout:
                now = time.time()
                for p, (i, t0) in list(running.items()):
                    if now - t0 > timeout:
                        os.kill(p, signal.SIGKILL)
                        os.waitpid(p, 0)
                        del running[p]
                        out.write(json.dumps({"id": i, "rc": None, "timeout": True, "seconds": round(now - t0, 2)})
                                  + "\n")
                        out.flush()
            time.sleep(0.005)
            continue
        if pid not in running:
            continue
        i, t0 = running.pop(pid)
        rc = os.waitstatus_to_exitcode(status)
        out.write(json.dumps({"id": i, "rc": rc, "timeout": False, "seconds": round(time.time() - t0, 2)}) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
