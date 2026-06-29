#!/usr/bin/env python3
"""Generate Google Ads Editor CSV + campaign brief — import at ads.google.com."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "marketing" / "google-ads"
SITE = "https://leopreciadov-bit.github.io/seller-tools"

CAMPAIGNS = [
    {
        "name": "SellerTools - Etsy Tags",
        "budget_daily_usd": 10,
        "final_url": f"{SITE}/etsy-tag-finder/",
        "headlines": [
            "Free Etsy Tag Generator",
            "13 SEO Tags in Seconds",
            "No Signup Required",
        ],
        "descriptions": [
            "Generate exactly 13 Etsy tags. 20-char limit enforced. Long-tail SEO combos.",
            "Free tool for Etsy sellers. Pro unlimited $14 lifetime. Pay USDC or card.",
        ],
        "keywords": [
            "etsy tag generator",
            "etsy tags tool",
            "etsy seo tags",
            "etsy keyword generator",
            "free etsy tags",
            "[etsy tag finder]",
            "etsy listing tags",
        ],
    },
    {
        "name": "SellerTools - Listing Lab",
        "budget_daily_usd": 10,
        "final_url": f"{SITE}/listing-lab/",
        "headlines": [
            "Etsy Listing Generator Free",
            "Titles + Descriptions + Tags",
            "Shopify Mode Included",
        ],
        "descriptions": [
            "Stop spending an hour per listing. SEO copy in one click.",
            "5 free generations daily. Pro $19 lifetime. Crypto checkout live.",
        ],
        "keywords": [
            "etsy listing generator",
            "shopify description generator",
            "product listing generator",
            "etsy title generator",
            "[listing generator etsy]",
            "etsy description generator",
        ],
    },
]


def write_csv() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "campaigns-import.csv"
    rows = []
    for camp in CAMPAIGNS:
        for kw in camp["keywords"]:
            rows.append({
                "Campaign": camp["name"],
                "Campaign daily budget": camp["budget_daily_usd"],
                "Campaign type": "Search",
                "Networks": "Google search",
                "Bid strategy type": "Maximize conversions",
                "Final URL": camp["final_url"],
                "Keyword": kw,
                "Criterion type": "Keyword",
                "Headline 1": camp["headlines"][0],
                "Headline 2": camp["headlines"][1],
                "Headline 3": camp["headlines"][2],
                "Description 1": camp["descriptions"][0],
                "Description 2": camp["descriptions"][1],
            })
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    return path


def write_brief() -> Path:
    path = OUT_DIR / "LAUNCH_STEPS.md"
    lines = [
        "# Google Ads — Launch in 10 minutes",
        "",
        f"**Site:** {SITE}",
        "",
        "## Steps",
        "1. Go to https://ads.google.com → New campaign → Sales → Search",
        "2. Import `campaigns-import.csv` via Tools → Bulk actions → Upload",
        "3. Set billing (card). Start **$10/day per campaign** ($20 total)",
        "4. Conversion: track clicks to `/listing-lab/` and `/etsy-tag-finder/`",
        "5. Pause keywords with 0 sales after 200 clicks",
        "",
        "## Campaigns",
    ]
    for c in CAMPAIGNS:
        lines.append(f"### {c['name']} — ${c['budget_daily_usd']}/day")
        lines.append(f"- URL: {c['final_url']}")
        lines.append(f"- Keywords: {', '.join(c['keywords'][:4])}…")
        lines.append("")
    lines += [
        "## Expected",
        "- 2% conv → ~20 clicks/sale → ~$15–40 CPC need tuning",
        "- First sale often within 48h of ads going live",
        "",
        "Re-run: `python3 scripts/google_ads_launch.py`",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    csv_path = write_csv()
    brief = write_brief()
    (OUT_DIR / "campaigns.json").write_text(json.dumps(CAMPAIGNS, indent=2) + "\n")
    print(f"Wrote {csv_path}")
    print(f"Wrote {brief}")
    print("Import CSV at ads.google.com → Tools → Bulk upload")


if __name__ == "__main__":
    main()