#!/usr/bin/env python3
"""Get Transak partner API key for embedded card → USDC widget."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from tempmail import create_inbox, wait_for_link  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"


def main() -> None:
    from playwright.sync_api import sync_playwright

    accounts = json.loads(ACCOUNTS.read_text())
    acct = next((a for a in reversed(accounts) if a["service"] == "transak"), None)
    if not acct:
        print("No transak account")
        return

    inbox = create_inbox("transak", provider="mail.tm")
    # use stored inbox creds from account
    from tempmail import Inbox, _req  # noqa: E402
    token_data = _req("POST", "https://api.mail.tm/token", {
        "address": acct["email"], "password": acct["inbox_password"],
    })
    inbox = Inbox(acct["email"], acct["inbox_password"], token_data["token"], "mail.tm")

    api_key = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://dashboard.transak.com/login", timeout=60000)
        page.wait_for_timeout(2000)
        if page.locator('input[type="email"]').count():
            page.locator('input[type="email"]').first.fill(acct["email"])
            page.locator('button[type="submit"], button:has-text("Continue")').first.click()
            page.wait_for_timeout(3000)
        link = wait_for_link(inbox, timeout=90)
        if link:
            page.goto(link, timeout=60000)
            page.wait_for_timeout(5000)
        for path in ["/developers", "/partner/setting", "/"]:
            page.goto(f"https://dashboard.transak.com{path}", timeout=60000)
            page.wait_for_timeout(3000)
            m = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page.content())
            if m:
                api_key = m.group(1)
                break
        page.screenshot(path=str(ROOT / "pipeline/transak-dashboard.png"))
        browser.close()

    if api_key:
        print("Transak API key found")
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "set-card", "--transak", api_key], cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT)
        subprocess.run(["git", "add", "pipeline/crypto.json", "site/assets/"], cwd=ROOT, check=False)
        subprocess.run(["git", "commit", "-m", "Transak card widget live"], cwd=ROOT, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)
        print("Card widget LIVE via Transak")
    else:
        print("No API key — see pipeline/transak-dashboard.png")


if __name__ == "__main__":
    main()