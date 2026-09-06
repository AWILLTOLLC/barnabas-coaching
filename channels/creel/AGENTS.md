# AGENTS.md - Eagle’s Operating Protocol

## Every Session

1. Read `SOUL.md` — your operating rules and personality
2. Read `USER.md` — who you're helping and what they care about
3. Read `MEMORY.md` — architecture knowledge and session history
4. If working on a specific feature/bug: check `tasks/` for active task state

Don't ask permission. Just do it.

## Before Any Coding Work

1. **Check build state:** `cd ~/.openclaw/extensions/vantage && npm run build 2>&1 | tail -20` — know if the codebase currently compiles
2. **Read the relevant source file** before touching it. Never assume you know the current state.
3. **Verify any `api.*` call** against TOOLS.md or the actual SDK types before using it. Invented methods broke V2 once.

## Scope

This agent's memory and task files live **in this directory** only.

Workspace: `~/.openclaw/workspace/channels/vantage-oc/`

You MAY read plugin source files at `~/.openclaw/extensions/vantage/` — that's your primary work surface.
You MAY read/write `~/.openclaw/openclaw.json` for config understanding (never blindly write it).
You MUST NOT read the main workspace `MEMORY.md` or `memory/` folder.
You MUST NOT read other channel workspaces.

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

## Memory Protocol

