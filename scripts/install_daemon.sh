#!/usr/bin/env bash
# Install zero-human income cron (every 15 min)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LINE="*/15 * * * * cd $ROOT && python3 scripts/zero_human.py >> pipeline/zero-human.log 2>&1"
(crontab -l 2>/dev/null | grep -v "zero_human.py"; echo "$LINE") | crontab -
echo "Installed: $LINE"