"""How often do changes edit code that runs at import? A static check, no tests run.

For every changed non-test Python file of a change, each changed line (removed lines on the old side, added lines on
the new side; blank and comment-only lines ignored) is placed by the file's syntax tree:
  body       inside a function body (runs only when the function is called)
  statement  a module- or class-level statement other than the kinds below (assignments, calls, loops, ifs, ...):
             computes values at import, e.g. lookup tables, registries, constants, class attributes
  import     an import statement at module or class level
  header     a def/class header: decorators, signature (defaults run at import), bases
  docstring  a module or class docstring
A change "edits import-time code" at three levels:
  any      some line is not 'body'
  code     some line is 'statement' or 'import' (headers and docstrings left out)
  values   some line is 'statement' (the values built at import: what Proviso's snapshot compares)
A file that does not parse on one side counts as 'unparsable' (and as import-time on every level).

Sources:
  real    the main benchmark's real commits, the same sample as report-all.md (python importtime_changes.py real)
  agent   the SWE-bench agent regressions (python importtime_changes.py agent [--all]): the sampled cases of
          results/swe/sample.json, or with --all every genuine regressing patch in regressions.jsonl. Needs the patch
          files and the repository clones that swe_regressions.py / swe_eval.py keep under $PROVISO_WORK/swe.
Writes results/importtime_<source>.jsonl (one row per change) and results/importtime_<source>.md."""
from __future__ import annotations

import ast
import collections
import difflib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

KINDS = ("body", "statement", "import", "header", "docstring")


def git(cwd, *args, check=True, input_=None, env=None):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, input=input_,
                       env={**os.environ, **(env or {})})
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])}: {p.stderr.decode(errors='replace')[:300]}")
    return p.stdout


def is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (any(p in ("tests", "test", "testing") for p in parts[:-1]) or name.startswith("test_")
            or name.endswith("_test.py") or name == "conftest.py")