**Episodic (session notes):** `memory/YYYY-MM-DD.md` — create `memory/` if needed
**Architecture knowledge:** `MEMORY.md` (this channel's) — curated, durable facts
**Task state:** `tasks/<feature>/todo.md` — for multi-session features

Write to memory when:
- A decision was made with trade-offs
- A bug pattern was discovered
- Something about the plugin architecture was clarified

## Subagent Policy

Spawn a subagent when:
- Reading 3+ source files to investigate a bug
- Running a multi-step build-test-fix cycle
- Generating verbose output where only the summary matters

Stay inline when:
- Direct file edits to known files
- 1-2 targeted reads
- Aaron is iterating in conversation

## Safety

**NEVER restart the gateway without Aaron's explicit approval.** Even if the fix is one line. Even if you're certain it's correct. Ask first.

Flag any change that affects:
- `openclaw.json`
- Plugin registration / `openclaw.plugin.json`
- Database schema (migrations)
- Session routing logic

## Quality Bar

Before calling anything done: would this pass a code review? If no, fix it.
For non-trivial changes: is there a more correct approach? Pause and consider.
If something goes sideways mid-task: STOP and re-plan. Don't keep pushing.

## File References

When you create or reference a file the operator might want to read, **always** format it as a Markdown link using the `vantage-file://` scheme:

```
[filename.md](vantage-file://~/.openclaw/workspace/channels/vantage-oc/filename.md)
```

**Never** just say "the file is at `/path/to/file`". Always wrap it in the link syntax so the Vantage client can render it as a tappable link.

Examples:
- ✅ `[todo.md](vantage-file://~/.openclaw/workspace/channels/vantage-oc/tasks/todo.md)`
- ✅ `[MEMORY.md](vantage-file://~/.openclaw/workspace/channels/vantage-oc/MEMORY.md)`
- ❌ `The file is at ~/.openclaw/workspace/channels/vantage-oc/todo.md`

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

# TOOLS.md - Forge's Reference

## Plugin Location

| Path | Contents |
|------|----------|
| `~/.openclaw/extensions/vantage/` | Plugin root |
| `~/.openclaw/extensions/vantage/src/` | TypeScript source |
| `~/.openclaw/extensions/vantage/dist/` | Compiled output (what runs) |
| `~/.openclaw/extensions/vantage/channeltemplates/` | Channel creation templates |
| `~/.openclaw/extensions/vantage/openclaw.plugin.json` | Plugin registration |
| `~/.openclaw/vantage-plugin.db` | SQLite database |

## Source File Map

| File | Responsibility |
|------|---------------|
| `src/index.ts` | Plugin entry point, `register()`, hook wiring |
| `src/runtime.ts` | Singleton runtime accessor (`getVantageRuntime()`) |
| `src/store.ts` | SQLite persistence (VantageStore class) |
| `src/rpc.ts` | All `api.registerGatewayMethod()` calls |
| `src/types.ts` | All TypeScript interfaces and type definitions |
| `src/broadcast.ts` | SSE client registry (`addSseClient`, `broadcast`) |
| `src/loopback.ts` | WS loopback for injecting messages into agent sessions |
| `src/subagent-hooks.ts` | Subagent lifecycle hooks (spawn/end/delivery_target) |
| `src/channel.ts` | Channel event parsing (if it exists) |

## Build Commands

```bash
cd ~/.openclaw/extensions/vantage

# Build TypeScript → dist/
npm run build

# Check current build state (quick sanity check)
npm run build 2>&1 | tail -20

# Install deps if needed
npm install
```

## Testing an RPC Method

Use the gateway WS directly (loopback pattern from loopback.ts):

```bash
# Quick test via node
node -e "
const ws = new (require('ws'))('ws://127.0.0.1:18789');
ws.on('message', d => console.log(JSON.parse(d)));
ws.on('open', () => ws.send(JSON.stringify({
  type: 'req', id: 'test1', method: 'connect',
  params: { minProtocol: 1, maxProtocol: 5,
    client: { id: 'test', version: '1.0.0', platform: 'linux', mode: 'backend' },
    caps: [], auth: { token: require('fs').existsSync('/Users/apollo/.openclaw/openclaw.json') ? JSON.parse(require('fs').readFileSync('/Users/apollo/.openclaw/openclaw.json','utf8')).gateway?.auth?.token : '' },
    role: 'operator', scopes: ['operator.admin'] }
})));
"
```

Then call methods via `{ type: 'req', id: 'X', method: 'vantage.METHOD', params: {...} }`.

Gateway responses always use `type: "res"` — never `type: "resp"`. Filter on `msg.type === 'res'`.

## Valid SDK Calls (verified)

These exist and work:

```typescript
api.registerGatewayMethod("vantage.METHOD_NAME", async ({ params, respond, context }) => { ... })
api.on("subagent_spawning", async (event) => { ... })
api.on("subagent_ended", async (event) => { ... })
api.on("subagent_delivery_target", (event) => { ... })
api.on("llm_output", async (event, ctx) => { ... })  // ← for mirroring main session output
```

## INVALID SDK Calls (do not use — invented by Claude Code)

```typescript
api.runtime.sendToChannel(...)         // DOES NOT EXIST
api.runtime.injectInboundMessage(...)  // DOES NOT EXIST
api.registerRpcMethod(...)             // DOES NOT EXIST (it's registerGatewayMethod)
```

## `llm_output` Hook Notes

- Fires for every LLM text chunk in any session
- `event.assistantTexts: string[]` — the outbound text
- Session key lives in `ctx` (second arg), NOT `event`. `event.sessionKey` is always `undefined`
- Filter: `ctx.sessionKey === "agent:main:main"` for main session
- This is the correct pattern for mirroring main session messages to Vantage

## Session Key Convention

| Session | Key |
|---------|-----|
| Main agent | `agent:main:main` |
| Channel agent (e.g. barnabas-coaching) | `agent:barnabas-coaching:main` |
| Channel agent (vantage-oc) | `agent:vantage-oc:main` |

## Channel Workspace Convention

```
~/.openclaw/workspace/channels/{slug}/
  SOUL.md
  IDENTITY.md
  AGENTS.md
  USER.md
  TOOLS.md
  HEARTBEAT.md
  MEMORY.md
```

## Database Schema Summary

Tables: `channels`, `channel_config`, `messages`, `read_markers`, `safety_alerts`, `drafts`, `tasks`, `proofs`, `client_connections`

DB access:
```bash
sqlite3 ~/.openclaw/vantage-plugin.db ".tables"
sqlite3 ~/.openclaw/vantage-plugin.db "SELECT slug, name FROM channels;"
```

## openclaw.json Agent Registration

Channels added via `vantage.channels.create` auto-write to `~/.openclaw/openclaw.json`:
```json
{ "id": "slug", "workspace": "/Users/apollo/.openclaw/workspace/channels/slug" }
```

Changes to `openclaw.json` require a gateway restart to take effect. **Always ask Aaron before restarting.**

## Gateway Port

Default: `18789`. Check with:
```bash
grep -o '"port":[0-9]*' ~/.openclaw/openclaw.json
```

## Projects (Client Side)

| Path | Contents |
|------|----------|
| `~/.openclaw/workspace/projects/vantage/` | Client-side specs and design docs |
| `SPEC.md` | V1 spec |
| `PROTOCOL_SPEC.md` | Protocol spec |
| `CHANNELS_SPEC.md` | Channel model spec |
| `VANTAGE_V2_SPEC.md` | Full V2 spec (3,512 lines) — TypeScript + Swift data models |
