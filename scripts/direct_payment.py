#!/usr/bin/env python3
"""Only count simple direct sends TO the merchant wallet (no Drift/bridges)."""

from __future__ import annotations

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
LAMPORTS = 1_000_000_000

BLOCKED_PROGRAMS = {
    "PERPHjGBqRHArX4DySjwM6UJHiR3sWAatqfdBS2qQJu",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
    "DoVEsk76QybCEHQGzkvYPWLQu9gzNoZZZt3TPiL597e",
}

BLOCKED_LOG_MARKERS = (
    "InstantDecreasePosition",
    "InstantIncreasePosition",
    "SwapWithTokenLedger",
    "shared_accounts_route",
    "Instruction: Route",
)


def account_keys(tx: dict) -> list[str]:
    keys = (tx.get("transaction") or {}).get("message", {}).get("accountKeys") or []
    out = []
    for k in keys:
        out.append(k if isinstance(k, str) else k.get("pubkey", ""))
    return out


def is_direct_payment(tx: dict | None, wallet: str) -> bool:
    """True only when another wallet sent funds directly to merchant (not Drift/self)."""
    if not tx or not tx.get("meta"):
        return False

    keys = account_keys(tx)
    if not keys or keys[0] == wallet:
        return False

    if any(k in BLOCKED_PROGRAMS for k in keys):
        return False

    for log in tx["meta"].get("logMessages") or []:
        if any(m in log for m in BLOCKED_LOG_MARKERS):
            return False

    meta = tx["meta"]
    pre: dict[str, float] = {}
    for t in meta.get("preTokenBalances") or []:
        if t.get("owner") == wallet:
            pre[t["mint"]] = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0)

    inbound = False
    for t in meta.get("postTokenBalances") or []:
        if t.get("owner") != wallet:
            continue
        mint = t.get("mint", "")
        if mint not in (USDC_MINT, USDT_MINT):
            continue
        delta = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0) - pre.get(mint, 0)
        if delta < -0.001:
            return False
        if delta > 0.001:
            inbound = True

    idx = keys.index(wallet) if wallet in keys else -1
    if idx >= 0 and meta.get("preBalances") and meta.get("postBalances"):
        lam = meta["postBalances"][idx] - meta["preBalances"][idx]
        if lam < -1_000_000:
            return False
        if lam > 1_000_000:
            inbound = True

    return inbound


def inbound_amount(tx: dict, wallet: str, sol_price: float = 0.0) -> tuple[float, str]:
    if not is_direct_payment(tx, wallet):
        return 0.0, ""

    meta = tx["meta"]
    keys = account_keys(tx)
    idx = keys.index(wallet) if wallet in keys else -1
    pre: dict[str, float] = {}
    for t in meta.get("preTokenBalances") or []:
        if t.get("owner") == wallet:
            pre[t["mint"]] = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0)

    best = 0.0
    asset = ""
    for t in meta.get("postTokenBalances") or []:
        if t.get("owner") != wallet:
            continue
        mint = t.get("mint", "")
        delta = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0) - pre.get(mint, 0)
        if delta <= 0:
            continue
        if mint == USDC_MINT:
            best = max(best, delta)
            asset = "USDC"
        elif mint == USDT_MINT:
            best = max(best, delta)
            asset = "USDT"

    if sol_price > 0 and idx >= 0:
        lam = meta["postBalances"][idx] - meta["preBalances"][idx]
        if lam > 0:
            sol_usd = (lam / LAMPORTS) * sol_price
            if sol_usd > best:
                return sol_usd, "SOL"

    return best, asset


def token_delta(tx: dict, wallet: str) -> tuple[float, float, str]:
    """Returns (inbound_usdc_equiv, outbound_usdc_equiv, asset_label)."""
    if not tx or not tx.get("meta"):
        return 0.0, 0.0, ""
    meta = tx["meta"]
    pre: dict[str, float] = {}
    for t in meta.get("preTokenBalances") or []:
        if t.get("owner") == wallet:
            pre[t["mint"]] = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0)
    inbound = outbound = 0.0
    asset = ""
    for t in meta.get("postTokenBalances") or []:
        if t.get("owner") != wallet:
            continue
        mint = t.get("mint", "")
        if mint not in (USDC_MINT, USDT_MINT):
            continue
        delta = float((t.get("uiTokenAmount") or {}).get("uiAmount") or 0) - pre.get(mint, 0)
        name = "USDC" if mint == USDC_MINT else "USDT"
        if delta > 0.001:
            inbound = max(inbound, delta)
            asset = name
        elif delta < -0.001:
            outbound = max(outbound, abs(delta))
            asset = name
    return inbound, outbound, asset


def is_owner_trade(tx: dict | None, wallet: str) -> bool:
    """Your Drift/DeFi activity — not a buyer sale."""
    if not tx or not tx.get("meta"):
        return False
    keys = account_keys(tx)
    if keys and keys[0] == wallet:
        return True
    if any(k in BLOCKED_PROGRAMS for k in keys):
        return True
    for log in tx["meta"].get("logMessages") or []:
        if any(m in log for m in BLOCKED_LOG_MARKERS):
            return True
    return False


def classify_tx(tx: dict | None, wallet: str, sol_price: float = 0.0) -> str:
    """
    sale          — buyer sent directly to your wallet (>= $0.50)
    owner_trade   — you signed Drift/DeFi
    owner_outbound — you sent USDC out (sweep)
    owner_inbound — you moved funds in (not a buyer)
    other         — unrelated activity
    """
    if not tx or not tx.get("meta"):
        return "other"

    inbound, outbound, _ = token_delta(tx, wallet)
    keys = account_keys(tx)
    you_signed = bool(keys and keys[0] == wallet)

    if is_direct_payment(tx, wallet):
        amt, _ = inbound_amount(tx, wallet, sol_price)
        if amt >= 0.5:
            return "sale"

    if you_signed and outbound >= 0.5 and inbound < 0.5:
        return "owner_outbound"
    if you_signed and inbound >= 0.5 and outbound < 0.5:
        return "owner_inbound"
    if is_owner_trade(tx, wallet):
        return "owner_trade"
    return "other"