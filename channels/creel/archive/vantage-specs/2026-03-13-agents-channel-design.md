# Agents Channel — Design Document

**Date:** 2026-03-13
**Status:** Approved
**Approach:** Gateway-Mediated Fan-Out (Approach A)

## Overview

A shared channel where multiple per-channel agents can participate alongside humans in free-form conversation. The gateway handles fan-out, cooldown enforcement, and roster management. The client renders agent-attributed messages with name badges.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Participation model | Free-form | All opted-in agents see every message and decide whether to respond based on their soul. Most natural for emergent collaboration. |
| Rate limiting | Per-agent cooldown (30s default) | Simple, predictable. Prevents runaway loops without complex token budgeting. |
| Agent-to-agent | Allowed | Agents can respond to both human and agent messages. Cooldown prevents loops. This is where the real collaborative value lives. |
| Agent discovery | Injected roster on join | System message listing all participants (name, channel, purpose) injected on first fan-out. Updated when roster changes. |
| Architecture | Gateway-mediated fan-out | All logic server-side. Client just renders a normal channel. Rate limiting is centralized and reliable. Works regardless of client state. |

## Architecture

### Channel Properties

The agents channel is a special channel type:

- Flagged with `isAgentsChannel: true`
- Does NOT have its own soul/agent (it's a venue, not an actor)
- Maximum one agents channel per workspace
- Messages route via `vantage.message` (same as non-agent channels)
- Stores a roster of participating agent slugs

### Opt-In Mechanism

Per-channel agents (channels with a `soul`) can opt in via:

- A "Join Agents Channel" checkbox on channel creation
- A toggle on channel edit/rename for existing agents
- Sent as `joinAgentsChannel: bool` in RPC params

## Message Flow

### Human Message

```
User types in agents channel
  -> Client: vantage.message(channel: "agents-channel", content: "...")
  -> Gateway stores message in channel history (normal)
  -> Gateway fans out to each opted-in agent session via chat.send
  -> Each agent responds on its own session
  -> Gateway intercepts responses, tags with agentName, posts to agents channel
  -> Client picks up new messages via polling (normal 2s cycle)
  -> Client renders messages with agent attribution badges
```

### Agent-to-Agent

```
Agent A posts response to agents channel
  -> Gateway stores it, fans out to all OTHER opted-in agents (not back to A)
  -> Cooldown check: if Agent B responded < 30s ago, skip fan-out to B
  -> Agent C receives, decides to respond (or not, per its soul)
  -> Gateway posts Agent C's response, fans out to others (with cooldown)
  -> Natural conversation emerges, rate-limited by cooldown
```

## Server-Side Spec (Eagle)

### RPC Parameter Changes

| Existing RPC | New Parameter | Behavior |
|---|---|---|
| `vantage.channels.create` | `isAgentsChannel: bool` | Marks channel as agents channel. Max one per workspace. Reject if one already exists. |
| `vantage.channels.create` | `joinAgentsChannel: bool` | Registers this channel's agent on the agents channel roster. Requires channel to have a `soul`. |
| `vantage.channels.rename` | `joinAgentsChannel: bool` | Toggle opt-in/out for existing per-channel agents. |
| `vantage.channels.list` | (response) | Include `isAgentsChannel: bool` on each channel object. |

### Server-Side Data

- `isAgentsChannel` flag persisted on the channel record
- Roster: list of `{ slug, agentName, sessionKey, purpose }` for each opted-in agent
  - `purpose` derived from the first line of the agent's soul
- Per-agent cooldown tracker: in-memory `Map<slug, lastResponseTimestamp>`

### Fan-Out Logic

1. Message arrives in agents channel via `vantage.message`
2. Store message normally in channel history
3. For each agent on the roster:
   - **Self-suppression:** Skip if message originated from this agent
   - **Cooldown check:** Skip if `Date.now() - lastResponseTimestamp[slug] < cooldownMs`
   - **Inject:** Send to agent session via `chat.send` with context prefix:
     `[agents-channel] {authorName}: {content}`
4. When agent responds:
   - Store in agents channel (NOT the agent's own channel)
   - Include metadata: `{ "agentName": "Glimmer", "sourceChannel": "glimmer" }`
   - Broadcast to clients via normal `vantage.new` ping
   - Trigger fan-out to other roster agents (repeat step 3)
   - Update `lastResponseTimestamp[slug]`

### Roster Injection

On first fan-out to an agent (or when roster changes), inject a system message into the agent's session:

```
You are participating in a shared agents channel. Other participants:
- Glimmer (channel: glimmer) — Marketing content and brand voice
- Scout (channel: scout) — Research and competitive analysis
- Forge (channel: forge) — Code generation and technical tasks

Respond only when the conversation is relevant to your expertise.
Keep responses concise. You may address other agents by name.
```

### Message Payload Additions

Messages stored in the agents channel include in their metadata JSON:

```json
{
  "agentName": "Glimmer",
  "sourceChannel": "glimmer"
}
```

### Cooldown Configuration

Default 30 seconds. Hardcode initially, make configurable per-workspace later.

### Edge Cases

- **Agent session not running:** Skip fan-out to that agent. Don't start sessions on demand.
- **Agents channel deleted:** Remove all roster entries. Opted-in agents continue functioning in their own channels.
- **Agent channel deleted:** Remove from roster automatically.
- **Empty roster:** Channel functions as a normal channel (no fan-out).

## Client-Side Spec (VantageOC)

### Data Model Changes

**VantageChannel** — add field:

```swift
var isAgentsChannel: Bool  // defaults to false, decoded from server
```

**ChannelCreateParams** — add fields:

```swift
var isAgentsChannel: Bool?      // create as agents channel
var joinAgentsChannel: Bool?    // opt this channel's agent into the agents channel
```

**DisplayMessage** — add field:

```swift
var agentName: String?  // parsed from StoredMessage.metadata JSON
```

### UI Changes

**CreateChannelSheet:**

- New toggle: "Create as Agents Channel"
  - When on: hides soul/agent name fields (agents channel has no agent of its own)
  - When off: shows normal channel creation form
- New checkbox (visible when channel has a soul AND an agents channel exists):
  "Join Agents Channel"
  - Sends `joinAgentsChannel: true` in create params

**Channel Edit/Rename:**

- Same "Join Agents Channel" checkbox for existing per-channel agents
- Toggle join/leave at any time

**Sidebar:**

- Agents channel gets default icon `🤖` (user can override)
- Only one agents channel can exist (disable "Create as Agents Channel" toggle if one exists)

**ChatBubbleView — Agent Attribution:**

For messages in the agents channel where `agentName` is non-nil:

```
    Glimmer
    +---------------------------+
    | Here's what I think...    |
    +---------------------------+
```

- Small name label above the bubble (muted text, caption font)
- Left-aligned like assistant messages
- Human messages render normally (right-aligned, no badge)

**ViewModel:**

- No routing changes needed. Agents channel uses `vantage.message` like any non-agent channel
- `agentName` parsed from `StoredMessage.metadata` in `DisplayMessage.init(stored:)`

### Files to Modify

| File | Change |
|------|--------|
| `Models/Channel.swift` | Add `isAgentsChannel: Bool` |
| `Services/GatewayAPI.swift` | Add params to `ChannelCreateParams` |
| `Views/Sidebar/CreateChannelSheet.swift` | Add toggles for agents channel creation and join |
| `Views/Channel/ChatBubbleView.swift` | Add agent name badge above bubble |
| `ViewModels/ChannelViewModel.swift` | Parse `agentName` from metadata in `DisplayMessage.init(stored:)` |
| `Stores/ChannelStore.swift` | Track whether an agents channel exists (for UI gating) |
