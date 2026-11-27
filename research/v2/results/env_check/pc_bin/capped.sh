#!/bin/bash
# capped.sh NAME LOG CMD...: run CMD as a transient systemd user service under the 80% cap (12 CPUs, 24 GiB, nice 10),
# stdout/stderr appended to LOG; waits for it to finish (run this inside tmux). Survives closing the session (linger).
name=$1; log=$2; shift 2
systemctl --user reset-failed "$name" 2>/dev/null
exec systemd-run --user --wait --collect --unit="$name" \
  -p CPUQuota=1200% -p MemoryMax=24G -p Nice=10 -p LimitNOFILE=65536 \
  -p StandardOutput=append:"$log" -p StandardError=append:"$log" \
  -p WorkingDirectory="$HOME/proviso-dev" "$@"
