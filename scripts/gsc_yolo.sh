#!/usr/bin/env bash
# YOLO GSC prep: pass site URL + google verification file OR token.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage:"
  echo "  $0 --url https://your-site.com --html-file googleabc123.html"
  echo "  $0 --url https://your-site.com --token YOUR_META_TOKEN"
  echo "  $0 --scan   # auto-detect google*.html in site/"
  exit 1
}

URL=""
TOKEN=""
HTML=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url) URL="$2"; shift 2 ;;
    --token) TOKEN="$2"; shift 2 ;;
    --html-file) HTML="$2"; shift 2 ;;
    --scan) URL="__scan__"; shift ;;
    *) usage ;;
  esac
done

if [[ "$URL" == "__scan" ]]; then
  found=$(find site -maxdepth 2 -name 'google*.html' | head -1)
  if [[ -z "$found" ]]; then
    echo "No google*.html found in site/. Download from Search Console and place it in site/"
    exit 1
  fi
  HTML=$(basename "$found")
  echo "Found verification file: $HTML"
  URL="${SITE_URL:-}"
  if [[ -z "$URL" ]]; then
    echo "Set SITE_URL env var, e.g. SITE_URL=https://you.github.io/repo $0 --scan"
    exit 1
  fi
fi

[[ -n "$URL" && "$URL" != "__scan__" ]] || usage

python3 scripts/gsc_setup.py init --url "$URL"

if [[ -n "$HTML" ]]; then
  python3 scripts/gsc_setup.py set-html-file "$HTML"
elif [[ -n "$TOKEN" ]]; then
  python3 scripts/gsc_setup.py set-token "$TOKEN"
else
  echo "Provide --token or --html-file (or --scan with file in site/)"
  exit 1
fi

echo ""
echo "Deploy site/ folder, then Verify in Google Search Console."
echo "Sitemap to submit: ${URL%/}/sitemap.xml"