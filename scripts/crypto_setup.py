#!/usr/bin/env python3
"""Configure crypto wallets and build site/assets/crypto.js."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "crypto.json"
OUT = ROOT / "site" / "assets" / "crypto.js"

LICENSE_MAP = {
    "listinglab-pro": ROOT / "pipeline/licenses-listing-lab.txt",
    "etsy-tag-finder-pro": ROOT / "pipeline/licenses-etsy-tag-finder.txt",
    "seller-kit-bundle": ROOT / "pipeline/licenses-bundle.txt",
}


def load() -> dict:
    return json.loads(CONFIG.read_text())


def save(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2) + "\n")
    build(data)


def load_keys(path: Path, n: int = 15) -> list[str]:
    if not path.exists():
        return []
    return [ln.strip() for ln in path.read_text().splitlines() if ln.strip()][:n]


def build(data: dict | None = None) -> None:
    data = data or load()
    pool: dict[str, list[str]] = {}
    for slug, lic in LICENSE_MAP.items():
        pool[slug] = load_keys(lic)

    payload = {
        "wallets": data["wallets"],
        "preferred": data.get("preferred", "usdt_trc20"),
        "contact": data.get("contact", ""),
        "products": data["products"],
        "keyPool": pool,
    }
    OUT.write_text("window.CRYPTO = " + json.dumps(payload, indent=2) + ";\n")
    print(f"Built {OUT.relative_to(ROOT)}")


def cmd_set_wallet(args: argparse.Namespace) -> None:
    data = load()
    mapping = {
        "usdt_trc20": args.usdt_trc20,
        "usdc_sol": args.usdc_sol,
        "btc": args.btc,
        "eth": args.eth,
    }
    for k, v in mapping.items():
        if v:
            data["wallets"][k] = v.strip()
    if args.preferred:
        data["preferred"] = args.preferred
    if args.contact:
        data["contact"] = args.contact
    save(data)
    print("Wallets updated. Deploy site to go live.")


def cmd_status() -> None:
    print(json.dumps(load(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto payment config")
    sub = parser.add_subparsers(dest="cmd")

    sw = sub.add_parser("set-wallet", help="Set wallet addresses")
    sw.add_argument("--usdt-trc20")
    sw.add_argument("--usdc-sol")
    sw.add_argument("--btc")
    sw.add_argument("--eth")
    sw.add_argument("--preferred", choices=["usdt_trc20", "usdc_sol", "btc", "eth"])
    sw.add_argument("--contact")
    sw.set_defaults(func=cmd_set_wallet)

    sub.add_parser("build", help="Rebuild crypto.js from config").set_defaults(func=lambda _: build())
    sub.add_parser("status").set_defaults(func=lambda _: cmd_status())

    args = parser.parse_args()
    if not args.cmd:
        build()
        return
    args.func(args)


if __name__ == "__main__":
    main()