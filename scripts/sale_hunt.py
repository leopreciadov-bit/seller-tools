#!/usr/bin/env python3
"""
Non-stop sale hunt — promote until buyer sales flood in.
Only stops logging loudly on confirmed BUYER direct payments (not your trades).
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
STATE = ROOT / "pipeline" / "sale-hunt.json"
SALES = ROOT / "pipeline" / "sales.json"
LOG = ROOT / "pipeline" / "sale-hunt.log"
ALERT = ROOT / "pipeline" / "BUYER_SALE_ALERT.json"


def log(msg: str) -> None:
    line = f"[hunt] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def run(name: str, *args: str) -> None:
    p = ROOT / "scripts" / name
    if not p.exists():
        return
    log(f"→ {name}")
    subprocess.run([PY, str(p), *args], cwd=ROOT, check=False, timeout=600)


def buyer_sales_count() -> int:
    if not SALES.exists():
        return 0
    return len(json.loads(SALES.read_text()).get("sales", []))


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"cycles": 0, "last_buyer_count": 0}


def save_state(st: dict) -> None:
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def deploy() -> None:
    subprocess.run([PY, str(ROOT / "scripts" / "crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run([PY, str(ROOT / "scripts" / "build_sitemap.py"), "--base", "https://leopreciadov-bit.github.io/seller-tools"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "-A", "--", ".", ":!.venv"], cwd=ROOT, check=False)
    subprocess.run(
        ["git", "commit", "-m", "Sale hunt: promotion cycle"],
        cwd=ROOT,
        capture_output=True,
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)


def cycle(st: dict) -> None:
    st["cycles"] = st.get("cycles", 0) + 1
    before = buyer_sales_count()

    run("account_factory.py")
    run("platform_retry.py")

    run("sales_innovate.py")
    run("seo_content_factory.py", "--batch", "8")
    run("sales_channels.py")
    run("build_sitemap.py", "--base", "https://leopreciadov-bit.github.io/seller-tools")
    run("advertise_other.py")
    run("promote_autopilot.py")
    run("reddit_publish.py")
    run("gumroad_launch.py")
    run("check_sales.py", "--quick")
    run("support_mail.py")
    if st["cycles"] % 5 == 0:
        run("check_sales.py")
        run("wallet_report.py")

    # Double blast while zero buyer sales
    if buyer_sales_count() == 0:
        log("zero buyer sales — double promotion")
        run("advertise_other.py")
        run("sales_innovate.py")
        run("sales_channels.py")
        run("seo_content_factory.py", "--batch", "8")
        run("promote_autopilot.py")
        run("resubmit_indexnow.py")

    deploy()

    after = buyer_sales_count()
    if after > before:
        log(f"*** BUYER SALE DETECTED {before} → {after} ***")
    elif after > st.get("last_buyer_count", 0):
        log(f"*** NEW BUYER SALE — total {after} ***")
    st["last_buyer_count"] = after
    save_state(st)
    log(f"cycle {st['cycles']} done — buyer_sales={after}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles (default 5 min)")
    args = parser.parse_args()

    st = load_state()
    log(f"START buyer_sales={buyer_sales_count()} interval={args.interval}s")

    if not args.daemon:
        cycle(st)
        return

    while True:
        try:
            st = load_state()
            cycle(st)
        except Exception as e:
            log(f"error: {e}")
        wait = 60 if buyer_sales_count() == 0 else args.interval
        time.sleep(wait)


if __name__ == "__main__":
    main()