def line_kinds(src: str) -> dict[int, str] | None:
    """{line number: kind} for every line of a module; None if it does not parse."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    n = src.count("\n") + 1
    kinds = {i: "statement" for i in range(1, n + 1)}

    def mark(a, b, k):
        for i in range(a, b + 1):
            kinds[i] = k

    def visit_block(stmts, in_function: bool):
        for i, s in enumerate(stmts):
            end = s.end_lineno or s.lineno
            if in_function:
                mark(s.lineno, end, "body")
                continue
            if i == 0 and isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str):
                mark(s.lineno, end, "docstring")
            elif isinstance(s, (ast.Import, ast.ImportFrom)):
                mark(s.lineno, end, "import")
            elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = min([d.lineno for d in s.decorator_list] + [s.lineno])
                mark(start, end, "header")
                mark(s.body[0].lineno, end, "body")
                # a one-line def ("def f(): return 1") keeps its single line as body
            elif isinstance(s, ast.ClassDef):
                start = min([d.lineno for d in s.decorator_list] + [s.lineno])
                mark(start, s.body[0].lineno - 1 if s.body[0].lineno > s.lineno else s.lineno, "header")
                visit_block(s.body, False)
            else:
                mark(s.lineno, end, "statement")
                # functions defined inside module-level if/try blocks still have bodies that run only when called
                for node in ast.walk(s):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and node is not s:
                        if isinstance(node, ast.Lambda):
                            continue        # a lambda in a table is part of the value built at import
                        mark(node.body[0].lineno, node.end_lineno or node.lineno, "body")
    visit_block(tree.body, False)
    return kinds


def code_lines(src: str) -> set[int]:
    return {i for i, l in enumerate(src.splitlines(), 1) if l.strip() and not l.strip().startswith("#")}


def classify_file(old: str | None, new: str | None) -> collections.Counter:
    """Counter of kinds over the changed lines of one file (old None = added file, new None = deleted)."""
    a, b = (old or "").splitlines(), (new or "").splitlines()
    removed, added = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            removed.update(range(i1 + 1, i2 + 1))
        if tag in ("replace", "insert"):
            added.update(range(j1 + 1, j2 + 1))
    c = collections.Counter()
    for src, lines in ((old, removed), (new, added)):
        if src is None or not lines:
            continue
        lines &= code_lines(src)
        if not lines:
            continue
        k = line_kinds(src)
        if k is None:
            c["unparsable"] += len(lines)
            continue
        for i in lines:
            c[k.get(i, "statement")] += 1
    return c


def summarise_change(files: dict[str, collections.Counter]) -> dict:
    tot = collections.Counter()
    for c in files.values():
        tot.update(c)
    unp = tot["unparsable"] > 0
    return {"files": {f: dict(c) for f, c in files.items()}, "lines": dict(tot),
            "any": unp or any(tot[k] for k in ("statement", "import", "header", "docstring")),
            "code": unp or bool(tot["statement"] or tot["import"]),
            "values": unp or bool(tot["statement"]),
            "body_only": not unp and bool(tot["body"]) and not any(tot[k] for k in KINDS[1:]),
            "no_code": not unp and not sum(tot.values())}


def show(repo, rev, path):
    p = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=repo, capture_output=True)
    return p.stdout.decode("utf-8", errors="replace") if p.returncode == 0 else None


# ------------------------------------------------------------------------------------------------------- sources

def real_rows():
    import pipeline as PL
    out = []
    for repo in ["sqlglot", "sympy", "sqlalchemy", "pygments", "datasette"]:
        PL.use(repo)
        clone = os.path.join(os.environ.get("IMPORTTIME_CLONES", os.path.expanduser("~/proviso-work/static")), repo)
        if not os.path.isdir(os.path.join(clone, ".git")):
            subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", PL.CFG["url"], clone], check=True)
        ids = {r["id"] for r in PL.real_set()}
        rows = [r for r in PL.merged("realeval").values() if r["id"] in ids]
        rows = PL._confirmed(rows, "realeval")
        mine = PL.merged("mine")
        for r in rows:
            m = mine[r["id"]]
            commit = m["commit"]
            git(clone, "cat-file", "-e", commit + "^{commit}", check=False) or None
            names = git(clone, "diff", "--name-only", "--no-renames", commit + "^", commit).decode().split()
            files = {}
            for f in names:
                if not f.endswith(".py") or is_test(f):
                    continue
                files[f] = classify_file(show(clone, commit + "^", f), show(clone, commit, f))
            out.append({"source": "real", "repo": repo, "id": r["id"], "commit": commit,
                        "breaks_tests": bool(r["truth"]), **summarise_change(files)})
        print(repo, len(rows), flush=True)
    return out


def agent_rows(all_patches: bool, cases: list[dict] | None = None):
    import swe_probe as P
    import swe_regressions as R
    insts = {json.loads(l)["instance_id"]: json.loads(l)
             for l in open(os.path.join(HERE, "results", "swe", "instances.jsonl"))}
    if cases is not None:
        pass
    elif all_patches:
        cases = [r for r in map(json.loads, open(os.path.join(HERE, "results", "swe", "regressions.jsonl")))
                 if r.get("p2p_failed_genuine")]
        cases = [{"instance": r["instance"], "split": r["split"], "submission": r["submission"],
                  "patch": r["patch"], "reproduced": None} for r in cases]
    else:
        ev = {(r["instance"], r["case"]): r for r in map(json.loads, open(os.path.join(HERE, "results", "swe",
                                                                                      "eval-v2.3.jsonl")))}
        sample = json.load(open(os.path.join(HERE, "results", "swe", "sample.json")))
        cases = []
        for inst in sample["instances"]:
            for i, c in enumerate(inst["cases"]):
                e = ev.get((inst["instance"], i))
                cases.append({"instance": inst["instance"], "split": c["split"], "submission": c["submission"],
                              "patch": c["patch"], "reproduced": bool(e and e.get("reproduced"))})
    out, missing = [], 0
    for c in cases:
        inst = insts[c["instance"]]
        patch = os.path.join(R.WORK, "patches", c["split"], c["submission"], c["instance"] + ".diff")
        patch = patch if os.path.exists(patch) else c["patch"]
        if not (patch and os.path.exists(patch)):
            missing += 1
            continue
        clone = P.repo_clone(inst["repo"].replace("/", "__"))       # cloned if missing
        base = inst["base_commit"]
        P.ensure_commit(clone, base)
        diff = open(patch, "rb").read()
        with tempfile.NamedTemporaryFile(suffix=".index") as idx:
            env = {"GIT_INDEX_FILE": idx.name}
            git(clone, "read-tree", base, env=env)
            p = subprocess.run(["git", "apply", "--cached", "--whitespace=nowarn"], cwd=clone, input=diff,
                               capture_output=True, env={**os.environ, **env})
            if p.returncode:
                out.append({"source": "agent", "instance": c["instance"], "submission": c["submission"],
                            "error": "patch does not apply"})
                continue
            names = git(clone, "diff", "--cached", "--name-only", "--no-renames", base, env=env).decode().split()
            files = {}
            for f in names:
                if not f.endswith(".py") or is_test(f):
                    continue
                q = subprocess.run(["git", "show", f":{f}"], cwd=clone, capture_output=True, env={**os.environ, **env})
                new = q.stdout.decode("utf-8", errors="replace") if q.returncode == 0 else None
                files[f] = classify_file(show(clone, base, f), new)
        out.append({"source": "agent", "repo": inst["repo"], "instance": c["instance"], "submission": c["submission"],
                    "split": c["split"], "reproduced": c["reproduced"], **summarise_change(files)})
    if missing:
        print(f"{missing} cases skipped: patch file not found under {R.WORK}/patches", flush=True)
    return out


# ------------------------------------------------------------------------------------------------------- report

def pct(a, b):
    return f"{a} ({100 * a / b:.1f}%)" if b else "0"


def report(rows, title, group_key):
    rows = [r for r in rows if "error" not in r]
    lines = [f"# {title}", "", "| Group | Changes | Some import-time line (any) | Import-time statements or imports (code) "
             "| Import-time statements (values) | Function bodies only | No non-test Python code |",
             "|---|---|---|---|---|---|---|"]
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r[group_key]].append(r)
    for name, rs in sorted(groups.items()) + [("all", rows)]:
        n = len(rs)
        lines.append(f"| {name} | {n} | {pct(sum(r['any'] for r in rs), n)} | {pct(sum(r['code'] for r in rs), n)} | "
                     f"{pct(sum(r['values'] for r in rs), n)} | {pct(sum(r['body_only'] for r in rs), n)} | "
                     f"{pct(sum(r['no_code'] for r in rs), n)} |")
    tot = collections.Counter()
    for r in rows:
        tot.update(r["lines"])
    lines += ["", "Changed code lines by kind: " + ", ".join(f"{k} {tot[k]:,}" for k in (*KINDS, "unparsable"))]
    return lines


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "real"
    if src == "real":
        rows = real_rows()
        lines = report(rows, "Real commits of the main benchmark that edit import-time code", "repo")
        brk = [r for r in rows if r["breaks_tests"]]
        lines += ["", "Only commits that break a test:", ""] + report(brk, "Real commits that break tests", "repo")[2:]
    else:
        allp = "--all" in sys.argv
        rows = agent_rows(allp)
        src = "agent_all" if allp else "agent"
        lines = report(rows, "SWE-bench agent regressions that edit import-time code", "repo")
        if not allp:
            rep = [r for r in rows if r.get("reproduced")]
            lines += ["", "Only the reproduced regressions:", ""] + report(rep, "Reproduced", "repo")[2:]
        err = sum(1 for r in rows if "error" in r)
        lines += ["", f"Patches that did not apply to the base commit: {err}"]
    with open(os.path.join(HERE, "results", f"importtime_{src}.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    text = "\n".join(lines)
    open(os.path.join(HERE, "results", f"importtime_{src}.md"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
