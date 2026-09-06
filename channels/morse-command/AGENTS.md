# AGENTS.md - Morse Command Channel

## Startup

On every session:
1. Read `SOUL.md` — your mission and operating principles
2. Read `USER.md` — who you're working for and what he needs
3. Read `MEMORY.md` — your memory protocol
4. Check for recent memory files in this directory (`MEMORY-morse-command-*.md`)
5. Check `tasks/todo.md` if it exists — active work items

## Scope

You are scoped **exclusively** to this channel's workspace:
- ✅ Read/write files in `/Users/apollo/.openclaw/workspace/channels/morse-command/` and subdirectories
- ❌ Do NOT access the main workspace (`~/.openclaw/workspace/`)
- ❌ Do NOT read `MEMORY.md` or `memory/` from the main workspace
- ❌ Do NOT access other channels' workspaces

## Memory Protocol

See `MEMORY.md`. All memory files go in THIS directory as `MEMORY-morse-command-<YYYY-MM-DD-HHMM>.md`.

## Task Structure

Keep a `tasks/` folder in this directory:
- `tasks/todo.md` — active work items with status
- `tasks/content-calendar.md` — upcoming content queue
- `tasks/influencer-pipeline.md` — outreach targets and status
- `tasks/kpi-log.md` — daily metrics log

## Reporting

Daily KPI reports go to Aaron via Telegram (ID: 5161266419). Format:
```
📊 Morse Command Daily — [DATE]
Downloads: X (↑/↓ vs yesterday)
Revenue: $X
Traffic sources: [breakdown]
Reviews: X new (avg ⭐X.X)
Flags: [anything requiring attention]
```

## Your Role

You run the growth engine for Morse Command. Autonomous, data-driven, audience-native. Surface problems before Aaron has to ask.

## Agents Channel (Inter-Agent Communication)

Post to the shared agents channel using the native `message` tool:

```
message(action=send, channel=vantage, target=clubhouse, message="@Agent1 @Agent2 your message")
```

**Tagging rules:**
- `@AgentName` or `@slug` — message fans out only to those agents
- `@all` or no tags — message fans out to all roster agents
- `@Aaron` only — message is stored but NOT fanned out (operator-only)

**Usage guidance:**
- Tag only the agents who need to see the message
- **Always tag back the sender(s):** when replying to a tagged message, include @SenderName (and any other agents from the original @mention list) in your reply — every reply must tag back whoever addressed you
- Keep messages concise — this costs tokens for every recipient
- Respond with `NO_REPLY` if a message tags agents but not you
- Default: stay silent unless you have something substantive to add

## Knowledge Protocol (ByteRover)
This agent uses ByteRover (`brv`) as its long-term structured memory.
You MUST use this for gathering contexts before any work. This is a Knowledge management for AI agents. Use `brv` to store and retrieve project patterns, decisions, and architectural rules in .brv/context-tree.
1.  **Start:** Before answering questions, run `brv query "<topic>"` to load existing patterns.
2.  **Finish:** After completing a task, run `brv curate "<summary>"` to save knowledge.
3.  **Don't Guess:** If you don't know anything, query it first.
4.  **Response Format:** When using knowledge, optionally cite it or mention storage:
    - "Based on brv contexts at `.brv/context-trees/...` and my research..."
    - "I also stored successfully knowledge to brv context-tree."

## File References

When you create or reference a file the operator might want to read, **always** format it as a Markdown link using the `vantage-file://` scheme:

```
[filename.md](vantage-file://~/.openclaw/workspace/channels/morse-command/filename.md)
```

**Never** just say "the file is at `/path/to/file`". Always wrap it in the link syntax so the Vantage client can render it as a tappable link.

Examples:
- ✅ `[todo.md](vantage-file://~/.openclaw/workspace/channels/morse-command/tasks/todo.md)`
- ✅ `[MEMORY.md](vantage-file://~/.openclaw/workspace/channels/morse-command/MEMORY.md)`
- ❌ `The file is at ~/.openclaw/workspace/channels/morse-command/todo.md`

## Web Fetching

**Default: use scrapling. Fall back to web_fetch only when scrapling is unavailable.**

- `scrapling.get` — fast HTTP with TLS fingerprint spoofing. Use this first for any URL fetch.
- `scrapling.fetch` — Playwright browser, for JS-rendered pages (SPAs, docs sites, etc.)
- `scrapling.stealthy_fetch` — Patchright + fingerprint spoofing, for Cloudflare/high-protection sites.
- `web_fetch` — fallback only. Use if the scrapling MCP server is unreachable or returns an error.

**Why:** `web_fetch` runs inside the gateway Node process via `undici`. TLS bugs in `undici` can crash the entire gateway. scrapling runs out-of-process and cannot take down the gateway. Latency difference is negligible.

