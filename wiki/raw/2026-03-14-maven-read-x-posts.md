---
source: /Users/apollo/.openclaw/workspace/channels/marketing/references/read-x-posts.md
fetched: 2026-09-11
type: internal-doc
source-path: channels/marketing/references/read-x-posts.md
---

# How to Read X Posts (Tweet Fetching)

**Status:** Solved. Use the script below — do NOT use web_fetch or browser for X URLs.

---

## The Problem

- `web_fetch` on x.com always fails (JS-gated, privacy extension errors)
- Browser tool is often unavailable or slow
- Nitter instances are unreliable

## The Solution: X API v2 + Script

**Credentials:** `/Users/apollo/.openclaw/credentials/x_api.json`
**Script:** `scripts/read_x_post.py` (in this workspace)

### Usage

```bash
python3 /Users/apollo/.openclaw/workspace/channels/marketing/scripts/read_x_post.py <url_or_id>
```

**Examples:**
```bash
python3 /Users/apollo/.openclaw/workspace/channels/marketing/scripts/read_x_post.py https://x.com/user/status/1234567890
python3 /Users/apollo/.openclaw/workspace/channels/marketing/scripts/read_x_post.py 1234567890
```

### What It Fetches
- Root tweet (full text, author, timestamp)
- Quoted tweet (if present, including article titles)
- Full thread replies by the original author (Q&A replies labeled separately)

### Limitations
- `search/recent` only covers last 7 days — older threads may not return replies
- X articles (x.com/i/article/...) are still blocked; title only via API metadata
- The API does NOT return images/media content

### Quick Inline Version (for one-off fetches)

```python
import requests, json, re

BEARER = json.load(open("/Users/apollo/.openclaw/credentials/x_api.json"))["bearer_token"]
tweet_id = re.search(r"/status/(\d+)", URL).group(1)  # or just the ID

r = requests.get(
    f"https://api.twitter.com/2/tweets/{tweet_id}",
    headers={"Authorization": f"Bearer {BEARER}"},
    params={
        "tweet.fields": "text,author_id,created_at,conversation_id,referenced_tweets",
        "expansions": "author_id,referenced_tweets.id",
        "user.fields": "name,username",
    }
)
print(r.json()["data"]["text"])
```

---

## When Aaron Pastes an X URL

1. **Immediately** run the script — don't try web_fetch first
2. If tweet is older than 7 days, thread replies may be missing (root tweet always works)
3. For linked X articles, note the title from API metadata and offer to search for it separately

---

_Added 2026-03-14_
