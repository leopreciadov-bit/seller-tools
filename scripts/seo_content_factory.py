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
    <p>Free tool for Etsy and Shopify sellers. Upgrade with <strong>card or crypto</strong> — all payments settle to the seller Solana wallet.</p>
    <p><a class="btn" href="{tool_path(tool)}">Try free tool →</a></p>
    <p>Pro unlock: <span data-crypto-buy="{product}"></span></p>
    <p><a href="{SITE}/recover/">Paid? Recover your license key</a></p>
    <p class="muted">Seller Tools · <a href="{SITE}/">Home</a></p>
  </main>
</body>
</html>
"""


def main() -> None:
    data = load()
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
        if count >= 3:
            break
    data["last_run"] = datetime.now(timezone.utc).isoformat()
    save(data)
    if not count:
        print("No new SEO pages (all published)")


if __name__ == "__main__":
    main()