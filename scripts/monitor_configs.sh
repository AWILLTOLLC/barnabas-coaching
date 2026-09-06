#!/bin/bash
# Config File Audit
# Checksums key config files and alerts if anything changed since last run
# On first run, creates the baseline

BASELINE="/Users/apollo/.openclaw/workspace/scripts/.config_baseline"
TELEGRAM_TARGET="5161266419"

# Files to watch
WATCH_FILES=(
  "/etc/ssh/sshd_config"
  "/etc/sudoers"
  "/etc/hosts"
  "/etc/passwd"
  "/etc/shadow"
  "/etc/crontab"
  "/etc/ufw/user.rules"
  "/Users/apollo/.ssh/authorized_keys"
)

# Build current checksums (only for files that exist)
CURRENT=$(for f in "${WATCH_FILES[@]}"; do
  [ -f "$f" ] && sha256sum "$f" 2>/dev/null
done)

if [ ! -f "$BASELINE" ]; then
  echo "$CURRENT" > "$BASELINE"
  echo "Config baseline created ($(echo "$CURRENT" | wc -l) files tracked)."
  exit 0
fi

# Compare against baseline
DIFF=$(diff <(sort "$BASELINE") <(echo "$CURRENT" | sort))

if [ -n "$DIFF" ]; then
  CHANGED=$(echo "$DIFF" | grep '^[<>]' | awk '{print $NF}' | sort -u | tr '\n' ' ')
  MSG="🚨 Config Change Detected on $(hostname)
Changed files: ${CHANGED}
Run: sha256sum ${WATCH_FILES[*]} to inspect."
  openclaw message send --channel telegram --target "$TELEGRAM_TARGET" --message "$MSG"
  # Update baseline after alerting
  echo "$CURRENT" > "$BASELINE"
fi
