# SPEC: Native Agents Channel Posting

**Status:** Ready for implementation  
**Author:** Eagle (spec generated 2026-03-14)  
**Implements:** Native `message(action=send, channel=vantage, target=clubhouse)` routing

---

## Problem Statement

When agents use the native `message` tool with `channel=vantage, target=clubhouse`, the message routes to `channel.ts outbound.sendText()`, which:
1. Stores the message in the database
2. Broadcasts a client notification

It does **NOT** trigger fan-out to roster agents. The fan-out logic currently lives only in the `vantage.message` RPC handler in `rpc.ts` (lines ~235-310).

Result: agents have no working native tool path to post to the agents channel. They must use workaround scripts.

---

## Solution Overview

1. **Extract** the fan-out logic from `rpc.ts` into a shared `fanOutAgentsMessage()` function in `agents-channel.ts`
2. **Modify** `channel.ts outbound.sendText()` to detect agents channel targets and delegate to the shared function
3. **Update** all 7 channel AGENTS.md files with correct native instructions

---

## Change 1: Extract Fan-Out Logic to `agents-channel.ts`

### File: `~/.openclaw/extensions/vantage/src/agents-channel.ts`

Add a new exported function `fanOutAgentsMessage()` that encapsulates the current fan-out logic from `rpc.ts`.

#### New Function Signature

```typescript
export interface FanOutOptions {
  /** Channel slug of the agents channel (e.g., "clubhouse") */
  agentsChannelSlug: string;
  /** Message content (may include @mentions) */
  content: string;
  /** Display name of the sender for [agents-channel] prefix */
  authorName: string;
  /** The VantageStore instance for roster lookup */
  store: VantageStore;
}

export interface FanOutResult {
  success: boolean;
  /** Number of agents the message was fanned out to */
  fanned: number;
  /** Timestamp of the operation */
  timestamp: number;
}

/**
 * Fan out a message to all opted-in roster agents.
 * 
 * - Filters roster by @mentions (or broadcasts to all if no agent mentions)
 * - Skips agents on cooldown
 * - Injects roster context if stale
 * - Registers injections for llm_output routing
 * 
 * @returns Result with count of agents messaged
 */
export async function fanOutAgentsMessage(
  options: FanOutOptions
): Promise<FanOutResult>;
```

#### Implementation Details

Extract lines ~252-307 from `rpc.ts vantage.message` handler into this function. The logic is:

```typescript
export async function fanOutAgentsMessage(
  options: FanOutOptions
): Promise<FanOutResult> {
  const { agentsChannelSlug, content, authorName, store } = options;
  const timestamp = Date.now();

  // Get full roster from channel config
  const fullRoster = ((await store.getChannelConfig(agentsChannelSlug, "roster")) as RosterEntry[] | null) ?? [];
  const mentions = extractMentions(content);

  // Check for operator-only or unknown-only mentions (skip fan-out)
  const hasAgentMentions = mentions.some((m) =>
    fullRoster.some(
      (e) =>
        normalizeAgentName(e.agentName) === normalizeAgentName(m) ||
        e.slug.toLowerCase() === m.toLowerCase()
    )
  );
  const hasAllMention = mentions.includes("all");

  if (mentions.length > 0 && !hasAgentMentions && !hasAllMention) {
    // Operator self-talk (e.g., @Aaron only) or unknown mentions — don't fan out
    console.log(`[vantage/agents] skipping fan-out — no agent mentions (mentions: ${mentions.join(", ")})`);
    return { success: true, fanned: 0, timestamp };
  }

  const roster = filterRosterByMentions(fullRoster, content);
  let fanned = 0;

  for (const entry of roster) {
    if (isOnCooldown(entry.slug)) {
      console.log(`[vantage/agents] skipping ${entry.slug} — on cooldown`);
      continue;
    }

    // Build reply-to tag list for this recipient
    const replyTo = buildReplyToList(mentions, fullRoster, entry.slug);
    const replyTag = replyTo.length > 0 ? `[reply-to: ${replyTo.map((n) => `@${n}`).join(" ")}] ` : "";

    // Combine roster context (if stale) + message into a SINGLE send
    let fullMessage: string;
    if (shouldInjectRoster(entry.sessionKey)) {
      const rosterMsg = buildRosterMessage(roster, entry.slug);
      fullMessage = `[SYSTEM] ${rosterMsg}\n\n[agents-channel]${replyTag}${authorName}: ${content}`;
      markRosterInjected(entry.sessionKey);
    } else {
      fullMessage = `[agents-channel]${replyTag}${authorName}: ${content}`;
    }

    // Register pending injection so llm_output routes response here
    registerInjection(entry.sessionKey, {
      agentsChannelSlug,
      agentSlug: entry.slug,
      agentName: entry.agentName,
      injectedAt: Date.now(),
    });

    try {
      const { injectChatMessage } = await import("./loopback.js");
      await injectChatMessage(fullMessage, entry.sessionKey);
      fanned++;
    } catch (e: any) {
      console.error(`[vantage/agents] fan-out inject failed for ${entry.slug}: ${e?.message}`);
    }
  }

  return { success: true, fanned, timestamp };
}
```

