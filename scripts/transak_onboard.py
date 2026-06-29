#!/usr/bin/env python3
"""Get Transak partner API key for embedded card → USDC widget."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from tempmail import login_inbox, wait_for_link  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"
CRYPTO = ROOT / "pipeline" / "crypto.json"
PAYOUT = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"


def main() -> None:
    from playwright.sync_api import sync_playwright

    accounts = json.loads(ACCOUNTS.read_text())
    acct = next((a for a in reversed(accounts) if a["service"] == "transak"), None)
    if not acct:
        print("No transak account")
        return

    inbox = login_inbox(acct["email"], acct["inbox_password"])
    api_key = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://dashboard.transak.com/login", timeout=60000)
        page.wait_for_timeout(2000)
        if page.locator('input[type="email"]').count():
            page.fill('input[type="email"]', acct["email"])
            page.click('button[type="submit"], button:has-text("Continue")')
            page.wait_for_timeout(3000)
        link = wait_for_link(inbox, timeout=90)
        if link:
            page.goto(link, timeout=60000)
            page.wait_for_timeout(5000)
        page.goto("https://dashboard.transak.com/developers", timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(ROOT / "pipeline/transak-dashboard.png"))
        content = page.content()
        m = re.search(r'apiKey["\s:]+([a-f0-9-]{36})', content, re.I)
        if m:
            api_key = m.group(1)
        # try copy from page text
        if not api_key:
            for pat in [r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})']:
                m2 = re.search(pat, content)
                if m2:
                    api_key = m2.group(1)
                    break
        browser.close()

    if api_key:
        print("Transak API key:", api_key[:8] + "...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "set-card", "--transak", api_key], cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT)
        subprocess.run(["git", "add", "pipeline/crypto.json", "site/assets/crypto.js"], cwd=ROOT, check=False)
        subprocess.run(["git", "commit", "-m", "Transak card widget live"], cwd=ROOT, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)
        print("Card widget LIVE via Transak")
    else:
        print("No API key found — screenshot: pipeline/transak-dashboard.png")


if __name__ == "__main__":
    main()