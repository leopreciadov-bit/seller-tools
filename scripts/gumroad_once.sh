#!/usr/bin/env bash
# ONE-TIME Gumroad setup — set username after creating 3 products. Buy buttons go live on site.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Step 1: Prepare license key uploads ==="
python3 scripts/gumroad_launch.py

echo ""
echo "=== Step 2: Create 3 Gumroad products ==="
echo "Open: gumroad/COPY_PASTE_EVERYTHING.md"
echo "For each product upload the matching file from gumroad/upload/"
echo ""
echo "  listinglab-pro      \$19  →  gumroad/upload/listinglab-pro-keys.txt"
echo "  etsy-tag-finder-pro \$14  →  gumroad/upload/etsy-tag-finder-pro-keys.txt"
echo "  seller-kit-bundle   \$29  →  gumroad/upload/seller-kit-bundle-keys.txt"
echo ""

read -r -p "Your Gumroad username (from yourstore.gumroad.com): " USERNAME
if [[ -n "${USERNAME}" ]]; then
  python3 scripts/gumroad_setup.py set-username "$USERNAME"
  echo ""
  echo "✓ Buy buttons live on site. Deploy with: ./scripts/deploy_github_pages.sh"
fi

if [[ -z "${GUMROAD_ACCESS_TOKEN:-}" ]]; then
  echo ""
  echo "Optional: set GUMROAD_ACCESS_TOKEN or run:"
  echo "  python3 scripts/gumroad_setup.py set-token YOUR_TOKEN"
  echo "Token from: gumroad.com/settings/advanced"
else
  python3 scripts/gumroad_setup.py set-token "$GUMROAD_ACCESS_TOKEN"
fi

echo ""
echo "Done. Reddit: python3 scripts/reddit_post.py (needs Reddit env vars)"