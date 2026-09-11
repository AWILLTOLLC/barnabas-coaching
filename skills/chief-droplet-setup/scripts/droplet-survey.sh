#!/usr/bin/env bash
# Survey a customer droplet without tripping UFW limit / fail2ban.
# Usage: ./droplet-survey.sh <IP>
set -u
IP="${1:?usage: droplet-survey.sh <IP>}"
KEY="$HOME/.ssh/id_ed25519_barnabas_droplet"
OUT=/tmp/droplet-survey.txt
: > "$OUT"

# Bounded retry: never hammer; wait between attempts.
for i in 1 2 3 4 5 6; do
  sleep 20
  echo "--- attempt $i $(date +%T)" >> "$OUT"
  if ssh -i "$KEY" -o IdentitiesOnly=yes -o ConnectTimeout=10 "root@$IP" \
    'nproc; free -h | head -2; ps aux | grep -i openclaw | grep -v grep | head -4; ls /home/; swapon --show; df -h / | tail -1; grep PRETTY /etc/os-release' >> "$OUT" 2>&1; then
    echo "done exit=0" >> "$OUT"; exit 0
  fi
done
echo "all attempts failed" >> "$OUT"; exit 1
