#!/usr/bin/env python3
"""Generate + post community outreach — Facebook groups, forums, Discord paste."""

from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
STATE = ROOT / "pipeline" / "community-outreach.json"
TELEGRAPH = ROOT / "pipeline" / "telegraph-token.json"
OUT = ROOT / "marketing" / "COMMUNITY_POSTS_READY.txt"

POSTS = [
    {
        "title": "Free Etsy tag generator — 13 tags, 20 char limit enforced",
        "body": f"""I built a free browser tool for Etsy sellers — no signup.

Paste your product + keywords → get exactly 13 SEO tags (Etsy's 20-char limit enforced).

Try it: {SITE}/etsy-tag-finder/

Pro is $14 lifetime if you need unlimited + CSV export. There's also a listing generator for titles/descriptions: {SITE}/listing-lab/

Happy to hear feedback.""",
        "targets": ["Etsy Sellers United", "Etsy Entrepreneurs", "Handmade Business"],
    },
    {
        "title": "Listing generator for Etsy + Shopify (free, 5/day)",
        "body": f"""Sharing a free listing tool I've been using for my shop.

Generates SEO title, description, tags, and bullets from product basics. Works for Etsy and Shopify mode.

{SITE}/listing-lab/

Free tier is 5/day. Pro is $19 one-time (not monthly). Also has a 13-tag Etsy tool: {SITE}/etsy-tag-finder/""",
        "targets": ["Shopify Entrepreneurs", "Dropshipping", "Etsy Sellers"],
    },
    {
        "title": "Cheaper than Marmalead/eRank — free Etsy SEO tools",
        "body": f"""If you're tired of $20+/mo Etsy SEO subscriptions:

Free tools (browser, no account):
• 13-tag generator: {SITE}/etsy-tag-finder/
• Full listing writer: {SITE}/listing-lab/

Lifetime Pro is $14–$29, pay card or crypto. Comparison: {SITE}/guides/marmalead-alternative-free.html""",
        "targets": ["Etsy SEO", "Side Project", "Indie Hackers"],
    },
]

FORUMS = [
    ("etsy_community", "https://community.etsy.com/"),
    ("seller_hangout", "https://www.etsy.com/seller-handbook"),
]


def log(msg: str) -> None:
    print(f"[community] {msg}", flush=True)


def telegraph_post(title: str, body: str) -> str | None:
    if not TELEGRAPH.exists():
        return None
    token = json.loads(TELEGRAPH.read_text()).get("access_token", "")
    if not token:
        return None
    paras = [{"tag": "p", "children": [line]} for line in body.split("\n") if line.strip()]
    content = json.dumps(paras)
    data = urllib.parse.urlencode({
        "access_token": token, "title": title, "author_name": "Seller Tools", "content": content,
    }).encode()
    req = urllib.request.Request("https://api.telegra.ph/createPage", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read())
        return res["result"]["url"] if res.get("ok") else None
    except Exception:
        return None


def rentry_post(text: str) -> str | None:
    data = urllib.parse.urlencode({"url": "", "edit_code": "", "text": text}).encode()
    req = urllib.request.Request("https://rentry.co/api/new", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read())
        return res.get("url") if res.get("status") == "200" else None
    except Exception:
        return None


def main() -> None:
    st = {"runs": []} if not STATE.exists() else json.loads(STATE.read_text())
    log("=== Community outreach ===")

    post = random.choice(POSTS)
    lines = [f"# {post['title']}\n", post["body"], "\n## Post to these groups:\n"]
    for t in post["targets"]:
        lines.append(f"- Facebook: {t}")
    for name, url in FORUMS:
        lines.append(f"- Forum: {url}")
    lines.append(f"\nAffiliate link: {SITE}/affiliate/\n")
    OUT.write_text("\n".join(lines) + "\n")
    log(f"Wrote {OUT.name}")

    url = telegraph_post(post["title"], post["body"])
    if url:
        st["runs"].append({"channel": "telegraph", "url": url, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        log(f"Telegraph: {url}")

    rurl = rentry_post(post["body"])
    if rurl:
        st["runs"].append({"channel": "rentry", "url": rurl, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        log(f"Rentry: {rurl}")

    STATE.write_text(json.dumps(st, indent=2) + "\n")
    log("Manual step: paste COMMUNITY_POSTS_READY.txt into Facebook Etsy seller groups")
    log("=== Done ===")


if __name__ == "__main__":
    main()