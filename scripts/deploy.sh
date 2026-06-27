#!/usr/bin/env bash
# One-command deploy options. Pick one after setting credentials once.
set -euo pipefail
SITE="$(cd "$(dirname "$0")/.." && pwd)/site"
cd "$SITE"

echo "Deploying from: $SITE"
echo ""
echo "Option A — Cloudflare Pages (recommended, free):"
echo "  npx wrangler pages deploy . --project-name=passive-income-tools"
echo "  (requires: npx wrangler login)"
echo ""
echo "Option B — Vercel:"
echo "  npx vercel deploy --prod"
echo "  (requires: npx vercel login)"
echo ""
echo "Option C — Surge:"
echo "  npx surge . passive-income-tools.surge.sh"
echo ""
echo "Option D — GitHub Pages: push repo, workflow auto-deploys"
echo ""

if command -v wrangler &>/dev/null && [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  wrangler pages deploy . --project-name=passive-income-tools
elif command -v vercel &>/dev/null && [[ -n "${VERCEL_TOKEN:-}" ]]; then
  vercel deploy --prod --yes
else
  echo "No deploy credentials detected. Run one of the login commands above."
  exit 1
fi