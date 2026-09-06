# VantageOC V2 Technical Specification

**Version:** 2.0.1  
**Status:** Server-Side Complete — Client Implementation Ready  
**Date:** 2026-03-09  
**Author:** Principal Engineer (Dru)

> **Implementation Note (2026-03-09):** Server-side plugin is live and running. Several corrections were made during implementation — see callout boxes throughout. The client-side (Section 9 onward) is unimplemented and ready for work.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Server Side: New File Structure](#2-server-side-new-file-structure)
3. [index.ts — New Registration](#3-indexts--new-registration)
4. [src/runtime.ts](#4-srcruntimetsbr)
5. [src/types.ts](#5-srctypests)
6. [src/channel.ts — ChannelPlugin Definition](#6-srcchannelts--channelplugin-definition)
7. [src/subagent-hooks.ts](#7-srcsubagent-hooksts)
8. [src/rpc.ts](#8-srcrpcts)
9. [Client Side Changes](#9-client-side-changes)
10. [SQLite Schema](#10-sqlite-schema)
11. [RPC Reference Table](#11-rpc-reference-table)
12. [Migration: V1 → V2](#12-migration-v1--v2)
13. [Implementation Order](#13-implementation-order)

---

## 0. Confirmed SDK Facts (Verified Against Live Runtime)

These were discovered during server-side implementation. Do not revert to spec assumptions.

| Topic | Spec Assumption | Actual SDK Behavior |
|-------|----------------|---------------------|
| `listAccountIds` | `async (): Promise<string[]>` | **Synchronous** `(cfg?: unknown): string[]` — gateway iterates result directly |
| `resolveAccount` | `async (accountId): Promise<T \| null>` | **Synchronous** `(cfg: unknown, accountId: string): T \| null` — cfg is first arg |
| `defaultAccountId` | `async (): Promise<string>` | **Synchronous** `(cfg?: unknown): string` |
| `isConfigured` | `async (): Promise<boolean>` | `async (account: T, cfg?: unknown): Promise<boolean>` |
| `startAccount` | No-op, returns immediately | **Must block indefinitely** — returning immediately marks account "stopped", triggers crash-loop |
| `api.runtime.injectInboundMessage` | Exists, used for inbound injection | **Does not exist** in `PluginRuntime` — use WebSocket loopback (`chat.send` RPC) |
| `api.runtime.sendToChannel` | Exists, used for outbound broadcast | **Does not exist** — use `store.storeMessage()` + `broadcast()` from `rpc.ts` |
| `vantage.poll` param | `channelSlug: string` (single) | `channels: string[]` (array of slugs) |
| `vantage.poll` response cursor | `result.ts` | `result.serverTime` (Unix ms) |
| `api.registerRpcMethod` | Used for all RPC registration | **Does not exist** — actual SDK uses `api.registerGatewayMethod` with `({ params, respond, context })` handler signature |
| `ChannelMessageType` (Swift) | `case post, draft, report, alert, status` | **Wrong** — must match server `MessageType`: `chat`, `safety_alert`, `task_spawn`, `task_update`, `task_complete`, `task_failed`, `proof_receipt`, `draft`, `report`, `heartbeat`, `cron_status`, `system_event`, `context_compacting`, `context_compacted`, `channel_read`, `channel_created` |
| `OutboundEnvelope` (Swift) fields | `msgId`, `ts`, `channelSlug` | **Wrong** — actual fields: `payload.messageId`, `timestamp`, `channel` — see corrected `PollMessage` struct in Appendix B |

### Outbound Delivery Pattern (Actual)

```
Agent reply text
  → channel.ts sendText()
  → parseChannelPrefix() extracts envelope
  → store.storeMessage() persists to SQLite
  → getBroadcast() from rpc.ts fires "vantage.new" ping to all RPC clients
  → client calls vantage.poll?since=<cursor> to fetch new messages
```

### Inbound Delivery Pattern (Actual)

```
Client message (via RPC vantage.message)
  → rpc.ts handler
  → handleInboundMessage() in channel.ts
  → store.storeMessage() persists
  → loopback.ts injectChatMessage() → WebSocket → gateway chat.send RPC
  → OpenClaw agent session receives message
```

---

## 1. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VantageOC macOS Client                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Dashboard  │  │  Channels   │  │    Tasks    │  │   Safety Alerts     │ │
│  │    View     │  │    View     │  │    View     │  │       View          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                │                     │           │
│         └────────────────┴────────────────┴─────────────────────┘           │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │  WebSocket Client │                              │
│                          │   (JSON-RPC 2.0)  │                              │
│                          └─────────┬─────────┘                              │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     │ wss://gateway/rpc
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                          OpenClaw Gateway                                   │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │   RPC Transport   │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                        │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                        Vantage Channel Plugin                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │  │
│  │  │ channel  │  │ runtime  │  │   rpc    │  │ subagent │  │  store  │  │  │
│  │  │   .ts    │  │   .ts    │  │   .ts    │  │ hooks.ts │  │   .ts   │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │  │
│  │       │             │             │             │             │       │  │
│  │       └─────────────┴─────────────┴─────────────┴─────────────┘       │  │
│  │                                   │                                   │  │
│  │                         ┌─────────▼─────────┐                         │  │
│  │                         │   VantageStore    │                         │  │
│  │                         │     (SQLite)      │                         │  │
│  │                         └───────────────────┘                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │   OpenClaw Core   │                              │
│                          │  (Agent Runtime)  │                              │
│                          └───────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### V1 vs V2 Changes

| Aspect | V1 (Current) | V2 (New) |
|--------|--------------|----------|
| Plugin registration | `export default function register(api: any)` | Typed `OpenClawPluginApi` with `ChannelPlugin<T>` |
| Inbound messages | `loopbackChatSend` via self-connecting WebSocket | WebSocket loopback (preserved — `injectInboundMessage` does not exist in the SDK) |
| Session management | Manual `sessions.json` file writes | SDK session management |
| Subagent routing | None (replies go to main channel) | Subagent hooks bind replies to originating channel |
| Type safety | Loose `any` types throughout | Full TypeScript interfaces |
| Lifecycle hooks | Partial implementation | Full `before_compaction` / `after_compaction` |
| Config schema | None | Zod schema with validation |

### Key Architectural Decisions

1. **Module-scoped bindings over SQLite for subagent tracking**: Subagent bindings are ephemeral (live only while subagent runs). Using a `Map<string, string>` in module scope avoids DB writes for short-lived state.

2. **WebSocket loopback preserved for inbound**: The spec originally called for `api.runtime.injectInboundMessage()`, but this method does not exist in the OpenClaw Plugin SDK. The V1 loopback approach (`loopback.ts`) is retained — it self-connects to the gateway via WebSocket and calls `chat.send` RPC.

3. **Preserve VantageStore unchanged**: The SQLite store works well. Only the integration layer changes.

---

## 2. Server Side: New File Structure

```
~/.openclaw/extensions/vantage/
├── openclaw.plugin.json      # Plugin manifest
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── index.ts                  # Plugin entry point
└── src/
    ├── channel.ts            # ChannelPlugin implementation
    ├── runtime.ts            # Singleton runtime accessor
    ├── store.ts              # VantageStore (UNCHANGED from V1)
    ├── rpc.ts                # RPC method registrations
    ├── subagent-hooks.ts     # Subagent lifecycle hooks
    └── types.ts              # All TypeScript interfaces
```

### File Purposes

| File | Purpose | Key Exports |
|------|---------|-------------|
| `openclaw.plugin.json` | Plugin manifest for OpenClaw loader | N/A (JSON) |
| `index.ts` | Plugin entry, registration with SDK | `default` export (plugin object) |
| `src/channel.ts` | ChannelPlugin interface implementation | `vantagePlugin` |
| `src/runtime.ts` | Runtime singleton access | `setVantageRuntime`, `getVantageRuntime` |
| `src/store.ts` | SQLite persistence layer | `VantageStore` class |
| `src/rpc.ts` | JSON-RPC method handlers | `registerVantageRpcMethods` |
| `src/subagent-hooks.ts` | Subagent binding/delivery | `registerVantageSubagentHooks` |
| `src/types.ts` | All TypeScript types | All interfaces and type unions |

---

## 3. index.ts — New Registration

```typescript
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";

import { vantagePlugin } from "./src/channel.js";
import { setVantageRuntime } from "./src/runtime.js";
import { registerVantageSubagentHooks } from "./src/subagent-hooks.js";
import { registerVantageRpcMethods } from "./src/rpc.js";
import { VantageStore } from "./src/store.js";

// Initialize store singleton
const store = new VantageStore();

export default {
  id: "vantage",
  name: "Vantage",
  description: "VantageOC operator control center channel plugin",
  configSchema: emptyPluginConfigSchema(),
  
  register(api: OpenClawPluginApi) {
    // 1. Store runtime reference for cross-module access
    setVantageRuntime(api.runtime);
    
    // 2. Register channel plugin
    api.registerChannel({ plugin: vantagePlugin });
    
    // 3. Register subagent lifecycle hooks
    registerVantageSubagentHooks(api);
    
    // 4. Register RPC methods
    registerVantageRpcMethods(api, store);
    
    // 5. Register lifecycle hooks for context compaction
    // ⚠️ NOTE: api.runtime.sendToChannel does NOT exist in the SDK.
    // Outbound delivery uses store.storeMessage() + broadcast() pattern instead.
    // See channel.ts sendText() and rpc.ts getBroadcast() for the actual approach.
    // These hooks are aspirational — implement using broadcast if needed.
    api.on("before_compaction", async (event) => {
      const { sessionKey } = event;
      // TODO: broadcast context_compacting envelope to SSE clients
      console.log(`[vantage] before_compaction: ${sessionKey}`);
    });
    
    api.on("after_compaction", async (event) => {
      const { sessionKey, tokensBefore, tokensAfter } = event;
      // TODO: broadcast context_compacted envelope to SSE clients
      console.log(`[vantage] after_compaction: ${sessionKey} ${tokensBefore}→${tokensAfter}`);
    });
    
    // 6. Initialize proof tracker background service
    store.startProofTracker(api.runtime);
    
    console.log("[vantage] Plugin registered successfully");
  },
};
```

### openclaw.plugin.json

```json
{
  "id": "vantage",
  "name": "Vantage",
  "version": "2.0.0",
  "description": "VantageOC operator control center channel plugin",
  "main": "index.js",
  "engines": {
    "openclaw": ">=1.0.0"
  }
}
```

---

## 4. src/runtime.ts

The runtime singleton provides cross-module access to the OpenClaw runtime without passing it through every function call.

```typescript
import type { OpenClawRuntime } from "openclaw/plugin-sdk";

/**
 * Runtime reference for the Vantage plugin.
 * Provides access to core OpenClaw functionality.
 */
export interface VantageRuntime extends OpenClawRuntime {
  // OpenClawRuntime already includes:
  // - injectInboundMessage(opts: InjectMessageOptions): Promise<void>
  // - sendToChannel(channel: string, payload: unknown): Promise<void>
  // - getSessionState(sessionKey: string): SessionState | undefined
  // - listActiveSessions(): SessionInfo[]
  // - getCronJobs(): CronJob[]
}

let runtimeInstance: VantageRuntime | null = null;

/**
 * Store the runtime instance during plugin registration.
 * Called once from index.ts register().
 */
export function setVantageRuntime(runtime: VantageRuntime): void {
  if (runtimeInstance !== null) {
    console.warn("[vantage] Runtime already set, overwriting");
  }
  runtimeInstance = runtime;
}

/**
 * Get the runtime instance from any module.
 * Throws if called before registration.
 */
export function getVantageRuntime(): VantageRuntime {
  if (runtimeInstance === null) {
    throw new Error("[vantage] Runtime not initialized. Was register() called?");
  }
  return runtimeInstance;
}

/**
 * Check if runtime is available (for conditional logic).
 */
export function hasVantageRuntime(): boolean {
  return runtimeInstance !== null;
}
```

---

## 5. src/types.ts

### Message Types Enum

```typescript
/**
 * All possible outbound message types from the plugin to clients.
 * Each type has a corresponding payload interface.
 */
export type MessageType =
  | "chat"
  | "safety_alert"
  | "task_spawn"
  | "task_update"
  | "task_complete"
  | "task_failed"
  | "proof_receipt"
  | "draft"
  | "report"
  | "heartbeat"
  | "cron_status"
  | "system_event"
  | "context_compacting"
  | "context_compacted"
  | "channel_read"
  | "channel_created";
```

### Account Types

```typescript
/**
 * Resolved Vantage account for SDK operations.
 * Vantage uses a single implicit account (the connected client).
 */
export interface ResolvedVantageAccount {
  id: string;           // Always "default" for Vantage
  enabled: boolean;
  connectedClients: number;
  lastActivity: number; // Unix timestamp ms
}

/**
 * Vantage channel (business context).
 */
export interface VantageChannel {
  slug: string;           // e.g., "barnabas-coaching"
  name: string;           // e.g., "Barnabas Coaching"
  description?: string;
  icon?: string;          // Emoji or icon name
  workspacePath?: string; // Associated workspace directory
  createdAt: number;      // Unix timestamp ms
  unreadCount: number;
}
```

### Outbound Envelope

```typescript
/**
 * Base envelope wrapper for all outbound messages.
 * Clients receive this structure over WebSocket.
 */
export interface OutboundEnvelope<T extends MessageType = MessageType> {
  type: T;
  channel?: string;      // Channel slug if applicable
  sessionKey?: string;   // Session key if applicable
  timestamp: number;     // Unix timestamp ms
  payload: PayloadForType<T>;
}

/**
 * Type mapping from MessageType to payload interface.
 */
export type PayloadForType<T extends MessageType> =
  T extends "chat" ? ChatPayload :
  T extends "safety_alert" ? SafetyAlertPayload :
  T extends "task_spawn" ? TaskSpawnPayload :
  T extends "task_update" ? TaskUpdatePayload :
  T extends "task_complete" ? TaskCompletePayload :
  T extends "task_failed" ? TaskFailedPayload :
  T extends "proof_receipt" ? ProofReceiptPayload :
  T extends "draft" ? DraftPayload :
  T extends "report" ? ReportPayload :
  T extends "heartbeat" ? HeartbeatPayload :
  T extends "cron_status" ? CronStatusPayload :
  T extends "system_event" ? SystemEventPayload :
  T extends "context_compacting" ? ContextCompactingPayload :
  T extends "context_compacted" ? ContextCompactedPayload :
  T extends "channel_read" ? ChannelReadPayload :
  T extends "channel_created" ? ChannelCreatedPayload :
  never;
```

### Payload Interfaces

```typescript
/**
 * Chat message payload (streaming or complete).
 */
export interface ChatPayload {
  messageId: string;
  content: string;
  role: "assistant" | "user" | "system";
  streaming: boolean;
  streamIndex?: number;    // For ordering stream chunks
  streamComplete?: boolean;
  model?: string;
  tokensUsed?: number;
}

/**
 * Safety alert requiring operator approval/denial.
 */
export interface SafetyAlertPayload {
  alertId: string;
  severity: "low" | "medium" | "high" | "critical";
  category: "external_action" | "data_access" | "cost" | "auth" | "routing";
  title: string;
  description: string;
  action: string;           // Human-readable action description
  impact?: string;          // Potential impact
  rollback?: string;        // How to reverse if needed
  expiresAt?: number;       // Auto-deny after this timestamp
  metadata?: Record<string, unknown>;
}

/**
 * Task spawn notification (subagent created).
 */
export interface TaskSpawnPayload {
  taskId: string;
  sessionKey: string;       // Child session key
  parentSessionKey?: string;
  name: string;
  description?: string;
  channel?: string;         // Bound channel slug
  estimatedDuration?: number; // ms
  createdAt: number;
}

/**
 * Task progress update.
 */
export interface TaskUpdatePayload {
  taskId: string;
  sessionKey: string;
  status: "running" | "waiting" | "blocked";
  progress?: number;        // 0-100
  currentStep?: string;
  logs?: string[];          // Recent log lines
}

/**
 * Task completion notification.
 */
export interface TaskCompletePayload {
  taskId: string;
  sessionKey: string;
  result: "success" | "partial";
  summary: string;
  outputs?: string[];       // File paths, URLs, etc.
  duration: number;         // ms
  tokensUsed?: number;
}

/**
 * Task failure notification.
 */
export interface TaskFailedPayload {
  taskId: string;
  sessionKey: string;
  error: string;
  errorCode?: string;
  recoverable: boolean;
  suggestion?: string;      // What user can do
  duration: number;
}

/**
 * Proof of work receipt (task delivered evidence).
 */
export interface ProofReceiptPayload {
  proofId: string;
  taskId: string;
  sessionKey: string;
  proofType: "file" | "screenshot" | "url" | "log" | "artifact";
  title: string;
  description?: string;
  data: string;             // Base64 for binary, URL, or text
  mimeType?: string;
  size?: number;            // bytes
  verified: boolean;
  verifiedAt?: number;
}

/**
 * Draft content for approval.
 */
export interface DraftPayload {
  draftId: string;
  channel?: string;
  draftType: "email" | "tweet" | "post" | "document" | "code" | "other";
  title: string;
  content: string;
  contentHtml?: string;     // Rich content if applicable
  recipient?: string;       // For emails
  platform?: string;        // For social posts
  metadata?: Record<string, unknown>;
  expiresAt?: number;
}

/**
 * Report payload (daily briefings, summaries).
 */
export interface ReportPayload {
  reportId: string;
  reportType: "daily_briefing" | "weekly_summary" | "task_report" | "custom";
  title: string;
  sections: ReportSection[];
  generatedAt: number;
}

export interface ReportSection {
  heading: string;
  content: string;
  priority?: "high" | "medium" | "low";
  items?: ReportItem[];
}

export interface ReportItem {
  text: string;
  status?: "done" | "pending" | "blocked";
  link?: string;
}

/**
 * Heartbeat status notification.
 */
export interface HeartbeatPayload {
  status: "ok" | "degraded" | "error";
  uptime: number;           // ms
  activeSessions: number;
  pendingTasks: number;
  lastCheck: number;
  checks?: HeartbeatCheck[];
}

export interface HeartbeatCheck {
  name: string;
  status: "ok" | "warn" | "error";
  message?: string;
  lastRun?: number;
}

/**
 * Cron job status update.
 */
export interface CronStatusPayload {
  cronId: string;
  name: string;
  schedule: string;         // Cron expression
  status: "scheduled" | "running" | "completed" | "failed" | "disabled";
  lastRun?: number;
  nextRun?: number;
  lastResult?: string;
  lastError?: string;
}

/**
 * System event notification.
 */
export interface SystemEventPayload {
  eventType: "startup" | "shutdown" | "error" | "warning" | "info" | "config_change";
  message: string;
  details?: Record<string, unknown>;
  source?: string;
}

/**
 * Context compaction starting.
 */
export interface ContextCompactingPayload {
  sessionKey: string;
  reason?: string;
}

/**
 * Context compaction completed.
 */
export interface ContextCompactedPayload {
  sessionKey: string;
  tokensBefore: number;
  tokensAfter: number;
  compressionRatio: number;
}

/**
 * Channel marked as read.
 */
export interface ChannelReadPayload {
  channel: string;
  readAt: number;
  messageId?: string;       // Last read message
}

/**
 * New channel created.
 */
export interface ChannelCreatedPayload {
  channel: VantageChannel;
}
```

### Inbound Message Types

```typescript
/**
 * Inbound message from client (chat input).
 */
export interface InboundChatMessage {
  channel: string;
  content: string;
  attachments?: InboundAttachment[];
}

export interface InboundAttachment {
  filename: string;
  mimeType: string;
  data: string;             // Base64
  size: number;
}

/**
 * Parsed channel prefix from agent output.
 * Format: [CHANNEL:slug][TYPE]content
 */
export interface ParsedChannelPrefix {
  channel?: string;         // Extracted channel slug
  type?: MessageType;       // Extracted message type
  content: string;          // Remaining content
  isEnvelope: boolean;      // Was this a JSON envelope?
}
```

### RPC Types

```typescript
/**
 * RPC method parameter interfaces.
 */
export interface VantageMessageParams {
  channel: string;
  content: string;
  attachments?: InboundAttachment[];
}

export interface SafetyApproveParams {
  alertId: string;
  comment?: string;
}

export interface SafetyDenyParams {
  alertId: string;
  reason: string;
}

export interface DraftApproveParams {
  draftId: string;
  modifications?: string;   // Optional edits before sending
}

export interface DraftRejectParams {
  draftId: string;
  reason: string;
}

export interface TaskRegisterParams {
  taskId: string;
  name: string;
  description?: string;
  channel?: string;
  parentSessionKey?: string;
}

export interface TaskCompleteParams {
  taskId: string;
  result: "success" | "partial" | "failed";
  summary: string;
  outputs?: string[];
}

export interface TaskProofParams {
  taskId: string;
  proofType: ProofReceiptPayload["proofType"];
  title: string;
  description?: string;
  data: string;
  mimeType?: string;
}

export interface ChannelCreateParams {
  slug: string;
  name: string;
  description?: string;
  icon?: string;
  workspacePath?: string;
}

export interface ChannelDeleteParams {
  slug: string;
  deleteWorkspace?: boolean;
}

export interface ChannelConfigGetParams {
  slug: string;
  key: string;
}

export interface ChannelConfigSetParams {
  slug: string;
  key: string;
  value: unknown;
}

export interface ChannelHistoryParams {
  slug: string;
  limit?: number;
  before?: string;          // Message ID
  after?: string;           // Message ID
}

export interface ChannelPostParams {
  slug: string;
  content: string;
  type?: MessageType;
  metadata?: Record<string, unknown>;
}

export interface ChannelMarkReadParams {
  slug: string;
  messageId?: string;
}

export interface PollParams {
  channels?: string[];      // Filter by channels
  since?: number;           // Unix timestamp ms
  types?: MessageType[];    // Filter by message types
}

/**
 * RPC response interfaces.
 */
export interface TaskListResponse {
  tasks: TaskInfo[];
}

export interface TaskInfo {
  taskId: string;
  sessionKey: string;
  name: string;
  description?: string;
  channel?: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  createdAt: number;
  completedAt?: number;
}

export interface CronListResponse {
  crons: CronInfo[];
}

export interface CronInfo {
  cronId: string;
  name: string;
  schedule: string;
  enabled: boolean;
  lastRun?: number;
  nextRun?: number;
  lastStatus?: "ok" | "error";
}

export interface HeartbeatStatusResponse {
  status: HeartbeatPayload["status"];
  uptime: number;
  activeSessions: number;
  pendingTasks: number;
  checks: HeartbeatCheck[];
}

export interface ChannelListResponse {
  channels: VantageChannel[];
}

export interface ChannelHistoryResponse {
  messages: StoredMessage[];
  hasMore: boolean;
}

export interface StoredMessage {
  id: string;
  channel: string;
  type: MessageType;
  content: string;
  role: "user" | "assistant" | "system";
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface PollResponse {
  messages: OutboundEnvelope[];
  serverTime: number;
}
```

---

## 6. src/channel.ts — ChannelPlugin Definition

```typescript
import type { ChannelPlugin, ChannelContext, SendTextOptions } from "openclaw/plugin-sdk";
import { z } from "zod";

import type { ResolvedVantageAccount, ParsedChannelPrefix, MessageType, OutboundEnvelope } from "./types.js";
import { getVantageRuntime } from "./runtime.js";
import { VantageStore } from "./store.js";

const store = new VantageStore();

/**
 * Vantage channel configuration schema.
 */
const VantageConfigSchema = z.object({
  defaultChannel: z.string().default("general"),
  streamingEnabled: z.boolean().default(true),
  proofTrackingEnabled: z.boolean().default(true),
});

/**
 * Parse [CHANNEL:slug][TYPE] prefix from agent output.
 */
function parseChannelPrefix(text: string): ParsedChannelPrefix {
  // Try JSON envelope first
  if (text.trim().startsWith("{")) {
    try {
      const envelope = JSON.parse(text) as OutboundEnvelope;
      if (envelope.type && typeof envelope.payload !== "undefined") {
        return {
          channel: envelope.channel,
          type: envelope.type,
          content: JSON.stringify(envelope.payload),
          isEnvelope: true,
        };
      }
    } catch {
      // Not valid JSON, continue to prefix parsing
    }
  }

  // Parse [CHANNEL:slug][TYPE] prefix
  const channelMatch = text.match(/^\[CHANNEL:([^\]]+)\]/);
  const typeMatch = text.match(/^\[CHANNEL:[^\]]+\]\[([A-Z_]+)\]/);
  
  let channel: string | undefined;
  let type: MessageType | undefined;
  let content = text;

  if (channelMatch) {
    channel = channelMatch[1];
    content = content.replace(/^\[CHANNEL:[^\]]+\]/, "");
  }

  if (typeMatch) {
    const typeStr = typeMatch[1].toLowerCase() as MessageType;
    // Validate it's a known type
    const validTypes: MessageType[] = [
      "chat", "safety_alert", "task_spawn", "task_update", "task_complete",
      "task_failed", "proof_receipt", "draft", "report", "heartbeat",
      "cron_status", "system_event", "context_compacting", "context_compacted",
      "channel_read", "channel_created"
    ];
    if (validTypes.includes(typeStr)) {
      type = typeStr;
      content = content.replace(/^\[[A-Z_]+\]/, "");
    }
  }

  return {
    channel,
    type,
    content: content.trim(),
    isEnvelope: false,
  };
}

/**
 * Build outbound envelope from parsed content.
 */
function buildEnvelope(
  parsed: ParsedChannelPrefix,
  defaultChannel: string
): OutboundEnvelope {
  const channel = parsed.channel || defaultChannel;
  const type = parsed.type || "chat";

  if (parsed.isEnvelope) {
    // Already structured, just add metadata
    return {
      type,
      channel,
      timestamp: Date.now(),
      payload: JSON.parse(parsed.content),
    };
  }

  // Build chat envelope for plain text
  return {
    type: "chat",
    channel,
    timestamp: Date.now(),
    payload: {
      messageId: crypto.randomUUID(),
      content: parsed.content,
      role: "assistant",
      streaming: false,
    },
  };
}

/**
 * Vantage ChannelPlugin implementation.
 */
export const vantagePlugin: ChannelPlugin<ResolvedVantageAccount> = {
  id: "vantage",
  
  meta: {
    name: "VantageOC",
    description: "Operator control center for AI agent management",
    icon: "🎛️",
    website: "https://vantage.openclaw.dev",
  },
  
  capabilities: {
    chatTypes: ["direct", "channel"],
    polls: false,
    reactions: false,
    media: true,
    streaming: true,
  },
  
  streaming: {
    blockStreamingCoalesceDefaults: {
      minChars: 500,
      idleMs: 500,
    },
  },
  
  configSchema: VantageConfigSchema,
  
  // ⚠️ IMPLEMENTATION CORRECTION:
  // listAccountIds, resolveAccount, and defaultAccountId MUST be synchronous.
  // The gateway calls them synchronously and iterates the result directly.
  // Returning a Promise causes "accountIds.map is not a function" crash.
  // resolveAccount also receives (cfg, accountId) — cfg is the first argument.
  config: {
    listAccountIds(_cfg?: unknown): string[] {
      // Vantage uses single implicit account
      return ["default"];
    },
    
    resolveAccount(_cfg: unknown, accountId: string): ResolvedVantageAccount | null {
      if (accountId !== "default") return null;
      return {
        id: "default",
        enabled: true,
        connectedClients: store.getConnectedClientCount(),
        lastActivity: store.getLastActivityTimestamp(),
      };
    },
    
    defaultAccountId(_cfg?: unknown): string {
      return "default";
    },
    
    async setAccountEnabled(_accountId: string, enabled: boolean): Promise<void> {
      // Vantage account is always enabled
      if (!enabled) {
        console.warn("[vantage] Cannot disable Vantage account");
      }
    },
    
    async deleteAccount(_accountId: string): Promise<void> {
      // No-op for Vantage
      console.warn("[vantage] Cannot delete Vantage account");
    },
    
    async isConfigured(_account: ResolvedVantageAccount, _cfg?: unknown): Promise<boolean> {
      return true; // Always configured
    },
  },
  
  outbound: {
    deliveryMode: "direct",
    textChunkLimit: 50000, // Large limit for structured envelopes
    
    async sendText(
      ctx: ChannelContext<ResolvedVantageAccount>,
      options: SendTextOptions
    ): Promise<{ messageId: string }> {
      const { text, replyTo } = options;
      const runtime = getVantageRuntime();
      
      // Parse the text for channel/type prefixes or JSON envelope
      const parsed = parseChannelPrefix(text);
      
      // Get default channel from context or config
      const defaultChannel = ctx.to?.split(":")[1] || "general";
      
      // Build the outbound envelope
      const envelope = buildEnvelope(parsed, defaultChannel);
      
      // Store in database
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
      
      // Broadcast to connected Vantage clients
      await runtime.sendToChannel("vantage", {
        ...envelope,
        payload: {
          ...envelope.payload,
          messageId,
        },
      });
      
      return { messageId };
    },
    
    async sendMedia(
      ctx: ChannelContext<ResolvedVantageAccount>,
      options: { url?: string; buffer?: Buffer; filename: string; caption?: string }
    ): Promise<{ messageId: string }> {
      const runtime = getVantageRuntime();
      const channel = ctx.to?.split(":")[1] || "general";
      
      const messageId = crypto.randomUUID();
      const envelope: OutboundEnvelope = {
        type: "chat",
        channel,
        timestamp: Date.now(),
        payload: {
          messageId,
          content: options.caption || "",
          role: "assistant",
          streaming: false,
          attachment: {
            filename: options.filename,
            url: options.url,
            // Buffer would be base64 encoded in real implementation
          },
        },
      };
      
      await store.storeMessage({
        channel,
        type: "chat",
        content: options.caption || `[Attachment: ${options.filename}]`,
        role: "assistant",
        timestamp: envelope.timestamp,
        metadata: { attachment: options.filename },
      });
      
      await runtime.sendToChannel("vantage", envelope);
      
      return { messageId };
    },
  },
  
  status: {
    async probeAccount(account: ResolvedVantageAccount): Promise<{ ok: boolean; error?: string }> {
      return { ok: account.enabled };
    },
    
    async auditAccount(account: ResolvedVantageAccount): Promise<{ warnings: string[] }> {
      const warnings: string[] = [];
      if (account.connectedClients === 0) {
        warnings.push("No VantageOC clients connected");
      }
      return { warnings };
    },
    
    async buildChannelSummary(): Promise<string> {
      const channels = await store.listChannels();
      const clients = store.getConnectedClientCount();
      return `VantageOC: ${channels.length} channels, ${clients} connected clients`;
    },
  },
  
  gateway: {
    /**
     * Called when account should start monitoring.
     * Vantage doesn't need external polling, but we use this
     * to initialize any background services.
     */
    // ⚠️ IMPLEMENTATION CORRECTION:
    // startAccount MUST block indefinitely for push-based channels.
    // If it returns immediately, the gateway marks the account as "stopped"
    // and enters an exponential-backoff crash-loop (auto-restart attempt N/10).
    // Return a never-resolving promise. The gateway cancels it on restart/shutdown.
    async startAccount(_ctx: ChannelContext<ResolvedVantageAccount>): Promise<void> {
      console.log("[vantage] Gateway startAccount: channel running (push-based, blocking indefinitely)");
      // Block forever — gateway cancels this on restart/shutdown.
      return new Promise<void>(() => { /* intentionally never resolves */ });
    },
  },
};

/**
 * Handle inbound message from VantageOC client.
 * Called from RPC handler.
 *
 * ⚠️ IMPLEMENTATION CORRECTION:
 * The original spec called for api.runtime.injectInboundMessage() here.
 * That method does NOT exist in the OpenClaw Plugin SDK.
 * The actual implementation uses the V1 WebSocket loopback pattern (loopback.ts):
 * self-connect to the gateway and call chat.send RPC.
 *
 * V1: loopbackChatSend (self-connecting WebSocket to gateway → chat.send)
 * V2: Same pattern, extracted into loopback.ts as injectChatMessage()
 */
export async function handleInboundMessage(
  channel: string,
  content: string,
  attachments?: Array<{ filename: string; data: string; mimeType: string }>
): Promise<void> {
  // Store the inbound message
  await store.storeMessage({
    channel,
    type: "chat",
    content,
    role: "user",
    timestamp: Date.now(),
  });

  // Inject into agent session via gateway loopback (SDK has no direct injection API)
  const { injectChatMessage } = await import("./loopback.js");
  await injectChatMessage(content, `agent:${channel}:main`, attachments);
}
```

---

## 7. src/subagent-hooks.ts

```typescript
import type { OpenClawPluginApi, SubagentSpawningEvent, SubagentEndedEvent, SubagentDeliveryTargetEvent } from "openclaw/plugin-sdk";

/**
 * Module-scoped map for subagent channel bindings.
 * 
 * WHY MODULE SCOPE (not SQLite):
 * - Subagent bindings are ephemeral (live only while subagent runs)
 * - Writing to SQLite for every spawn/end adds latency
 * - No need for persistence across gateway restarts
 * - Memory footprint is minimal (typically <100 active bindings)
 * - Simplifies cleanup (process exit clears all)
 */
const subagentBindings = new Map<string, SubagentBinding>();

interface SubagentBinding {
  childSessionKey: string;
  parentSessionKey: string;
  channelSlug: string;
  taskId?: string;
  boundAt: number;
}

/**
 * Register Vantage-specific subagent lifecycle hooks.
 */
export function registerVantageSubagentHooks(api: OpenClawPluginApi): void {
  
  /**
   * Hook: subagent_spawning
   * Called when a subagent is about to be created.
   * We bind it to the originating Vantage channel.
   */
  api.on("subagent_spawning", async (event: SubagentSpawningEvent) => {
    // Only handle requests originating from Vantage channel
    if (event.requester?.channel !== "vantage") {
      return;
    }
    
    // Extract channel slug from the requester's target
    // Format: "channel:barnabas-coaching" or just the slug
    const channelSlug = extractChannelSlug(event.requester.to);
    if (!channelSlug) {
      console.warn("[vantage] Could not extract channel slug from requester.to:", event.requester.to);
      return;
    }
    
    // Store the binding
    const binding: SubagentBinding = {
      childSessionKey: event.childSessionKey,
      parentSessionKey: event.parentSessionKey,
      channelSlug,
      taskId: event.metadata?.taskId as string | undefined,
      boundAt: Date.now(),
    };
    
    subagentBindings.set(event.childSessionKey, binding);
    
    console.log(`[vantage] Bound subagent ${event.childSessionKey} to channel ${channelSlug}`);
    
    // Notify Vantage clients about the new task
    await api.runtime.sendToChannel("vantage", {
      type: "task_spawn",
      channel: channelSlug,
      sessionKey: event.childSessionKey,
      timestamp: Date.now(),
      payload: {
        taskId: binding.taskId || event.childSessionKey,
        sessionKey: event.childSessionKey,
        parentSessionKey: event.parentSessionKey,
        name: event.metadata?.name as string || "Subagent task",
        description: event.metadata?.description as string,
        channel: channelSlug,
        createdAt: binding.boundAt,
      },
    });
    
    return {
      status: "ok",
      threadBindingReady: true,
    };
  });
  
  /**
   * Hook: subagent_ended
   * Called when a subagent completes or fails.
   * We clean up the binding.
   */
  api.on("subagent_ended", async (event: SubagentEndedEvent) => {
    const binding = subagentBindings.get(event.childSessionKey);
    if (!binding) {
      return; // Not a Vantage-bound subagent
    }
    
    // Remove the binding
    subagentBindings.delete(event.childSessionKey);
    
    console.log(`[vantage] Unbound subagent ${event.childSessionKey} from channel ${binding.channelSlug}`);
    
    // Determine completion type
    const isSuccess = event.status === "completed";
    const eventType = isSuccess ? "task_complete" : "task_failed";
    
    // Notify Vantage clients
    if (isSuccess) {
      await api.runtime.sendToChannel("vantage", {
        type: "task_complete",
        channel: binding.channelSlug,
        sessionKey: event.childSessionKey,
        timestamp: Date.now(),
        payload: {
          taskId: binding.taskId || event.childSessionKey,
          sessionKey: event.childSessionKey,
          result: "success",
          summary: event.result?.summary || "Task completed",
          outputs: event.result?.outputs,
          duration: Date.now() - binding.boundAt,
          tokensUsed: event.result?.tokensUsed,
        },
      });
    } else {
      await api.runtime.sendToChannel("vantage", {
        type: "task_failed",
        channel: binding.channelSlug,
        sessionKey: event.childSessionKey,
        timestamp: Date.now(),
        payload: {
          taskId: binding.taskId || event.childSessionKey,
          sessionKey: event.childSessionKey,
          error: event.error?.message || "Unknown error",
          errorCode: event.error?.code,
          recoverable: event.error?.recoverable || false,
          suggestion: event.error?.suggestion,
          duration: Date.now() - binding.boundAt,
        },
      });
    }
  });
  
  /**
   * Hook: subagent_delivery_target
   * Called when the SDK needs to know where to deliver subagent output.
   * We return the bound Vantage channel.
   */
  api.on("subagent_delivery_target", (event: SubagentDeliveryTargetEvent) => {
    const binding = subagentBindings.get(event.childSessionKey);
    if (!binding) {
      return; // Not a Vantage-bound subagent, let SDK use default
    }
    
    // Return the Vantage channel as the delivery target
    return {
      origin: {
        channel: "vantage",
        to: `channel:${binding.channelSlug}`,
      },
    };
  });
}

/**
 * Extract channel slug from various target formats.
 */
function extractChannelSlug(to: string | undefined): string | undefined {
  if (!to) return undefined;
  
  // Format: "channel:barnabas-coaching"
  if (to.startsWith("channel:")) {
    return to.substring(8);
  }
  
  // Just the slug
  if (!to.includes(":")) {
    return to;
  }
  
  return undefined;
}

/**
 * Get binding for a session key (for external queries).
 */
export function getSubagentBinding(sessionKey: string): SubagentBinding | undefined {
  return subagentBindings.get(sessionKey);
}

/**
 * List all active bindings (for debugging/monitoring).
 */
export function listActiveBindings(): SubagentBinding[] {
  return Array.from(subagentBindings.values());
}

/**
 * Clear bindings for a specific channel (e.g., when channel is deleted).
 */
export function clearBindingsForChannel(channelSlug: string): number {
  let cleared = 0;
  for (const [key, binding] of subagentBindings) {
    if (binding.channelSlug === channelSlug) {
      subagentBindings.delete(key);
      cleared++;
    }
  }
  return cleared;
}
```

---

## 8. src/rpc.ts

```typescript
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

import type {
  VantageMessageParams,
  SafetyApproveParams,
  SafetyDenyParams,
  DraftApproveParams,
  DraftRejectParams,
  TaskRegisterParams,
  TaskCompleteParams,
  TaskProofParams,
  ChannelCreateParams,
  ChannelDeleteParams,
  ChannelConfigGetParams,
  ChannelConfigSetParams,
  ChannelHistoryParams,
  ChannelPostParams,
  ChannelMarkReadParams,
  PollParams,
  TaskListResponse,
  CronListResponse,
  HeartbeatStatusResponse,
  ChannelListResponse,
  ChannelHistoryResponse,
  PollResponse,
  VantageChannel,
} from "./types.js";
import { VantageStore } from "./store.js";
import { handleInboundMessage } from "./channel.js";
import { clearBindingsForChannel, listActiveBindings } from "./subagent-hooks.js";

/**
 * Register all Vantage RPC methods.
 * 
 * MIGRATION NOTES:
 * - loopbackChatSend preserved as injectChatMessage() in loopback.ts (SDK has no injection API)
 * - All `sessions.json` writes replaced with SDK session management
 * - Response shapes unchanged for client compatibility
 */
export function registerVantageRpcMethods(
  api: OpenClawPluginApi,
  store: VantageStore
): void {
  
  // ============================================================
  // MESSAGING
  // ============================================================
  
  /**
   * vantage.message
   * Send a message from the operator to the agent.
   * 
   * V1: Used loopbackChatSend (self-connecting WebSocket)
   * V2: Uses loopback.ts injectChatMessage() — same pattern, cleaner abstraction.
   *     api.runtime.injectInboundMessage does NOT exist in the SDK.
   */
  api.registerRpcMethod("vantage.message", async (params: VantageMessageParams) => {
    const { channel, content, attachments } = params;
    
    // Validate channel exists
    const channelInfo = await store.getChannel(channel);
    if (!channelInfo) {
      throw { code: -32602, message: `Channel not found: ${channel}` };
    }
    
    // Inject via WebSocket loopback (SDK has no direct injection API)
    await handleInboundMessage(channel, content, attachments);
    
    return { success: true, channel, timestamp: Date.now() };
  });
  
  // ============================================================
  // SAFETY ALERTS
  // ============================================================
  
  /**
   * vantage.safety.approve
   * Approve a pending safety alert.
   */
  api.registerRpcMethod("vantage.safety.approve", async (params: SafetyApproveParams) => {
    const { alertId, comment } = params;
    
    const alert = await store.getSafetyAlert(alertId);
    if (!alert) {
      throw { code: -32602, message: `Alert not found: ${alertId}` };
    }
    
    if (alert.status !== "pending") {
      throw { code: -32602, message: `Alert already resolved: ${alert.status}` };
    }
    
    // Update alert status
    await store.updateSafetyAlert(alertId, {
      status: "approved",
      resolvedAt: Date.now(),
      resolvedBy: "operator",
      comment,
    });
    
    // Resume the blocked session
    // V2: Use SDK session control
    await api.runtime.resumeBlockedSession(alert.sessionKey, {
      decision: "approved",
      comment,
    });
    
    // Notify clients
    await api.runtime.sendToChannel("vantage", {
      type: "system_event",
      timestamp: Date.now(),
      payload: {
        eventType: "info",
        message: `Safety alert approved: ${alert.title}`,
        details: { alertId, comment },
      },
    });
    
    return { success: true, alertId };
  });
  
  /**
   * vantage.safety.deny
   * Deny a pending safety alert.
   */
  api.registerRpcMethod("vantage.safety.deny", async (params: SafetyDenyParams) => {
    const { alertId, reason } = params;
    
    const alert = await store.getSafetyAlert(alertId);
    if (!alert) {
      throw { code: -32602, message: `Alert not found: ${alertId}` };
    }
    
    if (alert.status !== "pending") {
      throw { code: -32602, message: `Alert already resolved: ${alert.status}` };
    }
    
    // Update alert status
    await store.updateSafetyAlert(alertId, {
      status: "denied",
      resolvedAt: Date.now(),
      resolvedBy: "operator",
      reason,
    });
    
    // Abort the blocked session
    await api.runtime.resumeBlockedSession(alert.sessionKey, {
      decision: "denied",
      reason,
    });
    
    // Notify clients
    await api.runtime.sendToChannel("vantage", {
      type: "system_event",
      timestamp: Date.now(),
      payload: {
        eventType: "warning",
        message: `Safety alert denied: ${alert.title}`,
        details: { alertId, reason },
      },
    });
    
    return { success: true, alertId };
  });
  
  // ============================================================
  // DRAFT APPROVAL
  // ============================================================
  
  /**
   * vantage.draft.approve
   * Approve a draft for sending/publishing.
   */
  api.registerRpcMethod("vantage.draft.approve", async (params: DraftApproveParams) => {
    const { draftId, modifications } = params;
    
    const draft = await store.getDraft(draftId);
    if (!draft) {
      throw { code: -32602, message: `Draft not found: ${draftId}` };
    }
    
    if (draft.status !== "pending") {
      throw { code: -32602, message: `Draft already resolved: ${draft.status}` };
    }
    
    // Apply modifications if provided
    const finalContent = modifications || draft.content;
    
    // Update draft status
    await store.updateDraft(draftId, {
      status: "approved",
      finalContent,
      resolvedAt: Date.now(),
    });
    
    // Resume the blocked session with approval
    await api.runtime.resumeBlockedSession(draft.sessionKey, {
      decision: "approved",
      content: finalContent,
    });
    
    return { success: true, draftId };
  });
  
  /**
   * vantage.draft.reject
   * Reject a draft.
   */
  api.registerRpcMethod("vantage.draft.reject", async (params: DraftRejectParams) => {
    const { draftId, reason } = params;
    
    const draft = await store.getDraft(draftId);
    if (!draft) {
      throw { code: -32602, message: `Draft not found: ${draftId}` };
    }
    
    if (draft.status !== "pending") {
      throw { code: -32602, message: `Draft already resolved: ${draft.status}` };
    }
    
    // Update draft status
    await store.updateDraft(draftId, {
      status: "rejected",
      reason,
      resolvedAt: Date.now(),
    });
    
    // Resume the blocked session with rejection
    await api.runtime.resumeBlockedSession(draft.sessionKey, {
      decision: "rejected",
      reason,
    });
    
    return { success: true, draftId };
  });
  
  // ============================================================
  // TASK MANAGEMENT
  // ============================================================
  
  /**
   * vantage.task.register
   * Register a new task (usually from subagent spawn).
   */
  api.registerRpcMethod("vantage.task.register", async (params: TaskRegisterParams) => {
    const { taskId, name, description, channel, parentSessionKey } = params;
    
    await store.createTask({
      taskId,
      name,
      description,
      channel,
      parentSessionKey,
      status: "pending",
      createdAt: Date.now(),
    });
    
    return { success: true, taskId };
  });
  
  /**
   * vantage.task.complete
   * Mark a task as completed.
   */
  api.registerRpcMethod("vantage.task.complete", async (params: TaskCompleteParams) => {
    const { taskId, result, summary, outputs } = params;
    
    await store.updateTask(taskId, {
      status: result === "failed" ? "failed" : "completed",
      result,
      summary,
      outputs,
      completedAt: Date.now(),
    });
    
    return { success: true, taskId };
  });
  
  /**
   * vantage.task.proof
   * Submit proof of work for a task.
   */
  api.registerRpcMethod("vantage.task.proof", async (params: TaskProofParams) => {
    const { taskId, proofType, title, description, data, mimeType } = params;
    
    const proofId = crypto.randomUUID();
    
    await store.createProof({
      proofId,
      taskId,
      proofType,
      title,
      description,
      data,
      mimeType,
      verified: false,
      createdAt: Date.now(),
    });
    
    // Notify clients
    const task = await store.getTask(taskId);
    await api.runtime.sendToChannel("vantage", {
      type: "proof_receipt",
      channel: task?.channel,
      sessionKey: task?.sessionKey,
      timestamp: Date.now(),
      payload: {
        proofId,
        taskId,
        sessionKey: task?.sessionKey || "",
        proofType,
        title,
        description,
        data,
        mimeType,
        size: data.length,
        verified: false,
      },
    });
    
    return { success: true, proofId, taskId };
  });
  
  /**
   * vantage.tasks.list
   * List all tasks with optional filtering.
   */
  api.registerRpcMethod("vantage.tasks.list", async (params?: { channel?: string; status?: string }): Promise<TaskListResponse> => {
    const tasks = await store.listTasks(params);
    
    // Merge with active subagent bindings for live status
    const bindings = listActiveBindings();
    const bindingMap = new Map(bindings.map(b => [b.taskId || b.childSessionKey, b]));
    
    const enrichedTasks = tasks.map(task => ({
      ...task,
      isLive: bindingMap.has(task.taskId),
    }));
    
    return { tasks: enrichedTasks };
  });
  
  // ============================================================
  // CRON JOBS
  // ============================================================
  
  /**
   * vantage.crons.list
   * List all cron jobs.
   */
  api.registerRpcMethod("vantage.crons.list", async (): Promise<CronListResponse> => {
    const crons = await api.runtime.getCronJobs();
    
    return {
      crons: crons.map(c => ({
        cronId: c.id,
        name: c.name,
        schedule: c.schedule,
        enabled: c.enabled,
        lastRun: c.lastRun,
        nextRun: c.nextRun,
        lastStatus: c.lastStatus,
      })),
    };
  });
  
  // ============================================================
  // HEARTBEAT
  // ============================================================
  
  /**
   * vantage.heartbeat.status
   * Get current heartbeat status.
   */
  api.registerRpcMethod("vantage.heartbeat.status", async (): Promise<HeartbeatStatusResponse> => {
    const sessions = await api.runtime.listActiveSessions();
    const bindings = listActiveBindings();
    
    return {
      status: "ok",
      uptime: process.uptime() * 1000,
      activeSessions: sessions.length,
      pendingTasks: bindings.length,
      checks: [
        {
          name: "database",
          status: store.isHealthy() ? "ok" : "error",
          lastRun: Date.now(),
        },
        {
          name: "sessions",
          status: sessions.length > 0 ? "ok" : "warn",
          message: `${sessions.length} active sessions`,
        },
      ],
    };
  });
  
  // ============================================================
  // POLLING
  // ============================================================
  
  /**
   * vantage.poll
   * Poll for new messages (for clients that don't support push).
   */
  api.registerRpcMethod("vantage.poll", async (params?: PollParams): Promise<PollResponse> => {
    const { channels, since, types } = params || {};
    
    const messages = await store.getMessagesSince(since || 0, {
      channels,
      types,
      limit: 100,
    });
    
    return {
      messages,
      serverTime: Date.now(),
    };
  });
  
  // ============================================================
  // CHANNELS
  // ============================================================
  
  /**
   * vantage.channels.list
   * List all channels.
   */
  api.registerRpcMethod("vantage.channels.list", async (): Promise<ChannelListResponse> => {
    const channels = await store.listChannels();
    return { channels };
  });
  
  /**
   * vantage.channels.history
   * Get message history for a channel.
   */
  api.registerRpcMethod("vantage.channels.history", async (params: ChannelHistoryParams): Promise<ChannelHistoryResponse> => {
    const { slug, limit = 50, before, after } = params;
    
    const messages = await store.getChannelHistory(slug, { limit, before, after });
    const hasMore = messages.length === limit;
    
    return { messages, hasMore };
  });
  
  /**
   * vantage.channels.post
   * Post a message to a channel (internal, not from user).
   */
  api.registerRpcMethod("vantage.channels.post", async (params: ChannelPostParams) => {
    const { slug, content, type = "chat", metadata } = params;
    
    const messageId = await store.storeMessage({
      channel: slug,
      type,
      content,
      role: "system",
      timestamp: Date.now(),
      metadata,
    });
    
    // Broadcast to clients
    await api.runtime.sendToChannel("vantage", {
      type,
      channel: slug,
      timestamp: Date.now(),
      payload: {
        messageId,
        content,
        role: "system",
        streaming: false,
      },
    });
    
    return { success: true, messageId };
  });
  
  /**
   * vantage.channels.mark_read
   * Mark a channel as read.
   */
  api.registerRpcMethod("vantage.channels.mark_read", async (params: ChannelMarkReadParams) => {
    const { slug, messageId } = params;
    
    await store.markChannelRead(slug, messageId);
    
    // Notify clients
    await api.runtime.sendToChannel("vantage", {
      type: "channel_read",
      channel: slug,
      timestamp: Date.now(),
      payload: {
        channel: slug,
        readAt: Date.now(),
        messageId,
      },
    });
    
    return { success: true };
  });
  
  /**
   * vantage.channels.create
   * Create a new channel with optional workspace provisioning.
   */
  api.registerRpcMethod("vantage.channels.create", async (params: ChannelCreateParams) => {
    const { slug, name, description, icon, workspacePath } = params;
    
    // Check if channel already exists
    const existing = await store.getChannel(slug);
    if (existing) {
      throw { code: -32602, message: `Channel already exists: ${slug}` };
    }
    
    // Create the channel
    const channel: VantageChannel = {
      slug,
      name,
      description,
      icon,
      workspacePath,
      createdAt: Date.now(),
      unreadCount: 0,
    };
    
    await store.createChannel(channel);
    
    // Provision workspace directory if specified
    if (workspacePath) {
      const fs = await import("fs/promises");
      await fs.mkdir(workspacePath, { recursive: true });
    }
    
    // Notify clients
    await api.runtime.sendToChannel("vantage", {
      type: "channel_created",
      timestamp: Date.now(),
      payload: { channel },
    });
    
    return { success: true, channel };
  });
  
  /**
   * vantage.channels.delete
   * Delete a channel and optionally its workspace.
   */
  api.registerRpcMethod("vantage.channels.delete", async (params: ChannelDeleteParams) => {
    const { slug, deleteWorkspace = false } = params;
    
    const channel = await store.getChannel(slug);
    if (!channel) {
      throw { code: -32602, message: `Channel not found: ${slug}` };
    }
    
    // Clear any subagent bindings for this channel
    clearBindingsForChannel(slug);
    
    // Delete workspace if requested
    if (deleteWorkspace && channel.workspacePath) {
      const fs = await import("fs/promises");
      await fs.rm(channel.workspacePath, { recursive: true, force: true });
    }
    
    // Delete channel and its messages
    await store.deleteChannel(slug);
    
    // Notify clients
    await api.runtime.sendToChannel("vantage", {
      type: "system_event",
      timestamp: Date.now(),
      payload: {
        eventType: "config_change",
        message: `Channel deleted: ${slug}`,
        details: { slug, workspaceDeleted: deleteWorkspace },
      },
    });
    
    return { success: true };
  });
  
  /**
   * vantage.channels.config.get
   * Get channel configuration value.
   */
  api.registerRpcMethod("vantage.channels.config.get", async (params: ChannelConfigGetParams) => {
    const { slug, key } = params;
    const value = await store.getChannelConfig(slug, key);
    return { key, value };
  });
  
  /**
   * vantage.channels.config.set
   * Set channel configuration value.
   */
  api.registerRpcMethod("vantage.channels.config.set", async (params: ChannelConfigSetParams) => {
    const { slug, key, value } = params;
    await store.setChannelConfig(slug, key, value);
    return { success: true, key, value };
  });
}
```

---

## 9. Client Side Changes

### 9.1 What Changes

| Change | Impact | Client Action Required |
|--------|--------|------------------------|
| Subagent replies route to originating channel | Low | None, already renders by channel |
| New envelope types: `context_compacting`, `context_compacted` | Medium | Add handlers for these types |
| Connection state machine formalized | Low | Implement state enum if not present |
| Streaming coalesce parameters changed | None | Server-side only |

### 9.2 Connection State Machine

```
┌─────────────┐
│ Disconnected│
└──────┬──────┘
       │ connect()
       ▼
┌─────────────┐
│ Connecting  │◄──────────────────────┐
└──────┬──────┘                       │
       │ onopen                       │ retry (exponential backoff)
       ▼                              │
┌─────────────┐                       │
│  Connected  │                       │
└──────┬──────┘                       │
       │ onclose/onerror              │
       ▼                              │
┌─────────────┐                       │
│Reconnecting ├───────────────────────┘
└──────┬──────┘
       │ max retries exceeded
       ▼
┌─────────────┐
│   Failed    │
└─────────────┘
```

**Swift Implementation:**

```swift
enum ConnectionState {
    case disconnected
    case connecting
    case connected
    case reconnecting(attempt: Int, maxAttempts: Int)
    case failed(error: Error)
}
```

### 9.3 Envelope Rendering Table

| Type | Render Target | SwiftUI Component | Interactive Actions | RPC Methods |
|------|---------------|-------------------|---------------------|-------------|
| `chat` | Channel message list | `ChatMessageView` | Copy, React | None |
| `safety_alert` | Alert banner + modal | `SafetyAlertView` | Approve, Deny | `vantage.safety.approve`, `vantage.safety.deny` |
| `task_spawn` | Task list | `TaskRowView` | Expand details | None |
| `task_update` | Task list (update row) | `TaskRowView` | View logs | None |
| `task_complete` | Task list (update row) | `TaskRowView` | View outputs, proofs | None |
| `task_failed` | Task list (update row) + toast | `TaskRowView` | Retry suggestion | None |
| `proof_receipt` | Task detail sheet | `ProofItemView` | Preview, Download | None |
| `draft` | Draft approval modal | `DraftApprovalView` | Approve, Edit, Reject | `vantage.draft.approve`, `vantage.draft.reject` |
| `report` | Channel message list | `ReportView` | Expand sections | None |
| `heartbeat` | Dashboard status | `HeartbeatIndicator` | None | None |
| `cron_status` | Cron jobs list | `CronRowView` | Toggle enable | None |
| `system_event` | Toast notification | `SystemToast` | Dismiss | None |
| `context_compacting` | Status indicator | `CompactionIndicator` | None | None |
| `context_compacted` | Toast + status | `CompactionIndicator` | None | None |
| `channel_read` | Channel list (clear badge) | N/A | None | None |
| `channel_created` | Channel list (add item) | N/A | None | None |

### 9.4 Safety Alert End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SAFETY ALERT FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

1. TRIGGER
   ┌─────────┐     ┌─────────┐     ┌─────────────┐
   │  Agent  │────▶│ Gateway │────▶│   Plugin    │
   │ Action  │     │  Check  │     │ Block+Store │
   └─────────┘     └─────────┘     └──────┬──────┘
                                          │
2. NOTIFICATION                           ▼
   ┌─────────────┐     ┌────────────────────────┐
   │   Plugin    │────▶│  VantageOC Client(s)   │
   │ sendToChannel     │  (WebSocket push)      │
   └─────────────┘     └───────────┬────────────┘
                                   │
3. DISPLAY                         ▼
   ┌──────────────────────────────────────────┐
   │  SafetyAlertView (modal)                 │
   │  ┌─────────────────────────────────────┐ │
   │  │ ⚠️ HIGH SEVERITY                    │ │
   │  │ Action: Send email to client        │ │
   │  │ Impact: External communication      │ │
   │  │                                     │ │
   │  │ [Deny with reason]  [Approve]       │ │
   │  └─────────────────────────────────────┘ │
   └───────────────────────────┬──────────────┘
                               │
4a. APPROVE                    ▼ User taps Approve
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Client    │────▶│   Plugin    │────▶│   Agent     │
   │ RPC call    │     │ Update DB   │     │   Resume    │
   │ .approve()  │     │ Resume sess │     │             │
   └─────────────┘     └─────────────┘     └─────────────┘
   
4b. DENY                       ▼ User taps Deny
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Client    │────▶│   Plugin    │────▶│   Agent     │
   │ RPC call    │     │ Update DB   │     │   Abort     │
   │ .deny()     │     │ Abort sess  │     │   Action    │
   └─────────────┘     └─────────────┘     └─────────────┘

ERROR STATES:
- Alert expired (expiresAt passed): Auto-deny, show "Alert expired" toast
- RPC failure: Show error toast, keep modal open, retry button
- Session already ended: Show "Session ended" toast, dismiss modal
- Duplicate resolution: Show "Already resolved" toast, dismiss modal
```

### 9.5 Draft Approval End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        DRAFT APPROVAL FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

1. DRAFT CREATED
   ┌─────────┐     ┌─────────────┐     ┌─────────────┐
   │  Agent  │────▶│   Plugin    │────▶│  Store DB   │
   │ Creates │     │ Parse draft │     │ status=pend │
   │ Draft   │     │ envelope    │     │             │
   └─────────┘     └──────┬──────┘     └─────────────┘
                          │
2. PUSH TO CLIENT         ▼
   ┌─────────────┐     ┌─────────────┐
   │   Plugin    │────▶│   Client    │
   │ sendToChannel     │ Show modal  │
   └─────────────┘     └──────┬──────┘
                              │
3. USER REVIEW               ▼
   ┌──────────────────────────────────────────┐
   │  DraftApprovalView (sheet)               │
   │  ┌─────────────────────────────────────┐ │
   │  │ 📧 Email Draft                      │ │
   │  │ To: client@example.com              │ │
   │  │                                     │ │
   │  │ Subject: Project Update             │ │
   │  │ ─────────────────────────────────── │ │
   │  │ Hi John,                            │ │
   │  │                                     │ │
   │  │ Here's the weekly update...         │ │
   │  │ [editable text area]                │ │
   │  │                                     │ │
   │  │ [Reject]  [Edit & Approve] [Approve]│ │
   │  └─────────────────────────────────────┘ │
   └───────────────────────────┬──────────────┘
                               │
4a. APPROVE (with optional edits)
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Client    │────▶│   Plugin    │────▶│   Agent     │
   │ .approve({  │     │ Store final │     │ Send email  │
   │  mods: ... }│     │ Resume sess │     │ (modified)  │
   └─────────────┘     └─────────────┘     └─────────────┘
   
4b. REJECT
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Client    │────▶│   Plugin    │────▶│   Agent     │
   │ .reject({   │     │ Update DB   │     │ Abort send  │
   │  reason:... }     │ Resume sess │     │ Tell user   │
   └─────────────┘     └─────────────┘     └─────────────┘

DRAFT TYPES:
- email: Shows recipient, subject, body
- tweet/post: Shows platform, content, media preview
- document: Shows title, content preview, file type
- code: Shows language, filename, syntax-highlighted diff
```

### 9.6 Channel Message Rendering

Each message type renders differently within the channel message list:

```swift
// Message type to view mapping
func viewForMessage(_ message: StoredMessage) -> some View {
    switch message.type {
    case .chat:
        ChatBubbleView(message: message)
            // Standard chat bubble with avatar, content, timestamp
            
    case .draft:
        DraftCardView(message: message)
            // Card with type icon, title, preview
            // "View Draft" button opens DraftApprovalView
            
    case .report:
        ReportCardView(message: message)
            // Collapsible sections
            // Priority indicators on items
            
    case .safety_alert:
        AlertBannerView(message: message)
            // Red/orange/yellow banner based on severity
            // Inline Approve/Deny if still pending
            
    case .system_event:
        SystemEventView(message: message)
            // Small, centered, muted text
            // Icon based on eventType
            
    case .task_spawn, .task_update, .task_complete, .task_failed:
        TaskEventView(message: message)
            // Compact task status card
            // Links to Tasks tab for details
            
    case .proof_receipt:
        ProofCardView(message: message)
            // Thumbnail if image, icon if file
            // "View Proof" opens detail sheet
            
    default:
        // Fallback to plain text
        Text(message.content)
    }
}
```

---

## 10. SQLite Schema

### 10.1 Server-Side Schema (Plugin DB)

Location: `~/.openclaw/vantage-plugin.db`

```sql
-- ============================================================
-- CHANNELS
-- ============================================================
CREATE TABLE IF NOT EXISTS channels (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    workspace_path TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX idx_channels_created_at ON channels(created_at);

-- ============================================================
-- CHANNEL CONFIG (key-value per channel)
-- ============================================================
CREATE TABLE IF NOT EXISTS channel_config (
    channel_slug TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT, -- JSON encoded
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (channel_slug, key),
    FOREIGN KEY (channel_slug) REFERENCES channels(slug) ON DELETE CASCADE
);

-- ============================================================
-- MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    timestamp INTEGER NOT NULL,
    metadata TEXT, -- JSON encoded
    FOREIGN KEY (channel) REFERENCES channels(slug) ON DELETE CASCADE
);

CREATE INDEX idx_messages_channel_timestamp ON messages(channel, timestamp DESC);
CREATE INDEX idx_messages_type ON messages(type);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);

-- ============================================================
-- READ MARKERS (per channel, tracks last read message)
-- ============================================================
CREATE TABLE IF NOT EXISTS read_markers (
    channel_slug TEXT PRIMARY KEY,
    last_read_message_id TEXT,
    read_at INTEGER NOT NULL,
    FOREIGN KEY (channel_slug) REFERENCES channels(slug) ON DELETE CASCADE
);

-- ============================================================
-- SAFETY ALERTS
-- ============================================================
CREATE TABLE IF NOT EXISTS safety_alerts (
    alert_id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    channel TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    action TEXT NOT NULL,
    impact TEXT,
    rollback TEXT,
    expires_at INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied', 'expired')),
    resolved_at INTEGER,
    resolved_by TEXT,
    comment TEXT,
    reason TEXT,
    created_at INTEGER NOT NULL,
    metadata TEXT -- JSON encoded
);

CREATE INDEX idx_safety_alerts_status ON safety_alerts(status);
CREATE INDEX idx_safety_alerts_session ON safety_alerts(session_key);
CREATE INDEX idx_safety_alerts_created ON safety_alerts(created_at DESC);

-- ============================================================
-- DRAFTS
-- ============================================================
CREATE TABLE IF NOT EXISTS drafts (
    draft_id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    channel TEXT,
    draft_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT,
    recipient TEXT,
    platform TEXT,
    expires_at INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    final_content TEXT,
    resolved_at INTEGER,
    reason TEXT,
    created_at INTEGER NOT NULL,
    metadata TEXT -- JSON encoded
);

CREATE INDEX idx_drafts_status ON drafts(status);
CREATE INDEX idx_drafts_session ON drafts(session_key);
CREATE INDEX idx_drafts_created ON drafts(created_at DESC);

-- ============================================================
-- TASKS
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    session_key TEXT,
    parent_session_key TEXT,
    channel TEXT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER,
    result TEXT,
    summary TEXT,
    outputs TEXT, -- JSON array
    created_at INTEGER NOT NULL,
    completed_at INTEGER,
    metadata TEXT -- JSON encoded
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_channel ON tasks(channel);
CREATE INDEX idx_tasks_session ON tasks(session_key);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);

-- ============================================================
-- PROOFS
-- ============================================================
CREATE TABLE IF NOT EXISTS proofs (
    proof_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    proof_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    data TEXT NOT NULL, -- Base64 or URL
    mime_type TEXT,
    size INTEGER,
    verified INTEGER NOT NULL DEFAULT 0,
    verified_at INTEGER,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX idx_proofs_task ON proofs(task_id);
CREATE INDEX idx_proofs_created ON proofs(created_at DESC);

-- ============================================================
-- CLIENT CONNECTIONS (for tracking connected clients)
-- ============================================================
CREATE TABLE IF NOT EXISTS client_connections (
    connection_id TEXT PRIMARY KEY,
    client_info TEXT, -- JSON: device, version, etc.
    connected_at INTEGER NOT NULL,
    last_activity INTEGER NOT NULL
);

CREATE INDEX idx_connections_activity ON client_connections(last_activity DESC);
```

### 10.2 Client-Side Schema (macOS App)

Location: `~/Library/Application Support/VantageOC/vantage.db`

```sql
-- ============================================================
-- LOCAL CHANNELS (cached from server)
-- ============================================================
CREATE TABLE IF NOT EXISTS channels (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    created_at INTEGER NOT NULL,
    unread_count INTEGER NOT NULL DEFAULT 0,
    last_sync INTEGER NOT NULL
);

-- ============================================================
-- LOCAL MESSAGES (cached from server, with local-only fields)
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    role TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    metadata TEXT,
    -- Local-only fields
    sync_status TEXT NOT NULL DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending', 'failed')),
    local_created_at INTEGER NOT NULL,
    FOREIGN KEY (channel) REFERENCES channels(slug) ON DELETE CASCADE
);

CREATE INDEX idx_messages_channel_timestamp ON messages(channel, timestamp DESC);
CREATE INDEX idx_messages_sync_status ON messages(sync_status);

-- ============================================================
-- PENDING USER MESSAGES (queued when offline)
-- ============================================================
CREATE TABLE IF NOT EXISTS pending_messages (
    local_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    content TEXT NOT NULL,
    attachments TEXT, -- JSON array
    created_at INTEGER NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry INTEGER
);

-- ============================================================
-- ACTIVE TASKS (cached from server)
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    session_key TEXT,
    channel TEXT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    progress INTEGER,
    created_at INTEGER NOT NULL,
    completed_at INTEGER,
    last_sync INTEGER NOT NULL
);

CREATE INDEX idx_tasks_channel ON tasks(channel);
CREATE INDEX idx_tasks_status ON tasks(status);

-- ============================================================
-- PROOFS (cached from server)
-- ============================================================
CREATE TABLE IF NOT EXISTS proofs (
    proof_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    proof_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    data_url TEXT, -- URL or local file path
    mime_type TEXT,
    thumbnail_path TEXT, -- Local thumbnail cache
    verified INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- ============================================================
-- PENDING SAFETY ALERTS (need user action)
-- ============================================================
CREATE TABLE IF NOT EXISTS pending_alerts (
    alert_id TEXT PRIMARY KEY,
    channel TEXT,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    action TEXT NOT NULL,
    impact TEXT,
    expires_at INTEGER,
    received_at INTEGER NOT NULL
);

CREATE INDEX idx_pending_alerts_severity ON pending_alerts(severity);
CREATE INDEX idx_pending_alerts_expires ON pending_alerts(expires_at);

-- ============================================================
-- PENDING DRAFTS (need user approval)
-- ============================================================
CREATE TABLE IF NOT EXISTS pending_drafts (
    draft_id TEXT PRIMARY KEY,
    channel TEXT,
    draft_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT,
    recipient TEXT,
    platform TEXT,
    expires_at INTEGER,
    received_at INTEGER NOT NULL
);

-- ============================================================
-- APP SETTINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- ============================================================
-- SYNC STATE
-- ============================================================
CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
```

---

## 11. RPC Reference Table

### Client → Server (Outbound)

| Method | Params Interface | Response Interface | Error Codes |
|--------|------------------|-------------------|-------------|
| `vantage.message` | `VantageMessageParams` | `{ success: boolean, channel: string, timestamp: number }` | `-32602`: Channel not found |
| `vantage.safety.approve` | `SafetyApproveParams` | `{ success: boolean, alertId: string }` | `-32602`: Alert not found, Already resolved |
| `vantage.safety.deny` | `SafetyDenyParams` | `{ success: boolean, alertId: string }` | `-32602`: Alert not found, Already resolved |
| `vantage.draft.approve` | `DraftApproveParams` | `{ success: boolean, draftId: string }` | `-32602`: Draft not found, Already resolved |
| `vantage.draft.reject` | `DraftRejectParams` | `{ success: boolean, draftId: string }` | `-32602`: Draft not found, Already resolved |
| `vantage.task.register` | `TaskRegisterParams` | `{ success: boolean, taskId: string }` | |
| `vantage.task.complete` | `TaskCompleteParams` | `{ success: boolean, taskId: string }` | `-32602`: Task not found |
| `vantage.task.proof` | `TaskProofParams` | `{ success: boolean, proofId: string, taskId: string }` | `-32602`: Task not found |
| `vantage.tasks.list` | `{ channel?: string, status?: string }` | `TaskListResponse` | |
| `vantage.crons.list` | `{}` | `CronListResponse` | |
| `vantage.heartbeat.status` | `{}` | `HeartbeatStatusResponse` | |
| `vantage.poll` | `PollParams` | `PollResponse` | |
| `vantage.channels.list` | `{}` | `ChannelListResponse` | |
| `vantage.channels.history` | `ChannelHistoryParams` | `ChannelHistoryResponse` | `-32602`: Channel not found |
| `vantage.channels.post` | `ChannelPostParams` | `{ success: boolean, messageId: string }` | `-32602`: Channel not found |
| `vantage.channels.mark_read` | `ChannelMarkReadParams` | `{ success: boolean }` | |
| `vantage.channels.create` | `ChannelCreateParams` | `{ success: boolean, channel: VantageChannel }` | `-32602`: Channel already exists |
| `vantage.channels.delete` | `ChannelDeleteParams` | `{ success: boolean }` | `-32602`: Channel not found |
| `vantage.channels.config.get` | `ChannelConfigGetParams` | `{ key: string, value: unknown }` | |
| `vantage.channels.config.set` | `ChannelConfigSetParams` | `{ success: boolean, key: string, value: unknown }` | |

### Server → Client (Push Notifications via WebSocket)

| Envelope Type | Payload Interface | When Sent |
|--------------|-------------------|-----------|
| `chat` | `ChatPayload` | Agent generates text response |
| `safety_alert` | `SafetyAlertPayload` | Agent triggers safety check |
| `task_spawn` | `TaskSpawnPayload` | Subagent created |
| `task_update` | `TaskUpdatePayload` | Subagent progress |
| `task_complete` | `TaskCompletePayload` | Subagent finished successfully |
| `task_failed` | `TaskFailedPayload` | Subagent failed |
| `proof_receipt` | `ProofReceiptPayload` | Task submitted proof |
| `draft` | `DraftPayload` | Agent created draft for approval |
| `report` | `ReportPayload` | Agent generated report/briefing |
| `heartbeat` | `HeartbeatPayload` | Periodic health check |
| `cron_status` | `CronStatusPayload` | Cron job status change |
| `system_event` | `SystemEventPayload` | System notification |
| `context_compacting` | `ContextCompactingPayload` | Context compaction starting |
| `context_compacted` | `ContextCompactedPayload` | Context compaction completed |
| `channel_read` | `ChannelReadPayload` | Channel marked as read |
| `channel_created` | `ChannelCreatedPayload` | New channel created |

### Error Code Reference

| Code | Meaning | Recovery |
|------|---------|----------|
| `-32600` | Invalid request | Fix request format |
| `-32601` | Method not found | Check method name |
| `-32602` | Invalid params | Check params schema |
| `-32603` | Internal error | Retry or report bug |
| `-32700` | Parse error | Fix JSON syntax |

---

## 12. Migration: V1 → V2

### 12.1 Breaking Changes

| Change | Impact | Mitigation |
|--------|--------|------------|
| Plugin registration signature | Server restart required | Automatic on deploy |
| `sessions.json` no longer used | None (SDK manages) | Delete old file |
| Subagent replies route to channel | Better UX, no action | Clients already render by channel |
| New envelope types | V1 clients ignore unknown types | Graceful degradation |

### 12.2 V1 Client Compatibility

V2 plugin remains compatible with V1 clients:

1. **Unknown envelope types**: V1 clients should ignore `context_compacting` and `context_compacted`. If they crash, they need a fix, but most JSON parsers will just skip unknown fields.

2. **Subagent routing**: V1 clients render messages by channel already. Subagent replies going to the correct channel is invisible to them.

3. **RPC methods**: All V1 RPC methods preserved with identical signatures.

**Recommendation**: Ship V2 plugin first, then update clients at leisure.

### 12.3 Data Migration Steps

```bash
# 1. Stop the gateway
systemctl stop openclaw-gateway

# 2. Backup V1 plugin
cp -r ~/.openclaw/extensions/vantage ~/.openclaw/extensions/vantage.v1.backup

# 3. Backup V1 database (if exists)
cp ~/.openclaw/vantage-plugin.db ~/.openclaw/vantage-plugin.db.v1.backup

# 4. Deploy V2 plugin
# (copy new files to ~/.openclaw/extensions/vantage/)

# 5. Run schema migration (new tables are additive)
sqlite3 ~/.openclaw/vantage-plugin.db < migration-v2.sql

# 6. Delete sessions.json (no longer needed)
rm -f ~/.openclaw/extensions/vantage/sessions.json

# 7. Start the gateway
systemctl start openclaw-gateway

# 8. Verify
curl -s localhost:8080/health | jq .
```

**migration-v2.sql:**

```sql
-- Add any new columns to existing tables
-- (V2 uses same schema, just new code)

-- Ensure indexes exist
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);

-- Clean up any orphaned data
DELETE FROM messages WHERE channel NOT IN (SELECT slug FROM channels);
DELETE FROM proofs WHERE task_id NOT IN (SELECT task_id FROM tasks);
```

### 12.4 Rollback Procedure

```bash
# If V2 has issues, rollback to V1
systemctl stop openclaw-gateway

# Restore V1 plugin
rm -rf ~/.openclaw/extensions/vantage
mv ~/.openclaw/extensions/vantage.v1.backup ~/.openclaw/extensions/vantage

# Restore V1 database (if schema changed)
cp ~/.openclaw/vantage-plugin.db.v1.backup ~/.openclaw/vantage-plugin.db

systemctl start openclaw-gateway
```

---

## 13. Implementation Order

### Phase 1: Core Infrastructure (Days 1-2)

1. **Create `src/types.ts`**
   - All TypeScript interfaces
   - Export everything needed by other modules
   - No dependencies on other Vantage modules

2. **Create `src/runtime.ts`**
   - Singleton pattern
   - Simple, no dependencies

3. **Update `src/store.ts`** (if needed)
   - Add any new methods required by V2
   - Ensure schema matches spec
   - Keep backward compatible

### Phase 2: Plugin Registration (Day 2)

4. **Create `index.ts`**
   - Follow Discord pattern exactly
   - Import all modules
   - Register lifecycle hooks
   - Start proof tracker

5. **Update `openclaw.plugin.json`**
   - Bump version to 2.0.0
   - Verify manifest format

### Phase 3: Channel Plugin (Days 2-3)

6. **✅ COMPLETE: `src/channel.ts`**
   - `ChannelPlugin<ResolvedVantageAccount>` implemented
   - `parseChannelPrefix` logic ported
   - WebSocket loopback preserved for inbound (SDK injection does not exist)
   - `handleInboundMessage` implemented via `loopback.ts`
   - Config methods corrected to synchronous with proper SDK signatures
   - `startAccount` blocks indefinitely (push-based channel pattern)

### Phase 4: Subagent Hooks (Day 3)

7. **Create `src/subagent-hooks.ts`**
   - Implement all three hooks
   - Test binding lifecycle
   - Verify delivery routing

### Phase 5: RPC Methods (Days 3-4)

8. **Create `src/rpc.ts`**
   - Port all RPC methods
   - Inbound messages via `loopback.ts injectChatMessage()` (not SDK injection — that API does not exist)
   - Remove sessions.json writes
   - Test each method

### Phase 6: Integration Testing (Day 4)

9. **Test against V1 client**
   - Verify all RPC methods work
   - Check envelope delivery
   - Confirm no regressions

10. **Test new features**
    - Subagent routing to channels
    - Context compaction notifications
    - Proof tracker

### Phase 7: Client Updates (Days 5-6)

11. **Add new envelope handlers**
    - `context_compacting`
    - `context_compacted`
    - Update connection state machine

12. **Update task views**
    - Show subagent binding info
    - Handle routed replies

### Phase 8: Documentation & Deployment (Day 7)

13. **Update README**
14. **Write migration guide**
15. **Deploy to staging**
16. **Deploy to production**

---

## Appendix A: File Checksums

After implementation, verify files match expected structure:

```
~/.openclaw/extensions/vantage/
├── openclaw.plugin.json    # ~20 lines
├── package.json            # ~15 lines
├── tsconfig.json           # ~25 lines
├── index.ts                # ~80 lines
└── src/
    ├── channel.ts          # ~200 lines
    ├── runtime.ts          # ~40 lines
    ├── store.ts            # ~400 lines (existing)
    ├── rpc.ts              # ~350 lines
    ├── subagent-hooks.ts   # ~150 lines
    └── types.ts            # ~350 lines
```

Total new/modified code: ~1,200 lines (excluding store.ts)

---

## Appendix B: Testing Checklist

### Unit Tests

- [ ] `parseChannelPrefix` correctly handles all formats
- [ ] `buildEnvelope` produces valid envelopes
- [ ] Subagent binding CRUD operations
- [ ] Store methods for new tables

### Integration Tests

- [ ] RPC: `vantage.message` injects to SDK
- [ ] RPC: `vantage.safety.approve` resumes session
- [ ] RPC: `vantage.safety.deny` aborts session
- [ ] RPC: `vantage.draft.approve` with modifications
- [ ] RPC: `vantage.channels.create` provisions workspace
- [ ] RPC: `vantage.channels.delete` cleans up bindings

### End-to-End Tests

- [ ] Send message from VantageOC → agent responds → appears in channel
- [ ] Agent triggers safety alert → VantageOC shows modal → approve → agent continues
- [ ] Agent spawns subagent → task appears → completes → result in correct channel
- [ ] Agent creates draft → VantageOC shows approval → modify and approve → sent

---

*End of specification.*

---

## Appendix A: Complete Channel Create/Delete Implementation

The Opus-generated spec simplified `vantage.channels.create` and `vantage.channels.delete`. The actual production logic requires workspace provisioning, sessions bootstrapping, `openclaw.json` mutation, and a protected-channel guard. Below is the complete TypeScript that replaces the stub in Section 8 (rpc.ts).

### vantage.channels.create (complete)

```typescript
api.registerGatewayMethod('vantage.channels.create', async ({ params, respond, broadcast }: any) => {
  if (broadcast) captureBroadcast(broadcast);
  const { slug, displayName, icon, soul, identity, userContext } = params ?? {};

  if (!slug || !/^[a-z0-9_-]+$/.test(slug)) {
    return respond(false, undefined, { code: 'INVALID_REQUEST', message: 'slug must match [a-z0-9_-]+' });
  }

  try {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const os = await import('node:os');
    const { randomUUID } = await import('node:crypto');

    const ocDir = path.join(os.homedir(), '.openclaw');
    const workspacePath = path.join(ocDir, 'workspace', 'channels', slug);
    const name = displayName ?? slug;

    // Create workspace directory
    fs.mkdirSync(workspacePath, { recursive: true });

    // Write SOUL.md
    fs.writeFileSync(path.join(workspacePath, 'SOUL.md'),
      soul ?? `# SOUL.md\nYou are a focused AI agent for the ${name} channel. Be concise and helpful.\n`);

    // Write IDENTITY.md
    fs.writeFileSync(path.join(workspacePath, 'IDENTITY.md'),
      identity ?? `# IDENTITY.md\n- **Name:** ${name} Agent\n`);

    // Write USER.md
    fs.writeFileSync(path.join(workspacePath, 'USER.md'), userContext ?? '');

    // Write AGENTS.md
    fs.writeFileSync(path.join(workspacePath, 'AGENTS.md'),
      '# AGENTS.md\nRead SOUL.md and USER.md on startup.\n');

    // Create agent sessions directory
    const agentSessionsDir = path.join(ocDir, 'agents', slug, 'sessions');
    fs.mkdirSync(agentSessionsDir, { recursive: true });

    // Bootstrap sessions.json + empty transcript so chat.send works on first message
    const sessionId = randomUUID();
    const sessionFile = path.join(agentSessionsDir, `${sessionId}.jsonl`);
    const sessionKey = `agent:${slug}:main`;
    const now = Date.now();
    const sessionsJson = {
      [sessionKey]: {
        sessionId,
        updatedAt: now,
        systemSent: false,
        abortedLastRun: false,
        chatType: 'direct',
        deliveryContext: { channel: 'vantage', to: slug, accountId: slug },
        lastChannel: 'vantage',
        lastTo: slug,
        lastAccountId: slug,
        sessionFile,
      },
    };
    fs.writeFileSync(path.join(agentSessionsDir, 'sessions.json'), JSON.stringify(sessionsJson, null, 2));
    fs.writeFileSync(sessionFile, '');  // empty transcript

    // Update openclaw.json agents.list
    const configPath = path.join(ocDir, 'openclaw.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (!config.agents) config.agents = {};
    if (!config.agents.list) config.agents.list = [{ id: 'main', default: true }];
    if (!config.agents.list.find((a: any) => a.id === slug)) {
      config.agents.list.push({ id: slug, workspace: workspacePath });
    }

    // Register in DB
    store.getOrCreateChannel(slug);
    store.setChannelAgent(slug, slug, workspacePath);

    // Broadcast creating event before restart
    pushEnvelope(makeEnvelope('channel_creating', { channelSlug: slug, message: 'Agent registered, restarting gateway...' }, slug));

    // Write config — triggers gateway restart via file watcher
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    respond(true, { ok: true, slug, workspacePath, sessionId, message: 'Channel created. Gateway restarting...' });
  } catch (err: any) {
    respond(false, undefined, { code: 'INTERNAL_ERROR', message: err?.message ?? 'create failed' });
  }
});
```

### vantage.channels.delete (complete)

```typescript
// Protected channels — cannot be deleted
const PROTECTED_CHANNELS = ['main', 'barnabas-coaching', 'morse-marketing', 'black-raven', 'glimmer-cards'];

api.registerGatewayMethod('vantage.channels.delete', async ({ params, respond, broadcast }: any) => {
  if (broadcast) captureBroadcast(broadcast);
  const { slug } = params ?? {};

  if (!slug || !/^[a-z0-9_-]+$/.test(slug)) {
    return respond(false, undefined, { code: 'INVALID_REQUEST', message: 'slug required' });
  }
  if (PROTECTED_CHANNELS.includes(slug)) {
    return respond(false, undefined, { code: 'FORBIDDEN', message: `${slug} is a protected channel and cannot be deleted` });
  }

  try {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const os = await import('node:os');

    const ocDir = path.join(os.homedir(), '.openclaw');
    const workspacePath = path.join(ocDir, 'workspace', 'channels', slug);
    const agentDir = path.join(ocDir, 'agents', slug);

    // Remove from DB (cascades to channel_messages)
    const deleted = store.deleteChannel(slug);

    // Remove workspace directory
    if (fs.existsSync(workspacePath)) fs.rmSync(workspacePath, { recursive: true, force: true });

    // Remove agent sessions directory
    if (fs.existsSync(agentDir)) fs.rmSync(agentDir, { recursive: true, force: true });

    // Remove agent from openclaw.json
    const configPath = path.join(ocDir, 'openclaw.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (config.agents?.list) {
      config.agents.list = config.agents.list.filter((a: any) => a.id !== slug);
    }

    // Broadcast deletion before restart
    pushEnvelope(makeEnvelope('channel_deleted', { channelSlug: slug }, slug));

    // Write config — triggers gateway restart
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    respond(true, { ok: true, slug, dbDeleted: deleted, message: 'Channel deleted. Gateway restarting...' });
  } catch (err: any) {
    respond(false, undefined, { code: 'INTERNAL_ERROR', message: err?.message ?? 'delete failed' });
  }
});
```

---

## Appendix B: Swift Client Data Models and Architecture

### B.1 Data Models

```swift
// MARK: - Core Channel Types

struct VantageChannel: Identifiable, Codable, Hashable {
    let id: String           // UUID
    var slug: String         // "morse-marketing"
    var displayName: String  // "Morse Marketing"
    var icon: String         // emoji
    var sortOrder: Int
    var unreadCount: Int
    var hasPendingApprovals: Bool
    let createdAt: Date
    var updatedAt: Date
}

struct ChannelMessage: Identifiable, Codable {
    let id: String
    let channelSlug: String
    let agentId: String
    let agentName: String
    let type: ChannelMessageType
    var content: String
    var metadata: [String: String]?
    var status: MessageStatus?
    let createdAt: Date
    var resolvedAt: Date?
    var isRead: Bool
}

// ⚠️ CORRECTION: These cases must match server MessageType exactly.
// The original spec had wrong/abbreviated values.
enum ChannelMessageType: String, Codable {
    case chat
    case safetyAlert = "safety_alert"
    case taskSpawn = "task_spawn"
    case taskUpdate = "task_update"
    case taskComplete = "task_complete"
    case taskFailed = "task_failed"
    case proofReceipt = "proof_receipt"
    case draft
    case report
    case heartbeat
    case cronStatus = "cron_status"
    case systemEvent = "system_event"
    case contextCompacting = "context_compacting"
    case contextCompacted = "context_compacted"
    case channelRead = "channel_read"
    case channelCreated = "channel_created"
}

enum MessageStatus: String, Codable {
    case pending, approved, rejected, posted
}

// MARK: - Outbound Envelope
//
// ⚠️ CORRECTION: Field names come directly from the SQLite row mapping in store.ts.
// The original spec had wrong field names (ts, msgId, channelSlug).
// Actual shape returned by vantage.poll messages[]:
//
//   {
//     type: string,           // MessageType value e.g. "chat", "safety_alert"
//     channel: string,        // channel slug e.g. "general"
//     timestamp: Int64,       // Unix ms
//     payload: {
//       messageId: String,    // UUID
//       content: String,      // raw text or JSON string
//       role: String,         // "assistant" | "user"
//       streaming: Bool
//     }
//   }
//
// Note: payload.content may be a JSON string for complex types (draft, safety_alert, etc.)
// Decode content as JSON when type != "chat" | "system_event" | "heartbeat".

struct PollMessage: Codable, Identifiable {
    let type: ChannelMessageType
    let channel: String         // channel slug
    let timestamp: Int64        // Unix ms — use as cursor for next poll
    let payload: PollPayload

    var id: String { payload.messageId }
}

struct PollPayload: Codable {
    let messageId: String
    let content: String         // raw text or JSON string; parse based on `type`
    let role: String            // "assistant" | "user"
    let streaming: Bool
}

// For poll response root:
struct PollResponse: Codable {
    let messages: [PollMessage]
    let serverTime: Int64       // Unix ms — advance lastPollTs to this value
}

// Legacy name alias — DO NOT use the old OutboundEnvelope shape
// enum EnvelopePayload: Codable — removed, payload is always PollPayload above

// channel_read and channel_created
    case raw([String: AnyCodable])   // fallback for unknown types
}

struct ChatPayload: Codable {
    let text: String
    var streaming: Bool?
    var sender: String?
    var senderId: String?
}

struct SafetyAlertPayload: Codable {
    let level: String          // "red" | "yellow"
    let requestId: String
    let description: String
    var command: String?
    let blocking: Bool
    var expiresAt: Int64?
}

struct TaskSpawnPayload: Codable {
    let taskId: String
    var parentTaskId: String?
    let agentLabel: String
    var sessionKey: String?
    let task: String
    let proofRequirements: [ProofRequirement]
    let spawnedBy: String
}

struct ProofRequirement: Codable {
    let type: String
    let description: String
    let required: Bool
}

struct TaskCompletePayload: Codable {
    let taskId: String
    let status: String         // "verified" | "unverified" | "partial"
    let summary: String
    let proofLog: [ProofEntry]
    let durationMs: Int
    let toolCallCount: Int
    var verifiedBy: String?
}

struct ProofEntry: Codable, Identifiable {
    var id: String { "\(ts)-\(type)" }
    let type: String
    let ts: Int64
    let detail: String
    let verified: Bool
    var evidence: String?
}

struct DraftPayload: Codable {
    let draftId: String
    let platform: String
    let content: String
    var metadata: DraftMetadata?
    let agentId: String
    let agentName: String
}

struct DraftMetadata: Codable {
    var scheduledFor: String?
    var targetAudience: String?
    var wordCount: Int?
}

struct HeartbeatPayload: Codable {
    let status: String
    let checks: [HeartbeatCheck]
    let nextHeartbeatAt: Int64
    let sessionTokens: Int
    let activeTaskCount: Int
    let pendingApprovals: Int
}

struct HeartbeatCheck: Codable, Identifiable {
    var id: String { name }
    let name: String
    let status: String
    var detail: String?
}

// MARK: - Tasks

struct VantageTask: Identifiable, Codable {
    let id: String             // = taskId
    let taskId: String
    var parentTaskId: String?
    let agentLabel: String
    var sessionKey: String?
    let taskDescription: String
    let proofRequirements: [ProofRequirement]
    var status: TaskStatus
    var progress: String?
    var currentStep: String?
    var toolCallCount: Int
    var elapsedMs: Int
    var proofLog: [ProofEntry]
    let spawnedAt: Date
    var completedAt: Date?
}

enum TaskStatus: String, Codable {
    case running, blocked, verifying, complete, failed
    case verified, unverified, partial
}

// MARK: - Safety Alerts

struct SafetyAlert: Identifiable, Codable {
    let id: String             // = requestId
    let requestId: String
    let level: AlertLevel
    let description: String
    var command: String?
    let blocking: Bool
    var expiresAt: Date?
    let createdAt: Date
    var resolvedAt: Date?
    var resolution: AlertResolution?
}

enum AlertLevel: String, Codable { case red, yellow }
enum AlertResolution: String, Codable { case approved, denied, expired }

// MARK: - Drafts

struct VantageDraft: Identifiable, Codable {
    let id: String             // = draftId
    let draftId: String
    let channelSlug: String
    let platform: String
    var content: String
    var metadata: DraftMetadata?
    let agentId: String
    let agentName: String
    var status: DraftStatus
    let createdAt: Date
    var resolvedAt: Date?
    var editedContent: String?
}

enum DraftStatus: String, Codable { case pending, approved, rejected, posted }
```

### B.2 GatewayClient

```swift
@Observable
final class GatewayClient {
    var connectionState: ConnectionState = .disconnected
    var lastError: Error?

    private var webSocket: URLSessionWebSocketTask?
    private let session: URLSession
    private let gatewayURL: URL
    private let authToken: String
    private var reconnectTask: Task<Void, Never>?
    private var reconnectAttempt = 0
    private let maxReconnectAttempts = 10

    // Event stream — consumers subscribe to this
    let envelopes: AsyncStream<OutboundEnvelope>
    private let envelopeContinuation: AsyncStream<OutboundEnvelope>.Continuation

    init(gatewayURL: URL, authToken: String) {
        self.gatewayURL = gatewayURL
        self.authToken = authToken
        self.session = URLSession(configuration: .default)
        (envelopes, envelopeContinuation) = AsyncStream.makeStream()
    }

    func connect() {
        connectionState = .connecting
        var request = URLRequest(url: gatewayURL)
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        webSocket = session.webSocketTask(with: request)
        webSocket?.resume()
        listen()
    }

    func disconnect() {
        reconnectTask?.cancel()
        webSocket?.cancel(with: .normalClosure, reason: nil)
        connectionState = .disconnected
    }

    func send(method: String, params: some Encodable, id: String = UUID().uuidString) async throws -> Data {
        let frame = GatewayFrame(type: "req", id: id, method: method, params: params)
        let data = try JSONEncoder().encode(frame)
        try await webSocket?.send(.data(data))
        // Response correlation handled by pending map — simplified here
        return data
    }

    private func listen() {
        Task { [weak self] in
            guard let self else { return }
            do {
                while true {
                    let message = try await webSocket!.receive()
                    switch message {
                    case .data(let data):
                        handleIncoming(data)
                    case .string(let str):
                        handleIncoming(Data(str.utf8))
                    @unknown default: break
                    }
                }
            } catch {
                handleDisconnect(error)
            }
        }
    }

    private func handleIncoming(_ data: Data) {
        guard let event = try? JSONDecoder().decode(GatewayEvent.self, from: data),
              event.event == "vantage.event",
              let envelope = event.envelope else { return }
        envelopeContinuation.yield(envelope)
    }

    private func handleDisconnect(_ error: Error) {
        connectionState = .reconnecting(attempt: reconnectAttempt, maxAttempts: maxReconnectAttempts)
        reconnectTask = Task {
            let delay = min(pow(2.0, Double(reconnectAttempt)), 30.0)
            try? await Task.sleep(for: .seconds(delay))
            reconnectAttempt += 1
            if reconnectAttempt > maxReconnectAttempts {
                connectionState = .failed(error: error)
                return
            }
            connect()
        }
    }
}

enum ConnectionState {
    case disconnected
    case connecting
    case connected
    case reconnecting(attempt: Int, maxAttempts: Int)
    case failed(error: Error)
}

struct GatewayFrame<T: Encodable>: Encodable {
    let type: String
    let id: String
    let method: String
    let params: T
}

struct GatewayEvent: Decodable {
    let event: String?
    let envelope: OutboundEnvelope?
}
```

### B.3 ViewModels

```swift
// MARK: - AppViewModel (root)

@Observable
final class AppViewModel {
    var channels: [VantageChannel] = []
    var selectedChannel: VantageChannel?
    var activeSafetyAlert: SafetyAlert?
    var isCompacting: Bool = false
    var pendingApprovals: Int = 0

    private let gateway: GatewayClient
    private let store: LocalStore  // client-side SQLite cache

    func start() async {
        gateway.connect()
        await loadChannels()
        await listenForEnvelopes()
    }

    private func listenForEnvelopes() async {
        for await envelope in gateway.envelopes {
            await handleEnvelope(envelope)
        }
    }

    @MainActor
    private func handleEnvelope(_ envelope: OutboundEnvelope) async {
        switch envelope.type {
        case "safety_alert":
            guard case .safetyAlert(let p) = envelope.payload else { return }
            if p.level == "red" && p.blocking {
                activeSafetyAlert = SafetyAlert(from: p)
            }
        case "context_compacting":
            isCompacting = true
        case "context_compacted":
            isCompacting = false
        case "channel_read":
            guard case .channelRead(let p) = envelope.payload else { return }
            clearUnread(channelSlug: p.channelSlug)
        case "heartbeat":
            guard case .heartbeat(let p) = envelope.payload else { return }
            pendingApprovals = p.pendingApprovals
        default:
            // Route to the appropriate channel view model
            if let slug = envelope.channelSlug,
               let channelVM = channelViewModels[slug] {
                channelVM.handleEnvelope(envelope)
            }
        }
    }
}

// MARK: - ChannelViewModel

@Observable
final class ChannelViewModel {
    let channel: VantageChannel
    var messages: [ChannelMessage] = []
    var isLoading: Bool = false
    var hasMore: Bool = true
    private var oldestMessageTs: Int64?

    func loadHistory() async { /* vantage.channels.history */ }
    func loadMore() async { /* vantage.channels.history with before cursor */ }
    func markRead() async { /* vantage.channels.mark_read */ }

    func handleEnvelope(_ envelope: OutboundEnvelope) {
        // Append new messages, update task cards, etc.
    }
}

// MARK: - WorkPanelViewModel

@Observable
final class WorkPanelViewModel {
    var tasks: [VantageTask] = []
    var rootTasks: [VantageTask] { tasks.filter { $0.parentTaskId == nil } }
    func subtasks(of taskId: String) -> [VantageTask] {
        tasks.filter { $0.parentTaskId == taskId }
    }
}

// MARK: - DraftApprovalViewModel

@Observable
final class DraftApprovalViewModel {
    let draft: VantageDraft
    var editedContent: String
    var isSubmitting: Bool = false
    var result: DraftStatus?

    init(draft: VantageDraft) {
        self.draft = draft
        self.editedContent = draft.content
    }

    func approve(gateway: GatewayClient) async throws {
        isSubmitting = true
        defer { isSubmitting = false }
        let content = editedContent != draft.content ? editedContent : nil
        _ = try await gateway.send(
            method: "vantage.draft.approve",
            params: ["draftId": draft.draftId, "editedContent": content as Any]
        )
        result = .approved
    }

    func reject(reason: String?, gateway: GatewayClient) async throws {
        isSubmitting = true
        defer { isSubmitting = false }
        _ = try await gateway.send(
            method: "vantage.draft.reject",
            params: ["draftId": draft.draftId, "reason": reason as Any]
        )
        result = .rejected
    }
}
```

### B.4 Key SwiftUI Views (struct signatures)

```swift
// MARK: - Root

struct VantageApp: App {
    @State private var appVM = AppViewModel()
    var body: some Scene {
        WindowGroup { ContentView().environment(appVM) }
    }
}

struct ContentView: View {
    @Environment(AppViewModel.self) var appVM
    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            if let channel = appVM.selectedChannel {
                ChannelView(channel: channel)
            } else {
                ChatView()
            }
        }
        .overlay { if appVM.activeSafetyAlert != nil { SafetyAlertOverlay() } }
    }
}

// MARK: - Sidebar

struct SidebarView: View { /* navigation items + channels section */ }

struct ChannelRowView: View {
    let channel: VantageChannel
    // Shows icon, displayName, unreadCount badge (blue), pending dot (orange)
}

// MARK: - Channel

struct ChannelView: View {
    let channel: VantageChannel
    @State private var vm: ChannelViewModel
}

struct ChannelMessageListView: View {
    @Binding var messages: [ChannelMessage]
    // Infinite scroll — load more when scrolled to top
}

struct ChannelMessageRow: View {
    let message: ChannelMessage
    // Switches on message.type: post→PostBubble, draft→DraftCard, report→ReportCard, alert→AlertBanner
}

struct DraftCard: View {
    let message: ChannelMessage
    @State private var vm: DraftApprovalViewModel
    // Approve / Edit / Reject buttons. Edit opens inline TextEditor.
}

// MARK: - Safety Alert

struct SafetyAlertOverlay: View {
    @Environment(AppViewModel.self) var appVM
    // Full-screen .ultraThinMaterial background
    // Red card: requestId, description, optional command in monospace
    // Approve button (green) + Deny button (red) + optional reason TextEditor
    // Disabled during isSubmitting
    // Error toast if RPC fails: "Failed to send — will retry on reconnect"
}

// MARK: - Work Panel

struct WorkPanelView: View {
    @State private var vm = WorkPanelViewModel()
    // Tree of TaskCards, root tasks expanded by default
}

struct TaskCard: View {
    let task: VantageTask
    // Status badge: running (spinner), verified (green), unverified (yellow), failed (red)
    // Expandable proof log: ProofEntryRow per entry
    // "View Full Proof" button → calls vantage.task.proof
}

// MARK: - Chat

struct ChatView: View {
    // Token-streaming message list
    // Send field disabled when appVM.isCompacting == true
    // CompactingBanner shown at top when compacting
}

struct CompactingBanner: View {
    // "Reorganizing context..." with progress indicator
    // Disappears on context_compacted
}

// MARK: - Connection

struct ConnectionStatusBanner: View {
    let state: ConnectionState
    // Hidden when connected
    // "Reconnecting... (attempt X/Y)" when reconnecting
    // "Connection failed. Retry" when failed
}
```

### B.5 Polling Strategy

The client should use **push + fallback poll**:

1. **Primary:** Listen on the WebSocket for `vantage.event` push pings. On each ping, call `vantage.poll` with `since: lastTs` to fetch new envelopes.
2. **Fallback:** If no push received for 30 seconds, call `vantage.poll` to catch anything missed.
3. **On channel open:** Call `vantage.channels.history` for full message history. Then `vantage.poll` for any envelopes since last poll ts.
4. **Cursor:** Track `lastPollTs` per session. Use `since: lastPollTs` to get only new messages. Update after each poll.

```swift
// In GatewayClient or AppViewModel
var lastPollTs: Int64 = 0

// ⚠️ CORRECTION: server takes `channels` (array of slugs), not `channelSlug` (single string).
// Response has `serverTime` (not `ts`) — use that to advance the cursor.
func poll(channels: [String]? = nil) async {
    var params: [String: Any] = ["since": lastPollTs, "limit": 50]
    if let channels { params["channels"] = channels }
    let result = try? await gateway.send(method: "vantage.poll", params: params)
    // process result.messages
    if let serverTime = result?.serverTime { lastPollTs = serverTime }
}
```

