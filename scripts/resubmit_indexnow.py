#!/usr/bin/env python3
"""Re-ping IndexNow with saved key."""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "pipeline" / "indexnow.json").read_text())
base = "https://leopreciadov-bit.github.io/seller-tools"
payload = json.dumps({
    "host": "leopreciadov-bit.github.io",
    "key": cfg["key"],
    "keyLocation": f"{base}/{cfg['key_file']}",
    "urlList": cfg["submitted"],
}).encode()
req = urllib.request.Request(
    "https://api.indexnow.org/indexnow",
    data=payload,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=15) as r:
    print("IndexNow", r.status)