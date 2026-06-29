#!/usr/bin/env python3
"""Check Phantom wallet for payments; auto-reserve license keys on new sales."""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from direct_payment import classify_tx, inbound_amount, is_direct_payment, token_delta  # noqa: E402

OWNER_ACTIVITY = ROOT / "pipeline" / "owner-trades.json"
BUYER_ALERT = ROOT / "pipeline" / "BUYER_SALE_ALERT.json"
STATE = ROOT / "pipeline" / "state.json"
SALES_LOG = ROOT / "pipeline" / "sales.json"
SOLD_KEYS = ROOT / "pipeline" / "sold-keys.json"
CRYPTO_CFG = ROOT / "pipeline" / "crypto.json"
WALLET = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
LAMPORTS = 1_000_000_000
SELF_TRANSFERS = {78.51}
RPCS = [
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana",
    "https://api.mainnet-beta.solana.com",
]
LICENSE_MAP = {
    "listinglab-pro": ROOT / "pipeline/licenses-listing-lab.txt",
    "etsy-tag-finder-pro": ROOT / "pipeline/licenses-etsy-tag-finder.txt",
    "seller-kit-bundle": ROOT / "pipeline/licenses-bundle.txt",
}
RECOVER_URL = "https://leopreciadov-bit.github.io/seller-tools/recover/"


def rpc(method: str, params: list) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last_err = None
    for url in RPCS:
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as r:
                out = json.loads(r.read())
            if out.get("error"):
                last_err = out["error"]
                continue
            return out
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(last_err)


def fetch_sol_price() -> float:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        return float(data.get("solana", {}).get("usd", 0))
    except Exception:
        return 0.0


def load_products() -> list[tuple[float, str, str]]:
    if CRYPTO_CFG.exists():
        cfg = json.loads(CRYPTO_CFG.read_text())
        rows = []
        for slug, p in cfg.get("products", {}).items():
            rows.append((float(p["price_usd"]), slug, p.get("title", slug)))
        rows.sort(key=lambda x: -x[0])
        return rows
    return [
        (29.0, "seller-kit-bundle", "Seller Kit Bundle"),
        (19.0, "listinglab-pro", "ListingLab Pro"),
        (14.0, "etsy-tag-finder-pro", "Etsy Tag Finder Pro"),
    ]


def match_product(amount: float, products: list[tuple[float, str, str]]) -> tuple[str, str, float] | None:
    for price, slug, title in products:
        if price * 0.85 <= amount <= price * 1.15:
            return slug, title, price
    return None


def load_reserved_keys() -> set[str]:
    reserved: set[str] = set()
    if SOLD_KEYS.exists():
        for entry in json.loads(SOLD_KEYS.read_text()).values():
            if entry.get("key"):
                reserved.add(entry["key"])
    if SALES_LOG.exists():
        for s in json.loads(SALES_LOG.read_text()).get("sales", []):
            if s.get("key"):
                reserved.add(s["key"])
    return reserved


def next_license(slug: str, reserved: set[str]) -> str | None:
    path = LICENSE_MAP.get(slug)
    if not path or not path.exists():
        return None
    for line in path.read_text().splitlines():
        key = line.strip()
        if key and key not in reserved:
            return key
    return None


