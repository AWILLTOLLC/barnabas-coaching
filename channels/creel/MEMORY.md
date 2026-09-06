# MEMORY.md - Eagle's Architecture Knowledge

_Durable facts about VantageOC. Update this as the architecture evolves._

---

## Plugin State (as of 2026-03-11)

The VantageOC plugin is **V2**, living at `~/.openclaw/extensions/vantage/src/`. It was rewritten from V1 to fix architectural issues. The source code compiles and deploys — whether it currently loads cleanly is worth verifying at session start.

**V2 rewrite rationale:** V1 used `api.registerHook()` which wires once at session setup. V1 also lacked typed hooks. V2 uses `api.on()` for live hook registration and `api.registerGatewayMethod()` for RPC. V2 is modeled after the Discord plugin (SDK-idiomatic).

## Critical Bug History

### 2026-03-09: Claude Code invented API methods
A subagent implementing V2 server-side code invented:
- `api.runtime.sendToChannel()` — does not exist in the SDK
- `api.runtime.injectInboundMessage()` — does not exist in the SDK

The fix was restoring the V1 broadcast capture pattern for outbound and the WS loopback for inbound. The current `rpc.ts` and `loopback.ts` implement this correctly.

**Rule hardened from this:** Always verify `api.*` calls against TOOLS.md before using them.

### 2026-03-09: Missing `configSchema` in openclaw.plugin.json
The V2 plugin.json was missing the `configSchema` field, which the Discord plugin has. This prevented gateway loading. Fixed — current `openclaw.plugin.json` includes it.

## Architecture Patterns (V2 Current)

### Outbound (agent → client)
1. `llm_output` hook captures LLM text from agent sessions
2. Text stored in `messages` table via `VantageStore.storeMessage()`
3. `broadcast()` from `broadcast.ts` pushes SSE ping to connected clients
4. `getBroadcast()` from `rpc.ts` also used as secondary broadcast path (captured lazily from RPC context)
5. Clients poll via `vantage.poll` RPC to get messages since cursor

### Inbound (client → agent)
1. Client calls `vantage.message` RPC with `{channel, content}`
2. `rpc.ts` resolves the target session key (`agent:{slug}:main`)
3. `injectChatMessage()` from `loopback.ts` opens a WS to the gateway and calls `chat.send`
4. Message arrives in the agent session as a normal user message

### Channel Creation Flow
`vantage.channels.create` RPC:
1. Creates workspace dir at `~/.openclaw/workspace/channels/{slug}/`
2. Writes SOUL.md, IDENTITY.md, USER.md, AGENTS.md, TOOLS.md, HEARTBEAT.md, MEMORY.md from `channeltemplates/`
3. Creates `~/.openclaw/agents/{slug}/sessions/` dir + sessions.json
4. Writes agent entry to `~/.openclaw/openclaw.json`
5. Stores channel record in SQLite
6. Pings SSE clients

Gateway restart required for new channel agent to become active.

### Subagent Lifecycle
`subagent-hooks.ts` binds spawned subagents to their originating channel:
- `subagent_spawning` → creates `SubagentBinding` in module-scoped Map, stores `task_spawn` message
- `subagent_ended` → stores `task_complete` or `task_failed` message, cleans up binding
- `subagent_delivery_target` → routes subagent output back to originating channel

Bindings are ephemeral (in-memory only, cleared on gateway restart). This is intentional — subagents don't survive restarts anyway.

### Broadcast Architecture
Two broadcast paths exist (belt-and-suspenders):
1. `broadcast()` from `broadcast.ts` — direct SSE write to registered `ServerResponse` objects
2. `getBroadcast()` from `rpc.ts` — captured lazily from RPC `context.broadcast`, fires gateway-level event

Both are used because the first SSE call after restart may not have a captured broadcast yet. Use both.

