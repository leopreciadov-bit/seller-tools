#!/usr/bin/env python3
"""Generate license keys for Gumroad delivery."""

import argparse
import random
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def key(prefix: str) -> str:
    chunk = lambda: "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{chunk()}-{chunk()}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--product", choices=["listing-lab", "etsy-tag-finder", "bundle"], default="listing-lab")
    args = parser.parse_args()

    prefixes = {
        "listing-lab": "LISTING",
        "etsy-tag-finder": "TAGFINDER",
        "bundle": "SELLERKIT",
    }
    prefix = prefixes[args.product]
    out = ROOT / "pipeline" / f"licenses-{args.product}.txt"
    keys = [key(prefix) for _ in range(args.count)]
    out.write_text("\n".join(keys) + "\n")
    print(f"Wrote {args.count} keys to {out}")


if __name__ == "__main__":
    main()