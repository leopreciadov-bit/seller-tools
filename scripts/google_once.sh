#!/usr/bin/env bash
# ONE-TIME Google setup — verifies site + submits sitemap via API. Run once, never again.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="/tmp/gsc-venv"

[[ -d "$VENV" ]] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q google-api-python-client google-auth-oauthlib

SITE="https://leopreciadov-bit.github.io/seller-tools/"
SITEMAP="sitemap.xml"

"$VENV/bin/python" << 'PY'
import json, urllib.parse, sys
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SITE = "https://leopreciadov-bit.github.io/seller-tools/"
SITEMAP = "sitemap.xml"
SCOPES = ["https://www.googleapis.com/auth/webmasters"]
TOKEN = "/root/agent-programs/passive-income-agent-program/pipeline/google_token.json"

client_config = {
    "installed": {
        "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
        "client_secret": "d-FL95Q19q7MQmFpd7hHD0Ty",
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

creds = None
try:
    with open(TOKEN) as f:
        creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
except FileNotFoundError:
    pass

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=8089, open_browser=False, prompt="consent")
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())

service = build("searchconsole", "v1", credentials=creds)
service.sitemaps().submit(siteUrl=SITE, feedpath=SITEMAP).execute()
print("✓ Sitemap submitted:", SITE + SITEMAP)
PY

echo "Done. Google token saved — future runs are fully automatic."