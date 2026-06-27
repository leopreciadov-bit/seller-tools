#!/usr/bin/env bash
# Keep site + public tunnel alive (YOLO preview hosting)
set -euo pipefail
SITE_ROOT="$(cd "$(dirname "$0")/../site" && pwd)"
PORT="${PORT:-8888}"
CLOUDFLARED="${CLOUDFLARED:-/tmp/cloudflared}"

if ! curl -s -o /dev/null "http://127.0.0.1:${PORT}/"; then
  cd "$SITE_ROOT"
  nohup python3 -m http.server "$PORT" >/tmp/seller-tools-http.log 2>&1 &
  echo "Started http.server on $PORT"
fi

if [[ -x "$CLOUDFLARED" ]]; then
  pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" 2>/dev/null || true
  nohup "$CLOUDFLARED" tunnel --url "http://127.0.0.1:${PORT}" >/tmp/seller-tools-tunnel.log 2>&1 &
  sleep 4
  grep -o 'https://[^ ]*trycloudflare.com' /tmp/seller-tools-tunnel.log | head -1 || true
fi