#!/usr/bin/env python3
"""Fully automated card checkout — Payhip, Ko-fi, Polar, itch.io."""

from __future__ import annotations

import json
import random
import re
import string
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import create_inbox, wait_for_link  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"
CARD_CFG = ROOT / "pipeline" / "card-providers.json"
GUMROAD_CFG = ROOT / "pipeline" / "gumroad.json"
CRYPTO_CFG = ROOT / "pipeline" / "crypto.json"
SITE = "https://leopreciadov-bit.github.io/seller-tools"
PY = "/tmp/seller-venv/bin/python" if Path("/tmp/seller-venv/bin/python").exists() else sys.executable

PRODUCTS = [
    {"slug": "etsy-tag-finder-pro", "name": "Etsy Tag Finder Pro", "price": "14", "keys": "etsy-tag-finder-pro-keys.txt"},
    {"slug": "listinglab-pro", "name": "ListingLab Pro", "price": "19", "keys": "listinglab-pro-keys.txt"},
    {"slug": "seller-kit-bundle", "name": "Seller Kit Bundle", "price": "29", "keys": "seller-kit-bundle-keys.txt"},
]


def log(msg: str) -> None:
    print(f"[card] {msg}", flush=True)


def load_accounts() -> list:
    return json.loads(ACCOUNTS.read_text()) if ACCOUNTS.exists() else []


def save_accounts(accounts: list) -> None:
    ACCOUNTS.write_text(json.dumps(accounts, indent=2) + "\n")


def get_account(service: str) -> dict | None:
    for a in reversed(load_accounts()):
        if a.get("service") == service and a.get("password"):
            return a
    return None


def dismiss_overlays(page) -> None:
    for sel in [
        'button:has-text("Accept")', 'button:has-text("Got it")', 'button:has-text("OK")',
        '[aria-label="Close"]', '.cookie-accept', '#onetrust-accept-btn-handler',
    ]:
        try:
            if page.locator(sel).count():
                page.locator(sel).first.click(timeout=2000)
                page.wait_for_timeout(500)
        except Exception:
            pass


