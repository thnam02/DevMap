#!/bin/bash
# b1run.sh N PROJECT [PROJECT ...]: B1 (resumable) per project, one at a time; after each: report, commit
# research/v2/results/b1/PROJECT (and report.md) to eval-pc, push (stays local if the push fails).
set -u
cd "$HOME/proviso-dev"
export PATH=$HOME/.local/bin:$PATH PROVISO_WORK=$HOME/proviso-work/v2 PROVISO_WORKERS=12 NAMERTS_WORKERS=1
export NAMERTS_HOME=$PROVISO_WORK/NameRTS TDAD_SRC=$PROVISO_WORK/TDAD/tdad/src
n=$1; shift
G="git -c user.name=thnam02 -c user.email=tranhainam187@gmail.com"
for p in "$@"; do
  case $p in
    sqlglot|pygments|datasette|sqlalchemy) PY=$HOME/proviso-work/venv/bin/python; unset NAMERTS_DEPS ;;
    *) PY=$PROVISO_WORK/nrbench-venvs/$p/bin/python; export NAMERTS_DEPS=$PROVISO_WORK/nr-deps-3.13 ;;
  esac
  # datasette: temporary files on tmpfs (per-test SQLite fixture databases; fsync on WSL2's virtual disk ~7 ms/commit)
  if [ "$p" = datasette ]; then export TMPDIR=/dev/shm/proviso-tmp-datasette; mkdir -p "$TMPDIR"; else unset TMPDIR; fi
  [ -n "$(git status --porcelain -- src)" ] && { echo "== STOP: src/ has local changes"; exit 1; }
  echo "== B1 $p N=$n start $(date -u +%FT%TZ) py=$PY timeout=${PROVISO_TEST_TIMEOUT:-1800}"; s=$(date +%s)
  "$PY" research/v2/b1.py "$p" "$n" --workers 1
  rc=$?
  echo "== B1 $p exit $rc after $(( $(date +%s) - s )) s"
  "$HOME/proviso-work/venv/bin/python" research/v2/b1.py report > /dev/null 2>&1 || echo "== report failed"
  if [ "${B1_COMMIT:-1}" = 1 ]; then
    git add "research/v2/results/b1/$p" research/v2/results/b1/report.md 2>/dev/null
    if ! git diff --cached --quiet; then
      ok=$(python3 -c "import json,glob;rs=[json.loads(l) for f in glob.glob('research/v2/results/b1/$p/rows.w*.jsonl') for l in open(f) if l.strip()];print(sum(r.get('status')=='ok' for r in rs),'ok,',sum(r.get('status')=='skip' for r in rs),'skip,',sum(r.get('status')=='error' for r in rs),'error')" 2>/dev/null)
      $G commit -q -m "B1 $p on the PC (WSL2, 80% cap, Proviso v2.3.1): $ok"
      GIT_TERMINAL_PROMPT=0 git push -q origin eval-pc 2>&1 | grep -vE 'moved|new location|DevMap' ; echo "== committed $p ($ok); push status: $(git status -sb | head -1)"
    fi
  fi
done
echo "== B1RUN FINISHED $* $(date -u +%FT%TZ)"
