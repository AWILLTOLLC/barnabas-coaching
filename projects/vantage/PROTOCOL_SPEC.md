# VantageOC — Full Protocol Spec

**Status:** Ready for implementation  
**Scope:** OpenClaw channel plugin (TypeScript) + Vantage macOS client (Swift)  
**Purpose:** Replace text-parsing hacks with a typed, verifiable, bidirectional protocol between Dru and Vantage

---

## Overview

Right now Vantage communicates with Dru through text conventions: `[SAFETY:RED:r-TIMESTAMP]`, `[CHANNEL:slug]`, `HEARTBEAT_OK`. This is fragile, unverifiable, and limited.

This spec defines a proper typed protocol. Every message has a `type`, a structured payload, and a `msgId`. Vantage renders based on type, not text parsing. Dru sends structured envelopes, not formatted strings. The approve/deny flow is cryptographically tied to a session-authenticated RPC call, not a chat message anyone could type.

---

## Architecture

```
Dru (OpenClaw agent)
        │
        │  TypeScript channel plugin
        ▼
OpenClaw Gateway (JSON-RPC WebSocket)
        │
        │  Existing authenticated WS connection
        ▼
VantageOC (macOS app)
```

The channel plugin registers:
1. A `vantage` channel in OpenClaw (outbound: push typed events to Vantage)
2. Gateway RPC methods for inbound (Vantage → Dru)
3. A background service that tracks task state, proof of work logs, and cron data

---

## OpenClaw Plugin

### File structure

```
~/.openclaw/extensions/vantage/
├── openclaw.plugin.json
├── index.ts
├── types.ts
├── store.ts          # SQLite state: tasks, proofs, cron log
└── package.json      # if any deps needed
```

### `openclaw.plugin.json`

```json
{
  "id": "vantage",
  "name": "VantageOC Channel",
  "version": "1.0.0",
  "openclaw": {
    "extensions": ["./index.ts"],
    "channel": {
      "id": "vantage",
      "label": "VantageOC",
      "selectionLabel": "VantageOC (local)",
      "docsPath": "/channels/vantage",
      "blurb": "Private operator control center channel.",
      "aliases": ["vantage", "vc"]
    }
  }
}
```

### `index.ts` — plugin entry

