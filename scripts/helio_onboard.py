#!/usr/bin/env python3
"""Complete Helio merchant onboarding + create dynamic paylink."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import _create_mailtm, _req, wait_for_code  # noqa: E402
from dataclasses import dataclass

ACCOUNTS = ROOT / "pipeline/accounts.json"
PAYOUT = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
SITE = "https://leopreciadov-bit.github.io/seller-tools"


@dataclass
class Inbox:
    address: str
    password: str
    token: str
    provider: str = "mail.tm"


def login_inbox(address: str, password: str) -> Inbox:
    token_data = _req("POST", "https://api.mail.tm/token", {"address": address, "password": password})
    return Inbox(address=address, password=password, token=token_data["token"])


def helio_login(page, inbox: Inbox) -> bool:
    page.goto("https://moonpay.hel.io/", wait_until="networkidle", timeout=60000)
    page.locator('input[type="email"]').first.fill(inbox.address)
    for sel in ['button:has-text("Continue")', 'button[type="submit"]']:
        if page.locator(sel).count():
            page.locator(sel).first.click()
            break
    page.wait_for_timeout(5000)
    if "Complete Profile" in page.content() or "Create Payment" in page.content():
        print("Already logged in")
        return True
    if page.locator('text=Resend email').count():
        page.locator('text=Resend email').first.click()
        page.wait_for_timeout(3000)
    code = wait_for_code(inbox, timeout=120)
    if not code:
        print("No verification code")
        return False
    print("Code:", code)
    for sel in ['input[placeholder*="6-digit" i]', 'input[placeholder*="code" i]', 'input[inputmode="numeric"]']:
        if page.locator(sel).count():
            page.locator(sel).first.fill(code)
            break
    for sel in ['button:has-text("Verify")', 'button:has-text("Continue")', 'button[type="submit"]']:
        if page.locator(sel).count():
            page.locator(sel).first.click()
            break
    page.wait_for_timeout(8000)
    return True


def fill_if_empty(page, label: str, value: str) -> None:
    for sel in [f'input[placeholder*="{label}" i]', f'input:near(:text("{label}"))']:
        loc = page.locator(sel)
        if loc.count():
            if not loc.first.input_value():
                loc.first.fill(value)
            return


def main() -> None:
    from playwright.sync_api import sync_playwright

    accounts = json.loads(ACCOUNTS.read_text())
    helio = next((a for a in reversed(accounts) if a["service"] == "helio"), None)
    if not helio:
        print("No helio account in accounts.json")
        sys.exit(1)

    inbox = login_inbox(helio["email"], helio["inbox_password"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if not helio_login(page, inbox):
            browser.close()
            sys.exit(1)

        # Step 1: profile
        for sel, val in [
            ('input:near(:text("Company name"))', "Seller Tools"),
            ('input:near(:text("Company website"))', SITE),
            ('input:near(:text("Company email"))', helio["email"]),
        ]:
            if page.locator(sel).count():
                page.locator(sel).first.fill(val)

        for _ in range(4):
            if page.locator('button:has-text("NEXT")').count():
                page.locator('button:has-text("NEXT")').first.click()
                page.wait_for_timeout(3000)
            elif page.locator('button:has-text("Next")').count():
                page.locator('button:has-text("Next")').first.click()
                page.wait_for_timeout(3000)

        # Try create payment
        if page.locator('button:has-text("Create Payment")').count():
            page.locator('button:has-text("Create Payment")').first.click()
            page.wait_for_timeout(3000)

        page.screenshot(path=str(ROOT / "pipeline/helio-onboard-final.png"))
        content = page.content()
        paylink = re.search(r'"paylinkId"\s*:\s*"([a-f0-9]{24})"', content)
        browser.close()

    if paylink:
        pid = paylink.group(1)
        print("Paylink:", pid)
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "set-card", "--helio", pid], check=False)
    else:
        print("Profile progressed — connect wallet in Phantom for payout:", PAYOUT)
        print("Screenshot: pipeline/helio-onboard-final.png")


if __name__ == "__main__":
    main()