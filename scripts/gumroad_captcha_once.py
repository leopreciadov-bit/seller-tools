#!/usr/bin/env python3
"""Gumroad signup — stops at CAPTCHA. One human click, then finishes automatically."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gumroad_autopilot import signup_gumroad, create_products, wire_gumroad_checkout  # noqa: E402

NEEDED = ROOT / "pipeline" / "GUMROAD_CAPTCHA_NEEDED.json"
PY = "/tmp/seller-venv/bin/python" if Path("/tmp/seller-venv/bin/python").exists() else sys.executable


def main() -> None:
    print("=== Gumroad: card + PayPal checkout ===\n")
    print("A browser will open with email/password filled.")
    print("YOU: click the CAPTCHA checkbox, then 'Create account'.")
    print("Script continues automatically after you press ENTER here.\n")

    acct = signup_gumroad(headless=False, manual_captcha=True)
    username = acct.get("username") or create_products(acct, headless=False)
    if username:
        acct["username"] = username
        wire_gumroad_checkout(username, acct)
        if NEEDED.exists():
            NEEDED.unlink()
        subprocess.run(["git", "add", "-A", "--", "pipeline/", "site/assets/"], cwd=ROOT, check=False)
        subprocess.run(["git", "commit", "-m", "Gumroad live: card + PayPal checkout"], cwd=ROOT, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)
        print(f"\nLIVE — https://{username}.gumroad.com")
        print("Site updated with Gumroad + Payhip checkout.")
    else:
        print("Signup ok but could not read username — check Gumroad dashboard.")


if __name__ == "__main__":
    main()