```typescript
import { VantageStore } from './store';
import { OutboundEnvelope } from './types';

export default function register(api: any) {
  const store = new VantageStore();

  // --- Channel definition ---
  const plugin = {
    id: 'vantage',
    meta: {
      id: 'vantage',
      label: 'VantageOC',
      selectionLabel: 'VantageOC (local)',
      docsPath: '/channels/vantage',
      blurb: 'Private operator control center.',
      aliases: ['vantage', 'vc'],
    },
    capabilities: {
      chatTypes: ['direct'],
      actions: true,
      threading: false,
      media: true,
    },
    config: {
      listAccountIds: (cfg: any) => ['default'],
      resolveAccount: (cfg: any, accountId: string) => ({ accountId }),
    },
    outbound: {
      deliveryMode: 'direct' as const,
      sendText: async ({ text, metadata }: { text: string; metadata?: any }) => {
        // Parse structured envelope from Dru if present, else wrap as chat
        let envelope: OutboundEnvelope;
        try {
          envelope = JSON.parse(text);
          if (!envelope.type) throw new Error('not an envelope');
        } catch {
          envelope = { type: 'chat', msgId: genId(), payload: { text }, ts: Date.now() };
        }
        pushToVantage(api, envelope);
        return { ok: true };
      },
    },
  };

  api.registerChannel({ plugin });

  // --- Inbound RPC methods (Vantage → OpenClaw) ---

  // Operator sends a chat message from Vantage
  api.registerGatewayMethod('vantage.message', async ({ params, respond }: any) => {
    const { text, channelId, senderId } = params;
    await api.runtime.injectInboundMessage({
      channel: 'vantage',
      text,
      senderId: senderId ?? 'operator',
      chatId: channelId ?? 'vantage:default',
      metadata: { surface: 'vantage', provider: 'vantage' },
    });
    respond(true, { ok: true });
  });

  // Operator approves a safety alert
  api.registerGatewayMethod('vantage.safety.approve', async ({ params, respond }: any) => {
    const { requestId } = params;
    store.resolveSafetyAlert(requestId, 'approved');
    await api.runtime.injectInboundMessage({
      channel: 'vantage',
      text: `[SAFETY:APPROVED:${requestId}]`,
      senderId: 'operator',
      chatId: 'vantage:default',
      metadata: { surface: 'vantage', isSafetyResponse: true },
    });
    respond(true, { ok: true });
  });

  // Operator denies a safety alert
  api.registerGatewayMethod('vantage.safety.deny', async ({ params, respond }: any) => {
    const { requestId, reason } = params;
    store.resolveSafetyAlert(requestId, 'denied');
    await api.runtime.injectInboundMessage({
      channel: 'vantage',
      text: `[SAFETY:DENIED:${requestId}]${reason ? ' ' + reason : ''}`,
      senderId: 'operator',
      chatId: 'vantage:default',
      metadata: { surface: 'vantage', isSafetyResponse: true },
    });
    respond(true, { ok: true });
  });

  // Operator approves a channel draft
  api.registerGatewayMethod('vantage.draft.approve', async ({ params, respond }: any) => {
    const { draftId, editedContent } = params;
    store.resolveDraft(draftId, 'approved', editedContent);
    await api.runtime.injectInboundMessage({
      channel: 'vantage',
      text: `[DRAFT:APPROVED:${draftId}]${editedContent ? '\n' + editedContent : ''}`,
      senderId: 'operator',
      chatId: 'vantage:default',
      metadata: { surface: 'vantage', isDraftResponse: true },
    });
    respond(true, { ok: true });
  });

  // Operator rejects a channel draft
  api.registerGatewayMethod('vantage.draft.reject', async ({ params, respond }: any) => {
    const { draftId, reason } = params;
    store.resolveDraft(draftId, 'rejected');
    await api.runtime.injectInboundMessage({
      channel: 'vantage',
      text: `[DRAFT:REJECTED:${draftId}]${reason ? ' ' + reason : ''}`,
      senderId: 'operator',
      chatId: 'vantage:default',
      metadata: { surface: 'vantage', isDraftResponse: true },
    });
    respond(true, { ok: true });
  });

  // Query task proof
  api.registerGatewayMethod('vantage.task.proof', ({ params, respond }: any) => {
    const { taskId } = params;
    const proof = store.getTaskProof(taskId);
    respond(true, proof ?? { error: 'not found' });
  });

  // Query all active tasks
  api.registerGatewayMethod('vantage.tasks.list', ({ params, respond }: any) => {
    respond(true, store.listActiveTasks());
  });

  // Query cron schedule
  api.registerGatewayMethod('vantage.crons.list', async ({ respond }: any) => {
    const crons = await api.runtime.getCronJobs?.() ?? [];
    respond(true, crons);
  });

  // Query heartbeat status
  api.registerGatewayMethod('vantage.heartbeat.status', ({ respond }: any) => {
    respond(true, store.getHeartbeatStatus());
  });

  // Background service: tool call interceptor for proof of work
  api.registerService({
    id: 'vantage-proof-tracker',
    start: () => {
      api.runtime.onToolCall?.((event: any) => {
        const { sessionId, tool, params, result, durationMs } = event;
        store.recordToolCall(sessionId, { tool, params, result, durationMs, ts: Date.now() });
      });
    },
    stop: () => {},
  });
}

function pushToVantage(api: any, envelope: OutboundEnvelope) {
  api.runtime.pushGatewayEvent?.('vantage.event', envelope);
}

function genId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
```

---

## Outbound Envelope Protocol

Every message Dru sends to Vantage is a JSON envelope. Vantage renders based on `type`.

### Base envelope

```typescript
interface OutboundEnvelope {
  type: MessageType;
  msgId: string;       // unique per message
  ts: number;          // unix ms
  payload: object;     // type-specific
  channelSlug?: string; // if targeting a specific channel
}

type MessageType =
  | 'chat'
  | 'safety_alert'
  | 'task_spawn'
  | 'task_update'
  | 'task_complete'
  | 'task_failed'
  | 'proof_receipt'
  | 'draft'
  | 'report'
  | 'heartbeat'
  | 'cron_status'
  | 'system_event';
```

---

## Message Type Payloads

### `chat` — regular conversation message

```typescript
{
  type: 'chat',
  msgId: string,
  ts: number,
  payload: {
    text: string,         // markdown
    streaming?: boolean,  // true if more tokens coming
    thinkingText?: string // collapsed reasoning (if available)
  }
}
```

**Vantage renders:** chat bubble in main Chat view, streaming token-by-token.

