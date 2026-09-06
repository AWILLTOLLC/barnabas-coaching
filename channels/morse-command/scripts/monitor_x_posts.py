#!/usr/bin/env python3
"""
Morse Command — X Post Monitor
Polls X API v2 timelines for target accounts, scores posts for relevance to
Morse Command, and emails Aaron any new relevant posts via FastMail JMAP.

Primary: X API v2 (bearer token auth)
Fallback: Nitter RSS (if X API credits depleted)

Accounts tracked:
  @arrl          — ARRL, 45k followers
  @hamradio2dot0 — Community ham radio, 12k followers
  @cwmorse_us    — CW paddle maker (niche overlap)
  @aa9pw         — AA9PW.com ham/CW training
  @Ham_Radio_World — CW demos and engagement

Run nightly via cron. State persisted to seen_posts.json.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Optional, Tuple, List

# ── Config ────────────────────────────────────────────────────────────────────

WORKSPACE = Path("/Users/apollo/.openclaw/workspace/channels/morse-command")
CREDENTIALS_DIR = Path("/Users/apollo/.openclaw/credentials")
STATE_FILE = WORKSPACE / "scripts" / "seen_posts.json"
LOG_FILE = WORKSPACE / "scripts" / "monitor_x_posts.log"

X_CREDS_PATH = CREDENTIALS_DIR / "x_api.json"
FASTMAIL_CREDS = CREDENTIALS_DIR / "fastmail_dash.json"
JMAP_SESSION_URL = "https://api.fastmail.com/jmap/session"
ACCOUNT_ID = "uc3964053"
IDENTITY_ID = "177038383"
FROM_EMAIL = "dash@morsecommand.com"
FROM_NAME = "Morse Command"
TO_EMAIL = "aaron@merkleandbloom.com"
TO_NAME = "Aaron"

NITTER_BASE = "https://nitter.net"

# Max tweets to fetch per account per run (X API: 5–100)
MAX_RESULTS = 20

ACCOUNTS = [
    {"handle": "arrl",           "label": "ARRL",           "followers": "45k"},
    {"handle": "hamradio2dot0",  "label": "Ham Radio 2.0",  "followers": "12k"},
    {"handle": "cwmorse_us",     "label": "CW Morse US",    "followers": "small"},
    {"handle": "aa9pw",          "label": "AA9PW",          "followers": "small"},
    {"handle": "Ham_Radio_World","label": "Ham Radio World", "followers": "6k"},
]

# ── Relevance Scoring ─────────────────────────────────────────────────────────

KEYWORD_SCORES = {
    "morse": 10,
    "cw ": 8,
    "morse code": 12,
    "continuous wave": 8,
    "dit dah": 10,
    "dit-dah": 10,
    "koch": 10,
    "farnsworth": 8,
    "lcwo": 7,
    "cw ops": 7,
    "straight key": 8,
    "paddle": 7,
    "iambic": 7,
    "keyer": 7,
    "wpm": 6,
    "words per minute": 6,
    "qrs": 6,
    "qrq": 6,
    "cw trainer": 10,
    "code trainer": 7,
    "morse trainer": 10,
    "learn morse": 10,
    "morse practice": 10,
    "cw practice": 9,
    "morse app": 10,
    "ham app": 6,
    "radio app": 5,
    "amateur radio app": 7,
    "cw contest": 7,
    "morse contest": 8,
    "straight key night": 9,
    "skn": 7,
    "cq ww cw": 8,
    "cqww": 6,
    "naqp cw": 7,
    "ham radio": 4,
    "amateur radio": 4,
    "hf radio": 3,
    "qrz": 3,
    "arrl": 3,
    "technician": 2,
    "general class": 2,
    "extra class": 2,
    "license exam": 3,
    "radio license": 3,
    "ares": 2,
    "emcomm": 3,
    "prepper": 5,
    "off grid": 4,
    "emergency comm": 6,
    "grid down": 5,
    "shtf": 4,
    "survival radio": 5,
    "bug out": 3,
    "ios game": 5,
    "app store": 4,
    "mobile game": 3,
    "learn by playing": 5,
    "gamif": 5,
}

EXCLUDE_WORDS = ["cryptocurrency", "bitcoin", "nft", "defi", "crypto"]

RELEVANCE_THRESHOLD = 8


def score_post(text: str) -> Tuple[int, List[str]]:
    low = text.lower()
    for ex in EXCLUDE_WORDS:
        if ex in low:
            return 0, []
    score = 0
    matched = []
    for kw, points in KEYWORD_SCORES.items():
        if kw in low:
            score += points
            matched.append(kw.strip())
    return score, matched


# ── HTML stripping ────────────────────────────────────────────────────────────

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts).strip()


def strip_html(html_text: str) -> str:
    p = HTMLStripper()
    p.feed(html_text)
    return p.get_text()


# ── X API v2 ──────────────────────────────────────────────────────────────────

def load_bearer_token() -> str:
    creds = json.loads(X_CREDS_PATH.read_text())
    return creds["bearer_token"]


def x_get(path: str, bearer: str, params: dict = None) -> Optional[dict]:
    url = f"https://api.twitter.com/2/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        log(f"  X API error {e.code}: {body[:200]}")
        return None
    except Exception as e:
        log(f"  X API error: {e}")
        return None


def get_user_id(handle: str, bearer: str) -> Optional[str]:
    data = x_get(f"users/by/username/{handle}", bearer,
                 {"user.fields": "id"})
    if data and "data" in data:
        return data["data"]["id"]
    return None


def fetch_x_api(handle: str, bearer: str, since_id: str = None) -> list[dict]:
    """Fetch recent tweets via X API v2. Returns list of post dicts."""
    user_id = get_user_id(handle, bearer)
    if not user_id:
        log(f"  Could not resolve @{handle} via X API")
        return []

    params = {
        "max_results": MAX_RESULTS,
        "tweet.fields": "created_at,text,public_metrics",
        "exclude": "retweets",
    }
    if since_id:
        params["since_id"] = since_id

    data = x_get(f"users/{user_id}/tweets", bearer, params)
    if not data or "data" not in data:
        return []

    posts = []
    for tweet in data["data"]:
        tid = tweet["id"]
        text = tweet.get("text", "")
        created = tweet.get("created_at", "")
        x_link = f"https://x.com/{handle}/status/{tid}"
        posts.append({
            "id": tid,
            "handle": handle,
            "text": text,
            "link": x_link,
            "pub_raw": created,
            "pub_dt": None,
            "source": "xapi",
        })

    return posts


# ── Nitter RSS fallback ───────────────────────────────────────────────────────

def fetch_nitter_rss(handle: str) -> list[dict]:
    """Fallback: fetch from Nitter RSS."""
    url = f"{NITTER_BASE}/{handle}/rss"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if not data:
            return []
    except Exception as e:
        log(f"  Nitter RSS error for @{handle}: {e}")
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    posts = []
    for item in channel.findall("item"):
        guid_el = item.find("guid")
        link_el = item.find("link")
        title_el = item.find("title")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")

        guid = guid_el.text if guid_el is not None else None
        link = link_el.text if link_el is not None else ""
        title = title_el.text if title_el is not None else ""
        desc_html = desc_el.text if desc_el is not None else ""
        pub_raw = pub_el.text if pub_el is not None else ""

        x_link = f"https://x.com/{handle}/status/{guid}" if guid else link
        full_text = title + " " + strip_html(desc_html)

        try:
            pub_dt = parsedate_to_datetime(pub_raw)
        except Exception:
            pub_dt = None

        posts.append({
            "id": guid,
            "handle": handle,
            "text": full_text.strip(),
            "link": x_link,
            "pub_raw": pub_raw,
            "pub_dt": pub_dt,
            "source": "nitter",
        })

    return posts


def fetch_posts(handle: str, bearer: str, since_id: str = None) -> list[dict]:
    """Try Nitter RSS first, fall back to X API only if Nitter returns nothing."""
    posts = fetch_nitter_rss(handle)
    if posts:
        log(f"  Got {len(posts)} posts via Nitter RSS")
        return posts
    log(f"  Nitter returned nothing, falling back to X API...")
    posts = fetch_x_api(handle, bearer, since_id)
    log(f"  Got {len(posts)} posts via X API")
    return posts


# ── State ─────────────────────────────────────────────────────────────────────

def load_seen() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_seen(seen: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(seen, indent=2))


# ── FastMail JMAP ─────────────────────────────────────────────────────────────

def load_fastmail_token() -> str:
    return json.loads(FASTMAIL_CREDS.read_text())["api_token"]


def jmap_request(api_url: str, token: str, payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def get_jmap_api_url(token: str) -> str:
    req = urllib.request.Request(JMAP_SESSION_URL,
                                  headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["apiUrl"]


def get_drafts_id(api_url: str, token: str) -> str:
    result = jmap_request(api_url, token, {
        "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
        "methodCalls": [["Mailbox/get", {"accountId": ACCOUNT_ID}, "0"]]
    })
    for mb in result["methodResponses"][0][1]["list"]:
        if mb.get("role") == "drafts":
            return mb["id"]
    raise RuntimeError("Could not find Drafts mailbox")


def send_email(api_url: str, token: str, subject: str, body_text: str, body_html: str):
    drafts_id = get_drafts_id(api_url, token)
    email_obj = {
        "mailboxIds": {drafts_id: True},
        "from": [{"email": FROM_EMAIL, "name": FROM_NAME}],
        "to": [{"email": TO_EMAIL, "name": TO_NAME}],
        "subject": subject,
        "bodyValues": {
            "text": {"value": body_text, "charset": "utf-8"},
            "html": {"value": body_html, "charset": "utf-8"},
        },
        "textBody": [{"partId": "text", "type": "text/plain"}],
        "htmlBody": [{"partId": "html", "type": "text/html"}],
        "keywords": {"$draft": True},
    }
    payload = {
        "using": [
            "urn:ietf:params:jmap:core",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:submission",
        ],
        "methodCalls": [
            ["Email/set", {"accountId": ACCOUNT_ID, "create": {"draft1": email_obj}}, "0"],
            ["EmailSubmission/set", {
                "accountId": ACCOUNT_ID,
                "onSuccessUpdateEmail": {
                    "#send1": {
                        f"mailboxIds/{drafts_id}": None,
                        "keywords/$draft": None,
                        "keywords/$sent": True,
                    }
                },
                "create": {
                    "send1": {
                        "emailId": "#draft1",
                        "identityId": IDENTITY_ID,
                        "envelope": {
                            "mailFrom": {"email": FROM_EMAIL},
                            "rcptTo": [{"email": TO_EMAIL}],
                        },
                    }
                },
            }, "1"],
        ],
    }
    result = jmap_request(api_url, token, payload)
    if result["methodResponses"][0][1].get("notCreated"):
        raise RuntimeError(f"Email create failed: {result['methodResponses'][0][1]['notCreated']}")
    if result["methodResponses"][1][1].get("notCreated"):
        raise RuntimeError(f"Email send failed: {result['methodResponses'][1][1]['notCreated']}")
    log("  Email sent OK")


# ── Email formatting ──────────────────────────────────────────────────────────

def build_email(hits: List[dict]) -> Tuple[str, str, str]:
    count = len(hits)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"Morse Command — {count} X post{'s' if count > 1 else ''} worth replying to ({date_str})"

    lines_text = []
    lines_html = [
        "<html><body style='font-family:sans-serif;color:#111'>",
        f"<h2 style='color:#0055aa'>Morse Command — X Monitoring Report</h2>",
        f"<p><strong>{date_str}</strong> · {count} relevant post{'s' if count > 1 else ''} found</p>",
        "<hr>",
    ]

    for h in hits:
        handle = h["handle"]
        label = h.get("label", handle)
        text = h["text"]
        link = h["link"]
        score = h["score"]
        matched = h["matched"]
        pub = h.get("pub_raw", "")

        lines_text += [
            f"@{handle} ({label})",
            f"Score: {score} | Keywords: {', '.join(matched)}",
            f"Posted: {pub}" if pub else "",
            f"Post: {text[:280]}",
            f"Link: {link}",
            "",
        ]

        kw_str = " · ".join(
            f"<code style='background:#e8eef8;padding:2px 5px;border-radius:3px'>{kw}</code>"
            for kw in matched
        )
        lines_html += [
            "<div style='margin-bottom:24px;padding:16px;border-left:4px solid #0055aa;background:#f5f8ff'>",
            f"<p style='margin:0 0 4px'><strong>@{handle}</strong> <span style='color:#666'>({label})</span></p>",
            f"<p style='margin:0 0 8px;color:#888;font-size:13px'>{pub}</p>" if pub else "",
            f"<p style='margin:0 0 8px'>{text[:400]}</p>",
            f"<p style='margin:0 0 8px'><a href='{link}' style='color:#0055aa'>→ View on X</a></p>",
            f"<p style='margin:0;font-size:12px;color:#666'>Score {score} · {kw_str}</p>",
            "</div>",
        ]

    lines_html += [
        "<hr><p style='font-size:12px;color:#999'>Sent by Dash · Morse Command growth engine</p>",
        "</body></html>",
    ]

    return subject, "\n".join(lines_text), "\n".join(lines_html)


# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=== X Post Monitor starting ===")
    seen = load_seen()

    try:
        bearer = load_bearer_token()
    except Exception as e:
        log(f"ERROR loading X credentials: {e}")
        sys.exit(1)

    hits = []
    new_seen = {}

    for acct in ACCOUNTS:
        handle = acct["handle"]
        label = acct["label"]
        log(f"Checking @{handle} ({label})...")

        # Pass highest seen ID for this account so API returns only newer tweets
        since_id = seen.get(f"_since_{handle}")
        posts = fetch_posts(handle, bearer, since_id)

        # Track the newest ID for next run
        if posts:
            valid_ids = [p["id"] for p in posts if p["id"] and not p["id"].startswith("http")]
            if valid_ids:
                newest_id = max(valid_ids)
                new_seen[f"_since_{handle}"] = newest_id

        for post in posts:
            pid = post["id"]
            if pid is None:
                continue
            new_seen[pid] = True

            if pid in seen:
                continue

            score, matched = score_post(post["text"])
            log(f"  [{pid}] score={score} kw={matched} — {post['text'][:60]}...")

            if score >= RELEVANCE_THRESHOLD:
                hits.append({**post, "label": label, "score": score, "matched": matched})

    merged_seen = {**seen, **new_seen}
    save_seen(merged_seen)
    log(f"State saved. {len(new_seen)} updates, {len(merged_seen)} total keys.")

    if not hits:
        log("No relevant posts found. No email sent.")
        log("=== Done ===")
        return

    hits.sort(key=lambda h: h["score"], reverse=True)
    log(f"Found {len(hits)} relevant post(s). Sending email...")

    try:
        token = load_fastmail_token()
        api_url = get_jmap_api_url(token)
        subject, body_text, body_html = build_email(hits)
        send_email(api_url, token, subject, body_text, body_html)
        log(f"Email sent: {subject}")
    except Exception as e:
        log(f"ERROR sending email: {e}")
        sys.exit(1)

    log("=== Done ===")


if __name__ == "__main__":
    main()
