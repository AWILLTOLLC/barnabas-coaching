#!/bin/bash
# Re-run all scenario sims against current scout data. Output per sim saved to
# sims/history/ with a dated combined report. Expects to run from project root.
set -u
cd "$(dirname "$0")/.."
PROJ="$(pwd)"
STAMP="$(date '+%Y-%m-%d')"
OUTDIR="$PROJ/sims/history"
mkdir -p "$OUTDIR"
REPORT="$OUTDIR/$STAMP.md"

cp "$PROJ/data/scout.db" /tmp/bt.db || { echo "FAILED: could not copy scout.db"; exit 1; }

{
  echo "# Scenario re-run — $STAMP"
  echo
  echo "Data window: $(sqlite3 /tmp/bt.db 'SELECT MIN(datetime(first_seen_ms/1000,\"unixepoch\")) FROM coins') to $(sqlite3 /tmp/bt.db 'SELECT MAX(datetime(first_seen_ms/1000,\"unixepoch\")) FROM coins') on $(sqlite3 /tmp/bt.db 'SELECT COUNT(*) FROM coins WHERE alerted=1') alerted coins."
  echo
  for sim in "$PROJ"/sims/sim*.ts; do
    name="$(basename "$sim" .ts)"
    echo "## $name"
    echo '```'
    npx --prefix "$PROJ" tsx "$sim" 2>&1
    echo '```'
    echo
  done
} > "$REPORT" 2>&1

echo "Report written: $REPORT"
# print just the verdict-bearing first lines of each section for quick reading
grep -E "^# Scenario|^flat|^ladder|^BASELINE|^Scenario 1.*valued|^Scenario 2.*valued|boundary: total|alerts by regime|coins with" "$REPORT" | head -40

# metrics extraction + delta comparison (zero-LLM). Exit 2 = verdict flip.
python3 "$(dirname "$0")/compare.py"
