#!/usr/bin/env python3
"""
Zero-human income daemon — promote, detect sales, fulfill keys.
Card + crypto: all payments settle as crypto on Phantom (read-only monitoring).
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
STATE = ROOT / "pipeline" / "zero-human.json"
SALES = ROOT / "pipeline" / "sales.json"
KPI = ROOT / "pipeline" / "daily-kpi.json"
CRYPTO = ROOT / "pipeline" / "crypto.json"


def log(msg: str) -> None:
    print(f"[zero] {datetime.now(timezone.utc).strftime('%H:%M:%S')} {msg}", flush=True)


def run_script(name: str, *args: str) -> None:
    path = ROOT / "scripts" / name
    if not path.exists():
        return
    log(f"run {name}")
    subprocess.run([PY, str(path), *args], cwd=ROOT, check=False)


def card_live() -> bool:
    if not CRYPTO.exists():
        return False
    card = json.loads(CRYPTO.read_text()).get("card", {})
    return bool(
        card.get("helio_paylink_id")
        or card.get("transak_api_key")
        or card.get("moonpay_publishable_key")
    )


def sales_today() -> int:
    if not SALES.exists():
        return 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for s in json.loads(SALES.read_text()).get("sales", []):
        t = str(s.get("time", ""))
        if t.startswith(today):
            count += 1
    return count


def update_kpi() -> dict:
    kpi = json.loads(KPI.read_text()) if KPI.exists() else {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if kpi.get("date") != today:
        kpi = {"target_sales_per_day": 10, "sales_today": 0, "date": today, "escalation_level": 0}
    kpi["sales_today"] = sales_today()
    kpi["updated_at"] = datetime.now(timezone.utc).isoformat()
    KPI.write_text(json.dumps(kpi, indent=2) + "\n")
    return kpi


def cycle(escalate: bool = False) -> None:
    run_script("account_factory.py")
    run_script("platform_retry.py")
    run_script("check_sales.py")
    run_script("support_mail.py")
    run_script("seo_content_factory.py")
    run_script("advertise_other.py")
    if card_live():
        run_script("google_ads_launch.py")
    if escalate:
        log("KPI escalation — extra promotion")
        run_script("advertise_other.py")
        run_script("seo_content_factory.py")
        run_script("reddit_publish.py")
        run_script("promote_autopilot.py")
    run_script("wallet_audit.py")
    subprocess.run([PY, str(ROOT / "scripts" / "crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "-A", "--", ".", ":!.venv"], cwd=ROOT, check=False)
    subprocess.run(
        ["git", "commit", "-m", "Zero-human: card+crypto checkout cycle"],
        cwd=ROOT,
        capture_output=True,
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval", type=int, default=900, help="Seconds (default 15 min)")
    args = parser.parse_args()

    kpi = update_kpi()
    hour = datetime.now(timezone.utc).hour
    escalate = kpi["sales_today"] < kpi.get("target_sales_per_day", 10) and hour >= 12
    if escalate:
        kpi["escalation_level"] = kpi.get("escalation_level", 0) + 1
        KPI.write_text(json.dumps(kpi, indent=2) + "\n")

    log(f"sales_today={kpi['sales_today']}/{kpi.get('target_sales_per_day', 10)} card_live={card_live()}")

    if not args.daemon:
        cycle(escalate=escalate)
        return

    while True:
        kpi = update_kpi()
        hour = datetime.now(timezone.utc).hour
        escalate = kpi["sales_today"] < kpi.get("target_sales_per_day", 10) and hour >= 12
        cycle(escalate=escalate)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()