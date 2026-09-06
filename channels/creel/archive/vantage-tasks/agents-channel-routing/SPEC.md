# Agents Channel @Mention Routing Spec

**Status:** Draft  
**Author:** Eagle (planning subagent)  
**Date:** 2026-03-14  
**Location:** `tasks/agents-channel-routing/SPEC.md`

---

## 1. Problem Statement

The agents channel currently broadcasts every message to ALL agent sessions. Each agent processes every message regardless of relevance, wasting tokens and creating noise.

**Goal:** Route messages containing @mentions ONLY to the mentioned agents. Maintain broadcast behavior when no @mentions are present.

---

## 2. Architecture Overview

### 2.1 Current Flow

```
Operator sends message via vantage.message RPC
    ↓
rpc.ts: vantage.message handler
    ↓
Checks if channel.isAgentsChannel
    ↓
If yes: filterRosterByMentions() → fan-out to filtered roster
    ↓
For each agent: injectChatMessage() via loopback WebSocket
    ↓
Agent processes message, llm_output hook routes response back
```

### 2.2 Key Insight

**The @mention filtering already exists.** The `filterRosterByMentions()` function in `agents-channel.ts` extracts @mentions and filters the roster. The current implementation:

1. Extracts @mentions using regex
2. Matches against `agentName` or `slug` (case-insensitive)
3. Returns matched agents, or full roster if no matches (typo fallback)
4. Returns full roster if `@all` is mentioned

### 2.3 What's Missing

1. **Operator (@Aaron) handling** — not in roster, needs special treatment
2. **Reply tag injection** — agents should know who else was tagged
3. **Agent registry sync** — roster updates when agents are created/renamed/deleted
4. **Unknown @mention handling** — what happens with `@FakeAgent`?

---

## 3. Agent Registry Design

### 3.1 Current State

The roster is stored per-agents-channel in `channel_config`:

```typescript
// store.getChannelConfig(agentsChannelSlug, "roster")
interface RosterEntry {
  slug: string;          // e.g. "vantage-oc"
  agentName: string;     // e.g. "Eagle"
  sessionKey: string;    // e.g. "agent:vantage-oc:main"
  purpose?: string;      // e.g. "VantageOC plugin development"
}
```

### 3.2 Recommendation: Keep Current Design

The roster-based design is correct. It:
- Lives in SQLite (persists across restarts)
- Is channel-specific (supports multiple agents channels if needed)
- Already syncs on channel create/rename/delete (via `vantage.channels.create`, `vantage.channels.rename`)

### 3.3 Agent Name Normalization

For @mention matching, we need consistent normalization:

```typescript
function normalizeAgentName(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}

// @Eagle → "eagle"
// @Black Raven → "blackraven" 
// @morse-command → "morsecommand"
```

### 3.4 Registry (Reference)

| Name | Channel Slug | Session Key | Normalized |
|------|-------------|-------------|------------|
| Eagle | vantage-oc | agent:vantage-oc:main | eagle |
| Spark | glimmer | agent:glimmer:main | spark |
| Dash | morse-command | agent:morse-command:main | dash |
| Forge | black-raven | agent:black-raven:main | forge |
| Barrett | barnabas-coaching | agent:barnabas-coaching:main | barrett |
| Vera | merkle-and-bloom | agent:merkle-and-bloom:main | vera |
| Maven | marketing | agent:marketing:main | maven |
| Dru | main | agent:main:main | dru |

---

## 4. Tag Parsing Rules

### 4.1 Current Implementation

```typescript
// agents-channel.ts
export function extractMentions(content: string): string[] {
  const matches = content.match(/@([A-Za-z][A-Za-z0-9 _-]*)/g) ?? [];
  return matches.map((m) => m.slice(1).trim().toLowerCase());
}
```

### 4.2 Parsing Rules

| Rule | Behavior |
|------|----------|
| Syntax | `@Name` — @ followed by alphanumeric + spaces/hyphens/underscores |
| Case sensitivity | Case-insensitive (`@EAGLE` = `@eagle` = `@Eagle`) |
| Position | Anywhere in message |
| Multi-word | Supported up to first non-name character (`@Black Raven` captures "Black Raven") |
| Partial matches | NOT supported (`@Eag` does NOT match Eagle) |
| Special: `@all` | Broadcasts to all agents |
| Special: `@Aaron` | Routes to operator (see §5) |

### 4.3 Enhanced Regex (Recommended)

The current regex is acceptable but could be tightened:

```typescript
// More precise: capture up to 3 words for multi-word names
/@([A-Za-z][A-Za-z0-9]*(?:[ _-][A-Za-z][A-Za-z0-9]*){0,2})/g
```

---

## 5. Routing Logic

### 5.1 Decision Matrix

