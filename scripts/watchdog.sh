#!/usr/bin/env bash
# Restart promotion daemons if they died (e.g. max_runtime kill).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

alive() { pgrep -f "$ROOT/scripts/$1" >/dev/null 2>&1; }

if ! alive blast_loop.py; then
  nohup flock -n "$ROOT/pipeline/.blast-loop.lock" bash -c \
    "cd $ROOT && python3 scripts/blast_loop.py --daemon --interval 45 >> pipeline/blast-loop.log 2>&1" &
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restarted blast_loop" >> "$ROOT/pipeline/watchdog.log"
fi

if ! alive sale_hunt.py; then
  nohup flock -n "$ROOT/pipeline/.sale-hunt.lock" bash -c \
    "cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 60 >> pipeline/sale-hunt.log 2>&1" &
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restarted sale_hunt" >> "$ROOT/pipeline/watchdog.log"
fi