#!/usr/bin/env python3
"""Prepare Gumroad products: license uploads + delivery copy. Optional API create."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPLOAD = ROOT / "gumroad" / "upload"
PIPELINE = ROOT / "pipeline"
SITE = "https://leopreciadov-bit.github.io/seller-tools"

PRODUCTS = [
    {
        "id": "listing-lab",
        "slug": "listinglab-pro",
        "price": 19,
        "license_file": "licenses-listing-lab.txt",
        "upload_name": "listinglab-pro-keys.txt",
        "title": "ListingLab Pro — Unlimited Listing Generator",
        "unlock_url": f"{SITE}/listing-lab/",
        "key_hint": "LISTING-XXXX-XXXX",
    },
    {
        "id": "etsy-tag-finder",
        "slug": "etsy-tag-finder-pro",
        "price": 14,
        "license_file": "licenses-etsy-tag-finder.txt",
        "upload_name": "etsy-tag-finder-pro-keys.txt",
        "title": "Etsy Tag Finder Pro — 13 Perfect SEO Tags",
        "unlock_url": f"{SITE}/etsy-tag-finder/",
        "key_hint": "TAGFINDER-XXXX-XXXX",
    },
    {
        "id": "bundle",
        "slug": "seller-kit-bundle",
        "price": 29,
        "license_file": "licenses-bundle.txt",
        "upload_name": "seller-kit-bundle-keys.txt",
        "title": "Seller Kit — ListingLab Pro + Etsy Tag Finder Pro",
        "unlock_url": SITE,
        "key_hint": "SELLERKIT-XXXX-XXXX (unlocks BOTH tools)",
    },
]


def delivery_email(product: dict) -> str:
    if product["id"] == "bundle":
        return f"""Thanks for purchasing the Seller Kit!

Your license key (unlocks BOTH tools) is in this email / your Gumroad library:

ListingLab: {SITE}/listing-lab/
Tag Finder: {SITE}/etsy-tag-finder/

Paste the key into "Unlock Pro" on either tool — it works on both.
"""
    return f"""Thanks for purchasing {product['title']}!

Your license key is in this email / your Gumroad library:

Unlock at: {product['unlock_url']}
Scroll to "Unlock Pro" and paste your key.
"""


def prepare_uploads() -> None:
    UPLOAD.mkdir(parents=True, exist_ok=True)
    manifest = []

    for p in PRODUCTS:
        src = PIPELINE / p["license_file"]
        if not src.exists():
            print(f"Missing {src} — run: python3 scripts/generate_licenses.py --product {p['id']}")
            sys.exit(1)

        dst = UPLOAD / p["upload_name"]
        shutil.copy2(src, dst)

        email_path = UPLOAD / f"{p['slug']}-delivery-email.txt"
        email_path.write_text(delivery_email(p))

        keys = [k.strip() for k in src.read_text().splitlines() if k.strip()]
        manifest.append(
            {
                "slug": p["slug"],
                "price_usd": p["price"],
                "title": p["title"],
                "keys_available": len(keys),
                "license_upload": str(dst.relative_to(ROOT)),
                "delivery_email": str(email_path.relative_to(ROOT)),
                "gumroad_url": f"https://YOURNAME.gumroad.com/l/{p['slug']}",
            }
        )
        print(f"✓ {p['title']}: {len(keys)} keys → {dst.name}")

    (UPLOAD / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nUpload files ready in {UPLOAD.relative_to(ROOT)}/")


def try_api_create() -> None:
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("\nNo GUMROAD_ACCESS_TOKEN — manual create (see gumroad/COPY_PASTE_EVERYTHING.md)")
        return

    try:
        import urllib.error
        import urllib.parse
        import urllib.request
    except ImportError:
        return

    # Gumroad API is read-heavy; product create may not be supported.
    req = urllib.request.Request(
        "https://api.gumroad.com/v2/products",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"\nGumroad API connected. Existing products: {len(data.get('products', []))}")
            print("Product creation via API is not supported — use COPY_PASTE_EVERYTHING.md")
    except urllib.error.HTTPError as e:
        print(f"\nGumroad API error ({e.code}). Check token at gumroad.com/settings/advanced")


def write_gumroad_js(cfg: dict) -> None:
    out = ROOT / "site" / "assets" / "gumroad.js"
    user = cfg.get("username") or "YOURNAME"
    products = {}
    for slug, p in cfg.get("products", {}).items():
        url = p.get("url") or f"https://{user}.gumroad.com/l/{p.get('slug', slug)}"
        products[slug] = {"title": p.get("title", slug), "price": p.get("price_usd", 0), "url": url}
    payload = {"username": user if user != "YOURNAME" else None, "products": products}
    out.write_text("window.GUMROAD = " + json.dumps(payload, indent=2) + ";\n")
    print(f"Wrote {out.relative_to(ROOT)}")


def main() -> None:
    prepare_uploads()
    cfg_path = PIPELINE / "gumroad.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    write_gumroad_js(cfg)
    try_api_create()
    print("\nNext: Gumroad → New Product → Digital → Content → License keys → upload txt from gumroad/upload/")


if __name__ == "__main__":
    main()