| Message Contains | Routing Behavior |
|------------------|------------------|
| No @mentions | Broadcast to ALL agents (current behavior) |
| `@all` | Broadcast to ALL agents |
| `@AgentName(s)` | Route ONLY to mentioned agents |
| `@Aaron` only | NO agents receive (operator self-talk) |
| `@Aaron @Eagle` | Route to Eagle only |
| `@UnknownAgent` | Broadcast to ALL (typo fallback) |

### 5.2 Implementation Change

The current `filterRosterByMentions()` returns the full roster when no matches are found. This is the correct fallback behavior for typos but doesn't handle the "no agents, just operator" case.

**Change required in `rpc.ts`:**

```typescript
// In vantage.message handler, after filterRosterByMentions()
const mentions = extractMentions(content);
const hasAgentMentions = mentions.some(m => 
  roster.some(e => 
    normalizeAgentName(e.agentName) === normalizeAgentName(m) ||
    e.slug.toLowerCase() === m.toLowerCase()
  )
);
const hasOperatorMention = mentions.includes("aaron");
const hasAllMention = mentions.includes("all");

// If only @Aaron mentioned (no agents), skip fan-out entirely
if (mentions.length > 0 && !hasAgentMentions && !hasAllMention) {
  // Message is operator self-addressing or unknown mentions only
  // Store in channel history but don't fan out
  respond(true, { success: true, channel: channelSlug, timestamp: Date.now(), fanned: 0 });
  return;
}
```

### 5.3 Sequence Diagram

```
Operator: "@Eagle @Maven what about this approach?"
    ↓
vantage.message handler
    ↓
extractMentions() → ["eagle", "maven"]
    ↓
filterRosterByMentions() → [Eagle entry, Maven entry]
    ↓
For Eagle: injectChatMessage("[agents-channel] Operator: @Eagle @Maven what about this approach?")
For Maven: injectChatMessage("[agents-channel] Operator: @Eagle @Maven what about this approach?")
    ↓
(Spark, Dash, Forge, Barrett, Vera, Dru never see the message)
```

---

## 6. Operator Passthrough

### 6.1 `@Aaron` Semantics

`@Aaron` is the operator's handle in the agents channel. It is NOT in the roster (Aaron is not an agent).

