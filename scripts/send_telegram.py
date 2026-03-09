#!/usr/bin/env python3
"""Send a Telegram message via the bot API. Usage: send_telegram.py <chat_id> <message>"""
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

def get_bot_token():
    config = json.loads(Path("/root/.openclaw/openclaw.json").read_text())
    return config['channels']['telegram']['botToken']

def send(chat_id, text):
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": ""
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: send_telegram.py <chat_id> <message>")
        sys.exit(1)
    result = send(sys.argv[1], sys.argv[2])
    print("ok" if result.get("ok") else f"error: {result}")