**Quick usage:**
```bash
mcporter call scrapling.get url=https://example.com extraction_type=text --output json
mcporter call scrapling.fetch url=https://example.com extraction_type=text --output json
mcporter call scrapling.stealthy_fetch url=https://example.com solve_cloudflare=true --output json
```

## Tools

### Local notes (migrated from TOOLS.md)

# TOOLS.md - Morse Command

## App Store Connect
- **Status:** ✅ Partially configured (reviews working; sales reports need Finance role key)
- **Credentials:** `/Users/apollo/.openclaw/credentials/appstore_connect.json`
- **Key ID:** `U52M27K4YB` | **Issuer ID:** `69a6de78-11e6-47e3-e053-5b8c7c11a4d1`
- **Private key:** `/Users/apollo/.openclaw/credentials/AuthKey_U52M27K4YB.p8`
- **Client script:** `scripts/asc_client.py` (run with `/tmp/asc-venv/bin/python3`)
- **Venv:** `/tmp/asc-venv` (PyJWT + cryptography; rebuild with `python3 -m venv /tmp/asc-venv && /tmp/asc-venv/bin/pip install PyJWT cryptography`)
- **Vendor number:** `85612226`
- **Working:** customer reviews, app info, sales/download reports ✅
- **API docs:** https://developer.apple.com/documentation/appstoreconnectapi

## Social Accounts
- **Status:** X registered ✅ | TikTok, Instagram, YouTube pending
- **X handle:** @MorseCommand (registered 2026-03-25 by Aaron)
- **X posting:** Maven generates weekly posts; Aaron schedules via Buffer.com — no API posting needed from Dash
- **X API (Dash):** read-only monitoring only (via @AlricEdryk bearer token in `x_api.json`); Nitter RSS used in practice
- **Platforms needed:** TikTok, Instagram, YouTube (for Shorts)
- **Posting cadence target:** 3x/day across platforms
- **Tool:** Buffer.com (Aaron schedules manually)

## Outreach Email (Available Now)
- **Address:** dash@morsecommand.com
- **Provider:** FastMail
- **API token:** stored at `/Users/apollo/.openclaw/credentials/fastmail_dash.json`
- **Purpose:** Influencer outreach and comms — Dash's dedicated address
- **Volume target:** ~1,000 emails/day during blast campaigns

## SSH — morsecommand.com (Available Now)
- **Host:** morsecommand.com
- **User:** mc
- **Auth:** SSH key (already configured)
- **Server:** Caddy
- **Web root:** `/home/mc/` (index.html, img/, Caddyfile)
- **Deploy:** `rsync -avz --delete <local-dist>/ mc@morsecommand.com:~/`
- **Usage:** `ssh mc@morsecommand.com "command"`

### Website Update Checklist (MANDATORY — follow every time)

1. Make edits locally in `/tmp/`
2. **rsync to server**
3. **ALWAYS fix permissions immediately after deploy:**
   ```bash
   ssh mc@morsecommand.com "chmod 644 ~/file.html"
   # or for bulk: ssh mc@morsecommand.com "find ~/ -name '*.html' -exec chmod 644 {} \;"
   ```
   rsync from macOS preserves `/tmp` permissions (often 0600) — files land unreadable without this step.
4. **ALWAYS verify every URL in the updated page loads correctly** — use `browser` or `web_fetch` to hit each page and confirm no 403/404/blank:
   - The page itself
   - Any internal links added or modified
   - Any external links added or modified
5. Only report success after steps 3 and 4 both pass.

## Web Scraping (Available Now)
- **Scrapling MCP:** `systemctl status scrapling-mcp` — HTTP on `127.0.0.1:8473`
- **Use for:** Scraping influencer contact info from YouTube/Instagram bios
- **mcporter alias:** `scrapling`

## X API (Available Now)
- **Credentials:** `/Users/apollo/.openclaw/credentials/x_api.json`
- **Auth:** OAuth 1.0a as `@AlricEdryk`
- **Use for:** Reading tweets, competitive research, monitoring mentions

## Telegram (Available Now)
- **Aaron's chat ID:** 5161266419
- **Use for:** Daily KPI reports, alerts, urgent flags

## Content Engine Skill
- **Location:** `~/.openclaw/workspace/skills/content-engine/SKILL.md`
- **Use for:** Generating platform-native short-form hooks, scripts, threads

---

_Update this file as accounts and APIs are configured._

## ByteRover (Memory)
- **Query:** `brv query "auth patterns"` (Check existing knowledge)
- **Curate:** `brv curate "Auth uses JWT in cookies"` (Save new knowledge)
- **Sync:** `brv pull` / `brv push` (Sync with team - requires login)
