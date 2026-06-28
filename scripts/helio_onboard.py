#!/usr/bin/env python3
"""Complete Helio merchant onboarding + create dynamic paylink."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import _req, list_messages, read_message, wait_for_link  # noqa: E402
from dataclasses import dataclass

ACCOUNTS = ROOT / "pipeline/accounts.json"
STATE = ROOT / "pipeline/helio-session.json"
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


def click_first(page, selectors: list[str]) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            loc.first.click()
            return True
    return False


def fill_code(page, code: str) -> None:
    digits = page.locator('input[inputmode="numeric"], input[maxlength="1"]')
    if digits.count() >= 6:
        for i, ch in enumerate(code[:6]):
            digits.nth(i).fill(ch)
        return
    for sel in [
        'input[placeholder*="6-digit" i]',
        'input[placeholder*="code" i]',
        'input[autocomplete="one-time-code"]',
        'input[inputmode="numeric"]',
    ]:
        loc = page.locator(sel)
        if loc.count():
            loc.first.fill(code)
            return


def logged_in(page) -> bool:
    text = page.content()
    markers = ("Complete Profile", "Create Payment", "Get started", "Verify Profile", "Dashboard")
    return any(m in text for m in markers)


def fresh_code(inbox: Inbox, seen: set[str], timeout: int = 90) -> str | None:
    deadline = time.time() + timeout
    pattern = re.compile(r"\b(\d{6})\b")
    while time.time() < deadline:
        for msg in list_messages(inbox):
            mid = msg.get("id", "")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            full = read_message(inbox, mid)
            text = full.get("text") or ""
            html_body = full.get("html") or ""
            if isinstance(text, list):
                text = " ".join(str(x) for x in text)
            if isinstance(html_body, list):
                html_body = " ".join(str(x) for x in html_body)
            body = str(text) + str(html_body)
            m = pattern.search(body)
            if m:
                return m.group(1)
        time.sleep(3)
    return None


def helio_login(page, inbox: Inbox) -> bool:
    page.goto("https://moonpay.hel.io/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    if logged_in(page):
        print("Already logged in")
        return True

    seen = {m.get("id", "") for m in list_messages(inbox)}
    email = page.locator('input[type="email"], input[placeholder*="email" i]')
    if email.count():
        email.first.fill(inbox.address)
        email.first.press("Enter")
        page.wait_for_timeout(3000)

    if logged_in(page):
        return True

    if page.locator('text=Resend email').count():
        page.locator('text=Resend email').first.click()
        page.wait_for_timeout(3000)

    code = fresh_code(inbox, seen, timeout=90)
    if code:
        print("Code:", code)
        fill_code(page, code)
        click_first(page, ['button:has-text("Verify")', 'button[type="submit"]'])
        for _ in range(12):
            page.wait_for_timeout(2000)
            if logged_in(page):
                print("Logged in via code")
                return True
    else:
        link = wait_for_link(inbox, sender_contains="hel", timeout=60)
        if not link:
            link = wait_for_link(inbox, timeout=30)
        if link:
            print("Magic link:", link[:80])
            page.goto(link, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            if logged_in(page):
                return True

    print("Login failed — url:", page.url)
    page.screenshot(path=str(ROOT / "pipeline/helio-login-fail.png"))
    return False


def complete_profile(page, email: str) -> str:
    """Returns onboarding status: profile | kyc_required | ready."""
    body = page.inner_text("body")
    if "Complete Profile" in body:
        website = page.locator('input').nth(1)
        if website.count():
            val = website.input_value()
            if not val or "commerce.moonpay.com" in val:
                website.fill(SITE)
        click_first(page, ['button:has-text("Next")', 'button:has-text("NEXT")'])
        page.wait_for_timeout(3000)

    body = page.inner_text("body")
    if "Verify Profile" in body or "Account not verified" in body:
        if page.locator('button:has-text("Business")').count():
            page.locator('button:has-text("Business")').first.click()
            page.wait_for_timeout(2000)
        return "kyc_required"

    btn = page.locator('[data-testid="@dashboard/create-payment-button"]')
    if btn.count() and btn.is_enabled():
        return "ready"
    return "kyc_required"


def create_dynamic_paylink(page) -> str | None:
    btn = page.locator('[data-testid="@dashboard/create-payment-button"]')
    if not btn.count() or not btn.is_enabled():
        return None
    btn.first.click()
    page.wait_for_timeout(4000)

    click_first(page, ['button:has-text("Pay Link")', 'text=Pay Link'])
    page.wait_for_timeout(1500)

    name_loc = page.locator('input[placeholder*="name" i], input:near(:text("Name"))')
    if name_loc.count():
        name_loc.first.fill("Seller Tools Dynamic")

    for sel in ['text=Dynamic', 'label:has-text("Dynamic")']:
        loc = page.locator(sel)
        if loc.count():
            loc.first.click()
            page.wait_for_timeout(500)

    for sel in ['text=Card', 'label:has-text("Card")']:
        loc = page.locator(sel)
        if loc.count():
            loc.first.click()
            page.wait_for_timeout(500)

    click_first(page, ['button:has-text("Create")', 'button:has-text("Publish")', 'button:has-text("Save")'])
    page.wait_for_timeout(5000)

    content = page.content()
    m = re.search(r'"paylinkId"\s*:\s*"([a-f0-9]{24})"', content)
    if m:
        return m.group(1)
    m = re.search(r"/pay/([a-f0-9]{24})", page.url)
    if m:
        return m.group(1)
    return None


def save_session(context) -> None:
    cookies = context.cookies()
    STATE.write_text(json.dumps({"cookies": cookies}, indent=2))


def load_session(context) -> bool:
    if not STATE.exists():
        return False
    data = json.loads(STATE.read_text())
    if data.get("cookies"):
        context.add_cookies(data["cookies"])
        return True
    return False


def main() -> None:
    from playwright.sync_api import sync_playwright

    accounts = json.loads(ACCOUNTS.read_text())
    helio = next((a for a in reversed(accounts) if a["service"] == "helio"), None)
    if not helio:
        print("No helio account in accounts.json")
        sys.exit(1)

    inbox = login_inbox(helio["email"], helio["inbox_password"])
    paylink_id = None
    status = "unknown"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        load_session(context)
        page = context.new_page()

        if not helio_login(page, inbox):
            browser.close()
            sys.exit(1)

        save_session(context)
        page.screenshot(path=str(ROOT / "pipeline/helio-logged-in.png"))
        print("URL after login:", page.url)

        status = complete_profile(page, helio["email"])
        page.screenshot(path=str(ROOT / "pipeline/helio-onboard-final.png"))

        if status == "ready":
            paylink_id = create_dynamic_paylink(page)
            page.screenshot(path=str(ROOT / "pipeline/helio-paylink.png"))

        save_session(context)
        browser.close()

    helio["onboarding_status"] = status
    helio["embedded_wallet"] = "Hta5JM...ChccCw"
    helio["phantom_payout"] = PAYOUT
    if paylink_id:
        helio["paylink_id"] = paylink_id
    accounts = [a if a.get("email") != helio["email"] else helio for a in accounts]
    ACCOUNTS.write_text(json.dumps(accounts, indent=2) + "\n")

    if paylink_id:
        print("Paylink:", paylink_id)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/crypto_setup.py"), "set-card", "--helio", paylink_id],
            cwd=ROOT,
            check=False,
        )
        subprocess.run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT, check=False)
        print("Card checkout configured — deploy to go live")
    elif status == "kyc_required":
        print("BLOCKED: Helio requires identity verification (2 min in browser)")
        print("Login:", helio["email"], "| Inbox pass:", helio["inbox_password"])
        print("Steps: moonpay.hel.io → Business → Verify → Create Payment → Dynamic USDC paylink")
        print("Then: python3 scripts/crypto_setup.py set-card --helio YOUR_ID && git push")
    else:
        print("Screenshot: pipeline/helio-onboard-final.png")


if __name__ == "__main__":
    main()