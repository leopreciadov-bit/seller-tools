#!/usr/bin/env python3
"""Continuous sales innovation — new pages, outreach, directories, viral hooks."""

from __future__ import annotations

import json
import random
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
STATE = ROOT / "pipeline" / "sales-innovate.json"
GUIDES = ROOT / "site" / "guides"
BUY = ROOT / "site" / "buy"
SALES = ROOT / "pipeline" / "sales.json"
TELEGRAPH = ROOT / "pipeline" / "telegraph-token.json"

ROUND2_COMPARISONS = [
    ("everbee-alternative-free", "Everbee Alternative Free for Etsy", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Everbee charges monthly. Get 13 Etsy tags and listing copy free — $14–$29 lifetime Pro."),
    ("sale-samurai-alternative", "Sale Samurai Alternative — Free Etsy SEO", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Skip Sale Samurai fees. Long-tail tag combos and CSV export with one-time payment."),
    ("koalanda-alternative", "Koalanda Alternative for Etsy Tags", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Koalanda-style tag research without a subscription. Browser tool, no signup."),
    ("merch-titans-alternative", "Merch Titans Alternative Listing Tool", "listing-lab", "listinglab-pro",
     "POD sellers: generate Etsy/Shopify listings from product basics in seconds."),
    ("etsy-rank-alternative", "Etsy Rank Alternative Free Tool", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Rank higher with all 13 tags filled correctly — 20 char limit enforced."),
    ("cresta-alternative-etsy", "Cresta Etsy Alternative — Listing Writer", "listing-lab", "listinglab-pro",
     "AI-style listing structure without monthly AI writer subscriptions."),
    ("shopify-dropshipping-seo-tool", "Shopify Dropshipping SEO Tool Free", "listing-lab", "listinglab-pro",
     "Product titles and descriptions optimized for Google Shopping and store search."),
    ("etsy-christmas-tags-generator", "Etsy Christmas Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Seasonal holiday tags for handmade gifts — 13 tags ready to paste."),
    ("etsy-wedding-tags-generator", "Etsy Wedding Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro",
     "Bridal, wedding favor, and reception decor tags with long-tail SEO."),
    ("etsy-listing-not-selling", "Etsy Listing Not Selling? Fix SEO Tags & Copy", "listing-lab", "seller-kit-bundle",
     "Weak tags and thin descriptions kill sales. Regenerate both in one workflow."),
]

PROBLEM_PAGES = [
    ("how-to-rank-on-etsy-search", "How to Rank on Etsy Search (Free Tools)", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-seo-checklist-2026", "Etsy SEO Checklist 2026 for Sellers", "etsy-tag-finder", "seller-kit-bundle"),
    ("shopify-conversion-copy-tool", "Shopify Conversion Copy Generator", "listing-lab", "listinglab-pro"),
    ("etsy-title-too-short-fix", "Etsy Title Too Short? Generator Fix", "listing-lab", "listinglab-pro"),
    ("bulk-etsy-listing-generator", "Bulk Etsy Listing Generator", "listing-lab", "listinglab-pro"),
    ("etsy-tag-stuffing-avoid", "Etsy Tag Stuffing — What to Do Instead", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("long-tail-keywords-etsy-free", "Long Tail Keywords Etsy — Free Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("handmade-jewelry-etsy-tags", "Handmade Jewelry Etsy Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("crochet-etsy-listing-generator", "Crochet Etsy Listing Generator", "listing-lab", "listinglab-pro"),
    ("vintage-clothing-etsy-seo", "Vintage Clothing Etsy SEO Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
]

BUY_PAGES = {
    "etsy-tag-finder-pro": {
        "title": "Buy Etsy Tag Finder Pro — $14 Lifetime",
        "product": "etsy-tag-finder-pro",
        "price": "$14",
        "pitch": "Unlimited 13-tag generations, CSV export, no subscription.",
        "tool": "/etsy-tag-finder/",
    },
    "listinglab-pro": {
        "title": "Buy ListingLab Pro — $19 Lifetime",
        "product": "listinglab-pro",
        "price": "$19",
        "pitch": "Unlimited Etsy & Shopify listings — titles, descriptions, tags, bullets.",
        "tool": "/listing-lab/",
    },
    "seller-kit-bundle": {
        "title": "Buy Seller Kit Bundle — $29 Lifetime",
        "product": "seller-kit-bundle",
        "price": "$29",
        "pitch": "Both Pro tools. Best value for serious sellers.",
        "tool": "/",
        "bundle": True,
    },
}


def log(msg: str) -> None:
    print(f"[innovate] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"actions": [], "pages_created": []}


def save_state(st: dict) -> None:
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def record(st: dict, channel: str, **kw) -> None:
    entry = {"channel": channel, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    st["actions"].append(entry)
    log(f"{channel}: {kw.get('url', kw.get('status', kw))}")


def render_guide(slug: str, title: str, tool: str, product: str, blurb: str) -> str:
    tool_url = f"{SITE}/listing-lab/" if tool == "listing-lab" else f"{SITE}/etsy-tag-finder/"
    buy_url = f"{SITE}/buy/{product}/" if product != "seller-kit-bundle" else f"{SITE}/buy/seller-kit-bundle/"
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
      <p><a class="btn" href="{tool_url}">Try free →</a> · <a href="{buy_url}">Buy Pro direct</a></p>
      <p><span data-crypto-buy="{product}"></span></p>
    </div>
    <p><a href="{SITE}/deals/">All deals</a> · <a href="{SITE}/recover/">Recover key</a></p>
  </main>
  <link rel="stylesheet" href="/assets/crypto-checkout.css">
</body>
</html>
"""


def render_buy(slug: str, meta: dict) -> str:
    bundle_attr = ' data-crypto-bundle' if meta.get("bundle") else f' data-crypto-buy="{meta["product"]}"'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{meta["title"]}</title>
  <meta name="description" content="{meta["pitch"]} Pay card or USDC/USDT/SOL on Solana. Instant license key.">
  <meta name="robots" content="index, follow">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"Product","name":"{meta["title"]}","offers":{{"@type":"Offer","priceCurrency":"USD","availability":"https://schema.org/InStock"}}}}
  </script>
  <style>
    :root {{ --bg:#0f1117; --panel:#171b24; --border:#2a3142; --text:#e8ecf4; --muted:#9aa3b8; --accent:#6ee7b7; }}
    body {{ margin:0; font-family:system-ui,sans-serif; background:var(--bg); color:var(--text); }}
    .wrap {{ max-width:520px; margin:0 auto; padding:2.5rem 1.25rem 4rem; text-align:center; }}
    h1 {{ font-size:1.6rem; }}
    .price {{ font-size:2.2rem; color:var(--accent); font-weight:700; margin:1rem 0; }}
    .pitch {{ color:var(--muted); margin-bottom:1.5rem; }}
    .pay {{ display:flex; flex-wrap:wrap; gap:.5rem; justify-content:center; margin:1.5rem 0; }}
    .steps {{ text-align:left; background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1.25rem; margin-top:2rem; font-size:.9rem; color:var(--muted); }}
    a {{ color:var(--accent); }}
  </style>
  <link rel="stylesheet" href="/assets/crypto-checkout.css">
</head>
<body>
  <main class="wrap">
    <p style="color:#fbbf24;font-weight:700;text-transform:uppercase;font-size:.75rem;letter-spacing:.08em">Lifetime · No subscription</p>
    <h1>{meta["title"]}</h1>
    <div class="price">{meta["price"]}</div>
    <p class="pitch">{meta["pitch"]}</p>
    <div class="pay"><span{bundle_attr}></span></div>
    <p><a href="{SITE}{meta['tool']}">Try free first</a> · <a href="{SITE}/deals/">Compare plans</a></p>
    <div class="steps">
      <strong>Checkout:</strong>
      <ol>
        <li>Click Pay with Card or Crypto</li>
        <li>Send exact amount to Solana wallet (Phantom, etc.)</li>
        <li>Paste tx signature → instant license key</li>
      </ol>
    </div>
    <p style="margin-top:1.5rem;font-size:.85rem"><a href="{SITE}/recover/">Recover license</a> · <a href="{SITE}/">Home</a></p>
  </main>
  <script src="/assets/crypto.js"></script>
  <script src="/assets/gumroad.js"></script>
  <script src="/assets/crypto-checkout.js" defer></script>
  <script src="/assets/gumroad-ui.js" defer></script>
</body>
</html>
"""


def publish_pages(st: dict) -> None:
    BUY.mkdir(parents=True, exist_ok=True)
    created = set(st.get("pages_created", []))

    for slug, meta in BUY_PAGES.items():
        key = f"buy/{slug}"
        out = BUY / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        if key not in created or not out.exists():
            out.write_text(render_buy(slug, meta))
            created.add(key)
            record(st, "buy_page", url=f"{SITE}/buy/{slug}/")

    for slug, title, tool, product, blurb in ROUND2_COMPARISONS:
        key = f"guide/{slug}"
        out = GUIDES / f"{slug}.html"
        if key in created and out.exists():
            continue
        out.write_text(render_guide(slug, title, tool, product, blurb))
        created.add(key)
        record(st, "comparison_r2", url=f"{SITE}/guides/{slug}.html")

    for slug, title, tool, product in PROBLEM_PAGES:
        key = f"guide/{slug}"
        out = GUIDES / f"{slug}.html"
        if key in created and out.exists():
            continue
        blurb = f"{title}. Free daily quota — upgrade once with card or crypto ($14–$29 lifetime)."
        out.write_text(render_guide(slug, title, tool, product, blurb))
        created.add(key)
        record(st, "problem_page", url=f"{SITE}/guides/{slug}.html")

    st["pages_created"] = sorted(created)


def buyer_recovery(st: dict) -> None:
    """Reach buyers who paid but keys may be unclaimed."""
    if not SALES.exists() or not TELEGRAPH.exists():
        return
    data = json.loads(SALES.read_text())
    token = json.loads(TELEGRAPH.read_text()).get("access_token", "")
    if not token:
        return
    done = set(st.get("recovery_done", []))

    for ex in data.get("excluded_sales", []):
        tx = ex.get("tx", "")
        if not tx or tx in done:
            continue
        product = ex.get("product", "Seller Tools")
        key = ex.get("key", "")
        recover = ex.get("recover_url", f"{SITE}/recover/")
        title = f"Claim your {product} license key"
        content = json.dumps([
            {"tag": "p", "children": [f"You paid for {product}. Your license key is ready."]},
            {"tag": "p", "children": [{"tag": "strong", "children": [key]}]},
            {"tag": "p", "children": ["Recover page:"]},
            {"tag": "p", "children": [{"tag": "a", "attrs": {"href": recover}, "children": [recover]}]},
            {"tag": "p", "children": [f"Transaction: {tx[:20]}…"]},
        ])
        body = urllib.parse.urlencode({
            "access_token": token,
            "title": title,
            "author_name": "Seller Tools",
            "content": content,
        }).encode()
        req = urllib.request.Request("https://api.telegra.ph/createPage", data=body, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.loads(r.read())
            if res.get("ok"):
                url = res["result"]["url"]
                done.add(tx)
                record(st, "buyer_recovery", url=url, product=product, key=key)
        except Exception as e:
            record(st, "buyer_recovery", status="error", detail=str(e)[:80])
            break

    st["recovery_done"] = list(done)


def telegraph_angle_post(st: dict) -> None:
    if not TELEGRAPH.exists():
        return
    token = json.loads(TELEGRAPH.read_text()).get("access_token", "")
    angles = [
        ("Stop paying monthly for Etsy SEO", f"{SITE}/deals/", "One-time $14–$29. Card or USDC on Solana."),
        ("I built free Etsy listing tools (no signup)", f"{SITE}/", "13 tags + full listing copy in browser."),
        ("Etsy sellers: fix listings that don't sell", f"{SITE}/guides/etsy-listing-not-selling.html", "Tags + descriptions regenerated free."),
        ("Direct buy — Etsy Tag Finder Pro $14", f"{SITE}/buy/etsy-tag-finder-pro/", "Instant license after crypto payment."),
    ]
    title, link, blurb = random.choice(angles)
    content = json.dumps([
        {"tag": "p", "children": [blurb]},
        {"tag": "p", "children": [{"tag": "a", "attrs": {"href": link}, "children": [link]}]},
    ])
    data = urllib.parse.urlencode({
        "access_token": token, "title": title, "author_name": "Seller Tools", "content": content,
    }).encode()
    req = urllib.request.Request("https://api.telegra.ph/createPage", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read())
        if res.get("ok"):
            record(st, "telegraph_angle", url=res["result"]["url"])
    except Exception as e:
        record(st, "telegraph_angle", status="error", detail=str(e)[:80])


def paste_more(st: dict) -> None:
    text = f"Seller Tools Pro — lifetime deals\n{SITE}/deals/\n\n"
    text += "\n".join(f"{SITE}/buy/{s}/" for s in BUY_PAGES)
    for name, url, payload in [
        ("paste_ubuntu", "https://paste.ubuntu.com/", {"contents": text, "syntax": "text"}),
        ("paste_debian", "https://paste.debian.net/", {"raw": text}),
    ]:
        try:
            import requests
            r = requests.post(url, data=payload, timeout=20, headers={"User-Agent": "seller-tools/1.0"})
            record(st, name, status=r.status_code, url=r.url)
        except Exception as e:
            record(st, name, status="error", detail=str(e)[:80])


def github_readme_bump(st: dict) -> None:
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    body = readme.read_text()
    banner = f"\n> **Pro deals:** [{SITE}/deals/]({SITE}/deals/) · Direct buy: [Tag Finder $14]({SITE}/buy/etsy-tag-finder-pro/) · [ListingLab $19]({SITE}/buy/listinglab-pro/)\n"
    if SITE + "/deals/" not in body:
        lines = body.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#"):
                lines.insert(i + 1, banner)
                break
        readme.write_text("\n".join(lines))
        record(st, "readme_bump", status="updated")


def awesome_list_pr(st: dict) -> None:
    """Open PR to awesome-etsy if fork possible."""
    entry = f"- [Seller Tools]({SITE}/) — Free Etsy/Shopify listing generators, Pro crypto checkout"
    snippet = ROOT / "pipeline" / "awesome-etsy-entry.md"
    snippet.write_text(entry + "\n")
    r = subprocess.run(
        ["gh", "search", "repos", "awesome etsy", "--limit", "3", "--json", "nameWithOwner,url"],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        try:
            repos = json.loads(r.stdout)
            record(st, "awesome_search", repos=[x["nameWithOwner"] for x in repos[:3]])
        except json.JSONDecodeError:
            pass


def expand_seo_keywords(st: dict) -> None:
    """Feed seo_content_factory with new keyword batches."""
    kw_file = ROOT / "pipeline" / "seo-keywords.json"
    data = json.loads(kw_file.read_text())
    existing = {k["slug"] for k in data.get("keywords", [])}
    published = set(data.get("published", []))
    added = 0
    for slug, title, tool, product in PROBLEM_PAGES:
        if slug in existing:
            continue
        data.setdefault("keywords", []).append({
            "slug": slug, "title": title, "tool": tool, "product": product,
        })
        existing.add(slug)
        added += 1
    for slug, title, tool, product, _ in ROUND2_COMPARISONS:
        if slug in existing:
            continue
        data.setdefault("keywords", []).append({
            "slug": slug, "title": title, "tool": tool, "product": product,
        })
        existing.add(slug)
        added += 1
    if added:
        data["last_expand"] = datetime.now(timezone.utc).isoformat()
        kw_file.write_text(json.dumps(data, indent=2) + "\n")
        record(st, "seo_keywords", added=added)


def main() -> None:
    st = load_state()
    log("=== Sales innovate ===")
    expand_seo_keywords(st)
    publish_pages(st)
    for fn in [
        buyer_recovery,
        telegraph_angle_post,
        paste_more,
        github_readme_bump,
        awesome_list_pr,
    ]:
        try:
            fn(st)
        except Exception as e:
            record(st, fn.__name__, status="error", detail=str(e)[:120])
    save_state(st)
    log("=== Done ===")


if __name__ == "__main__":
    main()