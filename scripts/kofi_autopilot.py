#!/usr/bin/env python3
"""Ko-fi shop signup — card payments without Gumroad."""

from __future__ import annotations

import json
import random
import string
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from tempmail import create_inbox, wait_for_link  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"
SITE = "https://leopreciadov-bit.github.io/seller-tools"


def main() -> None:
    from playwright.sync_api import sync_playwright

    inbox = create_inbox("kofi")
    password = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    print(f"Email: {inbox.address}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://ko-fi.com/account/register", timeout=60000)
        page.wait_for_timeout(2000)
        if page.locator('input[name="email"]').count():
            page.fill('input[name="email"]', inbox.address)
        if page.locator('input[name="password"]').count():
            page.fill('input[name="password"]', password)
        if page.locator('button[type="submit"]').count():
            page.locator('button[type="submit"]').first.click()
            page.wait_for_timeout(5000)
        link = wait_for_link(inbox, timeout=120)
        if link:
            page.goto(link, timeout=60000)
            print(f"Verified: {page.url}")
        page.screenshot(path=str(ROOT / "pipeline/kofi-signup.png"))
        browser.close()

    acct = {
        "service": "kofi",
        "email": inbox.address,
        "password": password,
        "inbox_password": inbox.password,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    existing = json.loads(ACCOUNTS.read_text()) if ACCOUNTS.exists() else []
    existing.append(acct)
    ACCOUNTS.write_text(json.dumps(existing, indent=2) + "\n")
    print("Saved kofi account — create shop items manually at ko-fi.com/manage/shop")


if __name__ == "__main__":
    main()