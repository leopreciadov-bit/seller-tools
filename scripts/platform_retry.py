#!/usr/bin/env python3
"""Retry blocked platform signups/posts with fresh temp mail (24h backoff)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
STATE = ROOT / "pipeline" / "platform-retry.json"


def log(msg: str) -> None:
    print(f"[platform] {msg}", flush=True)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"platforms": {}}


def save_state(data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(data, indent=2) + "\n")


def due(name: str, state: dict, hours: int = 24) -> bool:
    p = state.setdefault("platforms", {}).get(name, {})
    last = p.get("last_attempt")
    if not last:
        return True
    try:
        t = datetime.fromisoformat(last.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - t >= timedelta(hours=hours)
    except Exception:
        return True


def mark(name: str, state: dict, ok: bool, detail: str = "") -> None:
    state.setdefault("platforms", {})[name] = {
        "last_attempt": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "detail": detail,
    }


def run_script(name: str) -> bool:
    path = ROOT / "scripts" / name
    if not path.exists():
        return False
    r = subprocess.run([PY, str(path)], cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0
    if r.stdout:
        print(r.stdout[-500:])
    if r.stderr and not ok:
        print(r.stderr[-300:])
    return ok


def main() -> None:
    state = load_state()
    subprocess.run([PY, str(ROOT / "scripts" / "account_factory.py")], cwd=ROOT, check=False)

    retries = [
        ("helio", "helio_onboard.py"),
        ("reddit", "reddit_publish.py"),
        ("gumroad", "gumroad_launch.py"),
    ]
    for name, script in retries:
        if not due(name, state):
            log(f"skip {name} — backoff")
            continue
        log(f"retry {name}")
        ok = run_script(script)
        mark(name, state, ok, script)
    save_state(state)


if __name__ == "__main__":
    main()