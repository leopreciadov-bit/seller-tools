#!/usr/bin/env python3
"""Post to r/Etsy if Reddit credentials exist; otherwise print ready copy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST_FILE = ROOT / "marketing" / "REDDIT_POST_READY.txt"


def parse_post(text: str) -> tuple[str, str]:
    title = ""
    body_lines: list[str] = []
    section = None

    for line in text.splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            section = "title"
        elif line.startswith("BODY:"):
            section = "body"
        elif section == "body":
            body_lines.append(line)

    return title, "\n".join(body_lines).strip()


def post_reddit(title: str, body: str, subreddit: str = "Etsy") -> bool:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    username = os.environ.get("REDDIT_USERNAME")
    password = os.environ.get("REDDIT_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        return False

    try:
        import praw  # type: ignore
    except ImportError:
        print("Install praw: pip install praw")
        return False

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent="seller-tools-launch/1.0",
    )
    sub = reddit.subreddit(subreddit)
    submission = sub.submit(title, body)
    print(f"Posted: {submission.url}")
    return True


def main() -> None:
    if not POST_FILE.exists():
        print(f"Missing {POST_FILE}")
        sys.exit(1)

    title, body = parse_post(POST_FILE.read_text())
    if not title or not body:
        print("Could not parse TITLE/BODY from REDDIT_POST_READY.txt")
        sys.exit(1)

    if post_reddit(title, body):
        return

    print("No Reddit credentials — copy/paste manually:\n")
    print(f"Subreddit: r/Etsy")
    print(f"\nTITLE:\n{title}\n")
    print(f"BODY:\n{body}\n")
    print("Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD to auto-post.")


if __name__ == "__main__":
    main()