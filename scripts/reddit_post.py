#!/usr/bin/env python3
"""Post to Reddit subs via PRAW using pipeline/reddit.json or env vars."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "reddit.json"

SUBREDDITS = [
    ("Etsy", "marketing/REDDIT_POST_READY.txt"),
    ("shopify", "marketing/REDDIT_SHOPIFY.txt"),
    ("SideProject", "marketing/REDDIT_SIDEPROJECT.txt"),
    ("InternetIsBeautiful", "marketing/REDDIT_IIB.txt"),
]


def parse_post(text: str) -> tuple[str, str]:
    title, body_lines, section = "", [], None
    for line in text.splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body_lines.append(line)
    return title, "\n".join(body_lines).strip()


def load_creds() -> dict | None:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    env = {
        "client_id": os.environ.get("REDDIT_CLIENT_ID", ""),
        "client_secret": os.environ.get("REDDIT_CLIENT_SECRET", ""),
        "username": os.environ.get("REDDIT_USERNAME", ""),
        "password": os.environ.get("REDDIT_PASSWORD", ""),
        "user_agent": os.environ.get("REDDIT_USER_AGENT", "seller-tools/1.0"),
    }
    if all(env[k] for k in ("client_id", "client_secret", "username", "password")):
        return env
    return None


def get_reddit(creds: dict):
    try:
        import praw  # type: ignore
    except ImportError:
        raise SystemExit("Install praw: pip install praw")

    return praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        username=creds["username"],
        password=creds["password"],
        user_agent=creds.get("user_agent", "seller-tools/1.0"),
    )


def post_all() -> list[dict]:
    creds = load_creds()
    if not creds:
        raise SystemExit(
            "No Reddit creds. Run:\n"
            "  python3 scripts/reddit_setup.py create\n"
            "  python3 scripts/reddit_setup.py set --client-id ID --client-secret SECRET"
        )

    reddit = get_reddit(creds)
    results = []
    for sub, rel in SUBREDDITS:
        path = ROOT / rel
        if not path.exists():
            continue
        title, body = parse_post(path.read_text())
        if not title:
            continue
        try:
            submission = reddit.subreddit(sub).submit(title, body)
            results.append({"sub": sub, "url": submission.url, "ok": True})
            print(f"Posted r/{sub}: {submission.url}")
            time.sleep(90)  # rate limit courtesy
        except Exception as e:
            results.append({"sub": sub, "error": str(e), "ok": False})
            print(f"r/{sub} failed: {e}")
    return results


def main() -> None:
    sub = sys.argv[1] if len(sys.argv) > 1 else None
    file = sys.argv[2] if len(sys.argv) > 2 else "marketing/REDDIT_POST_READY.txt"

    creds = load_creds()
    if not creds:
        title, body = parse_post((ROOT / file).read_text())
        print("No Reddit creds — copy/paste manually:\n")
        print(f"Subreddit: r/{sub or 'Etsy'}\nTITLE:\n{title}\n\nBODY:\n{body}\n")
        sys.exit(1)

    if sub == "--all" or (not sub):
        post_all()
        return

    if sub:
        title, body = parse_post((ROOT / file).read_text())
        reddit = get_reddit(creds)
        submission = reddit.subreddit(sub).submit(title, body)
        print(f"Posted: {submission.url}")
        return

    post_all()


if __name__ == "__main__":
    main()