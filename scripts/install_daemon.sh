#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Single instance via flock — no duplicate daemons
LINE="*/5 * * * * flock -n $ROOT/pipeline/.sale-hunt.lock -c 'cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 300 >> pipeline/sale-hunt.log 2>&1'"
(crontab -l 2>/dev/null | grep -v "sale_hunt.py" | grep -v "zero_human.py"; echo "$LINE") | crontab -
# Kill stray duplicate processes
pkill -f "python3 scripts/sale_hunt.py" 2>/dev/null || true
sleep 1
nohup flock -n "$ROOT/pipeline/.sale-hunt.lock" bash -c "cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 300 >> pipeline/sale-hunt.log 2>&1" &
echo "Sale hunt daemon installed (flock, every 5 min): $LINE"