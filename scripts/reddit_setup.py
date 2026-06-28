#!/usr/bin/env python3
"""Create Reddit script app + save API creds to pipeline/reddit.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS = ROOT / "pipeline" / "accounts.json"
CONFIG = ROOT / "pipeline" / "reddit.json"
APP_NAME = "Seller Tools Bot"


def load_account() -> dict:
    accounts = json.loads(ACCOUNTS.read_text())
    reddit = next((a for a in accounts if a.get("service") == "reddit"), None)
    if not reddit:
        raise SystemExit("No reddit account in accounts.json — run promote_autopilot first")
    return reddit


def save_config(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Saved {CONFIG}")


def cmd_set(args: argparse.Namespace) -> None:
    account = load_account()
    save_config({
        "client_id": args.client_id.strip(),
        "client_secret": args.client_secret.strip(),
        "username": args.username or account["username"],
        "password": args.password or account["password"],
        "user_agent": args.user_agent or "seller-tools/1.0 by sellertools0963",
    })


def pierce_fill(page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            try:
                loc.first.fill(value, timeout=5000)
                return True
            except Exception:
                pass
    # shadow DOM fallbacks
    for sel in [
        'faceplate-text-input[name="username"] >> input',
        'faceplate-text-input[name="password"] >> input',
        '[autocomplete="username"]',
        '[autocomplete="current-password"]',
    ]:
        loc = page.locator(sel)
        if loc.count():
            try:
                loc.first.fill(value, timeout=5000)
                return True
            except Exception:
                pass
    return False


def create_app_browser() -> dict | None:
    from playwright.sync_api import sync_playwright

    account = load_account()
    client_id = ""
    client_secret = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.reddit.com/login/", wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(4000)

        pierce_fill(page, ['input[name="username"]', '#loginUsername', 'input[id*="username"]'], account["username"])
        pierce_fill(page, ['input[name="password"]', '#loginPassword', 'input[type="password"]'], account["password"])

        for sel in ['button:has-text("Log In")', 'button[type="submit"]', 'faceplate-button[type="submit"]']:
            if page.locator(sel).count():
                page.locator(sel).first.click()
                break
        page.wait_for_timeout(8000)

        page.goto("https://www.reddit.com/prefs/apps", wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(4000)
        content = page.content()

        # existing app?
        m = re.search(r"personal use script[\s\S]{0,200}?<span[^>]*>([A-Za-z0-9_-]{10,20})</span>", content, re.I)
        if m:
            client_id = m.group(1)
            print("Found existing app id:", client_id)

        if not client_id and page.locator('button:has-text("create another app")').count():
            page.locator('button:has-text("create another app")').first.click()
            page.wait_for_timeout(2000)

        if page.locator('input[name="name"]').count():
            page.fill('input[name="name"]', APP_NAME)
            page.locator('input[value="script"]').check()
            page.fill('textarea[name="description"]', "Seller Tools autopost")
            page.fill('input[name="redirect_uri"]', "http://localhost:8080")
            page.click('button:has-text("create app"), input[type="submit"]')
            page.wait_for_timeout(5000)
            content = page.content()
            m = re.search(r"personal use script[\s\S]{0,300}?<span[^>]*>([A-Za-z0-9_-]{10,20})</span>", content, re.I)
            if m:
                client_id = m.group(1)
            sec = re.search(r'<span class="pre">([^<]+)</span>', content)
            if sec:
                client_secret = sec.group(1).strip()

        page.screenshot(path=str(ROOT / "pipeline/reddit-apps.png"))
        browser.close()

    if not client_id:
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "username": account["username"],
        "password": account["password"],
        "user_agent": f"seller-tools/1.0 by {account['username']}",
    }


def cmd_create(_: argparse.Namespace) -> None:
    creds = create_app_browser()
    if not creds:
        print("Could not create Reddit app in browser.")
        print("Manual: https://www.reddit.com/prefs/apps → create script app → run:")
        print("  python3 scripts/reddit_setup.py set --client-id ID --client-secret SECRET")
        sys.exit(1)
    if not creds.get("client_secret"):
        print("Got client_id but no secret on page — paste secret manually:")
        print(f"  python3 scripts/reddit_setup.py set --client-id {creds['client_id']} --client-secret YOUR_SECRET")
    save_config(creds)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set", help="Save Reddit API creds")
    s.add_argument("--client-id", required=True)
    s.add_argument("--client-secret", required=True)
    s.add_argument("--username")
    s.add_argument("--password")
    s.add_argument("--user-agent")
    s.set_defaults(func=cmd_set)
    c = sub.add_parser("create", help="Create script app via browser")
    c.set_defaults(func=cmd_create)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()