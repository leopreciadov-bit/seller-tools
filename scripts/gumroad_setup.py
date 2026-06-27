#!/usr/bin/env python3
"""Gumroad config: set username/token, sync buy URLs to site."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "gumroad.json"
SITE_JS = ROOT / "site" / "assets" / "gumroad.js"


def load() -> dict:
    return json.loads(CONFIG.read_text())


def save(data: dict) -> None:
    CONFIG.write_text(json.dumps(data, indent=2) + "\n")
    sync_site(data)


def sync_site(data: dict) -> None:
    username = data.get("username")
    products = {}
    for slug, p in data.get("products", {}).items():
        url = f"https://{username}.gumroad.com/l/{p['slug']}" if username else None
        products[slug] = {
            "title": p["title"],
            "price": p["price_usd"],
            "url": url,
        }

    js = "window.GUMROAD = " + json.dumps({"username": username, "products": products}, indent=2) + ";\n"
    SITE_JS.write_text(js)
    print(f"Wrote {SITE_JS.relative_to(ROOT)}")


def cmd_set_username(name: str) -> None:
    data = load()
    data["username"] = name.strip()
    save(data)
    print(f"Username set: {name}")
    for slug, p in data["products"].items():
        print(f"  {p['title']}: https://{name}.gumroad.com/l/{p['slug']}")


def cmd_set_token(token: str) -> None:
    data = load()
    data["access_token"] = token.strip()
    save(data)
    print("Token saved to pipeline/gumroad.json")


def cmd_status() -> None:
    data = load()
    print(json.dumps(data, indent=2))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: gumroad_setup.py set-username NAME | set-token TOKEN | sync | status")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "set-username" and len(sys.argv) >= 3:
        cmd_set_username(sys.argv[2])
    elif cmd == "set-token" and len(sys.argv) >= 3:
        cmd_set_token(sys.argv[2])
    elif cmd == "sync":
        sync_site(load())
    elif cmd == "status":
        cmd_status()
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()