---

### `safety_alert` — blocking or informational safety notice

```typescript
{
  type: 'safety_alert',
  msgId: string,
  ts: number,
  payload: {
    level: 'red' | 'yellow',
    requestId: string,      // e.g. "r-1741234567" — unique, used in approve/deny
    description: string,    // human-readable what Dru is about to do
    command?: string,       // optional: specific command/action text
    blocking: boolean,      // true = Dru is paused waiting for response
    expiresAt?: number      // optional unix ms: auto-deny if not resolved by then
  }
}
```

**Vantage renders:**
- `red` + `blocking: true`: Full-screen overlay card, red border, Approve/Deny buttons, critical system notification with sound. Dru is paused.
- `yellow`: Inline banner in Chat, amber color, no buttons needed (informational only).

**Approve/Deny flow:**
1. Operator clicks Approve → calls `vantage.safety.approve({ requestId })`
2. Operator clicks Deny → calls `vantage.safety.deny({ requestId, reason? })`
3. Plugin injects the appropriate `[SAFETY:APPROVED/DENIED:requestId]` message into Dru's session
4. Dru unblocks and proceeds (or stops)

**Why this beats text parsing:** the `requestId` is authenticated via the gateway session token. You can't spoof an approval by typing text — only a real gateway RPC call with a valid auth token triggers it.

---

### `task_spawn` — sub-agent spawned

```typescript
{
  type: 'task_spawn',
  msgId: string,
  ts: number,
  payload: {
    taskId: string,         // UUID, unique per spawn
    parentTaskId?: string,  // if this is a sub-sub-agent
    agentLabel: string,     // "SEO content writer", "influencer researcher", etc.
    sessionKey?: string,    // OpenClaw session key if available
    task: string,           // task description (truncated to 200 chars)
    proofRequirements: ProofRequirement[],
    spawnedBy: string       // agent id that spawned this
  }
}

interface ProofRequirement {
  type: 'file_written' | 'file_modified' | 'exec_success' | 'web_request' | 'screenshot' | 'custom';
  description: string;      // "Must write output to tasks/influencers/results.json"
  required: boolean;        // false = nice-to-have
}
```

**Vantage renders:** New card in Work Panel with status `running`, spinner, task description, proof requirements checklist.

---

### `task_update` — progress update from a running task

```typescript
{
  type: 'task_update',
  msgId: string,
  ts: number,
  payload: {
    taskId: string,
    status: 'running' | 'blocked' | 'verifying',
    progress?: string,      // "Found 8 of 50 targets"
    currentStep?: string,   // "Scraping YouTube channel list"
    toolCallCount: number,  // running total of tool calls made
    elapsedMs: number
  }
}
```

**Vantage renders:** Updates the task card in Work Panel. Progress text replaces previous.

---

### `task_complete` — task finished, with proof

```typescript
{
  type: 'task_complete',
  msgId: string,
  ts: number,
  payload: {
    taskId: string,
    status: 'verified' | 'unverified' | 'partial',
    summary: string,
    proofLog: ProofEntry[],
    durationMs: number,
    toolCallCount: number,
    verifiedBy?: string     // if a verifier agent ran: its session key
  }
}

interface ProofEntry {
  type: 'file_written' | 'file_modified' | 'exec_success' | 'web_request' | 'screenshot' | 'tool_call';
  ts: number,
  detail: string,          // "Wrote 3,241 bytes to tasks/influencers/results.json"
  verified: boolean,
  evidence?: string        // hash, exit code, byte count, URL, etc.
}
```

**Vantage renders:** Task card transitions to `complete`. Status badge: green `VERIFIED`, yellow `UNVERIFIED`, orange `PARTIAL`. Expandable proof log shows each ProofEntry. Operator can tap any entry to see full detail.

**Status meaning:**
- `verified`: Dru or a verifier agent independently confirmed all required outputs exist and are non-trivial
- `unverified`: Agent self-reported completion, no independent check performed
- `partial`: Some required proof requirements met, not all

---

### `task_failed` — task failed or was abandoned

```typescript
{
  type: 'task_failed',
  msgId: string,
  ts: number,
  payload: {
    taskId: string,
    reason: string,
    partialProofLog: ProofEntry[],
    durationMs: number,
    toolCallCount: number,
    recoverable: boolean
  }
}
```

**Vantage renders:** Task card transitions to `failed`, red badge. Expandable failure reason + partial proof log.

---

