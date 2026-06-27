#!/usr/bin/env python3
"""Passive income agent pipeline orchestrator."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPPORTUNITIES = ROOT / "opportunities"
PRODUCTS = ROOT / "products"
PIPELINE = ROOT / "pipeline"
STATE_FILE = PIPELINE / "state.json"

DEFAULT_STATE = {
    "version": 1,
    "lane_a": "digital_products",
    "lane_b": "micro_saas",
    "active_product": "listing-lab",
    "products": {},
    "metrics": {"visitors": 0, "sales": 0, "revenue_usd": 0.0},
    "last_updated": None,
}


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return dict(DEFAULT_STATE)


def save_state(state: dict) -> None:
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def cmd_status(_: argparse.Namespace) -> None:
    state = load_state()
    print("Passive Income Agent Factory")
    print("=" * 40)
    print(f"Active product: {state.get('active_product', 'none')}")
    print(f"Revenue: ${state['metrics'].get('revenue_usd', 0):.2f}")
    print(f"Sales: {state['metrics'].get('sales', 0)}")
    print(f"Visitors: {state['metrics'].get('visitors', 0)}")
    print()
    products = list(PRODUCTS.iterdir()) if PRODUCTS.exists() else []
    product_dirs = [p.name for p in products if p.is_dir()]
    print(f"Products ({len(product_dirs)}): {', '.join(product_dirs) or 'none'}")
    opps = list(OPPORTUNITIES.glob("*.md")) if OPPORTUNITIES.exists() else []
    print(f"Opportunities ({len(opps)}): {', '.join(o.stem for o in opps) or 'none'}")
    print()
    print("Next steps:")
    print("  1. Scout: spawn income-scout persona in Grok")
    print("  2. Validate: score ideas → opportunities/scored.json")
    print("  3. Build: cd products/listing-lab && python -m http.server 8080")
    print("  4. Publish: run income-publisher on GO_TO_MARKET.md")


def cmd_init_product(args: argparse.Namespace) -> None:
    name = args.name
    product_dir = PRODUCTS / name
    if not product_dir.exists():
        print(f"Product directory not found: {product_dir}")
        return
    state = load_state()
    state["active_product"] = name
    state["products"].setdefault(
        name,
        {
            "status": "built",
            "channels": ["gumroad", "cloudflare_pages", "etsy"],
            "pricing": {"free_tier": True, "paid_one_time_usd": 19},
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    save_state(state)
    print(f"Initialized product '{name}' in pipeline state.")


def cmd_record_sale(args: argparse.Namespace) -> None:
    state = load_state()
    state["metrics"]["sales"] = state["metrics"].get("sales", 0) + 1
    state["metrics"]["revenue_usd"] = (
        state["metrics"].get("revenue_usd", 0.0) + args.amount
    )
    save_state(state)
    print(f"Recorded sale: ${args.amount:.2f} (total: ${state['metrics']['revenue_usd']:.2f})")


def cmd_seed_opportunities(_: argparse.Namespace) -> None:
    OPPORTUNITIES.mkdir(parents=True, exist_ok=True)
    scored = [
        {
            "name": "listing-lab",
            "total": 35,
            "pain": 9,
            "build": 9,
            "distribution": 8,
            "moat": 9,
            "verdict": "BUILD NOW",
            "rationale": "Etsy/Shopify sellers pay for listing help; MVP ships in 1 day; Reddit/Etsy SEO distribution.",
        },
        {
            "name": "invoice-forge",
            "total": 30,
            "pain": 8,
            "build": 8,
            "distribution": 7,
            "moat": 7,
            "verdict": "backlog",
            "rationale": "Freelancer invoices are crowded but PDF export + agent reminders is a wedge.",
        },
        {
            "name": "review-reply-bot",
            "total": 28,
            "pain": 8,
            "build": 7,
            "distribution": 7,
            "moat": 6,
            "verdict": "backlog",
            "rationale": "Shopify store owners hate review responses; needs API for full value.",
        },
    ]
    (OPPORTUNITIES / "scored.json").write_text(json.dumps(scored, indent=2) + "\n")
    listing_lab = OPPORTUNITIES / "listing-lab.md"
    if not listing_lab.exists():
        listing_lab.write_text(
            """# Opportunity: ListingLab

## Pain
Etsy and Shopify sellers spend 30–90 minutes per product writing SEO titles, descriptions, and tags. Bad copy = no sales.

## Who pays
- Etsy sellers ($50–500/mo revenue) buying Canva templates and SEO guides
- Shopify dropshippers paying for product description tools ($10–30/mo)

## Competitors & gaps
- ChatGPT (generic, no platform rules)
- eRank/Marmalead (SEO research, not copy generation)
- Gap: instant, platform-specific, copy-paste ready output

## MVP scope (1 day)
Single-page app: product name + niche + keywords → Etsy OR Shopify listing pack.

## Monetization
- Free: 5/day
- $19 lifetime on Gumroad (unlimited + CSV export)

## Distribution
- r/Etsy, r/shopify, r/sidehustle posts with free tool link
- Etsy digital product: "Listing Template Pack + Generator Access"
- Product Hunt launch

## Score preview
pain 9 | build 9 | distribution 8 | moat 9 → 35/40 BUILD NOW
"""
        )
    print(f"Seeded opportunities in {OPPORTUNITIES}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Passive income pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show pipeline status")
    p_status.set_defaults(func=cmd_status)

    p_init = sub.add_parser("init-product", help="Register a product in state")
    p_init.add_argument("name")
    p_init.set_defaults(func=cmd_init_product)

    p_sale = sub.add_parser("record-sale", help="Record a sale")
    p_sale.add_argument("amount", type=float)
    p_sale.set_defaults(func=cmd_record_sale)

    p_seed = sub.add_parser("seed", help="Seed starter opportunities")
    p_seed.set_defaults(func=cmd_seed_opportunities)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()