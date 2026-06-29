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
    return json.loads(STATE.read_text()) if STATE.exists() else {"runs": [], "cycle": 0}


def save_state(st: dict) -> None:
    st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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
        "urlList": sitemap_urls(),
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
    st["cycle"] = st.get("cycle", 0) + 1
    n = st["cycle"]
    log(f"=== MAX REVENUE CYCLE #{n} ===")

    run("payhip_sales.py", timeout=45)
    run("check_sales.py", "--quick", "--no-payhip", "--skip-detect", timeout=5)

    # Traffic: SEO pages every cycle, full advertise blast every 3rd cycle
    run("seo_content_factory.py", "--batch", "5", timeout=60)
    if n % 3 == 0:
        run("advertise_other.py", "--fast", timeout=120)
    else:
        run("sales_channels.py", timeout=90)

    run("build_sitemap.py", "--base", SITE, timeout=30)
    bing_indexnow(st)
    ping_google_sitemap(st)
    if n % 10 == 0:
        submit_directories_playwright(st)

    subprocess.run([PY, str(ROOT / "scripts/crypto_setup.py"), "build"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "-A", "--", "pipeline/", "site/"], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-m", f"Max revenue cycle #{n}"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=False)

    save_state(st)
    log("=== DONE ===")


if __name__ == "__main__":
    main()