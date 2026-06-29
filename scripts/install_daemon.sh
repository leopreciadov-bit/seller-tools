#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUNT="*/2 * * * * flock -n $ROOT/pipeline/.sale-hunt.lock -c 'cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 60 >> pipeline/sale-hunt.log 2>&1'"
BLAST="* * * * * flock -n $ROOT/pipeline/.blast-loop.lock -c 'cd $ROOT && python3 scripts/blast_loop.py --daemon --interval 45 >> pipeline/blast-loop.log 2>&1'"
(crontab -l 2>/dev/null | grep -v "sale_hunt.py" | grep -v "blast_loop.py" | grep -v "zero_human.py"; echo "$HUNT"; echo "$BLAST") | crontab -
echo "pipeline/.blast-loop.lock" >> "$ROOT/.gitignore" 2>/dev/null || true
echo "pipeline/blast-loop.log" >> "$ROOT/.gitignore" 2>/dev/null || true
pgrep -f "$ROOT/scripts/sale_hunt.py" | xargs -r kill 2>/dev/null
pgrep -f "$ROOT/scripts/blast_loop.py" | xargs -r kill 2>/dev/null
sleep 1
nohup flock -n "$ROOT/pipeline/.blast-loop.lock" bash -c "cd $ROOT && python3 scripts/blast_loop.py --daemon --interval 45 >> pipeline/blast-loop.log 2>&1" &
nohup flock -n "$ROOT/pipeline/.sale-hunt.lock" bash -c "cd $ROOT && python3 scripts/sale_hunt.py --daemon --interval 60 >> pipeline/sale-hunt.log 2>&1" &
echo "Daemons: blast_loop 45s + sale_hunt 60s"