### `proof_receipt` — real-time proof event during task execution

```typescript
{
  type: 'proof_receipt',
  msgId: string,
  ts: number,
  payload: {
    taskId: string,
    entry: ProofEntry      // single proof event as it happens
  }
}
```

**Vantage renders:** Adds a checkmark tick to the task card's proof requirements list in real time. Operators can see work happening live.

---

### `draft` — content awaiting operator approval

```typescript
{
  type: 'draft',
  msgId: string,
  ts: number,
  channelSlug: string,    // which channel this belongs to
  payload: {
    draftId: string,      // unique, used in approve/reject RPC
    platform: string,     // "x-thread", "linkedin-post", "tiktok-script", etc.
    content: string,      // full draft content, markdown
    metadata: {
      scheduledFor?: string,   // ISO8601
      targetAudience?: string,
      wordCount?: number,
      estimatedReach?: string
    },
    agentId: string,
    agentName: string
  }
}
```

**Vantage renders:** Draft card in the target channel with Approve/Edit/Reject buttons.

---

### `report` — structured data / KPI output

```typescript
{
  type: 'report',
  msgId: string,
  ts: number,
  channelSlug?: string,
  payload: {
    title: string,
    content: string,        // markdown, may include tables
    reportType: string,     // "daily-kpi", "influencer-list", "weekly-summary", etc.
    data?: object,          // optional raw data for Vantage to render as chart/table
    agentId: string,
    agentName: string
  }
}
```

**Vantage renders:** Report card in channel or Chat. If `data` is present, render as native table or chart depending on `reportType`.

---

### `heartbeat` — operational health pulse

```typescript
{
  type: 'heartbeat',
  msgId: string,
  ts: number,
  payload: {
    status: 'ok' | 'alert' | 'error',
    checks: HeartbeatCheck[],
    nextHeartbeatAt: number,    // unix ms
    sessionTokens: number,       // current session token count
    activeTaskCount: number,
    pendingApprovals: number     // drafts + safety alerts awaiting action
  }
}

interface HeartbeatCheck {
  name: string,           // "email", "calendar", "crons", "memory"
  status: 'ok' | 'skip' | 'alert' | 'error',
  detail?: string
}
```

**Vantage renders:** NOT in chat. Updates the Heartbeat panel silently. If `status` is `alert` or `error`, show a badge on the Heartbeat nav item. If `pendingApprovals > 0`, show a badge in the sidebar.

---

### `cron_status` — scheduled job update

```typescript
{
  type: 'cron_status',
  msgId: string,
  ts: number,
  payload: {
    jobs: CronJob[]
  }
}

interface CronJob {
  id: string,
  label: string,
  schedule: string,       // cron expression, human-readable
  nextRunAt: number,      // unix ms
  lastRunAt?: number,
  lastStatus?: 'success' | 'failure' | 'running',
  lastDurationMs?: number,
  enabled: boolean
}
```

**Vantage renders:** Updates the Cron timeline in the Dashboard. Shows upcoming jobs sorted by `nextRunAt`. Status badges on last run result.

---

### `system_event` — low-level operational notice

```typescript
{
  type: 'system_event',
  msgId: string,
  ts: number,
  payload: {
    event: string,        // "session_reset", "gateway_restart", "memory_updated", "error"
    severity: 'info' | 'warn' | 'error',
    detail: string,
    data?: object
  }
}
```

**Vantage renders:** Appended to Logs view. Severity `error` also triggers a banner in current view.

---

## Inbound RPC Methods (Vantage → Gateway)

All methods require the existing gateway auth token. No anonymous calls accepted.

| Method | Params | Description |
|---|---|---|
| `vantage.message` | `{ text, channelId?, senderId? }` | Operator sends a chat message |
| `vantage.safety.approve` | `{ requestId }` | Approve a red safety alert |
| `vantage.safety.deny` | `{ requestId, reason? }` | Deny a red safety alert |
| `vantage.draft.approve` | `{ draftId, editedContent? }` | Approve a channel draft |
| `vantage.draft.reject` | `{ draftId, reason? }` | Reject a channel draft |
| `vantage.task.proof` | `{ taskId }` | Get full proof log for a task |
| `vantage.tasks.list` | `{}` | List all active/recent tasks |
| `vantage.crons.list` | `{}` | Get all scheduled jobs |
| `vantage.heartbeat.status` | `{}` | Get latest heartbeat state |
| `vantage.channels.list` | `{}` | List all channels |
| `vantage.channels.history` | `{ channelSlug, limit?, before? }` | Paginated channel message history |

