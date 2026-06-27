#!/usr/bin/env python3
"""Reddit signup via temp mail + post to r/Etsy. CAPTCHA may require --manual."""

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

POST_FILE = ROOT / "marketing" / "REDDIT_POST_READY.txt"
ACCOUNTS = ROOT / "pipeline" / "accounts.json"


def parse_post() -> tuple[str, str]:
    title, body_lines, section = "", [], None
    for line in POST_FILE.read_text().splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            section = "title"
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body_lines.append(line)
    return title, "\n".join(body_lines).strip()


def save_account(data: dict) -> None:
    existing = json.loads(ACCOUNTS.read_text()) if ACCOUNTS.exists() else []
    existing.append(data)
    ACCOUNTS.write_text(json.dumps(existing, indent=2) + "\n")


def signup_and_post(manual: bool = False) -> None:
    from playwright.sync_api import sync_playwright

    inbox = create_inbox("reddit", provider="guerrillamail")
    password = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    username = "sellertools" + "".join(random.choices(string.digits, k=4))
    title, body = parse_post()

    print(f"Temp mail: {inbox.address}")
    print(f"Username: {username}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not manual)
        page = browser.new_page()
        page.goto("https://www.reddit.com/register/", wait_until="networkidle", timeout=60000)

        for sel, val in [
            ('input[name="email"]', inbox.address),
            ('input[name="username"]', username),
            ('input[name="password"]', password),
        ]:
            if page.locator(sel).count():
                page.fill(sel, val)

        if manual:
            print(">>> Solve CAPTCHA, complete signup, press ENTER <<<")
            input()
        else:
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

        link = wait_for_link(inbox, timeout=120)
        if link:
            page.goto(link, wait_until="networkidle")

        page.goto("https://www.reddit.com/r/Etsy/submit", wait_until="networkidle")
        page.fill('textarea[name="title"], #innerTextArea', title)
        page.fill('textarea[name="body"], div[contenteditable="true"]', body)
        if manual:
            print(">>> Review post, submit, press ENTER <<<")
            input()
        else:
            page.click('button:has-text("Post")')
            page.wait_for_timeout(3000)

        browser.close()

    save_account({
        "service": "reddit",
        "username": username,
        "email": inbox.address,
        "password": password,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    print(f"Saved to {ACCOUNTS}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()
    signup_and_post(manual=args.manual)


if __name__ == "__main__":
    main()