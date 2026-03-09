#!/usr/bin/env python3
"""
Monitor a Reddit thread for new comments and send Telegram alerts.
Run via cron every 3 hours.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/root/.openclaw/workspace/tasks/reddit-monitor/state.json")
AARON_TELEGRAM_ID = "5161266419"

# Comments that likely need a response (questions, issues, feedback)
RESPONSE_KEYWORDS = [
    "?", "how", "when", "why", "will", "can", "does", "is there", "would",
    "invite", "link", "code", "crash", "bug", "error", "broken", "doesn't",
    "don't", "not working", "ipad", "android", "suggestion", "feature",
    "feedback", "issue", "problem", "help"
]

def fetch_comments(thread_id):
    url = f"https://www.reddit.com/comments/{thread_id}/.json?limit=100"
    result = subprocess.run(
        ["curl", "-s", "-A",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         url],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    comments = []
    children = data[1]['data']['children']
    for c in children:
        if c['kind'] == 't1':
            d = c['data']
            comments.append({
                "id": d['id'],
                "author": d['author'],
                "body": d['body'],
                "score": d.get('score', 0),
                "created_utc": d['created_utc']
            })
    return comments

def needs_response(comment):
    body_lower = comment['body'].lower()
    return any(kw in body_lower for kw in RESPONSE_KEYWORDS)

def send_telegram(message):
    subprocess.run(
        ["python3", "/root/.openclaw/workspace/scripts/send_telegram.py",
         AARON_TELEGRAM_ID, message],
        capture_output=True
    )

def load_state():
    return json.loads(STATE_FILE.read_text())

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def run():
    state = load_state()
    known_ids = set(state['known_ids'])

    try:
        comments = fetch_comments(state['thread_id'])
    except Exception as e:
        print(f"Error fetching comments: {e}", file=sys.stderr)
        return

    new_comments = [c for c in comments if c['id'] not in known_ids]

    if not new_comments:
        print(f"No new comments. Total known: {len(known_ids)}")
        state['last_checked'] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    # Update known IDs
    for c in new_comments:
        known_ids.add(c['id'])
    state['known_ids'] = list(known_ids)
    state['last_checked'] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    # Filter for ones that likely need a response
    actionable = [c for c in new_comments if needs_response(c)]
    non_actionable = [c for c in new_comments if not needs_response(c)]

    # Build telegram message
    lines = [f"🎮 Morse Command — {len(new_comments)} new comment(s) on r/HamRadio\n"]

    if actionable:
        lines.append(f"⚠️ {len(actionable)} may need a response:\n")
        for c in actionable:
            lines.append(f"u/{c['author']}:")
            lines.append(f"{c['body'][:280]}")
            if len(c['body']) > 280:
                lines.append("...")
            lines.append("")

    if non_actionable:
        lines.append(f"💬 {len(non_actionable)} other new comment(s):\n")
        for c in non_actionable:
            lines.append(f"u/{c['author']}: {c['body'][:150]}")
            lines.append("")

    lines.append(f"🔗 https://www.reddit.com/r/HamRadio/comments/{state['thread_id']}/")

    message = "\n".join(lines)
    send_telegram(message)
    print(f"Sent Telegram alert: {len(new_comments)} new comments ({len(actionable)} actionable)")

if __name__ == "__main__":
    run()
