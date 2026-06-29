#!/usr/bin/env python3
"""Configure crypto payout address and build site/assets/crypto.js."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "crypto.json"
OUT = ROOT / "site" / "assets" / "crypto.js"

LICENSE_MAP = {
    "listinglab-pro": ROOT / "pipeline/licenses-listing-lab.txt",
    "etsy-tag-finder-pro": ROOT / "pipeline/licenses-etsy-tag-finder.txt",
    "seller-kit-bundle": ROOT / "pipeline/licenses-bundle.txt",
}
SOLD_KEYS = ROOT / "pipeline" / "sold-keys.json"

SOLANA_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def load() -> dict:
    return json.loads(CONFIG.read_text())


def save(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2) + "\n")
    build(data)


def inject_payout(data: dict) -> dict:
    """All methods settle to payout_address; bridge URLs get updated too."""
    payout = data.get("payout_address", "")
    for method in data.get("methods", {}).values():
        if method.get("bridge_url") and payout:
            method["bridge_url"] = re.sub(
                r"toAddress=[^&]+",
                f"toAddress={payout}",
                method["bridge_url"],
            )
    return data


def load_keys(path: Path, n: int = 15) -> list[str]:
    if not path.exists():
        return []
    return [ln.strip() for ln in path.read_text().splitlines() if ln.strip()][:n]


def load_recoveries() -> dict:
    if not SOLD_KEYS.exists():
        return {}
    return json.loads(SOLD_KEYS.read_text())


def filter_methods(data: dict) -> dict:
    """When direct_only, drop bridges — buyers must send straight to payout wallet."""
    if not data.get("direct_only"):
        return data
    methods = {
        k: v for k, v in data.get("methods", {}).items()
        if v.get("direct") and not v.get("bridge_url")
    }
    data = {**data, "methods": methods}
    return data


def build(data: dict | None = None) -> None:
    data = filter_methods(inject_payout(data or load()))
    recoveries = load_recoveries()
    reserved = {e["key"] for e in recoveries.values() if e.get("key")}
    pool: dict[str, list[str]] = {}
    for slug, lic in LICENSE_MAP.items():
        pool[slug] = [k for k in load_keys(lic) if k not in reserved]

    payload = {
        "payout_address": data["payout_address"],
        "payout_network": data.get("payout_network", "solana"),
        "preferred": data.get("preferred", "usdc_sol"),
        "direct_only": data.get("direct_only", False),
        "contact": data.get("contact", ""),
        "card": data.get("card", {"enabled": True}),
        # fallbacks: { slug: { gumroad, payhip, kofi } }
        "products": data["products"],
        "methods": data["methods"],
        "keyPool": pool,
        "recoveries": recoveries,
    }
    OUT.write_text("window.CRYPTO = " + json.dumps(payload, indent=2) + ";\n")
    print(f"Built {OUT.relative_to(ROOT)}")
    print(f"Payout: {data['payout_address']} ({len(data.get('methods', {}))} payment methods)")


def cmd_set_payout(args: argparse.Namespace) -> None:
    addr = args.address.strip()
    if not SOLANA_RE.match(addr):
        print("Warning: address may not be valid Solana format")
    data = load()
    data["payout_address"] = addr
    if args.preferred:
        data["preferred"] = args.preferred
    if args.contact:
        data["contact"] = args.contact
    save(data)


def cmd_set_card(args: argparse.Namespace) -> None:
    data = load()
    card = data.setdefault("card", {"enabled": True, "provider": "auto"})
    if args.helio:
        card["helio_paylink_id"] = args.helio.strip()
    if args.transak:
        card["transak_api_key"] = args.transak.strip()
    if args.moonpay:
        card["moonpay_publishable_key"] = args.moonpay.strip()
    if args.provider:
        card["provider"] = args.provider
    card["enabled"] = True
    data["preferred"] = "card"
    save(data)
    print("Card payments configured. Deploy site to go live.")


def cmd_status() -> None:
    print(json.dumps(load(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto payment config")
    sub = parser.add_subparsers(dest="cmd")

    sp = sub.add_parser("set-payout", help="Set Solana payout address (all methods route here)")
    sp.add_argument("address", help="Solana wallet address")
    sp.add_argument("--preferred", help="Default tab, e.g. usdc_sol")
    sp.add_argument("--contact")
    sp.set_defaults(func=cmd_set_payout)

    # legacy alias
    sw = sub.add_parser("set-wallet", help="Alias for set-payout")
    sw.add_argument("--usdc-sol", dest="address", required=True)
    sw.add_argument("--preferred")
    sw.add_argument("--contact")
    sw.set_defaults(func=cmd_set_payout)

    sc = sub.add_parser("set-card", help="Enable card → USDC on Solana (Helio/Transak/MoonPay)")
    sc.add_argument("--helio", help="MoonPay Commerce paylinkId from moonpay.hel.io")
    sc.add_argument("--transak", help="Transak API key from dashboard.transak.com")
    sc.add_argument("--moonpay", help="MoonPay publishable API key")
    sc.add_argument("--provider", choices=["auto", "helio", "transak", "moonpay"])
    sc.set_defaults(func=cmd_set_card)

    sub.add_parser("build").set_defaults(func=lambda _: build())
    sub.add_parser("status").set_defaults(func=lambda _: cmd_status())

    args = parser.parse_args()
    if not args.cmd:
        build()
        return
    args.func(args)


if __name__ == "__main__":
    main()