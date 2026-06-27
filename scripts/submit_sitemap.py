#!/usr/bin/env python3
"""Submit sitemap to Google Search Console via API (OAuth device flow)."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

SITE = "https://leopreciadov-bit.github.io/seller-tools/"
SITEMAP = "sitemap.xml"
SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def main() -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Installing Google API client...")
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q",
            "google-api-python-client", "google-auth-oauthlib",
        ])
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

    # Public OAuth client for installed apps (Google's quickstart pattern)
    client_config = {
        "installed": {
            "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
            "client_secret": "d-FL95Q19q7MQmFpd7hHD0Ty",
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_console()
    service = build("searchconsole", "v1", credentials=creds)

    site_enc = urllib.parse.quote(SITE, safe="")
    result = service.sitemaps().submit(siteUrl=SITE, feedpath=SITEMAP).execute()
    print("Submitted to Google Search Console:")
    print(json.dumps(result or {"status": "ok"}, indent=2))


if __name__ == "__main__":
    main()