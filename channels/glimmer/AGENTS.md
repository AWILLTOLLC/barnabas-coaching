# AGENTS.md

Read SOUL.md and USER.md on startup.

## Scope
You are scoped exclusively to this channel's workspace. Do not read files outside this directory. Do not attempt to access the main session's memory, MEMORY.md, or any other channel's workspace.

## Memory
- Daily notes: memory/YYYY-MM-DD.md
- Long-term: MEMORY.md (this workspace only)

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

## Your role
You are a focused agent for the glimmer channel. Surface your work clearly. Your operator can observe your output.

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
[filename.md](vantage-file://~/.openclaw/workspace/channels/glimmer/filename.md)
```

**Never** just say "the file is at `/path/to/file`". Always wrap it in the link syntax so the Vantage client can render it as a tappable link.

Examples:
- ✅ `[todo.md](vantage-file://~/.openclaw/workspace/channels/glimmer/tasks/todo.md)`
- ✅ `[MEMORY.md](vantage-file://~/.openclaw/workspace/channels/glimmer/MEMORY.md)`
- ❌ `The file is at ~/.openclaw/workspace/channels/glimmer/todo.md`

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

Add whatever helps you do your job. This is your cheat sheet.

## ByteRover (Memory)
- **Query:** `brv query "auth patterns"` (Check existing knowledge)
- **Curate:** `brv curate "Auth uses JWT in cookies"` (Save new knowledge)
- **Sync:** `brv pull` / `brv push` (Sync with team - requires login)
