#!/usr/bin/env bash
# Run weekly via cron: indexing ping + health check. Zero human input.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="https://leopreciadov-bit.github.io/seller-tools"
LOG="/tmp/seller-tools-autopilot.log"

{
  echo "=== $(date -Iseconds) ==="
  for path in "" "/listing-lab/" "/etsy-tag-finder/" "/sitemap.xml"; do
    code=$(curl -sL -o /dev/null -w "%{http_code}" "$BASE$path")
    echo "$code $path"
    [[ "$code" == "200" ]] || echo "ALERT: $path returned $code"
  done
  python3 "$ROOT/scripts/resubmit_indexnow.py" 2>/dev/null || true
} >> "$LOG" 2>&1

echo "Autopilot done. Log: $LOG"