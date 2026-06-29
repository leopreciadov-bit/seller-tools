#!/usr/bin/env python3
"""Monitor support inbox and draft buyer recovery replies."""

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
STATE = ROOT / "pipeline" / "support-inbox.json"
REPLY = ROOT / "marketing" / "BUYER_RECOVERY_MESSAGE.txt"
SALES = ROOT / "pipeline" / "sales.json"

BUYER_HINTS = re.compile(
    r"license|listinglab|paid|payment|purchase|unlock|key|pro|crypto|usdc|phantom|refund|help|stuck",
    re.I,
)
SKIP_FROM = re.compile(r"noreply@hel\.io|moonpay|mail\.tm|no-?reply", re.I)


def log(msg: str) -> None:
    print(f"[support] {msg}", flush=True)


def support_account() -> dict:
    accounts = json.loads(ACCOUNTS.read_text())
    for a in accounts:
        if a.get("service") == "support":
            return a
    helio = next((a for a in accounts if a.get("service") == "helio" and a.get("email", "").startswith("seller0")), None)
    if not helio:
        raise SystemExit("No support/helio inbox in accounts.json")
    return {
        "service": "support",
        "email": helio["email"],
        "inbox_password": helio["inbox_password"],
        "provider": helio.get("provider", "mail.tm"),
    }


def login(account: dict):
    from tempmail import Inbox

    token_data = _req(
        "POST",
        "https://api.mail.tm/token",
        {"address": account["email"], "password": account["inbox_password"]},
    )
    return Inbox(
        address=account["email"],
        password=account["inbox_password"],
        token=token_data["token"],
        provider=account.get("provider", "mail.tm"),
    )


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"seen_ids": [], "tickets": [], "last_check": None}


def save_state(state: dict) -> None:
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def sender(msg: dict) -> str:
    f = msg.get("from") or {}
    return f.get("address", "") if isinstance(f, dict) else str(f)


def main() -> None:
    account = support_account()
    inbox = login(account)
    state = load_state()
    seen = set(state.get("seen_ids", []))
    reply_template = REPLY.read_text().strip() if REPLY.exists() else ""

    log(f"Inbox: {account['email']}")
    messages = list_messages(inbox)
    new_buyer = 0

    for msg in messages:
        mid = msg.get("id", "")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        from_addr = sender(msg)
        subject = msg.get("subject", "")
        intro = msg.get("intro", "") or ""

        if SKIP_FROM.search(from_addr):
            continue

        full = read_message(inbox, mid)
        body = (full.get("text") or "") + (full.get("html") or "")
        if isinstance(body, list):
            body = " ".join(str(x) for x in body)

        is_buyer = bool(BUYER_HINTS.search(subject + intro + body))
        ticket = {
            "id": mid,
            "from": from_addr,
            "subject": subject,
            "at": msg.get("createdAt", ""),
            "is_buyer": is_buyer,
            "preview": intro[:200],
        }
        state["tickets"].insert(0, ticket)
        state["tickets"] = state["tickets"][:50]

        if is_buyer:
            new_buyer += 1
            log(f"BUYER EMAIL from {from_addr}: {subject}")
            draft_path = ROOT / "pipeline" / f"reply-draft-{mid[:8]}.txt"
            draft_path.write_text(
                f"To: {from_addr}\nSubject: Re: {subject}\n\n{reply_template}\n"
            )
            log(f"Draft saved: {draft_path.name}")

    state["seen_ids"] = list(seen)[-500:]
    save_state(state)

    log(f"Checked {len(messages)} messages — {new_buyer} new buyer ticket(s)")
    if new_buyer == 0:
        log("No buyer emails yet. Support inbox ready at " + account["email"])

    # ensure support account logged in accounts.json
    accounts = json.loads(ACCOUNTS.read_text())
    if not any(a.get("service") == "support" for a in accounts):
        accounts.append({
            "service": "support",
            "email": account["email"],
            "inbox_password": account["inbox_password"],
            "provider": account.get("provider", "mail.tm"),
            "url": "https://mail.tm/",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        ACCOUNTS.write_text(json.dumps(accounts, indent=2) + "\n")


if __name__ == "__main__":
    main()