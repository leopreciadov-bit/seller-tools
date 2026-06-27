#!/usr/bin/env bash
# Temp-mail autopilot: Gumroad signup + product prep + Reddit
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/tmp/seller-venv/bin/python}"

[[ -x "$PY" ]] || { python3 -m venv /tmp/seller-venv && /tmp/seller-venv/bin/pip install -q playwright requests; }

echo "=== Gumroad license uploads ==="
python3 scripts/gumroad_launch.py

echo ""
echo "=== Gumroad signup (temp mail) ==="
echo "Headless hits reCAPTCHA. Use --manual to solve once:"
echo "  $PY scripts/gumroad_autopilot.py --signup --manual"
echo "  $PY scripts/gumroad_autopilot.py --products --manual"

echo ""
echo "=== Reddit r/Etsy (temp mail) ==="
echo "  $PY scripts/reddit_autopilot.py --manual"