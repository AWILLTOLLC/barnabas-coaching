#!/usr/bin/env python3
"""
FastMail JMAP email sender for Morse Command outreach.
Usage: python3 send_email.py --to email@example.com --subject "Subject" --body body.txt
       python3 send_email.py --bulk contacts.csv --template template.txt
"""

import json
import argparse
import csv
import sys
import time
import re
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

CREDENTIALS_PATH = "/root/.openclaw/credentials/fastmail_dash.json"
JMAP_SESSION_URL = "https://api.fastmail.com/jmap/session"
ACCOUNT_ID = "uc3964053"
IDENTITY_ID = "177038383"  # dash@morsecommand.com sending identity

def load_token():
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)
    return creds["api_token"]

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def get_api_url(token):
    resp = requests.get(JMAP_SESSION_URL, headers=get_headers(token))
    resp.raise_for_status()
    return resp.json()["apiUrl"]

def get_mailbox_id(token, api_url, role="sent"):
    """Get mailbox ID by role (sent, drafts, inbox, etc.)"""
    payload = {
        "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
        "methodCalls": [
            ["Mailbox/get", {"accountId": ACCOUNT_ID}, "0"]
        ]
    }
    resp = requests.post(api_url, headers=get_headers(token), json=payload)
    resp.raise_for_status()
    result = resp.json()
    mailboxes = result["methodResponses"][0][1]["list"]
    for mb in mailboxes:
        if mb.get("role") == role:
            return mb["id"]
    return None

def send_email(token, api_url, to_email, to_name, subject, body_text, body_html=None, draft_only=False):
    """Send a single email via JMAP. Returns (success, message_id, error)."""
    drafts_id = get_mailbox_id(token, api_url, "drafts")
    
    email_body = [{"partId": "text", "type": "text/plain"}]
    body_values = {"text": {"value": body_text, "charset": "utf-8"}}
    
    if body_html:
        email_body.append({"partId": "html", "type": "text/html"})
        body_values["html"] = {"value": body_html, "charset": "utf-8"}

    email_obj = {
        "mailboxIds": {drafts_id: True},
        "from": [{"email": "dash@morsecommand.com", "name": "Morse Command"}],
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "bodyValues": body_values,
        "textBody": [{"partId": "text", "type": "text/plain"}],
        "keywords": {"$draft": True},
    }
    
    if body_html:
        email_obj["htmlBody"] = [{"partId": "html", "type": "text/html"}]

    # Step 1: Create draft
    create_payload = {
        "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail", "urn:ietf:params:jmap:submission"],
        "methodCalls": [
            ["Email/set", {
                "accountId": ACCOUNT_ID,
                "create": {"draft1": email_obj}
            }, "0"],
        ]
    }
    
    if not draft_only:
        create_payload["methodCalls"].append(
            ["EmailSubmission/set", {
                "accountId": ACCOUNT_ID,
                "onSuccessUpdateEmail": {
                    "#send1": {
                        "mailboxIds/{drafts_id}": None,
                        "keywords/$draft": None,
                        "keywords/$sent": True
                    }
                },
                "create": {
                    "send1": {
                        "emailId": "#draft1",
                        "identityId": IDENTITY_ID,
                        "envelope": {
                            "mailFrom": {"email": "dash@morsecommand.com"},
                            "rcptTo": [{"email": to_email}]
                        }
                    }
                }
            }, "1"]
        )
    
    resp = requests.post(api_url, headers=get_headers(token), json=create_payload)
    resp.raise_for_status()
    result = resp.json()
    
    # Check for errors
    email_set_result = result["methodResponses"][0][1]
    if "notCreated" in email_set_result and email_set_result["notCreated"]:
        return False, None, str(email_set_result["notCreated"])
    
    email_id = email_set_result["created"]["draft1"]["id"]
    
    if draft_only:
        return True, email_id, None
    
    submission_result = result["methodResponses"][1][1]
    if "notCreated" in submission_result and submission_result["notCreated"]:
        return False, email_id, str(submission_result["notCreated"])
    
    return True, email_id, None

def render_template(template_text, variables):
    """Replace {{VAR}} placeholders in template with values."""
    for key, value in variables.items():
        template_text = template_text.replace(f"{{{{{key}}}}}", value)
    return template_text

def send_bulk(token, api_url, contacts_csv, template_file, subject_template, dry_run=False, delay_sec=2):
    """Send to multiple contacts from CSV. CSV columns: email,name,[extra vars...]"""
    template_text = Path(template_file).read_text()
    
    results = {"sent": [], "failed": [], "skipped": []}
    
    with open(contacts_csv) as f:
        reader = csv.DictReader(f)
        contacts = list(reader)
    
    print(f"{'DRY RUN: ' if dry_run else ''}Sending to {len(contacts)} contacts...")
    
    for i, contact in enumerate(contacts):
        email = contact.get("email", "").strip()
        name = contact.get("name", "").strip()
        
        if not email or "@" not in email:
            print(f"  [{i+1}/{len(contacts)}] SKIP (no valid email): {contact}")
            results["skipped"].append(contact)
            continue
        
        # Render template with contact variables
        body = render_template(template_text, contact)
        subject = render_template(subject_template, contact)
        
        if dry_run:
            print(f"  [{i+1}/{len(contacts)}] WOULD SEND to {name} <{email}>")
            print(f"    Subject: {subject}")
            print(f"    Body preview: {body[:100]}...")
            results["sent"].append({"email": email, "name": name, "status": "dry_run"})
            continue
        
        success, msg_id, error = send_email(token, api_url, email, name, subject, body)
        
        if success:
            print(f"  [{i+1}/{len(contacts)}] SENT to {name} <{email}> — ID: {msg_id}")
            results["sent"].append({"email": email, "name": name, "status": "sent", "id": msg_id})
        else:
            print(f"  [{i+1}/{len(contacts)}] FAILED to {name} <{email}> — {error}")
            results["failed"].append({"email": email, "name": name, "error": error})
        
        if i < len(contacts) - 1:
            time.sleep(delay_sec)
    
    print(f"\nResults: {len(results['sent'])} sent, {len(results['failed'])} failed, {len(results['skipped'])} skipped")
    return results

def main():
    parser = argparse.ArgumentParser(description="Morse Command email sender via FastMail JMAP")
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--name", default="", help="Recipient name")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Body text (inline)")
    parser.add_argument("--body-file", help="Body text file path")
    parser.add_argument("--bulk", help="CSV file for bulk send")
    parser.add_argument("--template", help="Template file for bulk send")
    parser.add_argument("--subject-template", help="Subject template for bulk send")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between bulk sends (seconds)")
    args = parser.parse_args()

    token = load_token()
    api_url = get_api_url(token)
    print(f"Connected: dash@morsecommand.com → {api_url}")

    if args.bulk:
        if not args.template:
            print("Error: --template required for bulk send")
            sys.exit(1)
        subject_template = args.subject_template or "Morse Command — new iOS app for Morse code training"
        send_bulk(token, api_url, args.bulk, args.template, subject_template, args.dry_run, args.delay)

    elif args.to:
        if not args.subject:
            print("Error: --subject required")
            sys.exit(1)
        body = args.body
        if args.body_file:
            body = Path(args.body_file).read_text()
        if not body:
            print("Error: --body or --body-file required")
            sys.exit(1)
        success, msg_id, error = send_email(token, api_url, args.to, args.name, args.subject, body, draft_only=args.dry_run)
        if success:
            print(f"{'Draft created' if args.dry_run else 'Sent'}: {msg_id}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
