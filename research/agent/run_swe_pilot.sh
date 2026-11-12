#!/usr/bin/env bash
# Agent study, SWE-bench pilot: does Proviso's test selection change what a coding agent costs and breaks?
#   2 arms x N SWE-bench tasks x 2 reps = Claude Code runs (Sonnet), one at a time, interleaved:
#     baseline         the agent alone; it runs whatever tests it chooses
#     impact-noreport  Proviso v2.3 rewrites the agent's broad test commands to the tests the change can affect
#   measures: hidden tests passed (FAIL_TO_PASS), PASS_TO_PASS tests broken, wall time, cost, test commands
# Spending: each run is capped at PROVISO_AGENT_BUDGET_USD (default 1.40), and the script refuses to start if
# runs x cap exceeds PROVISO_AGENT_TOTAL_USD (default 70): 12 tasks x 2 arms x 2 reps x $1.40 = $67.20 (a run can
# end slightly over its cap, as Claude Code checks it between requests, so this leaves a margin under $70).
# Pilot design (approved 12 Nov 2026): two runs per task measure run-to-run variation, to size the final study.
#
# Before this script (as your normal user, free; it reads the SWE-bench clones and environments):
#   python3 research/agent/swe_tasks.py SWE_EVAL_DIR --n 12     (tasks, Proviso assets, preflight; must print OK)
# Then, as the isolated agent user (no SSH keys, git credentials or other secrets), from its clone of the repository
# at the commit to evaluate, with ANTHROPIC_API_KEY exported in this shell (never written to a file):
#   PROVISO_AGENT_TASKS_FROM=SWE_EVAL_DIR bash research/agent/run_swe_pilot.sh
#   PROVISO_AGENT_DRY=1 ... prints the plan and calls no model (free)
# The agent user needs read and execute access to the task interpreters (the SWE-bench environments and the
# Python installation they link to); the tasks name them in their "python" field.
set -euo pipefail
cd "$(dirname "$0")/../.."
REPO_DIR=$(pwd)
SRC=${PROVISO_AGENT_TASKS_FROM:?set PROVISO_AGENT_TASKS_FROM to the directory swe_tasks.py built}
W=${PROVISO_AGENT_WORK:-$HOME/proviso-work/agent-swe}   # must be outside the repository (the harness refuses otherwise)
VENV=${PROVISO_AGENT_VENV:-$HOME/proviso-work/agent-venv}
BUDGET=${PROVISO_AGENT_BUDGET_USD:-1.40}   # Claude Code checks between requests: a run can end slightly over
TOTAL=${PROVISO_AGENT_TOTAL_USD:-70}
REPS=${PROVISO_AGENT_REPS:-2}
ARMS=baseline,impact-noreport
OUTDIR="$REPO_DIR/research/agent/results-swe-pilot"

command -v claude >/dev/null || { echo "Claude Code CLI not found: npm install -g @anthropic-ai/claude-code"; exit 1; }
# a Python 3.12+ for the harness (macOS's own python3 is older): PROVISO_AGENT_PYTHON, else the first that fits
HPY=${PROVISO_AGENT_PYTHON:-}
if [ -z "$HPY" ]; then
  for c in python3 python3.13 python3.12; do
    if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
      HPY=$(command -v "$c"); break
    fi
  done
fi
[ -n "$HPY" ] || { echo "Python 3.12+ needed: e.g. uv python install 3.12, then PROVISO_AGENT_PYTHON=\$(uv python find 3.12)"; exit 1; }
python3() { "$HPY" "$@"; }
# `timeout` is GNU coreutils (absent on macOS): fall back to gtimeout, else a perl alarm
# (an array, so it runs as a command after `env`; `eval` is a shell builtin that env cannot run)
if command -v timeout >/dev/null; then TO=(timeout); elif command -v gtimeout >/dev/null; then TO=(gtimeout)
else TO=(perl -e 'alarm shift; exec @ARGV'); fi
[ -d "$SRC/tasks" ] && [ -d "$SRC/impact" ] || { echo "no tasks/ and impact/ in $SRC: run swe_tasks.py first"; exit 1; }