---

## Proof of Work Protocol

### How it works

Every time Dru spawns a sub-agent, the spawn call includes:
- A unique `taskId` (UUID)
- A `proofRequirements` array defining what acceptable output looks like

The gateway plugin intercepts all tool calls made within that session and logs them against the `taskId`. This is objective — it happens at the gateway level, not self-reported by the agent.

When the agent reports completion, Dru runs a verification step before marking the task `verified`:
1. Check that at least one non-trivial tool call was made (filters out hollow completions)
2. Cross-check claimed file outputs actually exist and have non-zero size
3. For exec tasks: check exit code 0
4. For content tasks: check that written content exceeds a minimum length

Only after verification does Dru send `task_complete` with `status: "verified"`.

### Verification tiers

| Tier | When used | Method |
|---|---|---|
| `auto` | Low-stakes tasks | Gateway tool call count check only |
| `standard` | Normal business tasks | Dru checks claimed outputs (file exists, exec success) |
| `strict` | High-stakes or expensive tasks | Separate verifier sub-agent spawned with read-only access |

### The "hollow completion" catch

An agent that does nothing generates zero tool calls. The gateway proof log for that `taskId` is empty. Dru detects this and marks the task `unverified` with reason `"no tool calls recorded"` regardless of what the agent's final message says.

This catches the most common failure mode: an agent that generates a plausible-sounding completion message without actually doing any work.

### Spawn task format (how Dru embeds proof requirements)

When Dru spawns a sub-agent, the task description ends with a machine-readable block:

```
[TASK_CONTRACT]
taskId: uuid-here
requiredOutputs:
  - type: file_written
    path: tasks/influencers/results.json
    minBytes: 100
    required: true
  - type: exec_success
    description: Tests pass
    required: false
verificationTier: standard
[/TASK_CONTRACT]
```

The sub-agent should acknowledge this in its output, but even if it doesn't, the gateway is tracking tool calls independently.

---

## Dru's Behavior Changes

With this protocol, Dru changes how it communicates:

### Safety alerts (was text, now structured)

**Before:**
```
[SAFETY:RED:r-1234] About to delete production database — blocked, awaiting approval.
```

**After:**
Dru calls `message(channel="vantage")` with a JSON envelope:
```json
{
  "type": "safety_alert",
  "msgId": "msg-abc123",
  "ts": 1741234567000,
  "payload": {
    "level": "red",
    "requestId": "r-1741234567",
    "description": "About to delete production database",
    "command": "DROP TABLE users;",
    "blocking": true
  }
}
```

### Heartbeats (was chat messages, now silent)

**Before:** Sends `HEARTBEAT_OK` or an alert message to the chat stream.

**After:** Sends a `heartbeat` envelope. If `status: ok`, Vantage silently updates the Heartbeat panel. Only alerts surface in chat. Chat stays clean.

### Sub-agent spawns (now include task contracts)

Every `sessions_spawn` call appends a `[TASK_CONTRACT]` block to the task. Dru tracks all spawned taskIds in memory for the session and follows up with verification before reporting completion upstream.

---

## Vantage Implementation Checklist

### New event handler
- [ ] Parse incoming gateway WebSocket events for `vantage.event` type
- [ ] Route to appropriate renderer based on `envelope.type`
- [ ] Fall back to chat bubble for unrecognized types (forward compatibility)

### Per-type renderers
- [ ] `chat` — existing chat bubble (no change needed)
- [ ] `safety_alert` — overlay card (red) + banner (yellow), Approve/Deny buttons
- [ ] `task_spawn` — Work Panel card, proof requirements checklist
- [ ] `task_update` — update existing Work Panel card
- [ ] `task_complete` — finalize card, show proof log, status badge
- [ ] `task_failed` — finalize card with failure state
- [ ] `proof_receipt` — real-time checkmark on task card
- [ ] `draft` — draft card in target channel (existing channels feature)
- [ ] `report` — report card in channel or Chat
- [ ] `heartbeat` — silent panel update, badge if alert/error
- [ ] `cron_status` — Dashboard cron timeline
- [ ] `system_event` — Logs view, banner if error

