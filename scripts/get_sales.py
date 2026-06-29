#!/usr/bin/env python3
"""Drive sales: promotion blast + sales check + deploy."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=ROOT, check=False)


def main() -> None:
    print("=== GET SALES ===", flush=True)
    for script in [
        "advertise_other.py",
        "reddit_publish.py",
        "promote_autopilot.py",
        "support_mail.py",
        "check_sales.py",
    ]:
        run([PY, str(ROOT / "scripts" / script)])
    run([PY, str(ROOT / "scripts" / "crypto_setup.py"), "build"])
    run(["git", "add", "-A", "--", ".", ":!.venv"])
    subprocess.run(["git", "commit", "-m", "Get sales: promotion cycle"], cwd=ROOT, capture_output=True)
    run(["git", "push", "origin", "main"])
    print("\n=== DONE — site live, promotion pushed ===", flush=True)


if __name__ == "__main__":
    main()