#!/usr/bin/env python3
"""Detect Payhip card sales via merchant inbox + dashboard (not on-chain)."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import _req, list_messages, read_message  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"
SALES = ROOT / "pipeline" / "sales.json"
ALERT = ROOT / "pipeline" / "BUYER_SALE_ALERT.json"
STATE = ROOT / "pipeline" / "payhip-sales-state.json"

PRICE_MAP = [
    (29.0, "seller-kit-bundle", "Seller Kit Bundle"),
    (19.0, "listinglab-pro", "ListingLab Pro"),
    (14.0, "etsy-tag-finder-pro", "Etsy Tag Finder Pro"),
]
PAYHIP_URLS = {
    "1oqbL": "etsy-tag-finder-pro",
    "BQIej": "listinglab-pro",
    "TH7ju": "seller-kit-bundle",
}


def log(msg: str) -> None:
    print(f"[payhip] {msg}", flush=True)


def payhip_account() -> dict | None:
    for a in reversed(json.loads(ACCOUNTS.read_text()) if ACCOUNTS.exists() else []):
        if a.get("service") == "payhip" and a.get("inbox_password"):
            return a
    return None


def inbox_login(acct: dict):
    from tempmail import Inbox

    token = _req("POST", "https://api.mail.tm/token", {
        "address": acct["email"], "password": acct["inbox_password"],
    })
    return Inbox(acct["email"], acct["inbox_password"], token["token"], "mail.tm")


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"seen_ids": [], "sales": []}


def save_state(st: dict) -> None:
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def guess_product(text: str, amount: float) -> tuple[str, str]:
    low = text.lower()
    for code, slug in PAYHIP_URLS.items():
        if code.lower() in low:
            for price, s, title in PRICE_MAP:
                if s == slug:
                    return slug, title
    for price, slug, title in PRICE_MAP:
        if abs(amount - price) < 2.5 or slug.replace("-", " ") in low or title.lower() in low:
            return slug, title
    for price, slug, title in PRICE_MAP:
        if abs(amount - price) < 2.5:
            return slug, title
    return "unknown", "Seller Tools Pro"


def check_inbox(acct: dict, state: dict) -> list[dict]:
    inbox = inbox_login(acct)
    new_sales: list[dict] = []
    seen = set(state.get("seen_ids", []))

    for msg in list_messages(inbox):
        mid = msg.get("id", "")
        if mid in seen:
            continue
        seen.add(mid)
        subj = (msg.get("subject") or "").lower()
        sender = ""
        f = msg.get("from") or {}
        if isinstance(f, dict):
            sender = (f.get("address") or "").lower()
        if "payhip" not in sender and "payhip" not in subj:
            if not re.search(r"sale|purchase|order|payment|bought", subj):
                continue

        body = read_message(inbox, mid)
        text = f"{subj}\n{body}"
        if not re.search(r"sale|purchase|order|payment|bought|customer", text, re.I):
            continue

        amount = 0.0
        m = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)", text)
        if m:
            amount = float(m.group(1))
        slug, title = guess_product(text, amount)
        entry = {
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "amount": amount or next((p for p, s, _ in PRICE_MAP if s == slug), 0),
            "product": title,
            "slug": slug,
            "asset": "CARD",
            "channel": "payhip",
            "status": "payhip_sale",
            "note": "Payhip card checkout — check Payhip dashboard for buyer email",
            "tx": f"payhip-{mid}",
        }
        new_sales.append(entry)
        log(f"inbox sale: ${entry['amount']} {title}")

    state["seen_ids"] = list(seen)[-500:]
    return new_sales


def check_dashboard(acct: dict, state: dict) -> list[dict]:
    session = ROOT / "pipeline" / "payhip-session.json"
    if not session.exists():
        return []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    new_sales: list[dict] = []
    seen_orders = set(state.get("seen_orders", []))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(storage_state=str(session))
        page = context.new_page()
        for url in ["https://payhip.com/sales", "https://payhip.com/dashboard"]:
            page.goto(url, timeout=45000)
            page.wait_for_timeout(3000)
            if "login" not in page.url:
                break
        html = page.content()
        browser.close()

    for m in re.finditer(r'order[_-]?id["\s:=]+([A-Za-z0-9]+)', html, re.I):
        oid = m.group(1)
        if oid in seen_orders:
            continue
        seen_orders.add(oid)

    for m in re.finditer(r"\$\s*([0-9]+(?:\.[0-9]{2})?)", html):
        amount = float(m.group(1))
        if amount < 10:
            continue
        slug, title = guess_product(html, amount)
        key = f"dash-{amount}-{slug}"
        if key in seen_orders:
            continue
        seen_orders.add(key)
        new_sales.append({
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "amount": amount,
            "product": title,
            "slug": slug,
            "asset": "CARD",
            "channel": "payhip",
            "status": "payhip_sale",
            "note": "Payhip dashboard sale",
            "tx": key,
        })

    state["seen_orders"] = list(seen_orders)[-200:]
    return new_sales


def record_sales(new_sales: list[dict]) -> int:
    if not new_sales:
        return 0
    data = json.loads(SALES.read_text()) if SALES.exists() else {"sales": [], "self_transfers": []}
    existing = {s.get("tx") for s in data.get("sales", [])}
    added = []
    for sale in new_sales:
        if sale["tx"] in existing:
            continue
        data.setdefault("sales", []).append(sale)
        existing.add(sale["tx"])
        added.append(sale)

    if not added:
        return 0

    SALES.write_text(json.dumps(data, indent=2) + "\n")
    ALERT.write_text(json.dumps({
        "time": datetime.now(timezone.utc).isoformat(),
        "count": len(added),
        "sales": added,
        "message": "BUYER SALE — Payhip card payment",
    }, indent=2) + "\n")
    log(f"recorded {len(added)} Payhip sale(s)")
    return len(added)


def main() -> None:
    acct = payhip_account()
    if not acct:
        log("no payhip account")
        return
    state = load_state()
    new: list[dict] = []
    try:
        new.extend(check_inbox(acct, state))
    except Exception as e:
        log(f"inbox error: {e}")
    try:
        new.extend(check_dashboard(acct, state))
    except Exception as e:
        log(f"dashboard error: {e}")
    save_state(state)
    record_sales(new)


if __name__ == "__main__":
    main()