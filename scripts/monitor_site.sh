#!/bin/bash
# Site uptime monitor — fires a Telegram alert if the site is down
# Runs via crontab, zero agent overhead

URL="https://letsgoglimmer.com/"
BOT_TOKEN="8423797372:AAH8erjtkA6EpSxIJ55ag_YyBKuGkKIp_cE"
CHAT_ID="5161266419"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$URL")

if [ "$STATUS" != "200" ]; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=⚠️ letsgoglimmer.com is DOWN (HTTP ${STATUS}). Check it: ${URL}" \
        > /dev/null
fi
