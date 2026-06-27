#!/usr/bin/env python3
"""
Gumroad signup via temp mail + Playwright.
Creates account, verifies email, saves creds to pipeline/accounts.json.
Product creation still requires logged-in browser session (run with --products).
"""

from __future__ import annotations

import argparse
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
VENV_PYTHON = "/tmp/seller-venv/bin/python"

PRODUCTS = [
    {
        "slug": "listinglab-pro",
        "name": "ListingLab Pro — Unlimited Listing Generator",
        "price": "19",
        "description": """Stop spending an hour per Etsy listing.

ListingLab turns your product basics into a complete, SEO-ready listing in seconds:

✓ Platform-optimized title (Etsy 140-char aware)
✓ Full product description
✓ 13 Etsy tags / 10 Shopify SEO tags
✓ Bullet points — copy-paste ready

FREE TOOL: https://leopreciadov-bit.github.io/seller-tools/listing-lab/

PRO: Unlimited generations. License key delivered instantly.

HOW TO UNLOCK:
1. Open the free tool link
2. Scroll to "Unlock Pro"
3. Paste your license key""",
        "keys": ROOT / "gumroad/upload/listinglab-pro-keys.txt",
        "delivery": ROOT / "gumroad/upload/listinglab-pro-delivery-email.txt",
    },
    {
        "slug": "etsy-tag-finder-pro",
        "name": "Etsy Tag Finder Pro — 13 Perfect SEO Tags",
        "price": "14",
        "description": """Etsy's 13-tag / 20-character limit is brutal. This tool nails it.

✓ Exactly 13 tags, max 20 chars each
✓ Long-tail SEO, no duplicates
✓ Character count per tag

FREE: https://leopreciadov-bit.github.io/seller-tools/etsy-tag-finder/

Paste license key in Unlock Pro.""",
        "keys": ROOT / "gumroad/upload/etsy-tag-finder-pro-keys.txt",
        "delivery": ROOT / "gumroad/upload/etsy-tag-finder-pro-delivery-email.txt",
    },
    {
        "slug": "seller-kit-bundle",
        "name": "Seller Kit — ListingLab + Tag Finder Pro",
        "price": "29",
        "description": """Both Pro tools. One payment. Lifetime.

• ListingLab Pro — full listings
• Etsy Tag Finder Pro — 13 perfect tags

FREE: https://leopreciadov-bit.github.io/seller-tools/

ONE SELLERKIT KEY UNLOCKS BOTH TOOLS.""",
        "keys": ROOT / "gumroad/upload/seller-kit-bundle-keys.txt",
        "delivery": ROOT / "gumroad/upload/seller-kit-bundle-delivery-email.txt",
    },
]


def random_password() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits + "!@#$", k=18))


def save_account(data: dict) -> None:
    existing = []
    if ACCOUNTS.exists():
        existing = json.loads(ACCOUNTS.read_text())
    existing.append(data)
    ACCOUNTS.write_text(json.dumps(existing, indent=2) + "\n")


