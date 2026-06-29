#!/usr/bin/env python3
"""Non-stop lightweight promotion — never blocks on wallet RPC."""

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
LOG = ROOT / "pipeline" / "blast-loop.log"
SALES = ROOT / "pipeline" / "sales.json"

FAST = [
    "sales_innovate.py",
    "community_outreach.py",
    "advertise_other.py",
    "resubmit_indexnow.py",
    "sales_channels.py",
]

SLOW_EVERY = 5  # every N fast cycles run full seo + deploy


def log(msg: str) -> None:
    line = f"[blast] {datetime.now(timezone.utc).strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def run(name: str, *args: str, timeout: int = 300) -> None:
    p = ROOT / "scripts" / name
    if not p.exists():
        return
    subprocess.run([PY, str(p), *args], cwd=ROOT, check=False, timeout=timeout)


def buyer_count() -> int:
    if not SALES.exists():
        return 0
    return len(json.loads(SALES.read_text()).get("sales", []))


def deploy() -> None:
    subprocess.run([PY, str(ROOT / "scripts" / "crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run(
        [PY, str(ROOT / "scripts" / "build_sitemap.py"), "--base", "https://leopreciadov-bit.github.io/seller-tools"],
        cwd=ROOT, check=False,
    )
    subprocess.run(["git", "add", "-A", "--", ".", ":!.venv"], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-m", "Blast: promotion cycle"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)


def cycle(n: int) -> None:
    log(f"cycle {n} buyer_sales={buyer_count()}")
    for s in FAST:
        run(s, timeout=180)
    if n % SLOW_EVERY == 0:
        run("seo_content_factory.py", "--batch", "8", timeout=180)
        run("reddit_publish.py", timeout=120)
        deploy()
    run("payhip_sales.py", timeout=45)
    run("check_sales.py", "--quick", timeout=90)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval", type=int, default=45)
    args = parser.parse_args()
    n = 0
    log(f"START interval={args.interval}s")
    if not args.daemon:
        cycle(1)
        return
    while True:
        try:
            n += 1
            cycle(n)
        except Exception as e:
            log(f"error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()