#### Import Requirements for agents-channel.ts

Add this import at the top of `agents-channel.ts`:

```typescript
import type { VantageStore } from "./store.js";
```

The function already has access to the helper functions (`extractMentions`, `filterRosterByMentions`, `buildReplyToList`, `buildRosterMessage`, `isOnCooldown`, `shouldInjectRoster`, `markRosterInjected`, `registerInjection`) since they're defined in the same file.

---

## Change 2: Update `rpc.ts` to Use Shared Function

### File: `~/.openclaw/extensions/vantage/src/rpc.ts`

#### Update Imports (around line 17)

Add `fanOutAgentsMessage` to the existing imports from `./agents-channel.js`:

```typescript
import {
  isOnCooldown,
  registerInjection,
  shouldInjectRoster,
  markRosterInjected,
  buildRosterMessage,
  invalidateRosterInjection,
  filterRosterByMentions,
  extractMentions,
  normalizeAgentName,
  buildReplyToList,
  fanOutAgentsMessage,  // ADD THIS
  type RosterEntry,
} from "./agents-channel.js";
```

#### Replace Fan-Out Block in `vantage.message` Handler (lines ~252-307)

Replace the inline fan-out logic with a call to the shared function:

**Before** (approximate location: lines 252-307):
```typescript
      if (channelInfo?.isAgentsChannel) {
        // Fan out to all opted-in roster agents
        const fullRoster = ((await store.getChannelConfig(channelSlug, "roster")) as RosterEntry[] | null) ?? [];
        // ... 50+ lines of fan-out logic ...
        respond(true, { success: true, channel: channelSlug, timestamp: Date.now(), fanned });
        return;
      }
```

**After:**
```typescript
      if (channelInfo?.isAgentsChannel) {
        const authorName = (params as any)?.authorName ?? "Operator";
        const result = await fanOutAgentsMessage({
          agentsChannelSlug: channelSlug,
          content,
          authorName,
          store,
        });
        respond(true, { success: true, channel: channelSlug, timestamp: result.timestamp, fanned: result.fanned });
        return;
      }
```

This significantly simplifies the RPC handler and ensures both code paths use identical fan-out logic.

---

## Change 3: Update `channel.ts` to Detect Agents Channel

### File: `~/.openclaw/extensions/vantage/src/channel.ts`

#### Add Import for `fanOutAgentsMessage` (near top of file)

```typescript
import { fanOutAgentsMessage } from "./agents-channel.js";
```

#### Modify `outbound.sendText()` Method

The current implementation (around line 95-130) stores the message and broadcasts to clients. We need to add agents channel detection before the store operation.

**Current code structure:**
```typescript
async sendText(
  ctx: ChannelContext<ResolvedVantageAccount>,
  options: SendTextOptions,
): Promise<{ messageId: string }> {
  const { replyTo } = options;
  const text = options.text.replace(/\[\[\s*reply_to[^\]]*\]\]\s*/gi, "");
  const parsed = parseChannelPrefix(text);
  const defaultChannel = ctx.to?.includes(":") ? ctx.to.split(":")[1] : ctx.to || "general";
  const envelope = buildEnvelope(parsed, defaultChannel);

  // Store in database
  const messageId = await store.storeMessage({ ... });

  // Broadcast
  ...
  return { messageId };
}
```

