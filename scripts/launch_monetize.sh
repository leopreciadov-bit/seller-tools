#!/usr/bin/env bash
# One command: prepare Gumroad uploads + try Reddit post
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Gumroad license uploads ==="
python3 scripts/gumroad_launch.py

echo ""
echo "=== Reddit r/Etsy ==="
python3 scripts/reddit_post.py

echo ""
echo "=== Manual Gumroad (5 min) ==="
echo "Open: gumroad/COPY_PASTE_EVERYTHING.md"
echo "Upload keys from: gumroad/upload/*.txt"