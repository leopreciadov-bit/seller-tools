#!/usr/bin/env python3
"""Regenerate sitemap.xml with absolute URLs after deploy."""

import argparse
from pathlib import Path

PAGES = [
    ("/", "weekly", "1.0"),
    ("/listing-lab/", "weekly", "0.9"),
    ("/etsy-tag-finder/", "weekly", "0.9"),
    ("/guides/how-to-choose-etsy-tags.html", "monthly", "0.8"),
    ("/guides/etsy-listing-description-template.html", "monthly", "0.8"),
    ("/guides/shopify-product-listing-seo.html", "monthly", "0.8"),
]

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "sitemap.xml"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="e.g. https://user.github.io/repo")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, freq, priority in PAGES:
        lines.append("  <url>")
        lines.append(f"    <loc>{base}{path}</loc>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT} with base {base}")


if __name__ == "__main__":
    main()