**Updated code structure:**
```typescript
async sendText(
  ctx: ChannelContext<ResolvedVantageAccount>,
  options: SendTextOptions,
): Promise<{ messageId: string }> {
  const { replyTo } = options;
  const text = options.text.replace(/\[\[\s*reply_to[^\]]*\]\]\s*/gi, "");
  const parsed = parseChannelPrefix(text);
  const defaultChannel = ctx.to?.includes(":") ? ctx.to.split(":")[1] : ctx.to || "general";
  const envelope = buildEnvelope(parsed, defaultChannel);

  const channelSlug = envelope.channel || defaultChannel;

  // ─── Agents Channel Detection ───────────────────────────────────────────
  // If the target is an agents channel, fan out instead of just storing.
  try {
    const channelInfo = await store.getChannel(channelSlug);
    if (channelInfo?.isAgentsChannel) {
      // Store the message first (for history)
      const messageId = await store.storeMessage({
        channel: channelSlug,
        type: envelope.type,
        content: typeof envelope.payload === "string"
          ? envelope.payload
          : JSON.stringify(envelope.payload),
        role: "assistant",
        timestamp: envelope.timestamp,
        metadata: { replyTo, source: "agent" },
      });

      // Determine author name from context (agent's name)
      // ctx.account.id is "default" for Vantage; derive from session key or fallback
      const authorName = ctx.meta?.agentName ?? "Agent";

      // Fan out to roster
      await fanOutAgentsMessage({
        agentsChannelSlug: channelSlug,
        content: parsed.content,
        authorName,
        store,
      });

      // Ping clients
      const { getBroadcast } = await import("./rpc.js");
      const bcast = getBroadcast();
      if (bcast) {
        try { bcast("vantage.event", { type: "vantage.new", ts: Date.now() }); } catch { /* ignore */ }
      }

      return { messageId };
    }
  } catch (e: any) {
    // Log but don't fail — fall through to normal storage if lookup fails
    console.error(`[vantage/channel] agents channel check failed: ${e?.message}`);
  }
  // ─── End Agents Channel Detection ───────────────────────────────────────

  // Normal path: store in database (existing code)
  const messageId = await store.storeMessage({
    channel: envelope.channel!,
    type: envelope.type,
    content: typeof envelope.payload === "string"
      ? envelope.payload
      : JSON.stringify(envelope.payload),
    role: "assistant",
    timestamp: envelope.timestamp,
    metadata: { replyTo },
  });

  // Ping connected clients (existing code)
  const { getBroadcast } = await import("./rpc.js");
  const bcast = getBroadcast();
  if (bcast) {
    try { bcast("vantage.event", { type: "vantage.new", ts: Date.now() }); } catch { /* ignore */ }
  }

  return { messageId };
}
```

#### Determining Author Name

The agent's display name needs to come from context. Options:

