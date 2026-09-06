#!/usr/bin/env python3
"""
Send email via Posteo SMTP.
Usage: python3 send_email.py <to> <subject> <body> [--from alias_key]
       python3 send_email.py <to> <subject> - [--from alias_key]

alias_key: key in credentials file aliases dict (default: use primary account)
"""
import smtplib
import sys
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

CREDS_PATH = Path("/Users/apollo/.openclaw/credentials/email.json")

def load_creds():
    with open(CREDS_PATH) as f:
        return json.load(f)

def send(to: str, subject: str, body: str, from_alias: str = None):
    creds = load_creds()

    # Determine from address
    if from_alias and from_alias in creds.get("aliases", {}):
        alias = creds["aliases"][from_alias]
        from_addr = alias["email"]
        from_name = alias["name"]
    else:
        from_addr = creds["username"]
        from_name = creds["from_name"]

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to
    msg["Subject"] = subject
    # Set Reply-To to blackraven.com alias if available
    reply_to = creds.get("aliases", {}).get(from_alias or "", {}).get("reply_to")
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(creds["smtp_host"], creds["smtp_port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(creds["username"], creds["password"])
        server.send_message(msg)

    raw = msg.as_bytes()
    # Save to Sent folder via IMAP
    try:
        import imaplib, time
        imap = imaplib.IMAP4_SSL(creds["smtp_host"], 993)
        imap.login(creds["username"], creds["password"])
        imap.append("Sent", "\\Seen", imaplib.Time2Internaldate(time.time()), raw)
        imap.logout()
    except Exception as e:
        print(f"Warning: could not save to Sent folder: {e}")

    print(f"Sent from {from_addr} to {to}: {subject}")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]

    if len(args) < 3:
        print("Usage: send_email.py <to> <subject> <body> [--from alias_key]")
        sys.exit(1)

    to = args[0]
    subject = args[1]
    body = args[2] if args[2] != "-" else sys.stdin.read()

    from_alias = None
    if "--from" in flags:
        idx = flags.index("--from")
        if idx + 1 < len(flags):
            from_alias = flags[idx + 1]

    send(to, subject, body, from_alias)
