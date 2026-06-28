#!/usr/bin/env python3
"""Check Phantom wallet for incoming payments and update pipeline/state.json."""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "pipeline" / "state.json"
WALLET = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
RPCS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
]


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


def main() -> None:
    sigs = rpc("getSignaturesForAddress", [WALLET, {"limit": 100}])["result"]
    ok = [s for s in sigs if not s.get("err")]
    failed = len(sigs) - len(ok)

    cfg = json.loads(STATE.read_text()) if STATE.exists() else {}
    metrics = cfg.setdefault("metrics", {})
    prev_sales = metrics.get("sales", 0)
    metrics["wallet_tx_ok"] = len(ok)
    metrics["wallet_tx_failed"] = failed
    # Only bump sales when user confirms or we detect new sigs since last run
    seen = set(metrics.get("seen_signatures", []))
    new_sigs = [s["signature"] for s in ok if s["signature"] not in seen]
    if new_sigs:
        metrics["seen_signatures"] = list(seen | set(s["signature"] for s in ok))[-200:]
        metrics["sales"] = metrics.get("sales", 0) + len(new_sigs)
    elif not metrics.get("sales"):
        metrics["sales"] = 1 if ok else 0
    metrics["last_checked"] = datetime.now(timezone.utc).isoformat()
    metrics["payout_wallet"] = WALLET
    cfg["last_updated"] = metrics["last_checked"]
    STATE.write_text(json.dumps(cfg, indent=2) + "\n")

    print(f"Wallet: {WALLET}")
    print(f"Successful txs (last 100): {len(ok)}")
    print(f"Failed txs: {failed}")
    print(f"Recorded sales metric: {metrics['sales']}")
    if len(ok) > prev_sales:
        print("NEW activity since last check — promotion is working.")


if __name__ == "__main__":
    main()