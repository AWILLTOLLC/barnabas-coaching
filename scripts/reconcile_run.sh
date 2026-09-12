#!/bin/bash
set -euo pipefail

# reconcile_run.sh — Nightly memory-reconcile orchestrator for Barnabas pilot
# Usage: scripts/reconcile_run.sh [agent-id] (default: barnabas-coaching)

AGENT="${1:-barnabas-coaching}"
WORKSPACE="/Users/apollo/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
SCRIPTS_DIR="$WORKSPACE/scripts"
RUN_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Files
CURSOR_FILE="$MEMORY_DIR/reconcile-cursor-${AGENT}.json"
LEDGER_FILE="$MEMORY_DIR/reconcile-ledger-${AGENT}.jsonl"
SCAN_OUT="/tmp/reconcile-scan-${AGENT}-$$.json"
JUDGE_OUT="/tmp/reconcile-judge-${AGENT}-$$.json"

# Ensure dirs exist
mkdir -p "$MEMORY_DIR"
mkdir -p "$SCRIPTS_DIR"

# ── Step 1: Scan ─────────────────────────────────────────────────────────────
echo "[reconcile] Scanning agent=$AGENT ..."
if [ -f "$CURSOR_FILE" ]; then
  SINCE_ARG="--since $CURSOR_FILE"
else
  SINCE_ARG=""
fi
python3 "$SCRIPTS_DIR/reconcile_scan.py" \
  --agent "$AGENT" \
  --out "$SCAN_OUT" \
  $SINCE_ARG

SCANNED=$(python3 -c "import json; print(len(json.load(open('$SCAN_OUT'))))")
echo "[reconcile] Scanned candidates: $SCANNED"

if [ "$SCANNED" -eq 0 ]; then
  echo "[reconcile] No new candidates; nothing to do."
  rm -f "$SCAN_OUT"
  exit 0
fi

# ── Step 2: Judge ────────────────────────────────────────────────────────────
echo "[reconcile] Judging $SCANNED candidate(s) ..."
if ! python3 "$SCRIPTS_DIR/reconcile_judge.py" \
    --in "$SCAN_OUT" \
    --out "$JUDGE_OUT"; then
  echo "[reconcile] WARN: Judge script failed, falling back to unjudged."
  python3 -c "
import json, sys
candidates = json.load(open('$SCAN_OUT'))
unjudged = [{'id': c['id'], 'verdict': 'unjudged', 'rationale': 'judge script failed', 'candidate_type': c.get('type'), 'evidence': c.get('evidence'), 'source_ref': c.get('source_ref'), 'ts': c.get('ts')} for c in candidates]
json.dump(unjudged, open('$JUDGE_OUT', 'w'), indent=2)
"
fi

JUDGED_MATCH=$(python3 -c "import json; d=json.load(open('$JUDGE_OUT')); print(sum(1 for x in d if x.get('verdict')=='match'))")
JUDGED_SKIP=$(python3 -c "import json; d=json.load(open('$JUDGE_OUT')); print(sum(1 for x in d if x.get('verdict')=='skip'))")
JUDGED_JUNK=$(python3 -c "import json; d=json.load(open('$JUDGE_OUT')); print(sum(1 for x in d if x.get('verdict')=='junk'))")
JUDGED_UNJ=$(python3 -c "import json; d=json.load(open('$JUDGE_OUT')); print(sum(1 for x in d if x.get('verdict')=='unjudged'))")
echo "[reconcile] Judge results: match=$JUDGED_MATCH skip=$JUDGED_SKIP junk=$JUDGED_JUNK unjudged=$JUDGED_UNJ"

# ── Step 3: Append to ledger (atomic + dedupe) ───────────────────────────────
echo "[reconcile] Appending to ledger ..."

python3 -c "
import json, hashlib, os, sys

ledger_path = '$LEDGER_FILE'
judge_path = '$JUDGE_OUT'
run_ts = '$RUN_TS'
agent = '$AGENT'

# Load judged candidates
with open(judge_path) as f:
    judged = json.load(f)

# Build existing dedupe set from ledger (source_ref + evidence hash)
seen = set()
if os.path.exists(ledger_path):
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                key = entry.get('source_ref', '') + '|' + hashlib.sha256(entry.get('evidence','').encode()).hexdigest()
                seen.add(key)
            except json.JSONDecodeError:
                continue

new_rows = []
for j in judged:
    evidence = j.get('evidence', '')
    source_ref = j.get('source_ref', '')
    key = source_ref + '|' + hashlib.sha256(evidence.encode()).hexdigest()
    if key in seen:
        continue
    seen.add(key)
    row = {
        'ts': run_ts,
        'agent': agent,
        'candidate_id': j.get('id'),
        'type': j.get('candidate_type'),
        'verdict': j.get('verdict'),
        'rationale': j.get('rationale'),
        'evidence': evidence,
        'source_ref': source_ref,
    }
    new_rows.append(json.dumps(row))

if new_rows:
    # Atomic append: write to temp, append, fsync
    tmp_path = ledger_path + '.tmp.' + str(os.getpid())
    with open(tmp_path, 'w') as f:
        for row in new_rows:
            f.write(row + '\n')
        f.flush()
        os.fsync(f.fileno())
    with open(tmp_path, 'r') as f:
        data = f.read()
    with open(ledger_path, 'a') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.unlink(tmp_path)
    print(f'Wrote {len(new_rows)} new row(s) to ledger')
else:
    print('All candidates already in ledger; nothing new written.')
"

# ── Cleanup ──────────────────────────────────────────────────────────────────
rm -f "$SCAN_OUT" "$JUDGE_OUT"
echo "[reconcile] Done."
