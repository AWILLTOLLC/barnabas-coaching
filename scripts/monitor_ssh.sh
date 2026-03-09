#!/bin/bash
# SSH Failed Login Monitor
# Checks the last 10 minutes of journal for brute-force attempts
# Alerts via OpenClaw if any single IP hits 5+ failures

THRESHOLD=5
WINDOW="10 minutes ago"
TELEGRAM_TARGET="5161266419"

# Get failed SSH attempts from the last 10 min
FAILURES=$(journalctl _SYSTEMD_UNIT=ssh.service --since "$WINDOW" 2>/dev/null | \
  grep -oP '(?<=from )\d+\.\d+\.\d+\.\d+' | \
  sort | uniq -c | sort -rn)

if [ -z "$FAILURES" ]; then
  exit 0
fi

# Check if any IP exceeds the threshold
ALERT=""
while IFS= read -r line; do
  COUNT=$(echo "$line" | awk '{print $1}')
  IP=$(echo "$line" | awk '{print $2}')
  if [ "$COUNT" -ge "$THRESHOLD" ]; then
    ALERT="${ALERT}⚠️ ${COUNT} failed SSH attempts from ${IP}\n"
  fi
done <<< "$FAILURES"

if [ -n "$ALERT" ]; then
  MSG="🚨 SSH Alert on $(hostname)\n${ALERT}Check: journalctl _SYSTEMD_UNIT=ssh.service --since '10 minutes ago'"
  openclaw message send --channel telegram --target "$TELEGRAM_TARGET" --message "$(echo -e "$MSG")"
fi
