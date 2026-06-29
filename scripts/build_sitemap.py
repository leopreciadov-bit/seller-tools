#!/usr/bin/env python3
"""Regenerate sitemap.xml, feed.xml, and IndexNow URL list from all site pages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = SITE / "sitemap.xml"
FEED = SITE / "feed.xml"
INDEXNOW = ROOT / "pipeline" / "indexnow.json"

PRIORITY = {
    "/": ("weekly", "1.0"),
    "/listing-lab/": ("weekly", "0.95"),
    "/etsy-tag-finder/": ("weekly", "0.95"),
    "/deals/": ("daily", "0.95"),
    "/embed/": ("monthly", "0.7"),
    "/buy/etsy-tag-finder-pro/": ("daily", "0.95"),
    "/buy/listinglab-pro/": ("daily", "0.95"),
    "/buy/seller-kit-bundle/": ("daily", "0.95"),
    "/recover/": ("monthly", "0.5"),
}


def discover_paths() -> list[str]:
    paths = []
    for html in sorted(SITE.rglob("*.html")):
        rel = html.relative_to(SITE)
        if rel.name == "google5ddb8b4ec852634c.html":
            continue
        if rel.name == "index.html":
            path = "/" + str(rel.parent).replace("\\", "/")
            path = path if path != "/." else "/"
            if not path.endswith("/"):
                path += "/"
        else:
            path = "/" + str(rel).replace("\\", "/")
        paths.append(path)
    return sorted(set(paths))


def page_title(path: str) -> str:
    if path == "/":
        return "Seller Tools — Free Etsy & Shopify Listing Generators"
    if path == "/listing-lab/":
        return "ListingLab — Free Listing Generator"
    if path == "/etsy-tag-finder/":
        return "Etsy Tag Finder — 13 Tag Generator"
    if path == "/deals/":
        return "Seller Tools Pro — Launch Deals"
    if path.startswith("/guides/"):
        slug = path.split("/")[-1].replace(".html", "").replace("-", " ").title()
        return slug
    return path.strip("/").replace("-", " ").title()


def write_sitemap(base: str, paths: list[str]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for path in paths:
        freq, priority = PRIORITY.get(path, ("monthly", "0.75"))
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(base + path)}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    OUT.write_text("\n".join(lines))


def write_feed(base: str, paths: list[str]) -> None:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for path in paths[:40]:
        items.append(
            "    <item>\n"
            f"      <title>{escape(page_title(path))}</title>\n"
            f"      <link>{escape(base + path)}</link>\n"
            f"      <guid isPermaLink=\"true\">{escape(base + path)}</guid>\n"
            f"      <pubDate>{now}</pubDate>\n"
            "    </item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Seller Tools</title>\n"
        f"    <link>{escape(base + '/')}</link>\n"
        "    <description>Free Etsy and Shopify listing generators for marketplace sellers</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )
    FEED.write_text(feed)


def sync_indexnow(base: str, paths: list[str]) -> None:
    if not INDEXNOW.exists():
        return
    cfg = json.loads(INDEXNOW.read_text())
    urls = [base + p for p in paths]
    cfg["submitted"] = urls
    INDEXNOW.write_text(json.dumps(cfg, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="e.g. https://user.github.io/repo")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    paths = discover_paths()
    write_sitemap(base, paths)
    write_feed(base, paths)
    sync_indexnow(base, paths)
    print(f"Wrote {OUT} ({len(paths)} URLs), {FEED}, updated IndexNow")


if __name__ == "__main__":
    main()