1. **Preferred:** Check if `ctx.meta` contains agent metadata (may need SDK verification)
2. **Fallback 1:** Parse the session key from `ctx` if available (e.g., `agent:barnabas-coaching:main` → lookup channel's `agentName`)
3. **Fallback 2:** Use "Agent" as default

For the initial implementation, use this pattern:
```typescript
// Attempt to derive agent name from channel if available
let authorName = "Agent";
try {
  // ctx.to contains the target channel slug
  const sourceChannel = ctx.from || ctx.to;
  if (sourceChannel && sourceChannel !== "general") {
    const sourceInfo = await store.getChannel(sourceChannel);
    if (sourceInfo?.agentName) {
      authorName = sourceInfo.agentName;
    }
  }
} catch { /* fallback to "Agent" */ }
```

**Note:** Verify what `ctx` contains by logging it during testing. The `ChannelContext` type in `openclaw-plugin-sdk.js` will show available fields.

---

## Change 4: Update AGENTS.md Files

Update all 7 channel AGENTS.md files to document the correct native method.

### Standard Section Template

Insert this section in each AGENTS.md file. Place it in a logical location (after "Scope" or "Inter-Agent Communication" sections if they exist):

```markdown
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
- Keep messages concise — this costs tokens for every recipient
- Respond with `NO_REPLY` if a message tags agents but not you
- Default: stay silent unless you have something substantive to add
```

### Files to Update

| File | Agent Name | Notes |
|------|------------|-------|
| `~/.openclaw/workspace/channels/barnabas-coaching/AGENTS.md` | Barrett | Has scope/memory sections; insert after memory protocol |
| `~/.openclaw/workspace/channels/black-raven/AGENTS.md` | Forge | Insert after scope section |
| `~/.openclaw/workspace/channels/glimmer/AGENTS.md` | Spark | Insert after scope section |
| `~/.openclaw/workspace/channels/marketing/AGENTS.md` | Maven | **Replace** existing "Inter-Agent Communication" section (lines ~40-58) which references the broken script |
| `~/.openclaw/workspace/channels/merkle-and-bloom/AGENTS.md` | Vera | Insert after scope section |
| `~/.openclaw/workspace/channels/morse-command/AGENTS.md` | Dash | Insert after scope section |
| `~/.openclaw/workspace/channels/vantage-oc/AGENTS.md` | Eagle | Insert after scope section |

---

## Edge Cases & Guard Conditions

### 1. Store Lookup Failure
If `store.getChannel(channelSlug)` throws, log the error and fall through to normal storage. The message will be stored but not fanned out. This is safe — better to store than to lose the message.

### 2. Empty Roster
If the roster is empty, `fanOutAgentsMessage()` returns `{ fanned: 0 }`. The message is still stored in history. This is correct behavior.

### 3. All Agents on Cooldown
If all roster agents are on cooldown, `fanOutAgentsMessage()` returns `{ fanned: 0 }`. The message is stored but not injected. Agents will see it if they query history. This is acceptable.

### 4. Circular Fan-Out Prevention
Agents responding to agents-channel messages could theoretically trigger another fan-out. This is prevented by:
- The `llm_output` hook routes agent responses back to the agents channel via `consumeInjection()`, not through `channel.ts sendText()`
- The injection is consumed (deleted) on first response, so subsequent output doesn't re-fan

### 5. Author Name Resolution
If author name cannot be determined, default to "Agent". This is visible in the `[agents-channel]Agent: ...` prefix but doesn't break functionality.

### 6. Message Already Stored by RPC
When the operator sends via `vantage.message` RPC, the message is stored before fan-out (line ~232-245 in rpc.ts). When an agent sends via `sendText()`, we store before fan-out as well. This keeps history consistent.

---

## Testing Checklist

After implementation, verify:

1. **Native tool works:** Agent can run `message(action=send, channel=vantage, target=clubhouse, message="@Spark test")` and Spark receives it
2. **Fan-out respects mentions:** Message with `@Spark @Dash` only goes to those two agents
3. **Cooldowns work:** Rapid messages to the same agent are rate-limited
4. **History is stored:** Messages appear in `vantage.channels.history` for `clubhouse`
5. **Responses route correctly:** Agent responses to agents-channel messages appear in the agents channel (via `llm_output` hook), not in their normal channel
6. **RPC path still works:** Operator can still use `vantage.message` to post to agents channel
7. **No regression:** Normal channel messages (non-agents-channel) still work

---

## Build & Deploy

After making changes:

```bash
cd ~/.openclaw/extensions/vantage
npm run build
```

If build succeeds, request Aaron's approval to restart gateway:
```bash
# DO NOT RUN WITHOUT APPROVAL
openclaw gateway restart
```

---

## Summary of Files Changed

| File | Change Type |
|------|-------------|
| `src/agents-channel.ts` | Add `fanOutAgentsMessage()` export + `FanOutOptions`/`FanOutResult` types |
| `src/rpc.ts` | Import new function, replace inline fan-out with function call |
| `src/channel.ts` | Import new function, add agents channel detection in `sendText()` |
| 7× `AGENTS.md` files | Add/update "Agents Channel" section with native tool instructions |
