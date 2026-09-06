#!/usr/bin/env python3
"""
Barnabas Coaching Reddit Scanner
Scans SMB / AI / Seattle subreddits daily for posts from the last 24 hours
where Aaron can add genuine value. Emails a digest.

Usage: python3 barnabas_reddit_scan.py
"""

import json
import urllib.request
import datetime
import subprocess
import sys

# ── Config ────────────────────────────────────────────────────────────────
EMAIL_SCRIPT = "/Users/apollo/.openclaw/workspace/scripts/send_email.py"
AARON_EMAIL  = "a@kaw.cc"
LOOKBACK_HOURS = 24

SUBREDDITS = [
    "smallbusiness",
    "Entrepreneur",
    "Seattle",
    "artificial",
    "ChatGPT",
    "LocalLLaMA",
    "automation",
    "startups",
    "business",
    "productivity",
]

FEEDS = ["new", "hot"]
POSTS_PER_FEED = 30

HEADERS = {"User-Agent": "barnabas-coaching-research/1.0 (personal community research)"}

# Strong signals — someone actively wrestling with AI adoption or needing guidance
STRONG_KEYWORDS = [
    "ai consultant", "ai consulting", "hire ai", "ai strategy",
    "implement ai", "ai implementation", "ai for my business",
    "where to start with ai", "don't know where to start",
    "ai overwhelmed", "ai confused", "ai advice", "ai help",
    "automate my business", "ai automation", "is ai worth it",
    "ai roi", "ai not working", "ai failed", "wasted on ai",
    "how do i use ai", "ai for small business", "smb ai",
    "seattle business", "seattle startup", "seattle entrepreneur",
    "ai consultant seattle", "technology consultant seattle",
]

# Moderate signals — general AI/business frustration or exploration
MODERATE_KEYWORDS = [
    "ai", "chatgpt", "claude", "llm", "machine learning",
    "automation", "productivity", "consultant", "workflow",
    "digital transformation", "tech stack",
]

# Skip these — false positives
SKIP_IF_CONTAINS = [
    "sci-fi", "movie", "game", "art", "generated image", "midjourney",
    "stable diffusion", "dall-e", "meme", "funny", "dating",
    "relationship", "fitness", "recipe",
]

# ── Core logic ────────────────────────────────────────────────────────────

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
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=LOOKBACK_HOURS)
    post_time = datetime.datetime.fromtimestamp(created_utc, tz=datetime.timezone.utc)
    return post_time >= cutoff


def score_post(title: str, selftext: str, flair: str = "") -> tuple:
    title_lower = title.lower()
    body_lower  = (selftext or "").lower()
    flair_lower = (flair or "").lower()

    # Skip obvious false positives
    full_text = title_lower + " " + body_lower
    if any(skip in full_text for skip in SKIP_IF_CONTAINS):
        return 0, []

    strong_matched   = [kw for kw in STRONG_KEYWORDS   if kw in full_text]
    moderate_matched = [kw for kw in MODERATE_KEYWORDS if kw in title_lower]

    # Need strong keyword OR 3+ moderate keywords in title
    if len(strong_matched) == 0 and len(moderate_matched) < 3:
        return 0, []

    score = len(strong_matched) * 3 + len(moderate_matched)
    return score, strong_matched + moderate_matched


def scan() -> list:
    seen_urls = set()
    candidates = []

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
                flair    = d.get("link_flair_text", "") or ""
                score, matched = score_post(title, selftext, flair)

                if score == 0:
                    continue

                created = datetime.datetime.fromtimestamp(
                    d["created_utc"], tz=datetime.timezone.utc)
                age_hrs = int((datetime.datetime.now(datetime.timezone.utc) - created).total_seconds() / 3600)
                upvotes = d.get("ups", 0)
                num_comments = d.get("num_comments", 0)

                candidates.append({
                    "sub":      sub,
                    "title":    title,
                    "url":      url,
                    "matched":  matched,
                    "score":    score,
                    "age_hrs":  age_hrs,
                    "upvotes":  upvotes,
                    "comments": num_comments,
                    "preview":  selftext[:300] if selftext else "(no body)",
                })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:10]


def format_digest(posts: list) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    lines = [
        f"Barnabas Coaching — Reddit Opportunity Digest",
        f"{date_str} | Last 24 hours | {len(posts)} post(s) flagged",
        "",
        "These are real people asking real questions about AI adoption.",
        "Only engage where you have something genuinely useful to say.",
        "Post as Aaron, not as Barnabas Coaching.",
        "=" * 65,
    ]

    for i, p in enumerate(posts, 1):
        age_str = f"{p['age_hrs']}h ago"
        lines += [
            f"\n{i}. r/{p['sub']} | {age_str} | {p['upvotes']} upvotes | {p['comments']} comments",
            f"   {p['title']}",
            f"   Signals: {', '.join(p['matched'][:5])}",
            f"   Preview: {p['preview'][:200]}{'...' if len(p['preview']) > 200 else ''}",
            f"   Link: {p['url']}",
        ]

    lines += [
        "\n" + "=" * 65,
        "Sent by Maven — barnabas.coach",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print("Scanning Reddit for Barnabas Coaching opportunities...")
    posts = scan()

    if not posts:
        print("Nothing relevant in the last 24 hours. No email sent.")
        sys.exit(0)

    digest = format_digest(posts)
    today = datetime.date.today().strftime("%b %d")
    result = subprocess.run(
        ["python3", EMAIL_SCRIPT,
         AARON_EMAIL,
         f"Barnabas Reddit Digest — {today}",
         digest],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"Sent — {len(posts)} post(s) flagged.")
    else:
        print(f"Email failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