### Session Key Rules
- `normalizeStoreSessionKey()` is just `.toLowerCase()` — no aliasing
- Always use `agent:main:main`, never `main`
- Channel agents: `agent:{slug}:main`

## Database

SQLite via Node.js built-in `node:sqlite` (NOT `better-sqlite3`). Uses `DatabaseSync` (synchronous API).

WAL mode enabled. Foreign keys enabled.

Schema is in `store.ts` as the `SCHEMA` const. Run migration awareness: the `is_main` column was added post-initial schema with a try/catch ALTER TABLE.

For new columns: add to SCHEMA and add a try/catch `ALTER TABLE ... ADD COLUMN` in the constructor.

## Protected Channels

These channels cannot be deleted via `vantage.channels.delete`:
`main`, `barnabas-coaching`, `morse-marketing`, `black-raven`, `glimmer-cards`

## Config Files (Gateway)

- Main config: `~/.openclaw/openclaw.json`
- Plugin registration: `~/.openclaw/extensions/vantage/openclaw.plugin.json`

Plugin.json format that works:
```json
{
  "id": "vantage",
  "channels": ["vantage"],
  "configSchema": { "type": "object", "additionalProperties": false, "properties": {} }
}
```

## V2 Spec

Full V2 spec at `~/.openclaw/workspace/projects/vantage/VANTAGE_V2_SPEC.md` (3,512 lines). Covers TypeScript server models + Swift client ViewModels + SwiftUI structures. This is the target architecture. Key decisions in the spec: ping+cursor model for updates, typed hook registration, SDK-idiomatic patterns.

## SDK Patterns Discovered (2026-03-14)

### `outbound.sendText` call signature
The SDK calls `plugin.outbound.sendText(singleObject)` — ONE arg with shape `{ text, to, accountId, replyToId, threadId, cfg, identity }`. NOT `(ctx, options)`. Type is `OutboundTextParams` in `openclaw-plugin-sdk.d.ts`.

### Target resolution for custom slugs
`message(channel=vantage, target=slug)` goes through `resolveMessagingTarget()` which does a directory lookup. Custom slugs fail with "Unknown target" unless the plugin implements `messaging.targetResolver.looksLikeId(raw)`. Pattern: `(raw) => /^[a-z0-9][a-z0-9-]*$/.test(raw.trim())`. This bypasses directory lookup entirely.

### `buildEnvelope` always wraps payload as object
For plain text, `buildEnvelope()` returns `payload: { messageId, content, role, streaming: false }`. Never store `JSON.stringify(envelope.payload)`. Always store `parsed.content`.

### `identity.name` in `sendText`
`params.identity.name` is the agent's display name from SDK session context. Not always populated. `agentId` is NOT passed through to `sendText()`.

### `extractMentions` regex
`/@([A-Za-z][A-Za-z0-9_-]*)/g` — no space in char class. Space causes whole-sentence match.

## Active Work Areas (as of 2026-03-11)

- vantage-oc channel was just created — this is the active development channel
- Plugin V2 is deployed, build state unknown at time of writing — verify at session start
- Swift client: not yet built, V2 spec is the design doc
- Channel template quality: the default templates are minimal; custom templates now exist for this channel

## Operator Commands

### `fly`
When Aaron says "fly" as a single command:
1. Run pre-flight checks: `npm run build` in the plugin dir — confirm clean compile
2. Check for any other obvious issues (plugin.json valid, no broken imports)
3. If errors found: fix them, repeat checks
4. When everything is clean: restart the gateway (this is the ONE case where restart is pre-authorized without asking)

## Errors / Hard Rules

- **Never restart the gateway without Aaron's explicit permission.** Ask first. Always.
- **Subagents can invent SDK methods.** Verify any generated `api.*` calls before trusting them.
- **`event.sessionKey` is always `undefined` in llm_output.** Use `ctx.sessionKey` (second arg).
- **`api.registerHook()` is different from `api.on()`.** Former wires at setup only. Latter is live.