def detect_new_sales() -> list[dict]:
    sold = json.loads(SOLD_KEYS.read_text()) if SOLD_KEYS.exists() else {}
    known_sigs = set(sold.keys())
    products = load_products()
    sol_price = fetch_sol_price()
    reserved = load_reserved_keys()
    new_sales: list[dict] = []

    sigs = rpc("getSignaturesForAddress", [WALLET, {"limit": 8}])["result"]
    cutoff = time.time() - 86400 * 7
    for s in sigs:
        if s.get("err"):
            continue
        if s.get("blockTime") and s["blockTime"] < cutoff:
            continue
        sig = s["signature"]
        if sig in known_sigs:
            continue
        try:
            tx = rpc("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])["result"]
        except Exception:
            continue
        if not tx or not is_direct_payment(tx, WALLET):
            continue
        amount, asset = inbound_amount(tx, WALLET, sol_price)
        if amount <= 0 or round(amount, 2) in SELF_TRANSFERS:
            continue
        matched = match_product(amount, products)
        if not matched:
            continue
        slug, title, list_price = matched
        key = next_license(slug, reserved)
        if not key:
            continue
        reserved.add(key)
        block_time = s.get("blockTime")
        ts = (
            datetime.fromtimestamp(block_time, tz=timezone.utc).isoformat()
            if block_time
            else datetime.now(timezone.utc).isoformat()
        )
        entry = {
            "time": ts,
            "amount": round(amount, 2),
            "product": title,
            "slug": slug,
            "asset": asset or "USDC",
            "status": "recovery_ready",
            "note": "Direct send to merchant wallet only",
            "key": key,
            "tx": sig,
            "recover_url": RECOVER_URL,
            "payment_type": "card_or_crypto",
        }
        sold[sig] = {
            "key": key,
            "product": slug,
            "title": title,
            "amount": round(amount, 2),
            "time": ts,
            "status": "ready_to_claim",
        }
        new_sales.append(entry)
        known_sigs.add(sig)

    if new_sales:
        alert = {
            "time": datetime.now(timezone.utc).isoformat(),
            "count": len(new_sales),
            "sales": new_sales,
            "message": "BUYER SALE — direct payment to wallet",
        }
        BUYER_ALERT.write_text(json.dumps(alert, indent=2) + "\n")
        SOLD_KEYS.write_text(json.dumps(sold, indent=2) + "\n")
        log_data = json.loads(SALES_LOG.read_text()) if SALES_LOG.exists() else {"sales": [], "self_transfers": []}
        existing_txs = {x.get("tx") for x in log_data.get("sales", [])}
        for sale in new_sales:
            if sale["tx"] not in existing_txs:
                log_data.setdefault("sales", []).append(sale)
        SALES_LOG.write_text(json.dumps(log_data, indent=2) + "\n")
        subprocess_rebuild()

    return new_sales


def reaudit_sales() -> int:
    """Drop sales that are not simple direct sends to the merchant wallet."""
    if not SALES_LOG.exists():
        return 0
    log = json.loads(SALES_LOG.read_text())
    kept: list[dict] = []
    excluded: list[dict] = []
    sold = json.loads(SOLD_KEYS.read_text()) if SOLD_KEYS.exists() else {}
    sol_price = fetch_sol_price()

    for sale in log.get("sales", []):
        sig = sale.get("tx")
        if not sig:
            excluded.append({**sale, "exclude_reason": "no_tx"})
            continue
        try:
            tx = rpc("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])["result"]
        except Exception:
            kept.append(sale)
            continue
        if tx and is_direct_payment(tx, WALLET):
            amt, _ = inbound_amount(tx, WALLET, sol_price)
            if amt > 0:
                kept.append(sale)
                continue
        excluded.append({**sale, "exclude_reason": "not_direct_payment"})
        sold.pop(sig, None)

    if len(kept) != len(log.get("sales", [])):
        log["sales"] = kept
        log["excluded_sales"] = excluded
        SALES_LOG.write_text(json.dumps(log, indent=2) + "\n")
        SOLD_KEYS.write_text(json.dumps(sold, indent=2) + "\n")
        subprocess_rebuild()
    return len(excluded)


def subprocess_rebuild() -> None:
    import subprocess
    import sys

    script = ROOT / "scripts" / "crypto_setup.py"
    if script.exists():
        subprocess.run([sys.executable, str(script), "build"], cwd=ROOT, check=False)


def print_owner_vs_sales() -> None:
    import subprocess

    script = ROOT / "scripts" / "wallet_report.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=False)


def main() -> None:
    import argparse
    import subprocess

    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Skip reaudit and wallet report")
    parser.add_argument("--no-payhip", action="store_true", help="Skip Payhip inbox check")
    parser.add_argument("--skip-detect", action="store_true", help="Skip on-chain sale scan")
    args = parser.parse_args()

    if not args.no_payhip:
        payhip = ROOT / "scripts" / "payhip_sales.py"
        if payhip.exists():
            subprocess.run([sys.executable, str(payhip)], cwd=ROOT, check=False, timeout=30)

    ok: list = []
    failed = 0
    removed = 0
    new_sales: list[dict] = []

    if args.skip_detect:
        log_data = json.loads(SALES_LOG.read_text()) if SALES_LOG.exists() else {"sales": []}
        print(f"Wallet: {WALLET}")
        print(f"Confirmed sales: {len(log_data.get('sales', []))}")
        print(f"Revenue (confirmed): ${sum(s.get('amount', 0) for s in log_data.get('sales', [])):.2f}")
        return

    sigs = rpc("getSignaturesForAddress", [WALLET, {"limit": 8 if args.quick else 100}])["result"]
    ok = [s for s in sigs if not s.get("err")]
    failed = len(sigs) - len(ok)

    if not args.quick:
        removed = reaudit_sales()
        if removed:
            print(f"Re-audit: excluded {removed} non-direct payment(s)")
    new_sales = detect_new_sales()

    cfg = json.loads(STATE.read_text()) if STATE.exists() else {}
    metrics = cfg.setdefault("metrics", {})
    metrics["wallet_tx_ok"] = len(ok)
    metrics["wallet_tx_failed"] = failed
    metrics["wallet_activity"] = len(ok)
    metrics["last_checked"] = datetime.now(timezone.utc).isoformat()
    metrics["payout_wallet"] = WALLET
    cfg["last_updated"] = metrics["last_checked"]
    STATE.write_text(json.dumps(cfg, indent=2) + "\n")

    print(f"Wallet: {WALLET}")
    print(f"Successful txs (last 100): {len(ok)}")
    print(f"Failed txs: {failed}")
    log = json.loads(SALES_LOG.read_text()) if SALES_LOG.exists() else {}
    sales = log.get("sales", [])
    revenue = sum(s.get("amount", 0) for s in sales)
    print(f"Confirmed sales: {len(sales)}")
    print(f"Revenue (confirmed): ${revenue:.2f}")
    for s in sales:
        print(f"  - ${s.get('amount')} {s.get('product', '?')} ({s.get('time', '')})")
    for x in log.get("self_transfers", []):
        print(f"  (self-transfer ${x.get('amount')} — excluded)")
    if new_sales:
        print(f"NEW BUYER SALE(S): {len(new_sales)}")
        for s in new_sales:
            print(f"  + ${s['amount']} {s['product']} key={s['key']}")
    if not args.quick:
        print("\n--- Your trades vs buyer sales ---")
        print_owner_vs_sales()


if __name__ == "__main__":
    main()