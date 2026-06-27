#!/usr/bin/env bash
# Permanent deploy → GitHub Pages → auto GSC sitemap update
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! gh auth status &>/dev/null; then
  if [[ -n "${GH_TOKEN:-}" ]]; then
    echo "$GH_TOKEN" | gh auth login --with-token
  else
    echo "Run: gh auth login"
    echo "Or:  GH_TOKEN=ghp_xxx ./scripts/deploy_github_pages.sh"
    exit 1
  fi
fi

USER=$(gh api user -q .login)
REPO="${1:-seller-tools}"

echo "Creating/pushing repo: $USER/$REPO"
gh repo view "$USER/$REPO" &>/dev/null || gh repo create "$REPO" --public --source=. --remote=origin
git branch -M main
git push -u origin main --force

echo ""
echo "Enabling GitHub Pages (Actions)..."
gh api "repos/$USER/$REPO/pages" -X POST \
  -f build_type=workflow \
  -f source[branch]=main \
  -f source[path]=/ 2>/dev/null || true

PAGES_URL="https://${USER}.github.io/${REPO}"
echo ""
echo "Pages URL (may take 2-3 min): $PAGES_URL"
echo ""
echo "Updating sitemap for GSC..."
python3 scripts/gsc_setup.py init --url "$PAGES_URL"

echo ""
echo "Done. Next:"
echo "  1. Wait for Actions deploy: https://github.com/$USER/$REPO/actions"
echo "  2. GSC → add property: $PAGES_URL/"
echo "  3. Verify (google5ddb8b4ec852634c.html is already in site/)"
echo "  4. Submit sitemap: sitemap.xml"