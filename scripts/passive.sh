#!/usr/bin/env bash
# Full passive income autopilot — run weekly via cron
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-/tmp/seller-venv/bin/python}"

[[ -x "$PY" ]] || {
  python3 -m venv /tmp/seller-venv
  /tmp/seller-venv/bin/pip install -q playwright requests
  /tmp/seller-venv/bin/python -m playwright install chromium
  /tmp/seller-venv/bin/python -m playwright install-deps chromium 2>/dev/null || true
}

exec "$PY" "$ROOT/scripts/passive_income_autopilot.py"