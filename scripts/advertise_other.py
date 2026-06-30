#!/usr/bin/env python3
"""Advertise Seller Tools via channels that don't need Reddit."""

from __future__ import annotations

import json
import random
import re
import string
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://leopreciadov-bit.github.io/seller-tools"
STATE = ROOT / "pipeline" / "advertise-state.json"
TELEGRAPH = ROOT / "pipeline" / "telegraph-token.json"

SOCIAL_POSTS = [
    ("Etsy Chrome Extension (free)", f"{SITE}/extension/", "Generate 13 SEO tags inside Etsy listing editor. Load unpacked in Chrome."),
    ("Pro lifetime deals $14-29", f"{SITE}/deals/", "Pay once — unlimited Etsy & Shopify tools. Card or USDC/USDT/SOL on Solana."),
    ("Etsy 13-tag generator (free)", f"{SITE}/etsy-tag-finder/", "Etsy sellers: 13 tags, 20 chars each. Free generator enforces both."),
    ("Shopify listing generator", f"{SITE}/listing-lab/", "Titles, descriptions, bullets from product basics. Etsy + Shopify mode."),
    ("Etsy tag SEO guide", f"{SITE}/guides/how-to-choose-etsy-tags.html", "How to pick all 13 Etsy tags with long-tail SEO."),
    ("Listing description template", f"{SITE}/guides/etsy-listing-description-template.html", "Free Etsy listing description template + generator."),
    ("Shopify product SEO guide", f"{SITE}/guides/shopify-product-listing-seo.html", "Shopify dropshipping listing SEO structure."),
    ("Free Etsy listing generator", f"{SITE}/guides/etsy-listing-generator-free.html", "No signup — titles, tags, descriptions in one click."),
    ("Best free Etsy SEO tools", f"{SITE}/guides/best-free-etsy-seo-tools.html", "2026 roundup of free Etsy SEO tools for sellers."),
]

WAYBACK_URLS = [
    f"{SITE}/",
    f"{SITE}/listing-lab/",
    f"{SITE}/etsy-tag-finder/",
    f"{SITE}/guides/how-to-choose-etsy-tags.html",
    f"{SITE}/guides/etsy-listing-description-template.html",
    f"{SITE}/guides/shopify-product-listing-seo.html",
    f"{SITE}/guides/etsy-listing-generator-free.html",
    f"{SITE}/guides/best-free-etsy-seo-tools.html",
]


