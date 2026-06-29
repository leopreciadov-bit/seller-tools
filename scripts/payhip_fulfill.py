#!/usr/bin/env python3
"""Upload license keys to Payhip products so card buyers get keys automatically."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
SESSION = ROOT / "pipeline" / "payhip-session.json"

PRODUCTS = [
    {"slug": "etsy-tag-finder-pro", "name": "Etsy Tag Finder Pro", "keys": "gumroad/upload/etsy-tag-finder-pro-keys.txt", "url": "https://payhip.com/b/1oqbL"},
    {"slug": "listinglab-pro", "name": "ListingLab Pro", "keys": "gumroad/upload/listinglab-pro-keys.txt", "url": "https://payhip.com/b/BQIej"},
    {"slug": "seller-kit-bundle", "name": "Seller Kit Bundle", "keys": "gumroad/upload/seller-kit-bundle-keys.txt", "url": "https://payhip.com/b/TH7ju"},
]


def main() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(
            storage_state=str(SESSION) if SESSION.exists() else None,
            viewport={"width": 1400, "height": 1200},
        )
        page = ctx.new_page()
        for prod in PRODUCTS:
            page.goto(prod["url"], timeout=60000)
            page.wait_for_timeout(3000)
            edit = re.search(r"(https://payhip\.com/product/edit/[A-Za-z0-9]+)", page.content())
            if not edit:
                page.goto("https://payhip.com/products", timeout=60000)
                page.wait_for_timeout(3000)
                edit = re.search(r"(https://payhip\.com/product/edit/[A-Za-z0-9]+)", page.content())
            if not edit:
                print(f"[fulfill] {prod['slug']}: no edit URL")
                continue
            page.goto(edit.group(1), timeout=60000)
            page.wait_for_timeout(4000)
            keys = ROOT / prod["keys"]
            if keys.exists():
                try:
                    page.set_input_files('input[type="file"]', str(keys))
                except Exception as e:
                    print(f"[fulfill] {prod['slug']}: upload {e}")
            for ta in page.locator("textarea").all()[:2]:
                try:
                    if ta.is_visible():
                        ta.fill(f"License key included. Unlock at {SITE}")
                except Exception:
                    pass
            page.evaluate('document.querySelector("form")?.submit()')
            page.wait_for_timeout(5000)
            print(f"[fulfill] {prod['slug']}: ok")
        ctx.storage_state(path=str(SESSION))
        browser.close()


if __name__ == "__main__":
    main()