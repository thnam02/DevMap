"""Run EkstaP (NameRTS's file-level baseline: class EkstaziP in NameRTS's src/framework.py, approach "ekstap" in its
src/evaluate.py) on our changes, as NameRTS's evaluate_instance drives it (evaluate_ekstazip: use_isolation=False,
cached files dependencies.json and py_checksums_cache.json):

  init  (tree at the parent)  : EkstaziP(...).get_tests_to_run(init=True) + run_and_update(those tests) = its own
                                dependency run; its caches are then saved
  select (tree after a change): the caches are restored and EkstaziP(...).get_tests_to_run() returns the test FILES

Same environment set-up as namerts_driver.py (NAMERTS_HOME, the conda stand-in, scope and test-directory settings,
the one runtime fix). Usage: python ekstap_driver.py init|select TREE CACHE_DIR [repo]"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import namerts_driver as ND  # noqa: E402

CACHED = ["dependencies.json", "py_checksums_cache.json"]


def main():
    action, tree, cache = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
    repo = sys.argv[4] if len(sys.argv) > 4 else "sqlglot"
    ND.setup(tree, repo)
    from src.framework import EkstaziP
    n = int(os.environ.get("NAMERTS_WORKERS", "2"))
    if action == "init":
        obj = EkstaziP(project_path=tree, conda_env_name="local", n=n, use_isolation=False)
        tests = obj.get_tests_to_run(init=True)
        obj.run_and_update(tests)
        os.makedirs(cache, exist_ok=True)
        for f in CACHED:
            shutil.copy(os.path.join(tree, f), os.path.join(cache, f))
        print(json.dumps({"init_tests": len(tests), "test_time": obj.get_test_time()}))
    else:
        for f in CACHED:
            shutil.copy(os.path.join(cache, f), os.path.join(tree, f))
        obj = EkstaziP(project_path=tree, conda_env_name="local", n=n, use_isolation=False)
        tests = obj.get_tests_to_run()
        print("EKSTAP_SELECTED " + json.dumps(sorted(tests)))


if __name__ == "__main__":
    main()
