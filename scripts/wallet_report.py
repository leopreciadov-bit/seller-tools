#!/usr/bin/env python3
"""Separate buyer SALES from YOUR trades when you ask what's real revenue."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from direct_payment import classify_tx, inbound_amount, token_delta  # noqa: E402

WALLET = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
OUT = ROOT / "pipeline" / "wallet-activity.json"
RPC = "https://api.mainnet-beta.solana.com"


def rpc(method: str, params: list) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", RPC, "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True,
        text=True,
    )
    out = json.loads(r.stdout)
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["result"]


def ts(block_time: int | None) -> str:
    if not block_time:
        return "?"
    return datetime.fromtimestamp(block_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def scan(limit: int = 40) -> dict:
    sigs = rpc("getSignaturesForAddress", [WALLET, {"limit": limit}])
    sales: list[dict] = []
    owner_trades: list[dict] = []
    owner_out: list[dict] = []
    owner_in: list[dict] = []

    for s in sigs:
        if s.get("err"):
            continue
        sig = s["signature"]
        time.sleep(0.25)
        try:
            tx = rpc("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])
        except Exception:
            continue
        if not tx:
            continue
        kind = classify_tx(tx, WALLET)
        inbound, outbound, asset = token_delta(tx, WALLET)
        row = {
            "time": ts(s.get("blockTime")),
            "tx": sig,
            "asset": asset or "—",
            "in": round(inbound, 2),
            "out": round(outbound, 2),
        }
        if kind == "sale":
            amt, ast = inbound_amount(tx, WALLET)
            if amt < 0.5:
                continue
            row["amount_usd"] = round(amt, 2)
            row["asset"] = ast or asset
            sales.append(row)
        elif kind == "owner_trade":
            row["note"] = "Your Drift/DeFi — not a buyer"
            owner_trades.append(row)
        elif kind == "owner_outbound":
            row["note"] = "You sent out (sweep)"
            owner_out.append(row)
        elif kind == "owner_inbound":
            row["note"] = "You moved in — not a buyer"
            owner_in.append(row)

    report = {
        "wallet": WALLET,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "buyer_sales_count": len(sales),
            "buyer_sales_usd": round(sum(x.get("amount_usd", 0) for x in sales), 2),
            "your_trades_count": len(owner_trades),
            "your_sweeps_count": len(owner_out),
            "your_sweeps_usd": round(sum(x.get("out", 0) for x in owner_out), 2),
        },
        "buyer_sales": sales,
        "your_trades": owner_trades,
        "your_sweeps": owner_out,
        "your_inbound": owner_in,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    return report


def print_report(r: dict) -> None:
    s = r["summary"]
    print(f"\n=== Wallet report: {WALLET[:8]}…{WALLET[-6:]} ===\n")
    print(f"BUYER SALES:     {s['buyer_sales_count']}  (${s['buyer_sales_usd']:.2f} direct sends)")
    for x in r["buyer_sales"]:
        print(f"  + ${x.get('amount_usd', 0):.2f} {x['asset']}  {x['time']}  {x['tx'][:20]}…")
    print(f"\nYOUR TRADES:     {s['your_trades_count']}  (Drift/DeFi — not sales)")
    for x in r["your_trades"][:8]:
        print(f"  · in ${x['in']:.2f} out ${x['out']:.2f}  {x['time']}  {x['tx'][:20]}…")
    if len(r["your_trades"]) > 8:
        print(f"  … and {len(r['your_trades']) - 8} more")
    print(f"\nYOUR SWEEPS:     {s['your_sweeps_count']}  (${s['your_sweeps_usd']:.2f} sent out)")
    for x in r["your_sweeps"]:
        print(f"  - ${x['out']:.2f} {x['asset']}  {x['time']}  {x['tx'][:20]}…")
    print()


def main() -> None:
    r = scan()
    print_report(r)


if __name__ == "__main__":
    main()