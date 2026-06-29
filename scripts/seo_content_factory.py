#!/usr/bin/env python3
"""Publish SEO landing pages that funnel to free tools + card/crypto checkout."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS = ROOT / "pipeline" / "seo-keywords.json"
GUIDES = ROOT / "site" / "guides"
SITE = "https://leopreciadov-bit.github.io/seller-tools"


def load() -> dict:
    return json.loads(KEYWORDS.read_text())


def save(data: dict) -> None:
    KEYWORDS.write_text(json.dumps(data, indent=2) + "\n")


def tool_path(tool: str) -> str:
    return f"{SITE}/listing-lab/" if tool == "listing-lab" else f"{SITE}/etsy-tag-finder/"


def render_page(kw: dict) -> str:
    tool = kw["tool"]
    product = kw["product"]
    title = kw["title"]
    slug = kw["slug"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{title}. Free daily generations. Pay with card or crypto — seller receives on Solana.">
  <link rel="stylesheet" href="../assets/style.css">
  <script src="../assets/crypto.js"></script>
  <script src="../assets/crypto-checkout.js" defer></script>
</head>
<body>
  <main class="container">
    <h1>{title}</h1>
    <p>Free tool for Etsy and Shopify sellers. Pro: <strong>send USDC/USDT directly</strong> on Solana — $14–$29 lifetime.</p>
    <p><a class="btn" href="{tool_path(tool)}">Try free tool →</a></p>
    <p>Pro unlock: <span data-crypto-buy="{product}"></span></p>
    <p><a href="{SITE}/recover/">Paid? Recover your license key</a></p>
    <p class="muted">Seller Tools · <a href="{SITE}/">Home</a></p>
  </main>
</body>
</html>
"""


COMPARISON_TOPICS = [
    ("marmalead-alternative-free", "Marmalead Alternative Free", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("erank-alternative-free", "eRank Alternative Free", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("alura-etsy-alternative", "Alura Etsy Alternative", "listing-lab", "listinglab-pro"),
    ("etsy-hunt-alternative", "Etsy Hunt Alternative", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("vela-etsy-alternative", "Vela Etsy Alternative", "listing-lab", "listinglab-pro"),
    ("free-etsy-seo-tool-vs-paid", "Free Etsy SEO vs Paid", "etsy-tag-finder", "seller-kit-bundle"),
    ("best-etsy-tag-generator-2026", "Best Etsy Tag Generator 2026", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-listing-generator-comparison", "Etsy Listing Generator Comparison", "listing-lab", "listinglab-pro"),
    ("shopify-listing-tool-free", "Shopify Listing Tool Free", "listing-lab", "listinglab-pro"),
    ("print-on-demand-seo-tool", "Print on Demand SEO Tool", "listing-lab", "seller-kit-bundle"),
]

EXTRA_TOPICS = [
    ("etsy-alt-text-generator", "Etsy Alt Text Generator", "listing-lab", "listinglab-pro"),
    ("print-on-demand-listing-tool", "Print on Demand Listing Tool", "listing-lab", "listinglab-pro"),
    ("etsy-shop-seo-tool", "Etsy Shop SEO Tool Free", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("product-title-generator-ecommerce", "Ecommerce Product Title Generator", "listing-lab", "listinglab-pro"),
    ("etsy-keyword-research-free", "Etsy Keyword Research Free", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("shopify-title-generator", "Shopify Title Generator", "listing-lab", "listinglab-pro"),
    ("etsy-listing-optimizer", "Etsy Listing Optimizer Free", "listing-lab", "listinglab-pro"),
    ("handmade-etsy-tags", "Handmade Etsy Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("dropshipping-listing-generator", "Dropshipping Listing Generator", "listing-lab", "listinglab-pro"),
    ("etsy-seo-helper", "Etsy SEO Helper Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
]


def expand_keywords(data: dict) -> None:
    published = set(data.get("published", []))
    existing = {k["slug"] for k in data.get("keywords", [])}
    for slug, title, tool, product in COMPARISON_TOPICS + EXTRA_TOPICS:
        if slug in existing:
            continue
        data.setdefault("keywords", []).append({
            "slug": slug, "title": title, "tool": tool, "product": product,
        })
        existing.add(slug)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=3)
    args = parser.parse_args()

    data = load()
    expand_keywords(data)
    published = set(data.get("published", []))
    count = 0
    for kw in data.get("keywords", []):
        if kw["slug"] in published:
            continue
        out = GUIDES / f"{kw['slug']}.html"
        out.write_text(render_page(kw))
        published.add(kw["slug"])
        data.setdefault("published", []).append(kw["slug"])
        print(f"Published {out.relative_to(ROOT)}")
        count += 1
        if count >= args.batch:
            break
    data["last_run"] = datetime.now(timezone.utc).isoformat()
    save(data)
    if not count:
        print("No new SEO pages (all published)")


if __name__ == "__main__":
    main()