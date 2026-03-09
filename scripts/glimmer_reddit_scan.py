#!/usr/bin/env python3
"""
Glimmer Cards Reddit Scanner
Scans rave/festival subreddits daily for posts from the last 7 days
where an authentic Glimmer Cards comment could add real value.
Emails Aaron a digest of flagged posts. Stays quiet if nothing found.

Usage: python3 glimmer_reddit_scan.py
"""

import json
import urllib.request
import datetime
import subprocess
import sys

# ── Config ──────────────────────────────────────────────────────────────────
EMAIL_SCRIPT = "/root/.openclaw/workspace/scripts/send_email.py"
AARON_EMAIL  = "a@kaw.cc"
LOOKBACK_DAYS = 7

SUBREDDITS = [
    "aves",
    "electricdaisycarnival",
    "festivals",
    "plur",
    "raves",
]

FEEDS = ["new", "hot"]
POSTS_PER_FEED = 25

HEADERS = {"User-Agent": "glimmer-cards-community-scanner/1.0 (personal research)"}

# Strong single-word triggers — any one of these in title alone is a flag
STRONG_KEYWORDS = [
    "gifting", "gift", "compliment", "connection",
    "feel seen", "felt seen", "meaningful", "trinket",
    "wholesome", "what to bring", "spread love", "spread the love",
    "made my night", "made me feel", "kind stranger",
    "random act", "give away", "something to give",
    "first rave", "bucket list", "bring something",
]

# Weak keywords — only count if 2+ present together
WEAK_KEYWORDS = ["plur", "love", "vibes", "community"]

# If any of these dominate the title, skip (false positive filter)
SKIP_IF_TITLE_CONTAINS = [
    "outfit", "organizer", "platform", "ticket", "lineup",
    "set time", "drug", "hotel", "wristband", "shuttle",
    "camping spot", "rv waitlist", "merch",
]

# ── Core logic ───────────────────────────────────────────────────────────────

def fetch_posts(subreddit: str, feed: str) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/{feed}.json?limit={POSTS_PER_FEED}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read()).get("data", {}).get("children", [])
    except Exception as e:
        print(f"  Fetch error r/{subreddit}/{feed}: {e}", file=sys.stderr)
        return []


def is_within_lookback(created_utc: float) -> bool:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=LOOKBACK_DAYS)
    post_time = datetime.datetime.fromtimestamp(created_utc, tz=datetime.timezone.utc)
    return post_time >= cutoff


def score_post(title: str, selftext: str) -> tuple[int, list]:
    title_lower   = title.lower()
    body_lower    = selftext.lower() if selftext else ""

    # Bail out if title looks like a false-positive topic
    if any(skip in title_lower for skip in SKIP_IF_TITLE_CONTAINS):
        return 0, []

    full_text = title_lower + " " + body_lower
    strong_matched = [kw for kw in STRONG_KEYWORDS if kw in full_text]
    weak_matched   = [kw for kw in WEAK_KEYWORDS   if kw in full_text]

    # Need at least 1 strong keyword OR 2+ weak keywords
    if len(strong_matched) == 0 and len(weak_matched) < 2:
        return 0, []

    score = len(strong_matched) * 2 + len(weak_matched)
    return score, strong_matched + weak_matched


def scan() -> list:
    seen_urls: set = set()
    candidates   = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=LOOKBACK_DAYS)

    for sub in SUBREDDITS:
        for feed in FEEDS:
            for p in fetch_posts(sub, feed):
                d   = p.get("data", {})
                url = f"https://reddit.com{d.get('permalink','')}"
                if url in seen_urls:
                    continue

                if not is_within_lookback(d.get("created_utc", 0)):
                    continue

                seen_urls.add(url)
                title    = d.get("title", "").strip()
                selftext = d.get("selftext", "").strip()
                score, matched = score_post(title, selftext)

                if score == 0:
                    continue

                created = datetime.datetime.fromtimestamp(
                    d["created_utc"], tz=datetime.timezone.utc)
                age_days = (datetime.datetime.now(datetime.timezone.utc) - created).days

                candidates.append({
                    "sub":     sub,
                    "title":   title,
                    "url":     url,
                    "matched": matched,
                    "score":   score,
                    "age":     age_days,
                })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:7]


def format_digest(posts: list) -> str:
    today = datetime.date.today().strftime("%B %d, %Y")
    lines = [
        f"🃏 Glimmer Cards Reddit Digest — {today}",
        f"{len(posts)} post(s) flagged from the last {LOOKBACK_DAYS} days.",
        "",
        "Only comment where you genuinely have something to add.",
        "Post as yourself (@rave.witcher), not as the brand.",
        "=" * 60,
    ]

    for i, p in enumerate(posts, 1):
        age_str = "today" if p["age"] == 0 else f"{p['age']}d ago"
        lines += [
            f"\n{i}. [{p['sub']} | {age_str}] {p['title']}",
            f"   Matched:  {', '.join(p['matched'])}",
            f"   Link:     {p['url']}",
        ]

    lines += [
        "\n" + "=" * 60,
        "Sent by Dru 🧙 — letsgoglimmer.com",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print("Scanning Reddit for Glimmer Cards opportunities...")
    posts = scan()

    if not posts:
        print("Nothing relevant in the last 7 days. No email sent.")
        sys.exit(0)

    digest = format_digest(posts)
    result = subprocess.run(
        ["python3", EMAIL_SCRIPT,
         AARON_EMAIL,
         f"🃏 Glimmer Cards Reddit Digest — {datetime.date.today()}",
         digest],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"Sent — {len(posts)} post(s) flagged.")
    else:
        print(f"Email failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
