#!/usr/bin/env bash
# Agent study, replay design: the agent continues from a published agent's regressing patch (replay_tasks.py).
#   2 arms x every kept case x REPS = Claude Code runs (Sonnet), one at a time per shard, arms interleaved:
#     baseline         the agent alone; it runs whatever tests it chooses
#     impact-noreport  Proviso v2.3 rewrites the agent's broad test commands to the tests the change can affect
#   measures: whether the starting regression is repaired (start_broken tests pass at the end), any PASS_TO_PASS
#   broken at the end, hidden tests (FAIL_TO_PASS), wall time, cost, test commands
# Order: repetition 1 of every case first, then repetition 2, so stopping early still leaves complete pairs.
# Spending: each run is capped at PROVISO_AGENT_BUDGET_USD (default 1.00); the shard stops before a run that could
# take its recorded total past PROVISO_AGENT_TOTAL_USD / number of shards (default total 200).
#
# Before this script (as the agent user, free):
#   python3 research/agent/replay_tasks.py REPLAY_DIR        (cases, Proviso assets, start-state checks; prints OK)
# Then, as the isolated agent user, with ANTHROPIC_API_KEY exported in this shell (never written to a file):
#   PROVISO_REPLAY_FROM=REPLAY_DIR bash research/agent/run_replay.sh
#   PROVISO_AGENT_SHARD=1/2 ... and PROVISO_AGENT_SHARD=2/2 ... in two terminals: two runs at a time
#   PROVISO_AGENT_DRY=1 ... prints the plan and calls no model (free)
#   PROVISO_AGENT_MODEL=haiku ... another model (its own work folder and results folder)
#   PROVISO_AGENT_STUDY=nocode PROVISO_REPLAY_FROM=<nocode_tasks.py dir> ... the NoCode-bench feature tasks (no start
#   patch; same arms, outcomes and folders named agent-nocode / results-nocode)
#   PROVISO_AGENT_CASES=20 PROVISO_AGENT_REPS=1 PROVISO_AGENT_TOTAL_USD=15 ... the early check: 20 cases spread over the
#   repositories, one repetition (40 runs)
set -euo pipefail
cd "$(dirname "$0")/../.."
REPO_DIR=$(pwd)
SRC=${PROVISO_REPLAY_FROM:?set PROVISO_REPLAY_FROM to the directory replay_tasks.py built}
SHARD=${PROVISO_AGENT_SHARD:-1/1}
SI=${SHARD%/*}; SN=${SHARD#*/}
[ "$SI" -ge 1 ] && [ "$SI" -le "$SN" ] || { echo "PROVISO_AGENT_SHARD must be i/n with 1 <= i <= n"; exit 1; }
SUFFIX=$([ "$SN" -gt 1 ] && echo "-s$SI" || echo "")
STUDY=${PROVISO_AGENT_STUDY:-replay}   # replay (replay_tasks.py) or nocode (nocode_tasks.py): names the folders
W=${PROVISO_AGENT_WORK:-$HOME/proviso-work/agent-$STUDY${PROVISO_AGENT_MODEL:+-$PROVISO_AGENT_MODEL}$SUFFIX}
VENV=${PROVISO_AGENT_VENV:-$HOME/proviso-work/agent-venv}
BUDGET=${PROVISO_AGENT_BUDGET_USD:-1.00}
TOTAL=${PROVISO_AGENT_TOTAL_USD:-200}
REPS=${PROVISO_AGENT_REPS:-2}
MODEL=${PROVISO_AGENT_MODEL:-sonnet}
MSUF=$([ "$MODEL" = sonnet ] && echo "" || echo "-$MODEL")
ARMS=baseline,impact-noreport
OUTDIR="$REPO_DIR/research/agent/results-$STUDY$MSUF$SUFFIX"

command -v claude >/dev/null || { echo "Claude Code CLI not found: npm install -g @anthropic-ai/claude-code"; exit 1; }
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
if command -v timeout >/dev/null; then TO=(timeout); elif command -v gtimeout >/dev/null; then TO=(gtimeout)
else TO=(perl -e 'alarm shift; exec @ARGV'); fi
[ -d "$SRC/tasks" ] && [ -d "$SRC/impact" ] || { echo "no tasks/ and impact/ in $SRC: run replay_tasks.py first"; exit 1; }

