#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LINE="*/5 * * * * cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 300 >> pipeline/sale-hunt.log 2>&1"
(crontab -l 2>/dev/null | grep -v "sale_hunt.py" | grep -v "zero_human.py"; echo "$LINE") | crontab -
echo "Sale hunt daemon installed (every 5 min): $LINE"