### Inbound actions
- [ ] `vantage.safety.approve` / `vantage.safety.deny` — wired to Approve/Deny buttons
- [ ] `vantage.draft.approve` / `vantage.draft.reject` — wired to channel draft buttons
- [ ] `vantage.message` — wired to Chat compose field send action
- [ ] `vantage.task.proof` — triggered on "View Proof" tap in task card
- [ ] `vantage.tasks.list` — called on Work Panel open
- [ ] `vantage.crons.list` — called on Dashboard open, polled every 60s
- [ ] `vantage.heartbeat.status` — polled every 5 min

### Sidebar badges
- [ ] Heartbeat nav item: badge when `heartbeat.status` is `alert` or `error`
- [ ] Any channel: badge when `pendingApprovals > 0`
- [ ] Safety alert: global red indicator in window chrome when blocking alert is pending

---

## SQLite Schema (plugin-side)

The plugin maintains its own lightweight SQLite DB at `~/.openclaw/vantage-plugin.db`.

```sql
-- Task registry
CREATE TABLE IF NOT EXISTS tasks (
    task_id       TEXT PRIMARY KEY,
    parent_id     TEXT,
    session_key   TEXT,
    agent_label   TEXT NOT NULL,
    task_desc     TEXT NOT NULL,
    proof_reqs    TEXT NOT NULL,  -- JSON array
    status        TEXT NOT NULL DEFAULT 'running',
    verification  TEXT NOT NULL DEFAULT 'standard',
    spawned_at    INTEGER NOT NULL,
    completed_at  INTEGER,
    duration_ms   INTEGER,
    summary       TEXT
);

-- Tool call log (the objective proof record)
CREATE TABLE IF NOT EXISTS tool_calls (
    id            TEXT PRIMARY KEY,
    task_id       TEXT NOT NULL,
    session_key   TEXT NOT NULL,
    tool          TEXT NOT NULL,
    params_hash   TEXT,           -- SHA256 of params (not full params, for privacy)
    result_summary TEXT,          -- brief description of result
    duration_ms   INTEGER,
    ts            INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

-- Safety alert log
CREATE TABLE IF NOT EXISTS safety_alerts (
    request_id    TEXT PRIMARY KEY,
    level         TEXT NOT NULL,
    description   TEXT NOT NULL,
    blocking      INTEGER NOT NULL,
    created_at    INTEGER NOT NULL,
    resolved_at   INTEGER,
    resolution    TEXT   -- 'approved' | 'denied' | 'expired'
);

-- Draft log
CREATE TABLE IF NOT EXISTS drafts (
    draft_id      TEXT PRIMARY KEY,
    channel_slug  TEXT NOT NULL,
    platform      TEXT NOT NULL,
    content       TEXT NOT NULL,
    metadata      TEXT,           -- JSON
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    INTEGER NOT NULL,
    resolved_at   INTEGER,
    edited_content TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_task ON tool_calls(task_id, ts);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, spawned_at DESC);
```

---

## Future Considerations

These are not in scope for the initial implementation but the protocol is designed to support them.

### Multi-operator
The protocol is session-aware. Multiple Vantage instances could connect simultaneously. Safety alerts would broadcast to all and accept the first response. Draft approvals would record which operator resolved them.

### Agent-to-agent messaging
`vantage.message` could be extended to route messages between specific agents, not just from operator to main session. Supports future agent coordination UIs.

### Proof replay
Since every tool call is logged with a timestamp, Vantage could offer a "replay" view for any completed task — step-by-step timeline of what the agent actually did, in order.

### Streaming proof
`proof_receipt` events already support real-time proof streaming. A future "live task view" could show each tool call as it happens, full detail, with diff views for file writes.

### Budget enforcement
`task_spawn` could include `maxToolCalls` and `maxCostCents` limits. The gateway plugin enforces these and sends `task_failed` with reason `"budget_exceeded"` if crossed. Prevents runaway agents on expensive tasks.

### Approval delegation
Drafts and safety alerts could carry an `urgency` level and a `timeout`. If the operator doesn't respond within `timeout`, a configurable default action fires (auto-deny for safety, skip for drafts). Prevents tasks from blocking indefinitely.

### Per-channel agent assignment
Channels could have a default agent assignment. Messages posted to `#barnabas-coaching` automatically route to a Barnabas-specific agent context, not the main Dru session.

### Webhook bridge
A future `vantage.webhook` RPC method could accept inbound events from external services (Shopify order placed, App Store review submitted) and inject them as typed channel messages. Vantage becomes the aggregator for all business events, not just agent outputs.
