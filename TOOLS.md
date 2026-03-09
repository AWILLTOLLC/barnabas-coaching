# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Telegram
- **Aaron's chat ID:** 5161266419
- **Usage:** `message(action=send, channel=telegram, target=5161266419, message=...)`

---

## agent-browser (Headless Browser CLI)
- **Install:** `npm install -g agent-browser` + `agent-browser install` (Chromium downloaded)
- **Use for:** browser automation in scripts, cron jobs, and subagents (where the native browser tool isn't available)
- **Core workflow:** `agent-browser open <url>` → `agent-browser snapshot -i --json` → interact via refs (`@e1`, `@e2`, etc.)
- **Docs:** https://github.com/vercel-labs/agent-browser

---

## Email (Outbound Only)

- **Address:** drubot@posteo.com (Posteo — privacy-focused)
- **Purpose:** Sending summaries, todo lists, digests, and flags to Aaron
- **Direction:** Outbound only — inbox is intentionally not monitored (security)
- **Script:** `/root/.openclaw/workspace/scripts/send_email.py`
- **Credentials:** `/root/.openclaw/credentials/email.json` (chmod 600)
- **Usage:** `python3 scripts/send_email.py <to> <subject> <body>`
- **Aaron's address:** a@kaw.cc

---

## SSH Hosts

- **barnabas.coach** — Barnabas Coaching web server. SSH key auth. Caddy, web root: `/home/barnabas/html`
  - Deploy: `rsync -avz --delete projects/barnabas-coaching/dist/ barnabas.coach:/home/barnabas/html/`

Add whatever helps you do your job. This is your cheat sheet.

---

## Scrapling (Anti-bot Web Scraping)

- **Installed:** 2026-03-03, v0.4.1 (`pip install "scrapling[all]"`)
- **MCP server:** `systemctl status scrapling-mcp` — HTTP on `127.0.0.1:8473`, auto-starts on boot
- **mcporter config:** `~/.openclaw/workspace/config/mcporter.json` (server alias: `scrapling`)

### Tools available via `mcporter call scrapling.<tool>`:

| Tool | Use case |
|------|----------|
| `get` | Fast HTTP with TLS fingerprint spoofing — most sites |
| `bulk_get` | Batch HTTP for multiple URLs |
| `fetch` | Playwright browser — JS-heavy pages, mid protection |
| `bulk_fetch` | Batch Playwright |
| `stealthy_fetch` | Patchright + fingerprint spoofing — Cloudflare, high protection |
| `bulk_stealthy_fetch` | Batch stealthy |

### Quick usage:
```bash
# Fast HTTP
mcporter call scrapling.get url=https://example.com extraction_type=text --output json

# Stealthy (Cloudflare bypass)
mcporter call scrapling.stealthy_fetch url=https://target.com solve_cloudflare=true --output json
```

### In Python:
```python
from scrapling.fetchers import Fetcher, StealthyFetcher
page = Fetcher.get('https://example.com')
content = page.css('h1::text').getall()
```

### Primary use cases:
- Influencer outreach pipeline (ham radio/prepper YouTube/Instagram scraping)
- BlackRaven manufacturer directory scraping
- Any site that blocks `web_fetch` or `agent-browser`

---

## X (Twitter) API

- **Credentials:** `/root/.openclaw/credentials/x_api.json` (chmod 600)
- **Bearer Token:** app-only auth, read any public tweet by ID
- **OAuth 1.0a:** full user context (read/write), authorized as `@AlricEdryk`
- **Library:** `requests-oauthlib` (installed system-wide with --break-system-packages)

### Reading a tweet by ID:
```python
import json
from requests_oauthlib import OAuth1Session

creds = json.load(open("/root/.openclaw/credentials/x_api.json"))
oauth = OAuth1Session(creds["consumer_key"], creds["consumer_secret"],
    creds["access_token"], creds["access_token_secret"])

r = oauth.get("https://api.twitter.com/2/tweets/<TWEET_ID>",
    params={"tweet.fields": "text,author_id,created_at,article"})
print(r.json())
```

### Notes:
- X Articles (long-form posts) are accessible via user context OAuth — `article.plain_text` field
- Bearer token alone works for standard tweets but NOT article body
- Pay-per-usage pricing, credit-based, 2M post reads/month cap
- Tweet ID is the number at the end of any x.com URL