def signup_gumroad(headless: bool = True, manual_captcha: bool = False) -> dict:
    from playwright.sync_api import sync_playwright

    inbox = create_inbox("sellertools")
    password = random_password()
    print(f"Temp mail ({inbox.provider}): {inbox.address}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto("https://gumroad.com/signup", wait_until="networkidle", timeout=60000)

        # Gumroad signup form fields
        page.locator('input[type="email"]').first.fill(inbox.address)
        page.locator('input[type="password"]').first.fill(password)

        if manual_captcha:
            print("\n>>> Browser open. Solve reCAPTCHA, click 'Create account', then press ENTER here <<<")
            page.locator('button[type="submit"]:has-text("Create account")').click()
            input()
        else:
            page.locator('button[type="submit"]:has-text("Create account")').click()
            page.wait_for_timeout(5000)
            if "recaptcha" in page.content().lower() or page.url.endswith("/signup"):
                page.screenshot(path=str(ROOT / "pipeline/gumroad-captcha.png"))
                browser.close()
                raise RuntimeError(
                    "reCAPTCHA blocked signup. Re-run: python3 scripts/gumroad_autopilot.py --signup --manual"
                )

        print("Waiting for verification email...")
        link = wait_for_link(inbox, sender_contains="", timeout=180)
        if not link:
            page.screenshot(path=str(ROOT / "pipeline/gumroad-signup-fail.png"))
            browser.close()
            raise RuntimeError("No verification email received. Check pipeline/gumroad-signup-fail.png")

        print(f"Verification link: {link[:80]}...")
        page.goto(link, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        username = None
        url = page.url
        # Try to read username from dashboard/profile
        if "gumroad.com" in url:
            page.goto("https://gumroad.com/settings", wait_until="networkidle", timeout=30000)
            for sel in ['input[name="username"]', '#username', '[data-testid="username"]']:
                loc = page.locator(sel)
                if loc.count():
                    username = loc.first.input_value() or None
                    break

        browser.close()

    account = {
        "service": "gumroad",
        "email": inbox.address,
        "password": password,
        "inbox_password": inbox.password,
        "username": username,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_account(account)
    print(f"Saved to {ACCOUNTS}")
    return account


def create_products(account: dict, headless: bool = True) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        # Login
        page.goto("https://gumroad.com/login", wait_until="networkidle")
        page.fill('input[type="email"], #email', account["email"])
        page.fill('input[type="password"], #password', account["password"])
        page.click('button[type="submit"], button:has-text("Log in")')
        page.wait_for_timeout(4000)

        for prod in PRODUCTS:
            print(f"Creating: {prod['name']}")
            page.goto("https://gumroad.com/products/new", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            # Fill product form — Gumroad UI varies; try common selectors
            for sel in ['input[name="name"]', '#name', 'input[placeholder*="Name"]']:
                if page.locator(sel).count():
                    page.fill(sel, prod["name"])
                    break

            for sel in ['textarea[name="description"]', '#description', 'textarea']:
                if page.locator(sel).count():
                    page.fill(sel, prod["description"])
                    break

            for sel in ['input[name="price"]', '#price', 'input[placeholder*="Price"]']:
                if page.locator(sel).count():
                    page.fill(sel, prod["price"])
                    break

            for sel in ['input[name="url"]', '#url', 'input[placeholder*="URL"]']:
                if page.locator(sel).count():
                    page.fill(sel, prod["slug"])
                    break

            page.click('button:has-text("Save"), button:has-text("Publish"), button[type="submit"]')
            page.wait_for_timeout(3000)

            # License keys upload — navigate to content tab if needed
            keys_path = str(prod["keys"])
            if page.locator('input[type="file"]').count():
                page.set_input_files('input[type="file"]', keys_path)

            page.wait_for_timeout(2000)
            print(f"  → created (verify in Gumroad dashboard)")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signup", action="store_true", help="Create Gumroad account via temp mail")
    parser.add_argument("--products", action="store_true", help="Create 3 products (needs existing account)")
    parser.add_argument("--headed", action="store_true", help="Show browser (debug)")
    parser.add_argument("--manual", action="store_true", help="Pause for manual CAPTCHA solve")
    args = parser.parse_args()

    headless = not (args.headed or args.manual)

    if args.signup:
        acct = signup_gumroad(headless=headless, manual_captcha=args.manual)
        if acct.get("username"):
            import subprocess
            subprocess.run([sys.executable, str(ROOT / "scripts/gumroad_setup.py"), "set-username", acct["username"]], check=False)
        return

    if args.products:
        if not ACCOUNTS.exists():
            print("No accounts.json — run with --signup first")
            sys.exit(1)
        accounts = json.loads(ACCOUNTS.read_text())
        gumroad = next((a for a in reversed(accounts) if a["service"] == "gumroad"), None)
        if not gumroad:
            print("No gumroad account found")
            sys.exit(1)
        create_products(gumroad, headless=headless)
        return

    parser.print_help()


if __name__ == "__main__":
    main()