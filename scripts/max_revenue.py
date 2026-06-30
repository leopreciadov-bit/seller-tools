#!/usr/bin/env python3
"""
Revenue-first cycle — only actions that can lead to paid checkout.
Escalates promotion when buyer sales are zero.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = "/tmp/seller-venv/bin/python" if Path("/tmp/seller-venv/bin/python").exists() else sys.executable
SITE = "https://leopreciadov-bit.github.io/seller-tools"
STATE = ROOT / "pipeline" / "max-revenue.json"
SALES = ROOT / "pipeline" / "sales.json"

ESCALATION_SCRIPTS = [
    ("promote_autopilot.py", []),
    ("community_outreach.py", []),
    ("reddit_publish.py", []),
    ("resubmit_indexnow.py", []),
]


def log(msg: str) -> None:
    print(f"[revenue] {msg}", flush=True)


def run(script: str, *args: str, timeout: int = 180) -> None:
    p = ROOT / "scripts" / script
    if not p.exists():
        return
    try:
        subprocess.run([PY, str(p), *args], cwd=ROOT, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f"{script} timed out ({timeout}s)")


def buyer_count() -> int:
    if not SALES.exists():
        return 0
    return len(json.loads(SALES.read_text()).get("sales", []))


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"runs": [], "cycle": 0}


def save_state(st: dict) -> None:
    st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    st["buyer_sales"] = buyer_count()
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def sitemap_urls(limit: int = 40) -> list[str]:
    sm = ROOT / "site" / "sitemap.xml"
    if not sm.exists():
        return [f"{SITE}/", f"{SITE}/deals/", f"{SITE}/etsy-tag-finder/", f"{SITE}/listing-lab/"]
    import re
    urls = re.findall(r"<loc>([^<]+)</loc>", sm.read_text())
    priority = [u for u in urls if "/guides/" in u or "/deals" in u or "tag-finder" in u or "listing-lab" in u]
    rest = [u for u in urls if u not in priority]
    return (priority + rest)[:limit]


def bing_indexnow(st: dict) -> None:
    cfg_path = ROOT / "pipeline/indexnow.json"
    if not cfg_path.exists():
        return
    cfg = json.loads(cfg_path.read_text())
    payload = json.dumps({
        "host": "leopreciadov-bit.github.io",
        "key": cfg["key"],
        "keyLocation": f"{SITE}/{cfg['key_file']}",
        "urlList": sitemap_urls(50),
    }).encode()
    for ep in ["https://www.bing.com/indexnow", "https://api.indexnow.org/indexnow"]:
        try:
            req = urllib.request.Request(ep, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                log(f"indexnow {ep.split('/')[2]} → {r.status}")
                st["runs"].append({"bing": ep, "status": r.status})
        except Exception as e:
            log(f"indexnow fail: {e}")


def submit_directories_playwright(st: dict) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto("https://www.uneed.best/submit-a-tool", timeout=45000)
            page.wait_for_timeout(3000)
            if page.locator('input[type="url"], input[name*="url" i]').count():
                page.locator('input[type="url"], input[name*="url" i]').first.fill(SITE)
            if page.locator('input[type="text"]').count():
                page.locator('input[type="text"]').first.fill("Seller Tools")
            log("uneed.best form reached")
            st["runs"].append({"uneed": page.url})
        except Exception as e:
            log(f"uneed: {e}")
        browser.close()


def main() -> None:
    st = load_state()
    st["cycle"] = st.get("cycle", 0) + 1
    n = st["cycle"]
    sales = buyer_count()
    log(f"=== MAX REVENUE CYCLE #{n} buyer_sales={sales} ===")

    run("payhip_sales.py", timeout=45)
    if n % 15 == 0:
        run("check_sales.py", "--quick", "--no-payhip", timeout=30)
    else:
        run("check_sales.py", "--quick", "--no-payhip", "--skip-detect", timeout=5)

    run("seo_content_factory.py", "--batch", "5", timeout=60)

    if n % 3 == 0:
        run("advertise_other.py", "--fast", timeout=120)
    else:
        run("sales_channels.py", timeout=90)

    if sales == 0:
        script, args = ESCALATION_SCRIPTS[n % len(ESCALATION_SCRIPTS)]
        log(f"escalation (0 sales) → {script}")
        run(script, *args, timeout=120)

    run("build_sitemap.py", "--base", SITE, timeout=30)
    bing_indexnow(st)
    if n % 10 == 0:
        submit_directories_playwright(st)

    subprocess.run([PY, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "-A", "--", "pipeline/", "site/"], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-m", f"Max revenue #{n} sales={sales}"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)

    save_state(st)
    log("=== DONE ===")


if __name__ == "__main__":
    main()