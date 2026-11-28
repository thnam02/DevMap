"""Add b1b.collection()'s fields to B1b rows run without install (old build script) before that check existed.

Computed from each instance's saved outcomes at the fixed version ($PROVISO_WORK/b1b-<repo>/b1b/<id>/base_outcomes.json)
and a tree at the base commit + test patch (the reference fix changes source files only, so the test files on disk
are those of the fixed version). A row whose FAIL_TO_PASS tests were not all collected becomes a skip with b1b.py's
reason (its result kept under R_superseded). Run only while B1b is stopped (rows files are rewritten).
  python research/v2/b1b_collection_rows.py [--dry-run]"""
import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b1b  # noqa: E402
import pipeline as PL  # noqa: E402
import swe_probe as P  # noqa: E402


def main():
    dry = "--dry-run" in sys.argv
    meta, envs = P.load_instances(), b1b.envs_ok()
    for path in sorted(glob.glob(os.path.join(b1b.OUT, "rows.w*.jsonl"))):
        lines, changed = [], 0
        for line in open(path):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("install") == "skipped" and "collected_share" not in r and r.get("status") == "ok":
                x = meta[r["id"]]
                b1b.configure(r["repo"], envs[(r["repo"], x["version"])])
                base = PL.jload(os.path.join(PL.WORK, "b1b", r["id"], "base_outcomes.json"), {})
                f2p = json.loads(x["FAIL_TO_PASS"]) if isinstance(x["FAIL_TO_PASS"], str) else x["FAIL_TO_PASS"]
                with tempfile.TemporaryDirectory() as t:
                    subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", P.repo_clone(r["repo"]), t],
                                   check=True)
                    subprocess.run(["git", "-C", t, "checkout", "-q", "-f", x["base_commit"]], check=True)
                    subprocess.run(["git", "-C", t, "apply", "-"], input=x["test_patch"], text=True, check=True)
                    c = b1b.collection(t, base, f2p, x["test_patch"])
                r.update(c, collection_backfilled="from the saved outcomes at the fixed version (2026-11-28)")
                if c["f2p_not_collected_n"]:
                    r["R_superseded"] = r.pop("R", None)
                    r["status"] = "skip"
                    r["why"] = (f"{b1b.OLD_BUILD_WHY}; without install {c['f2p_not_collected_n']} of {len(f2p)} "
                                f"FAIL_TO_PASS tests not collected")
                changed += 1
                print(r["id"], r["status"], f"{c['collected_test_files']}/{c['test_files_total']} test files",
                      f"F2P not collected {c['f2p_not_collected_n']}/{len(f2p)}")
            lines.append(json.dumps(r) + "\n")
        if changed and not dry:
            open(path, "w").writelines(lines)


if __name__ == "__main__":
    main()
