#!/usr/bin/env python3
"""Create temp-mail accounts and store in pipeline/accounts.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from tempmail import create_inbox  # noqa: E402

ACCOUNTS = ROOT / "pipeline" / "accounts.json"


def load_accounts() -> list[dict]:
    if ACCOUNTS.exists():
        return json.loads(ACCOUNTS.read_text())
    return []


def save_accounts(rows: list[dict]) -> None:
    ACCOUNTS.write_text(json.dumps(rows, indent=2) + "\n")


def has_service(rows: list[dict], service: str) -> bool:
    return any(r.get("service") == service and r.get("status") != "failed" for r in rows)


def create_account(service: str, prefix: str | None = None) -> dict:
    prefix = prefix or f"{service[:6]}_"
    inbox = create_inbox(prefix=prefix)
    return {
        "service": service,
        "email": inbox.address,
        "inbox_password": inbox.password,
        "provider": inbox.provider,
        "token": inbox.token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }


def ensure_services(services: list[str]) -> list[dict]:
    rows = load_accounts()
    created = []
    for svc in services:
        if has_service(rows, svc):
            continue
        try:
            entry = create_account(svc)
            rows.append(entry)
            created.append(entry)
            print(f"Created {svc}: {entry['email']}")
        except Exception as e:
            rows.append({
                "service": svc,
                "status": "failed",
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            print(f"Failed {svc}: {e}")
    save_accounts(rows)
    return created


def main() -> None:
    services = ["helio", "transak", "moonpay", "reddit", "gumroad", "support"]
    ensure_services(services)


if __name__ == "__main__":
    main()