**Behavior:**
- When agents reply to a tagged message, they should include `@Aaron` in their response
- The operator always sees all messages (they're in the VantageOC client)
- `@Aaron` alone means "talking to self" — no agents receive

### 6.2 Implementation

No code change needed for operator passthrough. The operator receives messages via the VantageOC client polling/SSE, not via session injection. The operator is always "subscribed" to the agents channel.

---

## 7. Reply Tag Injection

### 7.1 Problem

When Eagle receives `@Eagle @Maven what do you think?`, Eagle's reply should tag `@Aaron @Maven` (operator + other tagged agents, minus self).

### 7.2 Options

| Option | Pros | Cons |
|--------|------|------|
| **A. SOUL.md convention** | Zero code changes, agents already instructed | Relies on agent compliance, inconsistent |
| **B. System message prefix** | Guaranteed consistency, explicit | Adds tokens, changes message format |
| **C. Context metadata** | Clean separation, SDK-native | Needs verification that SDK supports this |

### 7.3 Recommendation: Option B (System Message Prefix)

Inject the reply context directly into the message:

```typescript
// Current format:
`[agents-channel] Operator: @Eagle @Maven what do you think?`

// Enhanced format:
`[agents-channel][reply-to: @Aaron @Maven] Operator: @Eagle @Maven what do you think?`
```

The agent's SOUL.md already says:
> "If I AM tagged → include @Aaron plus all other agents from the original @mention list in my reply"

The `[reply-to: ...]` prefix makes it explicit and parseable.

### 7.4 Implementation

In `rpc.ts`, when building the injected message:

```typescript
function buildAgentsChannelMessage(
  authorName: string,
  content: string,
  recipientSlug: string,
  allMentions: string[],
): string {
  // Build reply-to list: @Aaron + all mentions except the recipient
  const replyTo = ["Aaron", ...allMentions.filter(m => 
    normalizeAgentName(m) !== normalizeAgentName(recipientSlug) &&
    m.toLowerCase() !== "all" &&
    m.toLowerCase() !== "aaron"
  )];
  
  const replyTag = replyTo.length > 0 
    ? `[reply-to: ${replyTo.map(n => `@${n}`).join(" ")}] `
    : "";
  
  return `[agents-channel]${replyTag}${authorName}: ${content}`;
}
```

---

## 8. Agent Registry Management

### 8.1 Current Behavior

Agents are added to the roster when:
1. `vantage.channels.create` is called with `joinAgentsChannel: true`
2. `vantage.channels.rename` is called with `joinAgentsChannel: true`

Agents are removed when:
1. `vantage.channels.rename` is called with `joinAgentsChannel: false`
2. `vantage.channels.delete` is called (needs verification)

### 8.2 Gap: Channel Deletion

The `vantage.channels.delete` handler does NOT currently remove the agent from the roster.

**Fix required in `rpc.ts`:**

```typescript
// In vantage.channels.delete handler, before clearBindingsForChannel()
const agentsChannelSlug = await store.getAgentsChannelSlug();
if (agentsChannelSlug) {
  const roster = ((await store.getChannelConfig(agentsChannelSlug, "roster")) as RosterEntry[] | null) ?? [];
  const filtered = roster.filter(e => e.slug !== slug);
  if (filtered.length !== roster.length) {
    await store.setChannelConfig(agentsChannelSlug, "roster", filtered);
    invalidateRosterInjection();
  }
}
```

### 8.3 Auto-Discovery

**Not recommended.** The roster pattern (explicit opt-in via `joinAgentsChannel: true`) is the correct design. Auto-discovery would:
- Add agents that shouldn't be in the agents channel
- Complicate the mental model
- Make it harder to control token spend

---

## 9. Plugin Changes Required

### 9.1 File: `src/agents-channel.ts`

| Change | Type | Description |
|--------|------|-------------|
| Add `normalizeAgentName()` | New function | Normalize names for matching |
| Add `buildReplyToList()` | New function | Generate reply-to mentions |
| Rename `extractMentions()` | Refactor | Make public, add operator detection |

### 9.2 File: `src/rpc.ts`

| Change | Location | Description |
|--------|----------|-------------|
| Operator-only detection | `vantage.message` handler | Skip fan-out if only @Aaron mentioned |
| Reply-to injection | `vantage.message` handler | Include `[reply-to: ...]` in message |
| Roster cleanup on delete | `vantage.channels.delete` handler | Remove agent from roster |

### 9.3 File: `src/types.ts`

No changes required. `RosterEntry` interface is already in `agents-channel.ts`.

### 9.4 File: `src/store.ts`

No changes required.

---

## 10. Config Schema Changes

### 10.1 No Changes to `openclaw.json`

The agents channel routing is entirely within the Vantage plugin. No gateway-level config changes.

### 10.2 No Changes to `openclaw.plugin.json`

The plugin config schema remains empty. All runtime config is in SQLite.

### 10.3 Roster Config (Reference)

Stored in `channel_config` table as JSON:

```sql
SELECT value FROM channel_config 
WHERE channel_slug = 'clubhouse' AND key = 'roster';
```

```json
[
  { "slug": "vantage-oc", "agentName": "Eagle", "sessionKey": "agent:vantage-oc:main", "purpose": "VantageOC development" },
  { "slug": "glimmer", "agentName": "Spark", "sessionKey": "agent:glimmer:main", "purpose": "Glimmer Cards" },
  ...
]
```

---

## 11. Edge Cases

### 11.1 Unknown @mentions

**Input:** `@FakeAgent @Eagle what do you think?`

**Current behavior:** `filterRosterByMentions()` returns only Eagle (matched).

**Correct.** Unknown mentions are ignored. If ALL mentions are unknown, full roster is returned (typo fallback).

### 11.2 Self-tagging

**Input:** Agent Eagle says `@Eagle I wonder if...`

**Behavior:** Eagle would receive its own message if fanned out again. This is a non-issue because:
1. Agents don't send to the agents channel via `vantage.message` — they respond via `llm_output`
2. The `llm_output` hook stores the response but doesn't re-fan-out

### 11.3 Operator tagging themselves

**Input:** Operator sends `@Aaron note to self`

**Behavior:** No agents receive (mentions.length > 0 but no agent matches). Message stored in channel history. Operator sees it in client.

### 11.4 Empty mentions (just `@`)

**Input:** `@ what about this?`

**Behavior:** Regex doesn't match bare `@`. Treated as no mentions → broadcast to all.

### 11.5 Agent mentions agent

**Input:** Eagle's response includes `@Maven can you help?`

**Behavior:** The response is stored via `llm_output` hook, NOT re-fanned. Maven won't see it until the operator relays it or a subsequent broadcast includes it.

**Future consideration:** Auto-relay agent-to-agent mentions. Out of scope for this spec.

### 11.6 Very long roster (>10 agents)

**Behavior:** Works correctly. The roster injection message may get long, but `ROSTER_REINJECT_MS` (60 minutes) limits frequency.

---

## 12. Implementation Checklist

- [ ] Add `normalizeAgentName()` to `agents-channel.ts`
- [ ] Add `buildReplyToList()` to `agents-channel.ts`
- [ ] Update `vantage.message` handler for operator-only detection
- [ ] Update `vantage.message` handler for reply-to injection
- [ ] Update `vantage.channels.delete` for roster cleanup
- [ ] Add unit tests for mention parsing edge cases
- [ ] Update SOUL.md templates to reference `[reply-to: ...]` format
- [ ] Manual test: tag single agent
- [ ] Manual test: tag multiple agents
- [ ] Manual test: tag @all
- [ ] Manual test: tag @Aaron only
- [ ] Manual test: unknown @mention fallback

---

## 13. Code Snippets (Reference Implementation)

### 13.1 `normalizeAgentName()`

```typescript
export function normalizeAgentName(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}
```

### 13.2 `buildReplyToList()`

```typescript
export function buildReplyToList(
  mentions: string[],
  roster: RosterEntry[],
  excludeSlug: string,
): string[] {
  const normalized = normalizeAgentName(excludeSlug);
  const agentMentions = mentions.filter(m => {
    const mn = normalizeAgentName(m);
    return (
      mn !== normalized &&
      mn !== "all" &&
      mn !== "aaron" &&
      roster.some(e => normalizeAgentName(e.agentName) === mn || e.slug.toLowerCase() === m.toLowerCase())
    );
  });
  
  // Always include Aaron first (operator)
  return ["Aaron", ...agentMentions.map(m => {
    const entry = roster.find(e => 
      normalizeAgentName(e.agentName) === normalizeAgentName(m) ||
      e.slug.toLowerCase() === m.toLowerCase()
    );
    return entry?.agentName ?? m;
  })];
}
```

### 13.3 Updated `vantage.message` handler (key section)

```typescript
// Inside vantage.message handler, after checking isAgentsChannel

const mentions = extractMentions(content);
const fullRoster = ((await store.getChannelConfig(channelSlug, "roster")) as RosterEntry[] | null) ?? [];

// Check for operator-only addressing
const hasAgentMentions = mentions.some(m =>
  fullRoster.some(e =>
    normalizeAgentName(e.agentName) === normalizeAgentName(m) ||
    e.slug.toLowerCase() === m.toLowerCase()
  )
);
const hasAllMention = mentions.includes("all");

if (mentions.length > 0 && !hasAgentMentions && !hasAllMention) {
  // Operator self-talk or unknown mentions only — don't fan out
  respond(true, { success: true, channel: channelSlug, timestamp: Date.now(), fanned: 0 });
  return;
}

// Filter roster to mentioned agents (or all if no mentions / @all)
const roster = filterRosterByMentions(fullRoster, content);
const authorName = (params as any)?.authorName ?? "Operator";

let fanned = 0;
for (const entry of roster) {
  if (isOnCooldown(entry.slug)) {
    console.log(`[vantage/agents] skipping ${entry.slug} — on cooldown`);
    continue;
  }

  // Build reply-to tag list
  const replyTo = buildReplyToList(mentions, fullRoster, entry.slug);
  const replyTag = replyTo.length > 0 ? `[reply-to: ${replyTo.map(n => `@${n}`).join(" ")}] ` : "";

  let fullMessage: string;
  if (shouldInjectRoster(entry.sessionKey)) {
    const rosterMsg = buildRosterMessage(roster, entry.slug);
    fullMessage = `[SYSTEM] ${rosterMsg}\n\n[agents-channel]${replyTag}${authorName}: ${content}`;
    markRosterInjected(entry.sessionKey);
  } else {
    fullMessage = `[agents-channel]${replyTag}${authorName}: ${content}`;
  }

  registerInjection(entry.sessionKey, {
    agentsChannelSlug: channelSlug,
    agentSlug: entry.slug,
    agentName: entry.agentName,
    injectedAt: Date.now(),
  });

  try {
    await injectChatMessage(fullMessage, entry.sessionKey);
    fanned++;
  } catch (e: any) {
    console.error(`[vantage/agents] fan-out inject failed for ${entry.slug}: ${e?.message}`);
  }
}

respond(true, { success: true, channel: channelSlug, timestamp: Date.now(), fanned });
```

---

## 14. Open Questions

1. **Agent-to-agent mentions:** Should `@Maven` in Eagle's response trigger a relay to Maven? (Recommendation: Out of scope, handle in future iteration)

2. **Mention deduplication:** If operator sends `@Eagle @Eagle`, should Eagle receive twice? (Current: No, roster filtering returns unique entries)

3. **Thread context:** Should agents have access to the full conversation thread, or just the current message? (Current: Just current message + roster context)

---

## 15. Summary

The core routing infrastructure already exists. This spec adds:

1. **Operator detection** — skip fan-out for `@Aaron`-only messages
2. **Reply-to injection** — explicit `[reply-to: @Aaron @Other]` tag in message
3. **Roster cleanup** — remove agents from roster on channel deletion
4. **Edge case handling** — unknown mentions, self-tagging, operator self-talk

Estimated implementation time: 2-3 hours including testing.
