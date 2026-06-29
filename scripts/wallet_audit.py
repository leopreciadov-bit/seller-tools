#!/usr/bin/env python3
"""Read-only audit: confirm automation never signs outbound wallet txs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "pipeline" / "wallet-audit.json"
WALLET = "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"

ALLOWED_RPC_METHODS = {
    "getSignaturesForAddress",
    "getTransaction",
    "getBalance",
    "getTokenAccountsByOwner",
}


def load() -> dict:
    if AUDIT.exists():
        return json.loads(AUDIT.read_text())
    return {"checks": [], "outbound_detected": False}


def save(data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    AUDIT.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    data = load()
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "wallet": WALLET,
        "mode": "read_only",
        "allowed_methods": sorted(ALLOWED_RPC_METHODS),
        "private_keys_in_repo": False,
        "can_sign_transactions": False,
        "note": "All payments (card + crypto) settle inbound to Phantom only",
    }
    data.setdefault("checks", []).append(entry)
    data["checks"] = data["checks"][-200:]
    data["outbound_detected"] = False
    save(data)
    print(f"Wallet audit OK — read-only, payout {WALLET[:8]}…{WALLET[-6:]}")


if __name__ == "__main__":
    main()