def fill_visible(page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    el.fill(value)
                    return True
            except Exception:
                continue
    return False


def click_visible(page, selectors: list[str]) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    el.click()
                    return True
            except Exception:
                continue
    return False


def wire_checkout(providers: dict) -> None:
    gum = {"username": None, "products": {}}
    prices = {"etsy-tag-finder-pro": 14, "listinglab-pro": 19, "seller-kit-bundle": 29}
    for slug, urls in providers.get("products", {}).items():
        url = urls.get("gumroad") or urls.get("payhip") or urls.get("kofi") or urls.get("polar") or urls.get("itch")
        if url:
            gum["products"][slug] = {"title": slug, "price": prices.get(slug, 0), "url": url}
            m = re.search(r"https://([^.]+)\.gumroad\.com", url)
            if m:
                gum["username"] = m.group(1)
    if gum["products"]:
        base = json.loads(GUMROAD_CFG.read_text()) if GUMROAD_CFG.exists() else {}
        base.update(gum)
        GUMROAD_CFG.write_text(json.dumps(base, indent=2) + "\n")
        (ROOT / "site" / "assets" / "gumroad.js").write_text("window.GUMROAD = " + json.dumps(gum, indent=2) + ";\n")

    crypto = json.loads(CRYPTO_CFG.read_text())
    crypto.setdefault("card", {})["enabled"] = True
    crypto["card"]["fallbacks"] = providers.get("products", {})
    crypto["card"]["provider"] = providers.get("primary", "fallback")
    CRYPTO_CFG.write_text(json.dumps(crypto, indent=2) + "\n")
    subprocess.run([PY, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT, check=False)
    log(f"Wired {len(gum['products'])} products to checkout")


def setup_payhip(page, results: dict) -> dict | None:
    log("Payhip...")
    acct = get_account("payhip")
    if not acct:
        inbox = create_inbox("payhip")
        password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        page.goto("https://payhip.com/auth/register", timeout=60000)
        page.wait_for_timeout(2000)
        dismiss_overlays(page)
        fill_visible(page, ['input[placeholder="First name"]', 'input[name="first_name"]'], "Seller")
        fill_visible(page, ['input[placeholder="Last name"]', 'input[name="last_name"]'], "Tools")
        fill_visible(page, ['input[placeholder="Enter your email"]', 'input[type="email"]'], inbox.address)
        fill_visible(page, ['input[placeholder="Choose password"]', 'input[type="password"]'], password)
        click_visible(page, ['button:has-text("Create account")', 'button[type="submit"]'])
        page.wait_for_timeout(5000)
        link = wait_for_link(inbox, timeout=120)
        if link:
            page.goto(link, timeout=60000)
            page.wait_for_timeout(3000)
        acct = {"service": "payhip", "email": inbox.address, "password": password,
                "inbox_password": inbox.password, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        save_accounts(load_accounts() + [acct])
    else:
        page.goto("https://payhip.com/auth/login", timeout=60000)
        page.wait_for_timeout(2000)
        fill_visible(page, ['input[type="email"]'], acct["email"])
        fill_visible(page, ['input[type="password"]'], acct["password"])
        click_visible(page, ['button:has-text("Log in")', 'button[type="submit"]'])
        page.wait_for_timeout(5000)

    page.screenshot(path=str(ROOT / "pipeline/payhip-dashboard.png"))

    for prod in PRODUCTS:
        try:
            page.goto("https://payhip.com/products/new", timeout=60000)
            page.wait_for_timeout(3000)
            fill_visible(page, ['input[name="title"]', '#title', 'input[placeholder*="title" i]'], prod["name"])
            fill_visible(page, ['input[name="price"]', '#price', 'input[placeholder*="price" i]'], prod["price"])
            fill_visible(page, ['textarea'], f"License key on purchase. Unlock at {SITE}/")
            keys = ROOT / "gumroad" / "upload" / prod["keys"]
            if keys.exists():
                try:
                    page.set_input_files('input[type="file"]', str(keys))
                except Exception:
                    pass
            click_visible(page, ['button:has-text("Save")', 'button:has-text("Publish")', 'button:has-text("Create")'])
            page.wait_for_timeout(5000)
            for m in re.finditer(r'(https://payhip\.com/b/[A-Za-z0-9]+)', page.content()):
                results.setdefault("products", {}).setdefault(prod["slug"], {})["payhip"] = m.group(1)
                log(f"  Payhip {prod['slug']}: {m.group(1)}")
        except Exception as e:
            log(f"  Payhip {prod['slug']}: {e}")
    return acct


def setup_kofi(page, account: dict, results: dict) -> None:
    log("Ko-fi...")
    page.goto("https://ko-fi.com/Account/Login", timeout=60000)
    page.wait_for_timeout(3000)
    dismiss_overlays(page)
    click_visible(page, ['a:has-text("Log in")', 'button:has-text("Log in")'])
    page.wait_for_timeout(1000)
    fill_visible(page, ['#Email', 'input[name="Email"]', 'input[type="email"]'], account["email"])
    fill_visible(page, ['#Password', 'input[name="Password"]', 'input[type="password"]'], account["password"])
    click_visible(page, ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log in")'])
    page.wait_for_timeout(6000)
    page.screenshot(path=str(ROOT / "pipeline/kofi-login.png"))

    if "login" in page.url.lower() and "manage" not in page.url.lower():
        log("  Ko-fi login failed")
        return

    for prod in PRODUCTS:
        try:
            page.goto("https://ko-fi.com/shop/manage/add", timeout=60000)
            page.wait_for_timeout(3000)
            fill_visible(page, ['input[name="Name"]', '#Name'], prod["name"])
            fill_visible(page, ['input[name="Price"]', '#Price'], prod["price"])
            click_visible(page, ['button:has-text("Publish")', 'button:has-text("Save")'])
            page.wait_for_timeout(4000)
            for m in re.finditer(r'(https://ko-fi\.com/s/[a-f0-9]+)', page.content()):
                results.setdefault("products", {}).setdefault(prod["slug"], {})["kofi"] = m.group(1)
                log(f"  Ko-fi {prod['slug']}: {m.group(1)}")
        except Exception as e:
            log(f"  Ko-fi {prod['slug']}: {e}")


def setup_polar(page, results: dict) -> dict | None:
    log("Polar.sh...")
    acct = get_account("polar")
    if not acct:
        inbox = create_inbox("polar")
        password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        page.goto("https://polar.sh/signup", timeout=60000)
        page.wait_for_timeout(3000)
        fill_visible(page, ['input[type="email"]'], inbox.address)
        fill_visible(page, ['input[type="password"]'], password)
        click_visible(page, ['button[type="submit"]', 'button:has-text("Sign up")', 'button:has-text("Continue")'])
        page.wait_for_timeout(5000)
        link = wait_for_link(inbox, timeout=120)
        if link:
            page.goto(link, timeout=60000)
        acct = {"service": "polar", "email": inbox.address, "password": password,
                "inbox_password": inbox.password, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        save_accounts(load_accounts() + [acct])
    page.screenshot(path=str(ROOT / "pipeline/polar-signup.png"))

    for prod in PRODUCTS:
        try:
            page.goto("https://polar.sh/dashboard/products/new", timeout=60000)
            page.wait_for_timeout(3000)
            fill_visible(page, ['input[name="name"]', 'input[placeholder*="name" i]'], prod["name"])
            fill_visible(page, ['input[name="price_amount"]', 'input[placeholder*="price" i]'], prod["price"])
            click_visible(page, ['button:has-text("Create")', 'button:has-text("Save")'])
            page.wait_for_timeout(4000)
            for m in re.finditer(r'(https://polar\.sh/purchases/[a-z0-9-]+|https://buy\.polar\.co/[a-z0-9-]+)', page.content()):
                results.setdefault("products", {}).setdefault(prod["slug"], {})["polar"] = m.group(1)
                log(f"  Polar {prod['slug']}: {m.group(1)}")
        except Exception as e:
            log(f"  Polar {prod['slug']}: {e}")
    return acct


def setup_itch(page, results: dict) -> dict | None:
    log("itch.io...")
    inbox = create_inbox("itch")
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    page.goto("https://itch.io/register", timeout=60000)
    page.wait_for_timeout(2000)
    fill_visible(page, ['input[name="username"]'], "sellertools" + str(random.randint(1000, 9999)))
    fill_visible(page, ['input[name="email"]', 'input[type="email"]'], inbox.address)
    fill_visible(page, ['input[name="password"]', 'input[type="password"]'], password)
    click_visible(page, ['button:has-text("Register")', 'input[type="submit"]'])
    page.wait_for_timeout(5000)
    link = wait_for_link(inbox, timeout=120)
    if link:
        page.goto(link, timeout=60000)
    page.screenshot(path=str(ROOT / "pipeline/itch-signup.png"))

    for prod in PRODUCTS:
        try:
            page.goto("https://itch.io/game/new", timeout=60000)
            page.wait_for_timeout(3000)
            fill_visible(page, ['input[name="title"]', '#game_title'], prod["name"])
            fill_visible(page, ['input[name="price"]', '#price'], prod["price"])
            click_visible(page, ['button:has-text("Save")', 'input[value="Save"]'])
            page.wait_for_timeout(4000)
            m = re.search(r'itch\.io/[^"\']+', page.url)
            if m:
                url = "https://" + m.group(0) if not page.url.startswith("http") else page.url
                results.setdefault("products", {}).setdefault(prod["slug"], {})["itch"] = url
                log(f"  itch {prod['slug']}: {url}")
        except Exception as e:
            log(f"  itch {prod['slug']}: {e}")

    acct = {"service": "itch", "email": inbox.address, "password": password,
            "inbox_password": inbox.password, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save_accounts(load_accounts() + [acct])
    return acct


def main() -> None:
    from playwright.sync_api import sync_playwright

    results: dict = {"products": {}, "primary": "fallback", "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    log("=== Card autopilot v2 ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1400, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        kofi = get_account("kofi")
        if kofi:
            try:
                setup_kofi(page, kofi, results)
            except Exception as e:
                log(f"Ko-fi failed: {e}")

        try:
            setup_payhip(page, results)
        except Exception as e:
            log(f"Payhip failed: {e}")

        try:
            setup_polar(page, results)
        except Exception as e:
            log(f"Polar failed: {e}")

        try:
            setup_itch(page, results)
        except Exception as e:
            log(f"itch failed: {e}")

        browser.close()

    CARD_CFG.write_text(json.dumps(results, indent=2) + "\n")

    if results.get("products"):
        for platform in ("payhip", "polar", "kofi", "itch", "gumroad"):
            if any(platform in v for v in results["products"].values()):
                results["primary"] = platform
                break
        wire_checkout(results)
        log(f"LIVE — card checkout via {results['primary']}")
    else:
        results["status"] = "blocked"
        CARD_CFG.write_text(json.dumps(results, indent=2) + "\n")
        log("All platforms blocked — crypto direct still works")

    subprocess.run(["git", "add", "-A", "--", "pipeline/", "site/assets/"], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-m", "Card autopilot: platform checkout links"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)
    log("=== Done ===")


if __name__ == "__main__":
    main()