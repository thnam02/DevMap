"""(v2.5) Loaded at start-up by Python processes started under a recording (this directory is put on PYTHONPATH by the
recorder): a worker spawned by multiprocessing records what it runs, like a forked one. Does nothing in the recorded
test process itself or outside a recording."""
import os

import sys

# only multiprocessing's spawned workers: its resource tracker lives as long as the test process, and other Python
# children (scripts run through subprocess) keep the always rule
if os.environ.get("PROVISO_MP_DIR") and os.environ.get("PROVISO_MP_PARENT") != str(os.getpid()) \
        and os.environ.get("COVMAP_OUT") \
        and any("multiprocessing.spawn import spawn_main" in a for a in getattr(sys, "orig_argv", [])):
    try:
        import dc_engine.covplugin as _c
        _c._enter_child()
    except Exception:  # noqa: BLE001  (a worker must start whatever happens here)
        pass
