"""trace_at.py TREE WANT_JSON TEST... [--env K=V] [--deselect-rest]: run tests in TREE (as is) under the trace plugin of
trace_changed.py; WANT_JSON = list of "relpath::qualname". Prints per-test hits."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, "/home/claude/proviso-dev/research/v2")
import trace_changed as T
args = sys.argv[1:]
env_extra = {}
while "--env" in args:
    i = args.index("--env"); k, v = args[i+1].split("=", 1); env_extra[k] = v; del args[i:i+2]
tree, want, *tests = args
want = json.loads(want)
pp = open(os.path.expanduser("~/proviso-work/static/pp.txt")).read().strip()
with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, "trace_plugin.py"), "w").write(T.PLUGIN)
    out = os.path.join(tmp, "out.json")
    env = {**os.environ, **env_extra, "TRACE_WANT": json.dumps(want), "TRACE_ROOT": tree.rstrip("/") + os.sep,
           "TRACE_OUT": out, "PYTHONPATH": os.pathsep.join([tmp, tree, os.path.join(tree, "lib"), pp]),
           "PYTHONDONTWRITEBYTECODE": "1"}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "trace_plugin", "-p", "no:cacheprovider",
                        "-o", "addopts=", *tests], cwd=tree, capture_output=True, text=True, env=env)
    res = json.load(open(out)) if os.path.exists(out) else {"hits": {}, "outcomes": {}}
hits = res["hits"]
print(json.dumps({"env": env_extra, "outcomes": {k: sum(1 for v in res["outcomes"].values() if v == k) for k in set(res["outcomes"].values())},
                  "before": hits.get("<before tests>", []), "between": hits.get("<between tests>", []),
                  "tests_hit": {t: v for t, v in hits.items() if not t.startswith("<")},
                  **({} if res["outcomes"] else {"tail": (p.stdout + p.stderr)[-1200:]})}, indent=1))
