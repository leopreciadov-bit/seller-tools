#!/usr/bin/env python3
"""
Income stream autopilot — promote until new sales detected.
Run: python3 scripts/income_stream.py
Background: python3 scripts/income_stream.py --daemon
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
STATE = ROOT / "pipeline" / "income-stream.json"
SALES = ROOT / "pipeline" / "sales.json"


def log(msg: str) -> None:
    print(f"[income] {datetime.now(timezone.utc).strftime('%H:%M:%S')} {msg}", flush=True)


def revenue() -> float:
    if not SALES.exists():
        return 0.0
    data = json.loads(SALES.read_text())
    return sum(s.get("amount", 0) for s in data.get("sales", []))


def sale_count() -> int:
    if not SALES.exists():
        return 0
    return len(json.loads(SALES.read_text()).get("sales", []))


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"cycles": 0, "started_at": None}


def save_state(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def run_script(name: str) -> None:
    path = ROOT / "scripts" / name
    if not path.exists():
        return
    log(f"run {name}")
    subprocess.run([PY, str(path)], cwd=ROOT, check=False)


def cycle(state: dict) -> bool:
    """Returns True if new sale detected."""
    before = sale_count()
    rev_before = revenue()

    subprocess.run([PY, str(ROOT / "scripts" / "zero_human.py")], cwd=ROOT, check=False)
    after = sale_count()
    rev_after = revenue()

    state["cycles"] = state.get("cycles", 0) + 1
    state["last_revenue"] = rev_after
    state["last_sale_count"] = after

    if after > before or rev_after > rev_before:
        log(f"NEW SALE — count {before}→{after} revenue ${rev_before:.2f}→${rev_after:.2f}")
        return True
    log(f"cycle {state['cycles']} done — sales: {after} revenue: ${rev_after:.2f}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Loop every 30 min until new sale")
    parser.add_argument("--interval", type=int, default=1800, help="Seconds between cycles")
    parser.add_argument("--max-cycles", type=int, default=48, help="Max cycles in daemon mode")
    args = parser.parse_args()

    state = load_state()
    if not state.get("started_at"):
        state["started_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    log(f"=== Income stream === sales={sale_count()} revenue=${revenue():.2f}")

    if not args.daemon:
        cycle(state)
        save_state(state)
        return

    for i in range(args.max_cycles):
        if cycle(state):
            save_state(state)
            log("Sale detected — stream success")
            return
        save_state(state)
        if i < args.max_cycles - 1:
            log(f"sleep {args.interval}s…")
            time.sleep(args.interval)

    log(f"Max cycles ({args.max_cycles}) — no new sale yet. Keep ads/Gumroad running.")


if __name__ == "__main__":
    main()