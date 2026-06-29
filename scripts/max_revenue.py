#!/usr/bin/env python3
"""
Revenue-first cycle — only actions that can lead to paid checkout.
Skips low-intent paste/telegraph spam.
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

# High-intent Etsy seller search queries → land on tools/deals
BING_PING_URLS = [
    f"{SITE}/etsy-tag-finder/",
    f"{SITE}/listing-lab/",
    f"{SITE}/deals/",
    f"{SITE}/guides/marmalead-alternative-free.html",
    f"{SITE}/guides/erank-alternative-free.html",
    f"{SITE}/guides/best-etsy-tag-generator-2026.html",
]

TOOL_DIRS = [
    ("tool_directories", "https://www.saashub.com/submit", SITE, "Seller Tools — Free Etsy listing & tag generators"),
    ("tool_directories", "https://www.alternativeto.net/browse/new/", SITE, "Seller Tools"),
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


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"runs": []}


def save_state(st: dict) -> None:
    st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def bing_indexnow(st: dict) -> None:
    cfg_path = ROOT / "pipeline/indexnow.json"
    if not cfg_path.exists():
        return
    cfg = json.loads(cfg_path.read_text())
    payload = json.dumps({
        "host": "leopreciadov-bit.github.io",
        "key": cfg["key"],
        "keyLocation": f"{SITE}/{cfg['key_file']}",
        "urlList": BING_PING_URLS,
    }).encode()
    for ep in ["https://www.bing.com/indexnow", "https://api.indexnow.org/indexnow"]:
        try:
            req = urllib.request.Request(ep, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                log(f"indexnow {ep.split('/')[2]} → {r.status}")
                st["runs"].append({"bing": ep, "status": r.status})
        except Exception as e:
            log(f"indexnow fail: {e}")


def ping_google_sitemap(st: dict) -> None:
    url = "https://www.google.com/ping?" + urllib.parse.urlencode({"sitemap": f"{SITE}/sitemap.xml"})
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            log(f"google sitemap ping → {r.status}")
            st["runs"].append({"google_ping": r.status})
    except Exception as e:
        log(f"google ping: {e}")


def submit_directories_playwright(st: dict) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        # Uneed — free tool listing
        try:
            page.goto("https://www.uneed.best/submit-a-tool", timeout=45000)
            page.wait_for_timeout(3000)
            if page.locator('input[type="url"], input[name*="url" i]').count():
                page.locator('input[type="url"], input[name*="url" i]').first.fill(SITE)
            if page.locator('input[type="text"]').count():
                page.locator('input[type="text"]').first.fill("Seller Tools")
            page.screenshot(path=str(ROOT / "pipeline/uneed-submit.png"))
            log("uneed.best form reached")
            st["runs"].append({"uneed": page.url})
        except Exception as e:
            log(f"uneed: {e}")
        browser.close()


def main() -> None:
    st = load_state()
    log("=== MAX REVENUE CYCLE ===")

    run("payhip_sales.py", timeout=60)
    run("check_sales.py", "--quick", timeout=45)
    run("sales_channels.py", timeout=180)  # comparison SEO pages
    bing_indexnow(st)
    ping_google_sitemap(st)
    if len(st.get("runs", [])) % 10 == 0:
        submit_directories_playwright(st)

    subprocess.run([PY, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "-A", "--", "pipeline/", "site/"], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-m", "Max revenue cycle"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)

    save_state(st)
    log("=== DONE ===")


if __name__ == "__main__":
    main()