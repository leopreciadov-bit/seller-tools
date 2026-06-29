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


PAYHIP = {
    "etsy-tag-finder-pro": "https://payhip.com/b/1oqbL",
    "listinglab-pro": "https://payhip.com/b/BQIej",
    "seller-kit-bundle": "https://payhip.com/b/TH7ju",
}


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
    <p>Pro unlock: <a class="btn" href="{PAYHIP.get(product, f'{SITE}/deals/')}" target="_blank" rel="noopener">Buy with Card</a> <span data-crypto-buy="{product}"></span></p>
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

# High-intent buyer searches (batch 2)
BUYER_INTENT_TOPICS = [
    ("etsy-tag-generator-free", "Etsy Tag Generator Free — 13 Tags", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-listing-generator-free-tool", "Etsy Listing Generator Free Tool", "listing-lab", "listinglab-pro"),
    ("marmalead-free-alternative-2026", "Marmalead Free Alternative 2026", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("erank-free-alternative-2026", "eRank Free Alternative 2026", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-seo-tool-no-subscription", "Etsy SEO Tool No Subscription", "etsy-tag-finder", "seller-kit-bundle"),
    ("etsy-title-and-tags-generator", "Etsy Title and Tags Generator", "listing-lab", "listinglab-pro"),
    ("shopify-seo-description-tool", "Shopify SEO Description Tool Free", "listing-lab", "listinglab-pro"),
    ("etsy-long-tail-keywords-tool", "Etsy Long Tail Keywords Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-listing-copywriter-free", "Etsy Listing Copywriter Free", "listing-lab", "listinglab-pro"),
    ("print-on-demand-etsy-tags", "Print on Demand Etsy Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("cricut-etsy-listing-generator", "Cricut Etsy Listing Generator", "listing-lab", "listinglab-pro"),
    ("jewelry-etsy-tags-generator", "Jewelry Etsy Tags Generator", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("vintage-etsy-seo-tags", "Vintage Etsy SEO Tags Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-digital-product-listing-tool", "Etsy Digital Product Listing Tool", "listing-lab", "listinglab-pro"),
    ("shopify-dropshipping-listing-writer", "Shopify Dropshipping Listing Writer", "listing-lab", "listinglab-pro"),
    ("etsy-13-tags-enforcer", "Etsy 13 Tags Enforcer Tool", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-keyword-tool-for-handmade", "Etsy Keyword Tool for Handmade Sellers", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-product-description-template-free", "Etsy Product Description Template Free", "listing-lab", "listinglab-pro"),
    ("best-etsy-listing-tool-2026", "Best Etsy Listing Tool 2026", "listing-lab", "seller-kit-bundle"),
    ("etsy-seller-tools-bundle", "Etsy Seller Tools Bundle Lifetime", "listing-lab", "seller-kit-bundle"),
    ("alura-free-alternative", "Alura Free Alternative for Etsy", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("etsy-hunt-free-alternative", "Etsy Hunt Free Alternative", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("salehoo-etsy-listing-tool", "SaleHoo Etsy Listing Tool Alternative", "listing-lab", "listinglab-pro"),
    ("etsy-seo-checklist-tool", "Etsy SEO Checklist Tool Free", "etsy-tag-finder", "etsy-tag-finder-pro"),
    ("shopify-product-title-seo", "Shopify Product Title SEO Generator", "listing-lab", "listinglab-pro"),
]


def expand_keywords(data: dict) -> None:
    published = set(data.get("published", []))
    existing = {k["slug"] for k in data.get("keywords", [])}
    for slug, title, tool, product in COMPARISON_TOPICS + EXTRA_TOPICS + BUYER_INTENT_TOPICS:
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