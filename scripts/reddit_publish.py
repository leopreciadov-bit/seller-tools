#!/usr/bin/env python3
"""Post Reddit marketing copy everywhere Reddit API can't reach."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
TOKEN = ROOT / "pipeline" / "telegraph-token.json"
POSTS = [
    ("marketing/REDDIT_POST_READY.txt", "r/Etsy"),
    ("marketing/REDDIT_SHOPIFY.txt", "r/shopify"),
    ("marketing/REDDIT_SIDEPROJECT.txt", "r/SideProject"),
    ("marketing/REDDIT_IIB.txt", "r/InternetIsBeautiful"),
]


def parse_post(path: Path) -> tuple[str, str]:
    title, body, section = "", [], None
    for line in path.read_text().splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body.append(line)
    return title, "\n".join(body).strip()


def telegraph(title: str, body: str, sub: str, token: str) -> str | None:
    content = json.dumps([
        {"tag": "p", "children": [f"Originally for {sub}"]},
        {"tag": "p", "children": [body[:3000]]},
        {"tag": "p", "children": [{"tag": "a", "attrs": {"href": SITE}, "children": [SITE]}]},
    ])
    data = urllib.parse.urlencode({
        "access_token": token,
        "title": f"{title[:100]} ({sub})",
        "author_name": "Seller Tools",
        "content": content,
    }).encode()
    req = urllib.request.Request("https://api.telegra.ph/createPage", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read())
    return res["result"]["url"] if res.get("ok") else None


def try_praw() -> bool:
    cfg = ROOT / "pipeline" / "reddit.json"
    if not cfg.exists():
        return False
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/reddit_post.py"), "--all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(r.stdout)
    return r.returncode == 0


def main() -> None:
    if try_praw():
        print("Reddit API posts live.")
        return

    token = ""
    if TOKEN.exists():
        token = json.loads(TOKEN.read_text()).get("access_token", "")

    for rel, sub in POSTS:
        title, body = parse_post(ROOT / rel)
        if token:
            url = telegraph(title, body, sub, token)
            if url:
                print(f"Telegraph {sub}: {url}")
        gist = subprocess.run(
            ["gh", "gist", "create", str(ROOT / rel), "--public", "--desc", f"Seller Tools {sub}"],
            capture_output=True,
            text=True,
        )
        if gist.returncode == 0:
            print(f"Gist {sub}: {gist.stdout.strip()}")

    subprocess.run([sys.executable, str(ROOT / "scripts/promote_autopilot.py")], cwd=ROOT, check=False)
    print("Reddit blocked (CAPTCHA). Content mirrored to Telegraph + Gists + search pings.")


if __name__ == "__main__":
    main()