# this shard's cases: every SN-th in name order; PROVISO_AGENT_CASES=N first narrows them to N cases taken round-robin
# across the repositories (the early check), and a later full run resumes those runs
mkdir -p "$W"
rm -rf "$W/tasks" "$W/impact"
mkdir -p "$W/tasks" "$W/impact"
ALL=$(cd "$SRC/tasks" && ls *.json | sort)
if [ -n "${PROVISO_AGENT_CASES:-}" ]; then
  ALL=$(python3 - "$PROVISO_AGENT_CASES" $ALL <<'PYEOF'
import collections, re, sys
n, names = int(sys.argv[1]), sys.argv[2:]
by = collections.OrderedDict()
for f in names:
    by.setdefault(re.sub(r"-\d+__c\d+\.json$", "", f), []).append(f)
out = []
while len(out) < n and any(by.values()):
    for q in by.values():
        if q and len(out) < n:
            out.append(q.pop(0))
print("\n".join(sorted(out)))
PYEOF
)
fi
i=0
for t in $ALL; do
  if [ $(( i % SN )) -eq $(( SI - 1 )) ]; then
    cp "$SRC/tasks/$t" "$W/tasks/"
    a=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("assets") or d["id"])' "$SRC/tasks/$t")
    [ -d "$W/impact/$a" ] || cp -R "$SRC/impact/$a" "$W/impact/$a"
  fi
  i=$(( i + 1 ))
done
NT=$(ls "$W"/tasks/*.json | wc -l | tr -d ' ')
LIMIT=$(python3 -c "import sys; print(f'{float(sys.argv[1]) / int(sys.argv[2]):.2f}')" "$TOTAL" "$SN")
echo "== shard $SHARD: $NT cases x 2 arms x $REPS reps = $(( NT * 2 * REPS )) runs; at most \$$BUDGET each; this shard stops at \$$LIMIT"

for t in "$W"/tasks/*.json; do
  py=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("python",""))' "$t")
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

if [ -n "${PROVISO_AGENT_DRY:-}" ]; then
  cd "$W"
  "$PY" -m dc_eval run --eval-dir "$W" --arms "$ARMS" --reps "$REPS" --model "$MODEL" --max-budget-usd "$BUDGET" \
    --max-total-usd "$LIMIT" --timeout 1800 --dry-run | tail -25
  exit 0
fi

[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "ANTHROPIC_API_KEY is not set in this shell (export it; do not save it to a file)."; exit 1; }
export DC_EVAL_CLAUDE_HOST_AUTH=1
# graded runs keep final.diff, logs and metrics, not their repository copy and venv (regrading rebuilds them)
export DC_EVAL_COMPACT=1

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

cd "$W"
for r in $(seq 1 "$REPS"); do
  echo "== repetition $r of every case ($(date +%T))"
  set +e
  "$PY" -m dc_eval run --eval-dir "$W" --arms "$ARMS" --reps "$r" --model "$MODEL" --max-budget-usd "$BUDGET" \
    --max-total-usd "$LIMIT" --timeout 1800 --resume
  rc=$?
  set -e
  [ "$rc" -eq 5 ] && { echo "== spending limit reached for this shard"; break; }
  [ "$rc" -eq 0 ] || { echo "== dc_eval stopped (exit $rc)"; break; }
done
"$PY" -m dc_eval report --eval-dir "$W" || true

cd "$REPO_DIR"
mkdir -p "$OUTDIR"
cp "$W/results.jsonl" "$OUTDIR/"
[ -f "$W/report.md" ] && cp "$W/report.md" "$OUTDIR/"
cp "$SRC/cases.jsonl" "$OUTDIR/cases.jsonl" 2>/dev/null || true
[ -d "$SRC/rejected" ] && (cd "$SRC/rejected" && for d in */; do printf '%s\t%s\n' "${d%/}" "$(head -c 300 "$d/reason.txt" | tr '\n' ' ')"; done) > "$OUTDIR/rejected.tsv" 2>/dev/null || true
"$PY" research/agent/inspect_runs.py "$W" > "$OUTDIR/inspect.txt" 2>&1 || echo "== inspect_runs failed (run it by hand later)"
python3 - "$OUTDIR/results.jsonl" <<'PYEOF'
import json, sys
rows = {}
for l in open(sys.argv[1]):
    if l.strip():
        r = json.loads(l)
        rows[(r.get("task"), str(r.get("arm")), str(r.get("rep")))] = r
err = sum(r.get("status") in ("grading_error", "setup_error", "agent_error") for r in rows.values())
print(f"== {len(rows)} runs ({err} with errors), total cost ${sum(r.get('cost_usd') or 0 for r in rows.values()):.2f}")
PYEOF
echo "== results in $OUTDIR: copy them to your own clone and push from there"
echo "== done ($(date +%T))"