NT=$(ls "$SRC"/tasks/*.json | wc -l)
NRUNS=$(( NT * 2 * REPS ))
python3 - "$NRUNS" "$BUDGET" "$TOTAL" <<'PYEOF' || exit 1
import sys
n, cap, total = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
print(f"== {n} runs, at most ${cap:.2f} each: at most ${n * cap:.2f} (limit ${total:.2f})")
sys.exit(0 if n * cap <= total + 1e-9 else "over the total limit: lower the cap, the tasks or the repetitions")
PYEOF

for t in "$SRC"/tasks/*.json; do
  py=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("python",""))' "$t")
  # pytest's own tasks: the environment's pytest is the project, linked from each run's copy, so check its dependencies
  case "$t" in *pytest-dev__pytest-*) chk='import pluggy, iniconfig' ;; *) chk='import pytest' ;; esac
  [ -x "$py" ] && "$py" -c "$chk" 2>/dev/null \
    || { echo "this user cannot run the task interpreter (or it lacks pytest): $py  ($t)"; exit 1; }
done
echo "== task interpreters usable by $(whoami)"

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -e "$REPO_DIR" pytest
fi
PY="$VENV/bin/python"
"$PY" -c "import dc_engine.impact as I; print('== Proviso', I.VERSION, 'from', I.__file__)"

mkdir -p "$W"
rm -rf "$W/tasks" "$W/impact"
cp -r "$SRC/tasks" "$SRC/impact" "$W/"

if [ -n "${PROVISO_AGENT_DRY:-}" ]; then
  cd "$W"
  "$PY" -m dc_eval run --eval-dir "$W" --arms "$ARMS" --reps "$REPS" --model sonnet --max-budget-usd "$BUDGET" \
    --timeout 1800 --dry-run
  exit 0
fi

[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "ANTHROPIC_API_KEY is not set in this shell (export it; do not save it to a file)."; exit 1; }
export DC_EVAL_CLAUDE_HOST_AUTH=1

# Pre-flight (free: an invalid key, so nothing reaches the model): does this Claude Code fire hooks from --settings?
PF=$(mktemp -d)
printf '{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"touch %s/fired"}]}]}}' "$PF" > "$PF/settings.json"
(cd "$PF" && env -i PATH="$PATH" HOME="$PF" ANTHROPIC_API_KEY=invalid-preflight-key \
   "${TO[@]}" 60 claude -p "hi" --settings "$PF/settings.json" --output-format stream-json --verbose >/dev/null 2>&1 || true)
if [ ! -f "$PF/fired" ]; then
  echo "Pre-flight failed: Claude Code did not run a hook from --settings. Proviso would be inactive; not starting."
  rm -rf "$PF"; exit 1
fi
rm -rf "$PF"
echo "== pre-flight: hooks fire"

echo "== running the pilot ($(date +%T)); cap \$$BUDGET per run"
cd "$W"
"$PY" -m dc_eval run --eval-dir "$W" --arms "$ARMS" --reps "$REPS" --model sonnet --max-budget-usd "$BUDGET" \
  --timeout 1800 --resume
"$PY" -m dc_eval report --eval-dir "$W"

cd "$REPO_DIR"
mkdir -p "$OUTDIR"
cp "$W/results.jsonl" "$W/report.md" "$OUTDIR/"
"$PY" research/agent/inspect_runs.py "$W" > "$OUTDIR/inspect.txt" 2>&1 || echo "== inspect_runs failed (run it by hand later)"
python3 - "$OUTDIR/results.jsonl" <<'PYEOF'
import json, sys
rows = {}
for l in open(sys.argv[1]):  # a regraded run appears twice: keep its last row
    if l.strip():
        r = json.loads(l)
        rows[(r.get("task"), r.get("arm"), r.get("rep"))] = r
rows = list(rows.values())
err = sum(r.get("status") in ("grading_error", "setup_error", "agent_error") for r in rows)
print(f"== {len(rows)} runs ({err} with errors), total cost ${sum(r.get('cost_usd') or 0 for r in rows):.2f}")
PYEOF
# the isolated agent user usually has no git identity or credentials: then the results stay in $OUTDIR to copy
if git add "$OUTDIR" && ! git diff --cached --quiet \
   && git commit -qm "Agent study, SWE-bench pilot results ($(hostname), $(date +%F))" 2>/dev/null; then
  if git pull -q --rebase 2>/dev/null && git push -q 2>/dev/null; then echo "== results pushed"
  else echo "== results committed locally only; copy $OUTDIR to your own clone and push from there"; fi
else
  git reset -q 2>/dev/null || true
  echo "== results not committed (no git identity here): copy $OUTDIR to your own clone and push from there"
fi
echo "== done ($(date +%T))"
