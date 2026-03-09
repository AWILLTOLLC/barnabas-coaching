#!/bin/bash
# Disk Space Monitor
# Alerts via OpenClaw if any partition hits 90% or above

THRESHOLD=90
TELEGRAM_TARGET="5161266419"

ALERT=""
while IFS= read -r line; do
  USE=$(echo "$line" | awk '{print $5}' | tr -d '%')
  MOUNT=$(echo "$line" | awk '{print $6}')
  FS=$(echo "$line" | awk '{print $1}')
  if [ -n "$USE" ] && [ "$USE" -ge "$THRESHOLD" ] 2>/dev/null; then
    ALERT="${ALERT}⚠️ ${MOUNT} is at ${USE}% (${FS})\n"
  fi
done < <(df -h | tail -n +2)

if [ -n "$ALERT" ]; then
  MSG="🚨 Disk Alert on $(hostname)\n${ALERT}Run: df -h"
  openclaw message send --channel telegram --target "$TELEGRAM_TARGET" --message "$(echo -e "$MSG")"
fi
