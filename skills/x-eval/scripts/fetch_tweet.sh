#!/bin/bash
# fetch_tweet.sh <tweet-url>
# Fetches an X/Twitter post via the fxTwitter API (no key, no login) and
# prints trimmed JSON: author, text, metrics, quote tweet, media, poll.
set -euo pipefail

URL="${1:?usage: fetch_tweet.sh <tweet-url>}"

# Accept x.com / twitter.com / fxtwitter / vxtwitter / nitter forms, with or
# without query strings. Capture handle + status id.
if [[ "$URL" =~ ^https?://([a-z0-9.-]+\.)?(x|twitter|fxtwitter|vxtwitter|fixupx)\.com/([A-Za-z0-9_]+)/status(es)?/([0-9]+)([/?#]|$) ]]; then
  HANDLE="${BASH_REMATCH[3]}"
  ID="${BASH_REMATCH[5]}"
else
  echo '{"error":"not a recognizable X/Twitter status URL"}' >&2
  exit 1
fi

curl -sf --max-time 15 "https://api.fxtwitter.com/${HANDLE}/status/${ID}" | python3 -c '
import json, sys

d = json.load(sys.stdin)
if d.get("code") != 200:
    print(json.dumps({"error": f"fxtwitter returned {d.get('"'"'code'"'"')}: {d.get('"'"'message'"'"')}"}))
    sys.exit(0)

def trim(t):
    if not t:
        return None
    a = t.get("author") or {}
    out = {
        "author": {
            "name": a.get("name"),
            "handle": a.get("screen_name"),
            "followers": a.get("followers"),
            "verified_type": a.get("verified_type") or ("verified" if a.get("verified") else None),
            "description": a.get("description"),
        },
        "text": t.get("text"),
        "created_at": t.get("created_at"),
        "metrics": {k: t.get(k) for k in ("likes", "retweets", "replies", "views", "bookmarks") if t.get(k) is not None},
        "lang": t.get("lang"),
    }
    media = (t.get("media") or {}).get("all") or []
    if media:
        out["media"] = [{"type": m.get("type"), "alt": m.get("altText")} for m in media]
    if t.get("poll"):
        out["poll"] = [{"label": c.get("label"), "pct": c.get("percentage")} for c in t["poll"].get("choices", [])]
    if t.get("article"):
        out["article_preview"] = (t["article"].get("text") or "")[:2000]
    return out

tweet = d.get("tweet") or {}
result = trim(tweet)
if tweet.get("quote"):
    result["quoted_tweet"] = trim(tweet["quote"])
if tweet.get("replying_to"):
    result["replying_to"] = tweet.get("replying_to")
print(json.dumps(result, ensure_ascii=False, indent=1))
'
