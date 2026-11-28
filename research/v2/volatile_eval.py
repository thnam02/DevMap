"""v2.5 run-varying values: snapshot-level evaluation on real projects (no test runs needed).

For each project (a git checkout at a fixed commit, importable with the given Python):
  noop      a comment line added to the package's __init__.py, compared with the base snapshot N times in fresh
            processes with different heap layouts: keys reported changed with the mechanism off (v2.3.2) and on.
            On must be empty every time; off shows what the mechanism removes.
  mask      per covered key: how many leaves of the value the pattern still compares exactly, how many it compares
            by shape only (kind, common start/end, length) and how many not at all.
  mutate    random single edits to a current value's tree (change a leaf, drop an element, add an element): the share
            still reported as changed. Undetected edits are listed by the kind of leaf they hit.
  seeded    source edits that are real import-time changes (given per project): each must be reported with the
            mechanism on, by the snapshot comparison itself or by the edited-statement guard (noted which).

Usage: python volatile_eval.py PROJECT ROOT PKGDIR OUT.json [--trials N]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
from dc_engine import impact as I  # noqa: E402
from dc_engine import importstate as S  # noqa: E402

PY = sys.executable


def git(root, *a):
    return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True).stdout


def package_files(root: str, pkgdir: str) -> list[str]:
    fs = [f for f in git(root, "ls-files", pkgdir).split("\n") if f.endswith(".py")]
    return sorted(f for f in fs if not I._is_test_path(f) and not I._is_test_support(f))


def with_off(off: bool, fn):
    old = os.environ.get("PROVISO_OFF")
    if off:
        os.environ["PROVISO_OFF"] = "volatile"
    else:
        os.environ.pop("PROVISO_OFF", None)
    try:
        return fn()
    finally:
        if old is None:
            os.environ.pop("PROVISO_OFF", None)
        else:
            os.environ["PROVISO_OFF"] = old


def leaves(n, acc):
    k = n[0]
    if k == "s":
        acc["exact"] += 1
    elif k == "w":
        acc["shape" if (n[2] or n[3] or n[4] >= 0) else "kind"] += 1
    elif k == "*":
        acc["any"] += 1
    elif k in ("l", "b"):
        for c in n[2]:
            leaves(c, acc)
    else:
        for a, b in n[2]:
            leaves(a, acc)
            leaves(b, acc)
    return acc


def paths(n, here=()):
    """Every node of a tree as (path, node)."""
    yield here, n
    if n[0] in ("l", "b"):
        for i, c in enumerate(n[2]):
            yield from paths(c, here + (i,))
    elif n[0] == "m":
        for i, (a, b) in enumerate(n[2]):
            yield from paths(a, here + (i, 0))
            yield from paths(b, here + (i, 1))


def node_at(n, path):
    path = list(path)
    while path:
        if n[0] == "m":
            n = n[2][path.pop(0)][path.pop(0)]
        else:
            n = n[2][path.pop(0)]
    return n


def mutate(tree, rng):
    """One random edit; returns (mutated tree, kind of edit, tag of the leaf hit or '')."""
    t = copy.deepcopy(tree)
    allp = list(paths(t))
    leafs = [p for p, n in allp if n[0] == "s"]
    conts = [p for p, n in allp if n[0] in ("l", "b", "m") and n[2]]
    kind = rng.choice(["leaf", "leaf", "drop", "add"]) if conts else "leaf"
    if kind == "leaf" and leafs:
        n = node_at(t, rng.choice(leafs))
        tag = n[1]
        if tag in ("int", "float"):
            n[2] = repr((int(float(n[2])) if n[2].replace(".", "").lstrip("-").isdigit() else 0) + rng.randint(1, 9))
        elif tag == "bool":
            n[2] = "False" if n[2] == "True" else "True"
        else:
            i = rng.randrange(len(n[2]) + 1)
            n[2] = n[2][:i] + "Z" + n[2][i + 1:] if i < len(n[2]) and n[2][i] != "Z" else n[2][:i] + "Q" + n[2][i:]
        return t, "leaf", tag
    if not conts:
        return t, "none", ""
    c = node_at(t, rng.choice(conts))
    if kind == "drop":
        c[2].pop(rng.randrange(len(c[2])))
        return t, "drop", ""
    c[2].append(copy.deepcopy(rng.choice(c[2])))
    return t, "add", ""


def run(project: str, root: str, pkgdir: str, out: str, trials: int, seeded: list) -> None:
    files = package_files(root, pkgdir)
    init = next(f for f in files if f.endswith("/__init__.py") and f.count("/") == pkgdir.rstrip("/").count("/") + 1)
    res: dict = {"project": project, "commit": git(root, "rev-parse", "--short", "HEAD").strip(), "files": len(files)}
    assert not git(root, "status", "--porcelain", "--", pkgdir).strip(), "package directory not clean"
    cache = {m: os.path.join(os.path.dirname(os.path.abspath(out)), f"{project}_base_{m}.json") for m in ("off", "on")}
    base = {}
    for m in ("off", "on"):
        if os.path.exists(cache[m]):
            os.remove(cache[m])
        t0 = time.time()
        base[m] = with_off(m == "off", lambda: S.base_snapshot(root, files, PY, cache[m]))
        res[f"base_seconds_{m}"] = round(time.time() - t0, 1)
        assert base[m] is not None, "no base snapshot"
    pats = base["on"].get("patterns", {})
    res.update(keys=len(base["on"]["state"]), unstable_off=len(base["off"]["unstable"]),
               unstable_on=len(base["on"]["unstable"]), patterns=len(pats),
               pattern_samples=base["on"].get("pattern_samples"), import_errors=len(base["on"]["errors"]))
    res["mask"] = {k: leaves(p, {"exact": 0, "shape": 0, "kind": 0, "any": 0}) for k, p in pats.items()}

    # ---- noop: a comment at the top of __init__.py
    src = open(os.path.join(root, init)).read()
    noop = {"off": [], "on": []}
    last_cur = None
    try:
        open(os.path.join(root, init), "w").write("# no-op change\n" + src)
        for i in range(trials):
            pad = [0, 5003, 7919, 20011, 30011, 1009, 40009, 12007, 2003, 60013][i % 10]
            cur = S.snapshot(root, files, PY, heap_pad=pad, tree_keys=sorted(pats))
            assert cur is not None
            last_cur = cur
            noop["off"].append(with_off(True, lambda: S.diff(base["off"], cur))["changed"])
            noop["on"].append(S.diff(base["on"], cur)["changed"])
    finally:
        open(os.path.join(root, init), "w").write(src)
    res["noop"] = {m: {"trials": trials, "trials_with_changes": sum(1 for c in v if c),
                       "keys_ever_changed": sorted({k for c in v for k in c})} for m, v in noop.items()}

    # ---- mutate: random edits to the current trees of covered keys
    rng = random.Random(1)
    mut = {}
    for k in sorted(pats):
        tree = (last_cur.get("trees") or {}).get(k)
        if tree is None or not S.covers(pats[k], tree):
            mut[k] = None
            continue
        n = det = 0
        missed: dict[str, int] = {}
        for _ in range(300):
            t, kind, tag = mutate(tree, rng)
            if kind == "none" or json.dumps(t) == json.dumps(tree):
                continue
            n += 1
            if not S.covers(pats[k], t):
                det += 1
            else:
                missed[f"{kind}:{tag}"] = missed.get(f"{kind}:{tag}", 0) + 1
        mut[k] = {"edits": n, "detected": det, "undetected_by_kind": missed}
    res["mutate"] = mut

    # ---- seeded: real import-time edits
    sd = []
    for name, f, old, new in seeded:
        srcf = open(os.path.join(root, f)).read()
        assert srcf.count(old) == 1, (name, srcf.count(old))
        try:
            open(os.path.join(root, f), "w").write(srcf.replace(old, new))
            cur = S.snapshot(root, files, PY, heap_pad=7919, tree_keys=sorted(pats))
            assert cur is not None, name
            d_on = S.diff(base["on"], cur)
            d_off = with_off(True, lambda: S.diff(base["off"], cur))
            tn = I._changed_top_names(git(root, "show", f"HEAD:{f}"), open(os.path.join(root, f)).read())[0]
            mod = I._module_of(f, I._layout_prefix(files))
            guard = [k for k in d_on["covered"] if k.split(":", 1)[0] == mod
                     and (tn is None or k.split(":", 1)[1].split(".", 1)[0] in tn)]
            off_real = sorted(set(d_off["changed"]) - set(res["noop"]["off"]["keys_ever_changed"]))
            sd.append({"edit": name, "file": f, "changed_on": d_on["changed"][:12], "n_changed_on": len(d_on["changed"]),
                       "guard_adds": guard, "detected_on": bool(d_on["changed"] or guard or d_on["errors"]),
                       "by": "snapshot" if d_on["changed"] or d_on["errors"] else ("guard" if guard else "none"),
                       "off_beyond_noise": off_real[:12], "n_off": len(d_off["changed"]),
                       "errors": d_on["errors"]})
        finally:
            open(os.path.join(root, f), "w").write(srcf)
    res["seeded"] = sd
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("mask", "mutate", "seeded")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("root")
    ap.add_argument("pkgdir")
    ap.add_argument("out")
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--seeded", default="")
    a = ap.parse_args()
    run(a.project, a.root, a.pkgdir, a.out, a.trials, json.load(open(a.seeded)) if a.seeded else [])
