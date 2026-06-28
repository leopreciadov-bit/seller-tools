#!/usr/bin/env python3
"""
Passive income autopilot — temp mail signups + config + deploy.
Run: /tmp/seller-venv/bin/python scripts/passive_income_autopilot.py
"""

from __future__ import annotations

import json
import random
import re
import string
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import create_inbox, wait_for_code, wait_for_link  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"
CRYPTO = ROOT / "pipeline/crypto.json"
STATE = ROOT / "pipeline/autopilot-state.json"
PAYOUT = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
SITE = "https://leopreciadov-bit.github.io/seller-tools"
VENV_PY = "/tmp/seller-venv/bin/python"


def log(msg: str) -> None:
    print(f"[autopilot] {msg}")


def save_state(data: dict) -> None:
    STATE.write_text(json.dumps(data, indent=2) + "\n")


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {}


def save_account(entry: dict) -> None:
    rows = json.loads(ACCOUNTS.read_text()) if ACCOUNTS.exists() else []
    rows.append(entry)
    ACCOUNTS.write_text(json.dumps(rows, indent=2) + "\n")


def run(cmd: list[str], **kw) -> int:
    log(" ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, **kw).returncode


def helio_signup() -> dict | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("Install: python3 -m venv /tmp/seller-venv && pip install playwright && playwright install chromium")
        return None

    inbox = None
    for attempt in range(5):
        try:
            inbox = create_inbox("seller")
            break
        except Exception as e:
            log(f"temp mail attempt {attempt + 1} failed: {e}")
            time.sleep(15 * (attempt + 1))
    if not inbox:
        return None

    log(f"Helio signup email: {inbox.address} ({inbox.provider})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://moonpay.hel.io/", wait_until="networkidle", timeout=60000)

        email_loc = page.locator('input[type="email"], input[placeholder*="email" i]')
        if not email_loc.count():
            page.goto("https://moonpay.hel.io/login", wait_until="networkidle", timeout=60000)
        email_loc.first.fill(inbox.address)
        clicked = False
        for sel in [
            'button:has-text("Continue")',
            'button:has-text("Sign up")',
            'button:has-text("Get started")',
            'button[type="submit"]',
        ]:
            if page.locator(sel).count():
                page.locator(sel).first.click()
                clicked = True
                break
        if not clicked:
            page.keyboard.press("Enter")

        page.wait_for_timeout(8000)
        page.screenshot(path=str(ROOT / "pipeline/helio-after-email.png"))

        code = wait_for_code(inbox, timeout=180)
        if code:
            log(f"Verification code received: {code}")
            for sel in [
                'input[placeholder*="6-digit" i]',
                'input[placeholder*="code" i]',
                'input[type="text"]',
                'input[inputmode="numeric"]',
            ]:
                if page.locator(sel).count():
                    page.locator(sel).first.fill(code)
                    break
            for sel in ['button:has-text("Verify")', 'button[type="submit"]']:
                if page.locator(sel).count():
                    page.locator(sel).first.click()
                    break
            page.wait_for_timeout(8000)
            page.screenshot(path=str(ROOT / "pipeline/helio-dashboard.png"))
        else:
            link = wait_for_link(inbox, timeout=30)
            if link:
                log(f"Magic link: {link[:80]}...")
                page.goto(link, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(5000)

        url = page.url
        content = page.content()
        browser.close()

    paylink_id = ""
    m = re.search(r'"paylinkId"\s*:\s*"([a-f0-9]{24})"', content)
    if m:
        paylink_id = m.group(1)

    entry = {
        "service": "helio",
        "email": inbox.address,
        "inbox_password": inbox.password,
        "provider": inbox.provider,
        "url": url,
        "paylink_id": paylink_id or None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_account(entry)

    if paylink_id:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/crypto_setup.py"), "set-card", "--helio", paylink_id],
            cwd=ROOT,
            check=False,
        )
    return entry


def reddit_post() -> bool:
    title = "I built two free tools for Etsy sellers (listing generator + 13-tag SEO helper)"
    body = f"""I got tired of spending 45+ minutes per listing, so I built two browser tools:

1. ListingLab — full Etsy/Shopify listing from product basics
2. Etsy Tag Finder — exactly 13 tags, 20 char limit enforced

Both free with daily limits. No signup.

{SITE}/

Feedback welcome — what would make these useful for your shop?"""

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    inbox = create_inbox("reddit")
    password = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    username = "sellertools" + "".join(random.choices(string.digits, k=4))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.reddit.com/register/", wait_until="networkidle", timeout=60000)

        for sel, val in [
            ('input[name="email"]', inbox.address),
            ('input[name="username"]', username),
            ('input[name="password"]', password),
        ]:
            if page.locator(sel).count():
                page.fill(sel, val)

        if page.locator('button[type="submit"]').count():
            page.click('button[type="submit"]')
        page.wait_for_timeout(5000)

        if "captcha" in page.content().lower() or page.url.endswith("/register/"):
            page.screenshot(path=str(ROOT / "pipeline/reddit-captcha.png"))
            browser.close()
            log("Reddit blocked by CAPTCHA — saved pipeline/reddit-captcha.png")
            return False

        vlink = wait_for_link(inbox, timeout=120)
        if vlink:
            page.goto(vlink, wait_until="networkidle")

        page.goto("https://www.reddit.com/r/Etsy/submit", wait_until="networkidle", timeout=60000)
        if page.locator('textarea[name="title"]').count():
            page.fill('textarea[name="title"]', title)
        if page.locator('textarea[name="body"]').count():
            page.fill('textarea[name="body"]', body)
        page.click('button:has-text("Post")')
        page.wait_for_timeout(5000)
        ok = "captcha" not in page.content().lower()
        browser.close()

    if ok:
        save_account({
            "service": "reddit",
            "username": username,
            "email": inbox.address,
            "password": password,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    return ok


def health_and_index() -> None:
    run([sys.executable, str(ROOT / "scripts/resubmit_indexnow.py")])
    for path in ("", "/listing-lab/", "/etsy-tag-finder/"):
        url = SITE + path
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                log(f"HTTP {r.status} {url}")
        except Exception as e:
            log(f"FAIL {url}: {e}")


def deploy() -> None:
    run(["git", "add", "-A", "--", ".", ":!.venv"])
    run(["git", "diff", "--cached", "--quiet"], check=False)
    subprocess.run(
        ["git", "commit", "-m", "Autopilot: passive income state update"],
        cwd=ROOT,
        capture_output=True,
    )
    run(["git", "push", "origin", "main"])


def main() -> None:
    state = load_state()
    log("=== Passive income autopilot ===")
    log(f"Payout wallet: {PAYOUT}")

    run([sys.executable, str(ROOT / "scripts/crypto_setup.py"), "build"])
    run([sys.executable, str(ROOT / "scripts/gumroad_launch.py")])

    if not state.get("helio_attempted"):
        entry = helio_signup()
        state["helio_attempted"] = True
        state["helio"] = entry
        if entry and entry.get("paylink_id"):
            state["card_live"] = True
            log(f"Card payments LIVE — paylink {entry['paylink_id']}")
        else:
            log("Helio needs manual wallet connect at moonpay.hel.io (email saved in accounts.json)")
    else:
        log("Helio already attempted — skip")

    if not state.get("reddit_attempted"):
        state["reddit_attempted"] = True
        try:
            state["reddit_posted"] = reddit_post()
        except Exception as e:
            log(f"Reddit failed: {e}")
            state["reddit_posted"] = False
    else:
        log("Reddit already attempted — skip")

    run([sys.executable, str(ROOT / "scripts/promote_autopilot.py")], check=False)
    run([sys.executable, str(ROOT / "scripts/advertise_other.py")], check=False)
    run([sys.executable, str(ROOT / "scripts/reddit_publish.py")], check=False)
    state["promote_attempted"] = True

    health_and_index()
    deploy()
    save_state(state)

    log("=== Done ===")
    log(f"Site: {SITE}")
    log(f"Accounts: {ACCOUNTS}")
    log(f"State: {STATE}")
    if not state.get("card_live"):
        log("NEXT: open accounts.json email → moonpay.hel.io → connect wallet → create dynamic paylink → set-card --helio ID")


if __name__ == "__main__":
    main()