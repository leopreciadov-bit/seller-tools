#!/usr/bin/env python3
"""New sales channels — directories, paste hosts, RSS pings, comparison SEO, GitHub releases."""

from __future__ import annotations

import json
import random
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
STATE = ROOT / "pipeline" / "sales-channels.json"
GUIDES = ROOT / "site" / "guides"

COMPARISON_PAGES = [
    ("marmalead-alternative-free", "Marmalead Alternative Free — Etsy Tag & Listing Tools", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Marmalead costs $19+/mo. Seller Tools gives you free daily generations plus $14–$29 lifetime Pro with direct crypto checkout."),
    ("erank-alternative-free", "eRank Alternative Free for Etsy Sellers", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Skip the eRank subscription. Generate 13 Etsy tags and full listings free — upgrade once, keep forever."),
    ("alura-etsy-alternative", "Alura Alternative — Free Etsy SEO Tools", "listing-lab", "listinglab-pro",
     "Alura is powerful but pricey. ListingLab + Etsy Tag Finder cover listing copy and 13-tag SEO for free."),
    ("etsy-hunt-alternative", "Etsy Hunt Alternative — Keyword & Tag Generator", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Research long-tail Etsy keywords and output 13 ready-to-paste tags without a monthly fee."),
    ("vela-etsy-alternative", "Vela Etsy Alternative — Listing Generator", "listing-lab", "listinglab-pro",
     "Bulk-edit listings faster: generate titles, descriptions, tags, and bullets in one click."),
    ("free-etsy-seo-tool-vs-paid", "Free Etsy SEO Tools vs Paid (2026 Comparison)", "etsy-tag-finder", "seller-kit-bundle",
     "Honest comparison: when free tools are enough and when Pro lifetime ($14–$29) beats monthly SaaS."),
    ("best-etsy-tag-generator-2026", "Best Etsy Tag Generator 2026 (Free & Pro)", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Side-by-side: 13-tag enforcement, long-tail combos, CSV export, and crypto checkout."),
    ("etsy-listing-generator-comparison", "Etsy Listing Generator Comparison — Free Tools", "listing-lab", "listinglab-pro",
     "Compare ListingLab to ChatGPT prompts and paid listing writers for Etsy sellers."),
    ("shopify-listing-tool-free", "Best Free Shopify Listing Tool for Dropshippers", "listing-lab", "listinglab-pro",
     "SEO titles, descriptions, and bullets for Shopify — 5 free generations daily."),
    ("print-on-demand-seo-tool", "Print on Demand SEO Tool — Etsy & Shopify", "listing-lab", "seller-kit-bundle",
     "POD sellers need fast listings. Generate copy + 13 Etsy tags in minutes."),
]

PASTE_BLURBS = [
    ("Launch deal", f"{SITE}/deals/", "Pro lifetime $14–$29 — pay USDC/USDT/SOL direct to Solana wallet."),
    ("Free tag tool", f"{SITE}/etsy-tag-finder/", "13 Etsy tags, 20 chars each. 3 free/day."),
    ("Listing generator", f"{SITE}/listing-lab/", "Etsy + Shopify titles, descriptions, bullets."),
    ("Bundle", f"{SITE}/deals/", "Seller Kit Bundle $29 — both Pro tools lifetime."),
]


def log(msg: str) -> None:
    print(f"[channels] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"runs": []}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def record(state: dict, channel: str, **kw) -> None:
    entry = {"channel": channel, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    state["runs"].append(entry)
    log(f"{channel}: {kw.get('status', kw.get('url', kw))}")


def http_post(url: str, data: bytes | dict, headers: dict | None = None) -> tuple[int, str]:
    if isinstance(data, dict):
        body = urllib.parse.urlencode(data).encode()
        hdrs = {"Content-Type": "application/x-www-form-urlencoded", **(headers or {})}
    else:
        body = data
        hdrs = headers or {}
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return 0, str(e)[:200]


def http_get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "seller-tools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return 0, str(e)[:200]


def render_comparison(slug: str, title: str, tool: str, product: str, blurb: str) -> str:
    tool_url = f"{SITE}/listing-lab/" if tool == "listing-lab" else f"{SITE}/etsy-tag-finder/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{blurb}">
  <meta name="robots" content="index, follow">
  <link rel="stylesheet" href="../assets/content.css">
  <script src="../assets/crypto.js"></script>
  <script src="../assets/crypto-checkout.js" defer></script>
</head>
<body class="content-page">
  <main class="container">
    <h1>{title}</h1>
    <p>{blurb}</p>
    <div class="cta-box">
      <p><strong>Try free →</strong> <a class="btn" href="{tool_url}">Open free tool</a></p>
      <p>Pro unlock (lifetime): <span data-crypto-buy="{product}"></span></p>
      <p><a href="{SITE}/deals/">See launch deals</a> · <a href="{SITE}/recover/">Recover license</a></p>
    </div>
    <h2>Why sellers switch</h2>
    <ul>
      <li>No signup — runs in browser</li>
      <li>Free daily quota on every tool</li>
      <li>Pay once ($14–$29) with card or direct USDC/USDT/SOL</li>
      <li>Instant license key after payment</li>
    </ul>
    <p class="muted"><a href="{SITE}/">Seller Tools</a> · <a href="{SITE}/guides/best-free-etsy-seo-tools.html">More free Etsy SEO tools</a></p>
  </main>
  <link rel="stylesheet" href="/assets/crypto-checkout.css">
</body>
</html>
"""


def publish_comparison_pages(state: dict) -> None:
    published = 0
    for slug, title, tool, product, blurb in COMPARISON_PAGES:
        out = GUIDES / f"{slug}.html"
        if out.exists():
            continue
        out.write_text(render_comparison(slug, title, tool, product, blurb))
        record(state, "comparison_page", url=f"{SITE}/guides/{slug}.html", slug=slug)
        published += 1
    if not published:
        record(state, "comparison_page", status="all_published")


def paste_rs(state: dict) -> None:
    text = "\n".join(f"{t}: {u}\n{b}" for t, u, b in PASTE_BLURBS)
    code, body = http_post("https://paste.rs/", text.encode(), {"Content-Type": "text/plain"})
    url = body.strip() if code == 201 and body.startswith("http") else ""
    record(state, "paste_rs", status=code, url=url or body[:80])


def bpaste(state: dict) -> None:
    text = f"Seller Tools — Etsy & Shopify listing generators\n{SITE}/\n\n"
    text += "\n".join(f"{t}: {u}" for t, u, _ in PASTE_BLURBS)
    code, body = http_post("https://bpaste.net/", {"code": text, "lexer": "text", "expiry": "1year"})
    m = re.search(r'href="(https://bpaste\.net/[^"]+)"', body)
    record(state, "bpaste", status=code, url=m.group(1) if m else body[:80])


def paste_ee(state: dict) -> None:
    try:
        import requests
        text = "\n".join(f"{t}: {u}\n{b}" for t, u, b in PASTE_BLURBS)
        r = requests.post(
            "https://api.paste.ee/v1/pastes",
            json={"description": "Seller Tools", "sections": [{"name": "links", "contents": text}]},
            timeout=20,
        )
        url = r.json().get("link", "") if r.status_code in (200, 201) else ""
        record(state, "paste_ee", status=r.status_code, url=url)
    except Exception as e:
        record(state, "paste_ee", status="error", detail=str(e)[:80])


def zerox_st(state: dict) -> None:
    text = f"Seller Tools deals: {SITE}/deals/\n" + "\n".join(f"{u}" for _, u, _ in PASTE_BLURBS)
    code, body = http_post("https://0x0.st", text.encode(), {"Content-Type": "text/plain"})
    url = body.strip().split()[0] if code == 200 and "http" in body else ""
    record(state, "0x0_st", status=code, url=url)


def rss_ping(state: dict) -> None:
    feed = urllib.parse.quote(f"{SITE}/feed.xml", safe="")
    for name, url in [
        ("pingomatic_rss", f"https://rpc.pingomatic.com/?title=Seller+Tools&blogurl={urllib.parse.quote(SITE + '/')}&rssurl={feed}"),
        ("feedburner_ping", f"https://ping.feedburner.google.com/ping?pubsubhub=hub&huburl={feed}"),
    ]:
        code, _ = http_get(url)
        record(state, name, status=code)


def github_release(state: dict) -> None:
    tag = time.strftime("promo-%Y%m%d-%H%M")
    notes = f"""## Seller Tools — Free Etsy & Shopify Tools

- **Site:** {SITE}/
- **Deals:** {SITE}/deals/
- **ListingLab:** {SITE}/listing-lab/
- **Etsy Tag Finder:** {SITE}/etsy-tag-finder/

Pro: $14–$29 lifetime · Pay USDC/USDT/SOL direct on Solana.
"""
    r = subprocess.run(
        ["gh", "release", "create", tag, "--repo", "leopreciadov-bit/seller-tools",
         "--title", f"Seller Tools update {tag}", "--notes", notes],
        capture_output=True, text=True,
    )
    record(state, "github_release", status="ok" if r.returncode == 0 else "error",
           url=r.stdout.strip() or r.stderr[:100])


def github_repo_bump(state: dict) -> None:
    desc = "Free Etsy & Shopify listing generators — Pro $14-29 lifetime, crypto checkout"
    r = subprocess.run(
        ["gh", "repo", "edit", "leopreciadov-bit/seller-tools",
         "--description", desc,
         "--add-topic", "etsy", "--add-topic", "shopify", "--add-topic", "seo",
         "--add-topic", "ecommerce", "--add-topic", "solana"],
        capture_output=True, text=True,
    )
    record(state, "github_repo", status="ok" if r.returncode == 0 else "error", detail=r.stderr[:80])


def deals_rentry(state: dict) -> None:
    text = f"""# Seller Tools — Launch Deals

{SITE}/deals/

## Pro lifetime (pay card or crypto)
- Etsy Tag Finder Pro — $14
- ListingLab Pro — $19
- Seller Kit Bundle — $29 (both tools)

## Free tools (no signup)
- {SITE}/etsy-tag-finder/
- {SITE}/listing-lab/

Direct USDC/USDT/SOL → Solana wallet. Instant license key.
"""
    code, body = http_post("https://rentry.co/api/new", {"url": "", "edit_code": "", "text": text})
    try:
        res = json.loads(body)
        record(state, "rentry_deals", url=res.get("url", ""), status=res.get("status", code))
    except json.JSONDecodeError:
        record(state, "rentry_deals", status=code, detail=body[:80])


def indiehackers_ping(state: dict) -> None:
    """Warm IH product URL for crawlers."""
    code, _ = http_get("https://www.indiehackers.com/products/seller-tools")
    record(state, "indiehackers", status=code, note="needs manual product page")


def startup_directories(state: dict) -> None:
    """Ping indexable directory/search endpoints."""
    q = urllib.parse.quote(SITE)
    for name, url in [
        ("curlie_search", f"https://curlie.org/search?q=etsy+listing+generator"),
        ("startpage", f"https://www.startpage.com/sp/search?query=site:leopreciadov-bit.github.io+seller+tools"),
    ]:
        code, _ = http_get(url)
        record(state, name, status=code)


def main() -> None:
    state = load_state()
    log("=== Sales channels ===")

    publish_comparison_pages(state)

    for fn in [
        rss_ping,
        deals_rentry,
        paste_rs,
        bpaste,
        zerox_st,
        paste_ee,
        github_repo_bump,
        github_release,
        indiehackers_ping,
        startup_directories,
    ]:
        try:
            fn(state)
        except Exception as e:
            record(state, fn.__name__, status="error", detail=str(e)[:120])

    save_state(state)
    log("=== Done ===")


if __name__ == "__main__":
    main()