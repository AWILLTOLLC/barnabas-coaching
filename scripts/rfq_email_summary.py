#!/usr/bin/env python3
"""
Check inbox for manufacturer RFQ replies and send a summary to Aaron.
Run at 7am PST via cron.
"""
import imaplib
import json
import email
from email.header import decode_header
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import sys

CREDS_PATH = Path("/root/.openclaw/credentials/email.json")
AARON_EMAIL = "a@kaw.cc"
CUTOFF_SUBJECT_KEYWORDS = ["auger", "rfq", "scotch", "black raven", "inquiry", "quotation", "quote"]

def load_creds():
    with open(CREDS_PATH) as f:
        return json.load(f)

def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8", errors="replace").strip()
    else:
        return msg.get_payload(decode=True).decode("utf-8", errors="replace").strip()
    return "(no plain text body)"

def check_inbox():
    creds = load_creds()
    mail = imaplib.IMAP4_SSL("posteo.de", 993)
    mail.login(creds["username"], creds["password"])
    mail.select("INBOX")

    # Search messages since yesterday
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'SINCE "{since}"')
    ids = messages[0].split()

    replies = []
    for mid in ids:
        status, data = mail.fetch(mid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        from_addr = decode_str(msg["From"])
        subject = decode_str(msg["Subject"])
        date = msg["Date"]
        to_addr = decode_str(msg["To"])

        # Skip messages from ourselves or Posteo support
        if "posteo.de" in from_addr and "support" in from_addr.lower():
            continue
        if "drubot@posteo.com" in from_addr or "augustcrane@posteo.com" in from_addr:
            continue

        body = get_body(msg)
        replies.append({
            "from": from_addr,
            "subject": subject,
            "date": date,
            "to": to_addr,
            "body": body[:1500]  # truncate for summary
        })

    mail.logout()
    return replies

def build_summary(replies):
    now = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    if not replies:
        return (
            f"Black Raven Manufacturer Outreach — Morning Summary\n"
            f"{now}\n\n"
            f"No replies received yet from manufacturer outreach. "
            f"Follow-ups may be warranted if nothing arrives by end of day.\n\n"
            f"— August"
        )

    lines = [
        f"Black Raven Manufacturer Outreach — Morning Summary",
        f"{now}",
        f"",
        f"{len(replies)} reply/replies received:",
        f"",
    ]
    for i, r in enumerate(replies, 1):
        lines.append(f"--- Reply {i} ---")
        lines.append(f"From: {r['from']}")
        lines.append(f"Subject: {r['subject']}")
        lines.append(f"Date: {r['date']}")
        lines.append(f"")
        lines.append(r['body'])
        lines.append("")

    lines.append("— August")
    return "\n".join(lines)

def send_summary(summary):
    subject = f"Manufacturer Outreach Summary — {datetime.now(timezone.utc).strftime('%b %d')}"
    result = subprocess.run(
        ["python3", "/root/.openclaw/workspace/scripts/send_email.py",
         AARON_EMAIL, subject, summary, "--from", "august"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("ERROR:", result.stderr, file=sys.stderr)

if __name__ == "__main__":
    replies = check_inbox()
    summary = build_summary(replies)
    send_summary(summary)
    print(f"Summary sent. {len(replies)} replies found.")
