#!/usr/bin/env python3
"""Run every promotion channel — retries blocked platforms with login flows."""

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

SITE = "https://leopreciadov-bit.github.io/seller-tools"
ACCOUNTS = ROOT / "pipeline" / "accounts.json"
STATE = ROOT / "pipeline" / "promote-all-state.json"

SUBREDDITS = [
    ("Etsy", "marketing/REDDIT_POST_READY.txt"),
    ("shopify", "marketing/REDDIT_SHOPIFY.txt"),
    ("SideProject", "marketing/REDDIT_SIDEPROJECT.txt"),
    ("InternetIsBeautiful", "marketing/REDDIT_IIB.txt"),
    ("ecommerce", "marketing/REDDIT_POST_READY.txt"),
    ("Entrepreneur", "marketing/REDDIT_SIDEPROJECT.txt"),
]


def log(msg: str) -> None:
    print(f"[all] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"channels": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def parse_post(path: Path) -> tuple[str, str]:
    title, body, section = "", [], None
    for line in path.read_text().splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            section = "body"
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body.append(line)
    return title, "\n".join(body).strip()


def dismiss_cookies(page) -> None:
    for sel in [
        'button:has-text("Accept")',
        'button:has-text("Accept all")',
        'button:has-text("Reject")',
        'button:has-text("Allow all")',
        '#onetrust-accept-btn-handler',
    ]:
        loc = page.locator(sel)
        if loc.count() and loc.first.is_visible():
            try:
                loc.first.click(timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                pass


def reddit_api_post(state: dict) -> None:
    config = ROOT / "pipeline" / "reddit.json"
    if not config.exists():
        log("No pipeline/reddit.json — create app at reddit.com/prefs/apps then:")
        log("  python3 scripts/reddit_setup.py set --client-id ID --client-secret SECRET")
        state["channels"]["reddit"] = {"status": "needs_api_creds"}
        return
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/reddit_post.py"), "--all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    state["channels"]["reddit"] = {
        "status": "ok" if r.returncode == 0 else "failed",
        "output": r.stdout[-2000:],
    }


def reddit_login_post(state: dict) -> None:
    reddit_api_post(state)
    if state["channels"].get("reddit", {}).get("status") == "ok":
        return

    from playwright.sync_api import sync_playwright

    accounts = json.loads(ACCOUNTS.read_text())
    reddit = next((a for a in accounts if a.get("service") == "reddit"), None)
    if not reddit:
        log("No reddit account — skip")
        return

    posts_done = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        page = ctx.new_page()

        page.goto("https://old.reddit.com/login", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        dismiss_cookies(page)
        page.fill("#user_login", reddit["username"])
        page.fill("#passwd_login", reddit["password"])
        page.click('button[type="submit"], .btn.login-required')
        page.wait_for_timeout(5000)

        if "login" in page.url and page.locator("#user_login").count():
            log("Reddit login failed — account may need email verify")
            page.screenshot(path=str(ROOT / "pipeline/reddit-login-fail.png"))
            state["channels"]["reddit"] = {"status": "login_failed"}
            browser.close()
            return

        log(f"Reddit logged in as {reddit['username']}")

        for sub, rel in SUBREDDITS:
            pf = ROOT / rel
            if not pf.exists():
                continue
            title, body = parse_post(pf)
            if not title:
                continue
            try:
                page.goto(f"https://old.reddit.com/r/{sub}/submit", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)
                if page.locator('input[name="title"]').count():
                    page.fill('input[name="title"]', title)
                if page.locator('textarea[name="text"]').count():
                    page.fill('textarea[name="text"]', body)
                submit = page.locator('button:has-text("submit"), button:has-text("Submit"), .btn[type="submit"]')
                if submit.count():
                    submit.first.click()
                    page.wait_for_timeout(8000)
                posts_done.append({"sub": sub, "url": page.url})
                log(f"r/{sub} → {page.url[:100]}")
            except Exception as e:
                log(f"r/{sub} error: {e}")
                posts_done.append({"sub": sub, "error": str(e)})

        browser.close()

    state["channels"]["reddit"] = {"status": "posted", "posts": posts_done}


def hackernews_submit(state: dict) -> None:
    from playwright.sync_api import sync_playwright
    from tempmail import create_inbox, wait_for_link

    title = "Show HN: Free Etsy/Shopify listing generators (13-tag SEO, no signup)"
    url = f"{SITE}/"

    inbox = create_inbox("hn")
    user = "sellertools" + "".join(random.choices(string.digits, k=4))
    pw = "".join(random.choices(string.ascii_letters + string.digits, k=14))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://news.ycombinator.com/login?goto=submit", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        if page.locator('input[name="acct"]').count():
            page.fill('input[name="acct"]', user)
        if page.locator('input[name="pw"]').count():
            page.fill('input[name="pw"]', pw)
        create = page.locator('input[value="create account"], input[type="submit"]')
        if create.count():
            create.first.click()
            page.wait_for_timeout(5000)

        page.goto("https://news.ycombinator.com/submit", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        if page.locator('input[name="title"]').count():
            page.fill('input[name="title"]', title)
        if page.locator('input[name="url"]').count():
            page.fill('input[name="url"]', url)
        if page.locator('input[type="submit"]').count():
            page.locator('input[type="submit"]').first.click()
            page.wait_for_timeout(5000)

        log(f"HN → {page.url}")
        page.screenshot(path=str(ROOT / "pipeline/hn-submit.png"))
        state["channels"]["hackernews"] = {"url": page.url, "user": user}
        browser.close()


def devto_publish(state: dict) -> None:
    from playwright.sync_api import sync_playwright
    from tempmail import create_inbox, wait_for_code, wait_for_link

    article = ROOT / "marketing" / "DEVTO_ARTICLE.md"
    text = article.read_text()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else "Free Etsy Listing Tools"
    body = re.sub(r"^#\s+.+\n", "", text, count=1).strip()

    inbox = create_inbox("devto")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://dev.to/enter?state=new-user", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        dismiss_cookies(page)

        email_in = page.locator('input[name="user[email]"], input[type="email"]')
        if email_in.count():
            email_in.first.fill(inbox.address)
        page.locator('button:has-text("Continue"), button:has-text("Sign up")').first.click()
        page.wait_for_timeout(5000)

        code = wait_for_code(inbox, timeout=120)
        link = wait_for_link(inbox, timeout=30) if not code else None
        if code:
            otp = page.locator('input[inputmode="numeric"], input[name="code"]')
            if otp.count():
                otp.first.fill(code)
            page.locator('button[type="submit"]').first.click()
            page.wait_for_timeout(5000)
        elif link:
            page.goto(link, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
        else:
            state["channels"]["devto"] = {"status": "signup_failed"}
            browser.close()
            return

        page.goto("https://dev.to/new", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.locator('textarea').first.fill(title)
        editors = page.locator('textarea')
        if editors.count() > 1:
            editors.nth(1).fill(body)
        page.locator('button:has-text("Publish")').first.click()
        page.wait_for_timeout(5000)
        log(f"Dev.to → {page.url}")
        state["channels"]["devto"] = {"url": page.url}
        browser.close()


def indiehackers_post(state: dict) -> None:
    from playwright.sync_api import sync_playwright
    from tempmail import create_inbox, wait_for_link

    inbox = create_inbox("ih")
    user = "sellertools" + "".join(random.choices(string.digits, k=4))
    body = (
        f"Shipped two free browser tools for Etsy/Shopify sellers — listing generator + 13-tag SEO helper.\n\n"
        f"Live: {SITE}/\n\nNo signup, static GitHub Pages. Would love feedback from sellers."
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.indiehackers.com/sign-up", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        dismiss_cookies(page)

        uname = page.locator('input[placeholder*="username" i], input[name="username"]')
        if not uname.count():
            uname = page.locator('input:visible').first
        uname.fill(user)
        page.locator('button:has-text("NEXT")').click()
        page.wait_for_timeout(3000)

        email_in = page.locator('input[type="email"]')
        if email_in.count():
            email_in.first.fill(inbox.address)
        page.locator('button:has-text("NEXT"), button[type="submit"]').first.click()
        page.wait_for_timeout(5000)

        link = wait_for_link(inbox, timeout=90)
        if link:
            page.goto(link, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

        page.goto("https://www.indiehackers.com/post/new", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        if page.locator('textarea').count():
            page.locator('textarea').first.fill(body)
        page.locator('button:has-text("Post"), button:has-text("Publish")').first.click()
        page.wait_for_timeout(5000)
        log(f"IH → {page.url}")
        state["channels"]["indiehackers"] = {"url": page.url}
        browser.close()


def telegraph_articles(state: dict) -> None:
    token_path = ROOT / "pipeline" / "telegraph-token.json"
    if token_path.exists():
        token = json.loads(token_path.read_text())["access_token"]
    else:
        acc = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(
                    "https://api.telegra.ph/createAccount?"
                    + urllib.parse.urlencode({"short_name": "SellerTools", "author_name": "Seller Tools"})
                ),
                timeout=20,
            ).read()
        )
        if not acc.get("ok"):
            state["channels"]["telegraph"] = {"error": str(acc)}
            return
        token = acc["result"]["access_token"]
        token_path.write_text(json.dumps(acc["result"], indent=2) + "\n")

    articles = [
        ("Free Etsy Listing Tools 2026", SITE),
        ("Etsy Tag Generator — 13 SEO Tags", f"{SITE}/etsy-tag-finder/"),
        ("Shopify Listing Generator Free", f"{SITE}/listing-lab/"),
    ]
    urls = []
    for title, link in articles:
        content = json.dumps([{"tag": "p", "children": [{"tag": "a", "attrs": {"href": link}, "children": [link]}]}])
        data = urllib.parse.urlencode({
            "access_token": token,
            "title": title,
            "author_name": "Seller Tools",
            "content": content,
        }).encode()
        req = urllib.request.Request("https://api.telegra.ph/createPage", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read())
        if res.get("ok"):
            urls.append(res["result"]["url"])
            log(f"Telegraph → {res['result']['url']}")
    state["channels"]["telegraph"] = {"urls": urls}


def github_launch(state: dict) -> None:
    body = (
        f"## Free Etsy & Shopify seller tools\n\n"
        f"- **ListingLab**: {SITE}/listing-lab/\n"
        f"- **Etsy Tag Finder**: {SITE}/etsy-tag-finder/\n\n"
        f"No signup. SEO guides included."
    )
    r = subprocess.run(
        [
            "gh", "api", "graphql", "-f", f"query=mutation {{ createDiscussion(input: {{"
            f"repositoryId: \"R_kgDOTHCmOw\", categoryId: \"DIC_kwDOTHCmO84DAB1X\","
            f"title: \"Launch: Free Etsy/Shopify listing generators\","
            f"body: {json.dumps(body)[1:-1]}"
            f"}}) {{ discussion {{ url }} }} }}",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        data = json.loads(r.stdout)
        url = data.get("data", {}).get("createDiscussion", {}).get("discussion", {}).get("url")
        if url:
            state["channels"]["github_discussion"] = {"url": url}
            log(f"GitHub Discussion → {url}")
            return
    subprocess.run(
        ["gh", "release", "create", "v1.0.1", "--repo", "leopreciadov-bit/seller-tools",
         "--title", "Seller Tools — traffic push", "--notes", body],
        capture_output=True,
    )
    state["channels"]["github"] = {"status": "release_or_discussion_attempted"}


def search_pings(state: dict) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/promote_autopilot.py")], check=False)
    state["channels"]["search_pings"] = {"status": "ran"}


def main() -> None:
    state = load_state()
    log("=== Promote ALL ===")

    search_pings(state)

    for name, fn in [
        ("telegraph", telegraph_articles),
        ("github", github_launch),
        ("reddit", reddit_login_post),
        ("hackernews", hackernews_submit),
        ("devto", devto_publish),
        ("indiehackers", indiehackers_post),
    ]:
        try:
            log(f"--- {name} ---")
            fn(state)
        except Exception as e:
            log(f"{name} failed: {e}")
            state["channels"][name] = {"error": str(e)}

    save_state(state)
    log("=== Done ===")


if __name__ == "__main__":
    main()