def log(msg: str) -> None:
    print(f"[ads] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"channels": []}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def record(state: dict, channel: str, **kw) -> None:
    entry = {"channel": channel, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    state["channels"].append(entry)
    log(f"{channel}: {kw.get('status', kw.get('url', kw))}")


def pingomatic(state: dict) -> None:
    params = urllib.parse.urlencode({
        "title": "Seller Tools — Free Etsy & Shopify Listing Generators",
        "blogurl": f"{SITE}/",
        "rssurl": f"{SITE}/sitemap.xml",
    })
    url = f"https://rpc.pingomatic.com/?{params}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            record(state, "pingomatic", status=r.status)
    except Exception as e:
        record(state, "pingomatic", status="error", detail=str(e)[:100])


def indexnow_all(state: dict) -> None:
    cfg = json.loads((ROOT / "pipeline/indexnow.json").read_text())
    urls = list(cfg.get("submitted", []))
    payload = json.dumps({
        "host": "leopreciadov-bit.github.io",
        "key": cfg["key"],
        "keyLocation": f"{SITE}/{cfg['key_file']}",
        "urlList": urls,
    }).encode()
    for name, ep in [
        ("indexnow", "https://api.indexnow.org/indexnow"),
        ("bing", "https://www.bing.com/indexnow"),
        ("yandex", "https://yandex.com/indexnow"),
        ("seznam", "https://search.seznam.cz/indexnow"),
        ("naver", "https://searchadvisor.naver.com/indexnow"),
    ]:
        try:
            req = urllib.request.Request(ep, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                record(state, name, status=r.status)
        except urllib.error.HTTPError as e:
            record(state, name, status=e.code)
        except Exception as e:
            record(state, name, status="error", detail=str(e)[:80])


def telegraph_blast(state: dict) -> None:
    if not TELEGRAPH.exists():
        record(state, "telegraph", status="no_token")
        return
    token = json.loads(TELEGRAPH.read_text()).get("access_token", "")
    for title, link, blurb in SOCIAL_POSTS:
        content = json.dumps([
            {"tag": "p", "children": [blurb]},
            {"tag": "p", "children": [{"tag": "a", "attrs": {"href": link}, "children": [link]}]},
            {"tag": "p", "children": [{"tag": "a", "attrs": {"href": SITE}, "children": ["All Seller Tools"]}]},
        ])
        data = urllib.parse.urlencode({
            "access_token": token,
            "title": title,
            "author_name": "Seller Tools",
            "content": content,
        }).encode()
        req = urllib.request.Request("https://api.telegra.ph/createPage", data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.loads(r.read())
            if res.get("ok"):
                record(state, "telegraph", url=res["result"]["url"])
        except Exception as e:
            record(state, "telegraph", status="error", detail=str(e)[:80])


def gist_blast(state: dict) -> None:
    posts_md = ROOT / "marketing" / "SOCIAL_POSTS.md"
    if not posts_md.exists():
        build_social_md(posts_md)
    r = subprocess.run(
        ["gh", "gist", "create", str(posts_md), "--public", "--desc", "Seller Tools social posts"],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        record(state, "gist_social", url=r.stdout.strip())
    for title, link, blurb in SOCIAL_POSTS[:3]:
        tmp = ROOT / "pipeline" / f"_gist_{random.randint(1000,9999)}.md"
        tmp.write_text(f"# {title}\n\n{blurb}\n\n{link}\n")
        r2 = subprocess.run(["gh", "gist", "create", str(tmp), "--public"], capture_output=True, text=True)
        tmp.unlink(missing_ok=True)
        if r2.returncode == 0:
            record(state, "gist", url=r2.stdout.strip())


def build_social_md(path: Path) -> None:
    lines = ["# Seller Tools — Social Posts\n", f"Site: {SITE}/\n"]
    for title, link, blurb in SOCIAL_POSTS:
        lines.append(f"## {title}\n\n{blurb}\n\n{link}\n")
    path.write_text("\n".join(lines))


def sitemap_ping(state: dict) -> None:
    sitemap = urllib.parse.quote(f"{SITE}/sitemap.xml", safe="")
    for name, url in [
        ("google_sitemap", f"https://www.google.com/ping?sitemap={sitemap}"),
        ("bing_sitemap", f"https://www.bing.com/ping?sitemap={sitemap}"),
    ]:
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                record(state, name, status=r.status)
        except urllib.error.HTTPError as e:
            record(state, name, status=e.code)
        except Exception as e:
            record(state, name, status="error", detail=str(e)[:80])


def rentry_paste(state: dict) -> None:
    """Anonymous markdown pages — indexable backlinks."""
    master = f"# Seller Tools — Free Etsy & Shopify Listing Generators\n\nSite: {SITE}/\n\n"
    for title, link, blurb in SOCIAL_POSTS:
        master += f"## {title}\n{blurb}\n{link}\n\n"
    try:
        data = urllib.parse.urlencode({"url": "", "edit_code": "", "text": master}).encode()
        req = urllib.request.Request("https://rentry.co/api/new", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read())
        if res.get("status") == "200":
            record(state, "rentry_master", url=res.get("url", ""))
    except Exception as e:
        record(state, "rentry_master", status="error", detail=str(e)[:80])

    for title, link, blurb in SOCIAL_POSTS[:4]:
        text = f"{title}\n\n{blurb}\n\n{link}\n\nMore: {SITE}/"
        try:
            data = urllib.parse.urlencode({"url": "", "edit_code": "", "text": text}).encode()
            req = urllib.request.Request("https://rentry.co/api/new", data=data, method="POST")
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.loads(r.read())
            if res.get("status") == "200":
                record(state, "rentry", url=res.get("url", ""))
        except Exception as e:
            record(state, "rentry", status="error", detail=str(e)[:80])


def github_discussions(state: dict) -> None:
    today = time.strftime("%Y-%m-%d", time.gmtime())
    last = state.get("last_github_discussion_day")
    if last == today:
        record(state, "github_discussion", status="skipped_daily_limit")
        return

    topics = [
        ("Free Etsy listing generator (no signup)", f"{SITE}/guides/etsy-listing-generator-free.html", "Titles, 13 tags, descriptions — free daily quota."),
        ("Best free Etsy SEO tools 2026", f"{SITE}/guides/best-free-etsy-seo-tools.html", "Roundup of free tools for Etsy sellers."),
        ("Etsy Tag Finder — 13 SEO tags", f"{SITE}/etsy-tag-finder/", "Enforces 13 tags × 20 characters."),
    ]
    topics = [topics[state.get("github_discussion_idx", 0) % len(topics)]]
    mutation = """
    mutation($repoId: ID!, $catId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repoId, categoryId: $catId, title: $title, body: $body}) {
        discussion { url }
      }
    }
    """
    repo_id = "R_kgDOTHCmOw"
    cat_id = "DIC_kwDOTHCmO84DAB1Y"  # General
    for title, link, blurb in topics:
        body = f"{blurb}\n\n{link}\n\nAll tools: {SITE}/"
        r = subprocess.run(
            [
                "gh", "api", "graphql",
                "-f", f"query={mutation}",
                "-f", f"repoId={repo_id}",
                "-f", f"catId={cat_id}",
                "-f", f"title={title}",
                "-f", f"body={body}",
            ],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            try:
                url = json.loads(r.stdout)["data"]["createDiscussion"]["discussion"]["url"]
                record(state, "github_discussion", url=url)
                state["last_github_discussion_day"] = today
                state["github_discussion_idx"] = state.get("github_discussion_idx", 0) + 1
            except (json.JSONDecodeError, KeyError, TypeError):
                record(state, "github_discussion", status="ok")
        else:
            record(state, "github_discussion", status="error", detail=r.stderr[:100])


def archive_save(state: dict) -> None:
    for url in WAYBACK_URLS:
        save_url = "https://web.archive.org/save/" + urllib.parse.quote(url, safe="")
        try:
            req = urllib.request.Request(save_url, headers={"User-Agent": "seller-tools/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                record(state, "wayback", url=url, status=r.status)
        except Exception as e:
            record(state, "wayback", url=url, status="error", detail=str(e)[:80])


def bluesky_post(state: dict) -> None:
    """Try Bluesky ATProto account + post."""
    import requests

    handle = "sellertools" + "".join(random.choices(string.digits, k=4)) + ".bsky.social"
    email = f"sellertools{random.randint(1000,9999)}@gmail.com"  # may fail
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    try:
        r = requests.post(
            "https://bsky.social/xrpc/com.atproto.server.createAccount",
            json={"handle": handle, "password": password, "email": email},
            timeout=20,
        )
        if r.status_code != 200:
            record(state, "bluesky", status=r.status_code, detail=r.text[:100])
            return
        sess = r.json()
        token = sess.get("accessJwt", "")
        did = sess.get("did", "")
        text = f"Free Etsy & Shopify listing generators — no signup\n{SITE}/"
        post_r = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                },
            },
            timeout=20,
        )
        record(state, "bluesky", status=post_r.status_code, handle=handle)
    except Exception as e:
        record(state, "bluesky", status="error", detail=str(e)[:100])


def hashnode_publish(state: dict) -> None:
    article = (ROOT / "marketing" / "DEVTO_ARTICLE.md").read_text()
    title_m = re.search(r"^#\s+(.+)$", article, re.M)
    title = title_m.group(1).strip() if title_m else "Free Etsy Listing Tools"
    body = re.sub(r"^#\s+.+\n", "", article, count=1).strip()

    mutation = """
    mutation Publish($input: PublishPostInput!) {
      publishPost(input: $input) { post { slug } }
    }
    """
    # Hashnode needs API key from dashboard — try anonymous publication endpoint
    try:
        import requests
        r = requests.post(
            "https://api.hashnode.com/",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "title": title,
                        "contentMarkdown": body,
                        "tags": [{"slug": "etsy"}, {"slug": "shopify"}, {"slug": "seo"}],
                        "publicationId": "",
                    }
                },
            },
            timeout=20,
        )
        record(state, "hashnode", status=r.status_code, detail=r.text[:120])
    except Exception as e:
        record(state, "hashnode", status="error", detail=str(e)[:80])


def github_wiki(state: dict) -> None:
    body = f"""# Seller Tools

Free Etsy & Shopify listing generators.

- [ListingLab]({SITE}/listing-lab/) — listing generator
- [Etsy Tag Finder]({SITE}/etsy-tag-finder/) — 13 SEO tags
- [All tools]({SITE}/)

## SEO Guides
- [Etsy tags guide]({SITE}/guides/how-to-choose-etsy-tags.html)
- [Description template]({SITE}/guides/etsy-listing-description-template.html)
- [Shopify SEO]({SITE}/guides/shopify-product-listing-seo.html)
"""
    wiki_dir = ROOT / ".wiki_tmp" / "repo"
    wiki_dir.parent.mkdir(exist_ok=True)
    if not (wiki_dir / ".git").exists():
        subprocess.run(
            ["git", "clone", "https://github.com/leopreciadov-bit/seller-tools.wiki.git", str(wiki_dir)],
            capture_output=True, text=True,
        )
    if (wiki_dir / ".git").exists():
        (wiki_dir / "Home.md").write_text(body)
        subprocess.run(["git", "-C", str(wiki_dir), "add", "Home.md"], capture_output=True)
        subprocess.run(["git", "-C", str(wiki_dir), "commit", "-m", "Update Seller Tools links"], capture_output=True)
        r = subprocess.run(["git", "-C", str(wiki_dir), "push"], capture_output=True, text=True)
        record(state, "github_wiki", status="pushed" if r.returncode == 0 else "error", detail=r.stderr[:80])
    else:
        record(state, "github_wiki", status="error", detail="wiki clone failed")


def paste_sites(state: dict) -> None:
    """Anonymous paste hosts — extra indexable backlinks."""
    text = f"Seller Tools — free Etsy & Shopify listing generators\n{SITE}/\n\n"
    for title, link, blurb in SOCIAL_POSTS[:5]:
        text += f"{title}: {link}\n{blurb}\n\n"

    for name, url, data in [
        ("dpaste", "https://dpaste.com/api/v2/", {"content": text, "expiry_days": 365, "title": "Seller Tools"}),
        ("controlc", "https://controlc.com/index.php?act=submit", {"paste_title": "Seller Tools", "paste_text": text}),
    ]:
        try:
            import requests
            r = requests.post(url, data=data, timeout=20, headers={"User-Agent": "seller-tools/1.0"})
            loc = r.headers.get("Location", r.url)
            if r.status_code in (200, 201, 302) and "seller" in (loc + r.text).lower() or r.status_code in (200, 201, 302):
                record(state, name, url=loc or r.url, status=r.status_code)
            else:
                record(state, name, status=r.status_code, detail=r.text[:80])
        except Exception as e:
            record(state, name, status="error", detail=str(e)[:80])


def github_issue_update(state: dict) -> None:
    body = f"""## Seller Tools links (auto-updated)

- Site: {SITE}/
- [ListingLab]({SITE}/listing-lab/)
- [Etsy Tag Finder]({SITE}/etsy-tag-finder/)
- [Free listing generator guide]({SITE}/guides/etsy-listing-generator-free.html)
- [Best Etsy SEO tools]({SITE}/guides/best-free-etsy-seo-tools.html)

Crypto checkout live → Phantom wallet."""
    r = subprocess.run(
        ["gh", "issue", "comment", "1", "--repo", "leopreciadov-bit/seller-tools", "--body", body],
        capture_output=True, text=True,
    )
    record(state, "github_issue_comment", status="ok" if r.returncode == 0 else "error", detail=r.stderr[:80])


def slashdot_submit(state: dict) -> None:
    try:
        import requests
        s = requests.Session()
        s.headers["User-Agent"] = "seller-tools/1.0"
        r = s.get("https://slashdot.org/submission", timeout=20)
        record(state, "slashdot", status=r.status_code, detail="form requires login")
    except Exception as e:
        record(state, "slashdot", status="error", detail=str(e)[:80])


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Skip slow channels (wayback, wiki, bluesky)")
    args = parser.parse_args()

    state = load_state()
    log("=== Advertise other channels ===")

    channels = [
        sitemap_ping,
        pingomatic,
        indexnow_all,
        telegraph_blast,
        rentry_paste,
        paste_sites,
        gist_blast,
        github_discussions,
        github_issue_update,
    ]
    if not args.fast:
        channels.extend([archive_save, github_wiki, bluesky_post, hashnode_publish, slashdot_submit])

    for fn in channels:
        try:
            fn(state)
        except Exception as e:
            record(state, fn.__name__, status="error", detail=str(e)[:120])

    save_state(state)
    log("=== Done ===")


if __name__ == "__main__":
    main()