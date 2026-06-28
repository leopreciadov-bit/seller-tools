#!/usr/bin/env python3
"""
Drive traffic to Seller Tools — search pings, directory submissions, social posts.
Run: python3 scripts/promote_autopilot.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

SITE = "https://leopreciadov-bit.github.io/seller-tools"
HOST = "leopreciadov-bit.github.io"
STATE = ROOT / "pipeline" / "promote-state.json"
INDEXNOW = ROOT / "pipeline" / "indexnow.json"
ACCOUNTS = ROOT / "pipeline" / "accounts.json"

URLS = [
    f"{SITE}/",
    f"{SITE}/listing-lab/",
    f"{SITE}/etsy-tag-finder/",
    f"{SITE}/guides/how-to-choose-etsy-tags.html",
    f"{SITE}/guides/etsy-listing-description-template.html",
    f"{SITE}/guides/shopify-product-listing-seo.html",
]

SUBREDDITS = [
    ("Etsy", "marketing/REDDIT_POST_READY.txt"),
    ("shopify", "marketing/REDDIT_SHOPIFY.txt"),
    ("SideProject", "marketing/REDDIT_SIDEPROJECT.txt"),
    ("InternetIsBeautiful", "marketing/REDDIT_IIB.txt"),
]


def log(msg: str) -> None:
    print(f"[promote] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"attempted": {}, "results": []}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def http(method: str, url: str, data: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    hdrs = headers or {}
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:500]
    except Exception as e:
        return 0, str(e)


def ping_search_engines(state: dict) -> None:
    sitemap = urllib.parse.quote(f"{SITE}/sitemap.xml", safe="")
    pings = [
        ("Google sitemap", f"https://www.google.com/ping?sitemap={sitemap}"),
        ("Bing sitemap", f"https://www.bing.com/ping?sitemap={sitemap}"),
    ]
    for name, url in pings:
        code, body = http("GET", url)
        log(f"{name}: HTTP {code}")
        state["results"].append({"channel": name, "status": code, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

    if INDEXNOW.exists():
        cfg = json.loads(INDEXNOW.read_text())
        payload = json.dumps({
            "host": HOST,
            "key": cfg["key"],
            "keyLocation": f"{SITE}/{cfg['key_file']}",
            "urlList": URLS,
        }).encode()
        for name, endpoint in [
            ("IndexNow", "https://api.indexnow.org/indexnow"),
            ("Bing IndexNow", "https://www.bing.com/indexnow"),
            ("Yandex IndexNow", "https://yandex.com/indexnow"),
        ]:
            code, _ = http("POST", endpoint, data=payload, headers={"Content-Type": "application/json"})
            log(f"{name}: HTTP {code}")
            state["results"].append({"channel": name, "status": code})


def parse_post_file(path: Path) -> tuple[str, str]:
    title, body_lines, section = "", [], None
    for line in path.read_text().splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            section = "title"
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body_lines.append(line)
    return title, "\n".join(body_lines).strip()


def reddit_post_all(state: dict) -> None:
    if state["attempted"].get("reddit"):
        log("Reddit already attempted — skip")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("Playwright not installed — skip Reddit")
        return

    from tempmail import create_inbox, wait_for_link  # noqa: E402
    import random
    import string

    results = []
    try:
        inbox = create_inbox("reddit", provider="mail.tm")
    except RuntimeError as e:
        log(f"Reddit temp mail failed: {e}")
        state["attempted"]["reddit"] = True
        return
    password = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    username = "sellertools" + "".join(random.choices(string.digits, k=4))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Signup
        page.goto("https://www.reddit.com/register/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        for sel, val in [
            ('input[name="email"]', inbox.address),
            ('input[name="username"]', username),
            ('input[name="password"]', password),
        ]:
            if page.locator(sel).count():
                page.locator(sel).first.fill(val)

        if page.locator('button[type="submit"]').count():
            page.locator('button[type="submit"]').first.click()
            page.wait_for_timeout(5000)

        if "captcha" in page.content().lower() or page.locator('iframe[src*="captcha"]').count():
            log("Reddit CAPTCHA — cannot auto-post")
            page.screenshot(path=str(ROOT / "pipeline/reddit-captcha.png"))
            state["attempted"]["reddit"] = True
            state["results"].append({"channel": "reddit", "status": "captcha"})
            browser.close()
            return

        link = wait_for_link(inbox, timeout=60)
        if link:
            page.goto(link, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

        for sub, rel_path in SUBREDDITS:
            post_file = ROOT / rel_path
            if not post_file.exists():
                continue
            title, body = parse_post_file(post_file)
            if not title:
                continue
            try:
                page.goto(f"https://www.reddit.com/r/{sub}/submit", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000)
                if page.locator('textarea[name="title"]').count():
                    page.locator('textarea[name="title"]').first.fill(title)
                if page.locator('textarea[name="body"]').count():
                    page.locator('textarea[name="body"]').first.fill(body)
                elif page.locator('div[contenteditable="true"]').count():
                    page.locator('div[contenteditable="true"]').first.fill(body)
                if page.locator('button:has-text("Post")').count():
                    page.locator('button:has-text("Post")').first.click()
                    page.wait_for_timeout(5000)
                results.append({"sub": sub, "url": page.url})
                log(f"r/{sub}: attempted → {page.url[:80]}")
            except Exception as e:
                log(f"r/{sub} failed: {e}")
                results.append({"sub": sub, "error": str(e)})

        browser.close()

    state["attempted"]["reddit"] = True
    state["results"].append({"channel": "reddit", "posts": results})
    if ACCOUNTS.exists():
        accounts = json.loads(ACCOUNTS.read_text())
        accounts.append({
            "service": "reddit",
            "username": username,
            "email": inbox.address,
            "password": password,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        ACCOUNTS.write_text(json.dumps(accounts, indent=2) + "\n")


def devto_post(state: dict) -> None:
    if state["attempted"].get("devto"):
        log("Dev.to already attempted — skip")
        return

    article = ROOT / "marketing" / "DEVTO_ARTICLE.md"
    if not article.exists():
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return

    from tempmail import create_inbox, wait_for_code, wait_for_link  # noqa: E402
    import random
    import string

    text = article.read_text()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else "Free Etsy Listing Tools"
    body = re.sub(r"^#\s+.+\n", "", text, count=1).strip()

    inbox = create_inbox("devto")
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://dev.to/enter", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        if page.locator('input[name="user[email]"]').count():
            page.locator('input[name="user[email]"]').first.fill(inbox.address)
        if page.locator('input[type="email"]').count():
            page.locator('input[type="email"]').first.fill(inbox.address)
        click = page.locator('button:has-text("Continue"), button:has-text("Sign up")')
        if click.count():
            click.first.click()
            page.wait_for_timeout(5000)

        code = wait_for_code(inbox, timeout=90)
        link = wait_for_link(inbox, timeout=30) if not code else None
        if code and page.locator('input[inputmode="numeric"]').count():
            page.locator('input[inputmode="numeric"]').first.fill(code)
            page.locator('button[type="submit"]').first.click()
            page.wait_for_timeout(5000)
        elif link:
            page.goto(link, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
        else:
            log("Dev.to signup incomplete")
            state["attempted"]["devto"] = True
            browser.close()
            return

        page.goto("https://dev.to/new", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        if page.locator('textarea[id*="title"]').count():
            page.locator('textarea[id*="title"]').first.fill(title)
        if page.locator('textarea[id*="body"]').count():
            page.locator('textarea[id*="body"]').first.fill(body)
        if page.locator('button:has-text("Publish")').count():
            page.locator('button:has-text("Publish")').first.click()
            page.wait_for_timeout(5000)
        log(f"Dev.to: {page.url}")
        state["results"].append({"channel": "devto", "url": page.url})
        state["attempted"]["devto"] = True
        browser.close()


def hackernews_submit(state: dict) -> None:
    if state["attempted"].get("hackernews"):
        return

    title = "Show HN: Free Etsy/Shopify listing generators (13-tag SEO, no signup)"
    url = f"{SITE}/"
    submit_url = "https://news.ycombinator.com/submitlink?u=" + urllib.parse.quote(url) + "&t=" + urllib.parse.quote(title)
    code, _ = http("GET", submit_url)
    log(f"Hacker News submit link prepared (HTTP {code}) — needs logged-in user")
    state["attempted"]["hackernews"] = True
    state["results"].append({"channel": "hackernews", "submit_url": submit_url})


def main() -> None:
    state = load_state()
    log(f"Promoting {SITE}")

    ping_search_engines(state)
    hackernews_submit(state)
    try:
        reddit_post_all(state)
    except Exception as e:
        log(f"Reddit error: {e}")
        state["attempted"]["reddit"] = True

    try:
        devto_post(state)
    except Exception as e:
        log(f"Dev.to error: {e}")
        state["attempted"]["devto"] = True

    save_state(state)
    log("Done — see pipeline/promote-state.json")


if __name__ == "__main__":
    main()