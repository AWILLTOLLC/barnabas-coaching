# Real-Time Subagent Activity Streaming

**Status:** Spec Complete  
**Author:** Forge (architect subagent)  
**Date:** 2026-03-11

## Summary

Wire subagent LLM output into a per-task activity feed so the VantageOC client can display real-time streaming progress while a task is running. Currently, between `task.register` and `task.complete`, the client sees nothing — subagent work is a black box.

### The Fix

1. Capture subagent LLM output via the existing `llm_output` hook
2. Map subagent sessions to tasks via the `SubagentBinding.taskId` field (currently unpopulated)
3. Store activity chunks in a new `task_activity` table
4. Expose activity via a new `vantage.task.activity` RPC and include in poll responses
5. Mark tasks as "live" when activity is streaming

---

## Architecture

### Current Data Flow (broken)

```
subagent spawns → subagent_spawning hook → SubagentBinding created (taskId: undefined)
                                         ↓
agent calls vantage.task.register → task row in DB (no link to binding)
                                         ↓
subagent produces LLM output → NOT CAPTURED (session key doesn't match agent:*:main filter)
                                         ↓
agent calls vantage.task.complete → task marked complete
```

### Fixed Data Flow

```
subagent spawns with taskId hint → subagent_spawning hook → SubagentBinding.taskId = hint
                                                          ↓
                                         (or falls back to using childSessionKey as taskId)
                                                          ↓
subagent produces LLM output → llm_output hook → lookup SubagentBinding by sessionKey
                                               → if bound, write to task_activity table
                                               → broadcast "task_activity" event
                                                          ↓
client polls vantage.task.activity or vantage.poll → receives activity chunks
```

---

## DB Schema Changes

### New Table: `task_activity`

```sql
CREATE TABLE IF NOT EXISTS task_activity (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_key TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_activity_task_created 
    ON task_activity(task_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_task_activity_session 
    ON task_activity(session_key);
```

### Migration Pattern

Add to `SCHEMA` constant in `store.ts`. SQLite handles `CREATE TABLE IF NOT EXISTS` idempotently.

No data migration needed — this is additive.

---

## TypeScript Type Changes

### `types.ts` — New Types

```typescript
/** Task activity chunk (streaming LLM output from subagent). */
export interface TaskActivityChunk {
  id: string;
  taskId: string;
  sessionKey: string;
  content: string;
  createdAt: number;
}

/** Task activity payload for streaming updates. */
export interface TaskActivityPayload {
  taskId: string;
  sessionKey: string;
  content: string;
  streaming: boolean;
  chunkIndex?: number;
}
```

### `types.ts` — Update `MessageType`

```typescript
export type MessageType =
  | "chat"
  | "safety_alert"
  | "task_spawn"
  | "task_update"
  | "task_complete"
  | "task_failed"
  | "task_activity"  // ← ADD THIS
  | "proof_receipt"
  // ... rest unchanged
```

### `types.ts` — Update `PayloadForType`

```typescript
export type PayloadForType<T extends MessageType> =
  // ... existing mappings ...
  T extends "task_activity" ? TaskActivityPayload :
  // ... rest unchanged
```

### `types.ts` — Update `TaskInfo`

The `isLive` field already exists but is optional. Make it more useful:

```typescript
export interface TaskInfo {
  taskId: string;
  sessionKey?: string;
  name: string;
  description?: string;
  channel?: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  createdAt: number;
  completedAt?: number;
  isLive?: boolean;           // true when subagent is actively producing output
  lastActivityAt?: number;    // ← ADD: timestamp of last activity chunk
  activityCount?: number;     // ← ADD: total chunks for this task
}
```

---

## `subagent-hooks.ts` Changes

### 1. Populate `taskId` from Spawn Event

The subagent spawn event may include metadata with a taskId hint. If present, use it. Otherwise, fall back to using the `childSessionKey` as the taskId (allows binding even without explicit task registration).

**File:** `subagent-hooks.ts`

**Replace the binding creation in `subagent_spawning` handler:**

```typescript
api.on("subagent_spawning", async (event) => {
  const channelSlug = event.requester?.channel === "vantage"
    ? (extractChannelSlug(event.requester.to) ?? "main")
    : "main";

  // Extract taskId from spawn metadata if provided
  // Agent can pass { taskId: "..." } in spawn params
  const taskIdHint = (event as any).metadata?.taskId 
                  ?? (event as any).taskId 
                  ?? (event as any).label;  // label often contains task description
  
  // Use hint or fall back to childSessionKey as implicit taskId
  const taskId = taskIdHint ?? event.childSessionKey;

  const binding: SubagentBinding = {
    childSessionKey: event.childSessionKey,
    parentSessionKey: (event as any).parentSessionKey ?? "",
    channelSlug,
    taskId,  // ← NOW POPULATED
    boundAt: Date.now(),
  };

  subagentBindings.set(event.childSessionKey, binding);
  // ... rest unchanged
```

### 2. Export Function to Get TaskId for Session

Add a helper function for external callers (the llm_output hook needs this):

```typescript
/**
 * Get the taskId associated with a subagent session, if any.
 */
export function getTaskIdForSession(sessionKey: string): string | undefined {
  return subagentBindings.get(sessionKey)?.taskId;
}
```

---

## `store.ts` Changes

### 1. Add Schema for `task_activity`

Add to the `SCHEMA` constant:

```typescript
-- TASK ACTIVITY (streaming subagent output)
CREATE TABLE IF NOT EXISTS task_activity (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_key TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_activity_task_created 
    ON task_activity(task_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_task_activity_session 
    ON task_activity(session_key);
```

### 2. Add Store Methods

```typescript
interface CreateActivityInput {
  taskId: string;
  sessionKey: string;
  content: string;
}

async storeTaskActivity(input: CreateActivityInput): Promise<string> {
  const id = randomUUID();
  this.db.prepare(`
    INSERT INTO task_activity (id, task_id, session_key, content, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(id, input.taskId, input.sessionKey, input.content, Date.now());
  return id;
}

async getTaskActivity(
  taskId: string, 
  options?: { since?: number; limit?: number }
): Promise<Array<{ id: string; content: string; createdAt: number }>> {
  const { since = 0, limit = 100 } = options ?? {};
  const rows = this.db.prepare(`
    SELECT id, content, created_at FROM task_activity
    WHERE task_id = ? AND created_at > ?
    ORDER BY created_at ASC
    LIMIT ?
  `).all(taskId, since, limit) as Array<{
    id: string;
    content: string;
    created_at: number;
  }>;
  
  return rows.map(r => ({
    id: r.id,
    content: r.content,
    createdAt: r.created_at,
  }));
}

async getTaskActivityCount(taskId: string): Promise<number> {
  const row = this.db.prepare(
    "SELECT COUNT(*) as count FROM task_activity WHERE task_id = ?"
  ).get(taskId) as { count: number };
  return row.count;
}

async getLastActivityTimestamp(taskId: string): Promise<number | null> {
  const row = this.db.prepare(
    "SELECT MAX(created_at) as latest FROM task_activity WHERE task_id = ?"
  ).get(taskId) as { latest: number | null };
  return row.latest;
}

async clearTaskActivity(taskId: string): Promise<number> {
  const result = this.db.prepare(
    "DELETE FROM task_activity WHERE task_id = ?"
  ).run(taskId);
  return (result as any).changes;
}
```

### 3. Update `listTasks` to Include Activity Metadata

Modify the existing `listTasks` method to join activity data:

```typescript
async listTasks(filters?: { channel?: string; status?: string }): Promise<TaskInfo[]> {
  let query = `
    SELECT t.*,
      (SELECT MAX(a.created_at) FROM task_activity a WHERE a.task_id = t.task_id) as last_activity_at,
      (SELECT COUNT(*) FROM task_activity a WHERE a.task_id = t.task_id) as activity_count
    FROM tasks t WHERE 1=1
  `;
  const params: (string | number | null)[] = [];

  if (filters?.channel) {
    query += " AND t.channel = ?";
    params.push(filters.channel);
  }
  if (filters?.status) {
    query += " AND t.status = ?";
    params.push(filters.status);
  }

  query += " ORDER BY t.created_at DESC";

  const rows = this.db.prepare(query).all(...params) as any[];

  // Determine which tasks are "live" (have active subagent bindings)
  const { listActiveBindings } = await import("./subagent-hooks.js");
  const activeTaskIds = new Set(
    listActiveBindings()
      .filter(b => b.taskId)
      .map(b => b.taskId)
  );

  return rows.map((r) => ({
    taskId: r.task_id,
    sessionKey: r.session_key,
    name: r.name,
    description: r.description,
    channel: r.channel,
    status: r.status as TaskInfo["status"],
    progress: r.progress,
    createdAt: r.created_at,
    completedAt: r.completed_at,
    isLive: activeTaskIds.has(r.task_id),
    lastActivityAt: r.last_activity_at ?? undefined,
    activityCount: r.activity_count ?? 0,
  }));
}
```

---

## `index.ts` Changes

### Update `llm_output` Hook to Capture Subagent Output

The existing hook only captures `agent:*:main` sessions. Extend it to also capture subagent sessions and route their output to task activity:

```typescript
api.on(
  "llm_output",
  async (event: any, ctx: any) => {
    try {
      const sessionKey = ctx?.sessionKey as string | undefined;
      if (!sessionKey?.startsWith("agent:")) return;

      const texts: string[] = event?.assistantTexts ?? [];
      const content = texts.filter((t: string) => t?.trim()).join("\n");
      if (!content) return;

      // CASE 1: Main agent sessions (existing behavior)
      if (sessionKey.endsWith(":main")) {
        const slug = sessionKey.slice("agent:".length, -":main".length);
        if (!slug) return;

        const targetChannel = slug === "main" ? "main" : slug;

        await store.storeMessage({
          channel: targetChannel,
          type: "chat",
          content,
          role: "assistant",
          timestamp: Date.now(),
          metadata: { mirrored: true, runId: event?.runId, sessionKey },
        });

        try { broadcast({ type: "vantage.new", ts: Date.now() }); } catch { /* ignore */ }
        const bcast = getBroadcast();
        if (bcast) {
          try { bcast("vantage.event", { type: "vantage.new", ts: Date.now() }); } catch { /* ignore */ }
        }
        return;
      }

      // CASE 2: Subagent sessions → route to task activity
      if (sessionKey.includes(":subagent:")) {
        const { getTaskIdForSession, getSubagentBinding } = await import("./src/subagent-hooks.js");
        const taskId = getTaskIdForSession(sessionKey);
        
        if (!taskId) {
          // No task binding — skip (shouldn't happen with our binding logic)
          return;
        }

        // Store as task activity
        await store.storeTaskActivity({
          taskId,
          sessionKey,
          content,
        });

        // Get channel for this subagent
        const binding = getSubagentBinding(sessionKey);
        const channel = binding?.channelSlug ?? "main";

        // Broadcast task_activity event
        try {
          broadcast({
            type: "task_activity",
            channel,
            timestamp: Date.now(),
            payload: {
              taskId,
              sessionKey,
              content,
              streaming: true,
            },
          });
        } catch { /* ignore */ }

        const bcast = getBroadcast();
        if (bcast) {
          try {
            bcast("vantage.event", {
              type: "task_activity",
              taskId,
              channel,
              ts: Date.now(),
            });
          } catch { /* ignore */ }
        }
      }
    } catch (err: any) {
      console.error("[vantage] llm_output handler failed:", err?.message ?? err);
    }
  },
);
```

---

## `rpc.ts` Changes

### 1. New RPC Method: `vantage.task.activity`

Add a dedicated method for fetching task activity:

```typescript
api.registerGatewayMethod("vantage.task.activity", async ({ params, respond }: any) => {
  const { taskId, since = 0, limit = 100 } = params ?? {};
  
  if (!taskId) {
    return respond(false, undefined, { 
      code: "INVALID_REQUEST", 
      message: "taskId is required" 
    });
  }

  try {
    const activity = await store.getTaskActivity(taskId, { since, limit });
    const { getTaskIdForSession, listActiveBindings } = await import("./subagent-hooks.js");
    
    // Check if task has an active subagent
    const isLive = listActiveBindings().some(b => b.taskId === taskId);
    
    respond(true, { 
      taskId,
      activity,
      isLive,
      serverTime: Date.now(),
    });
  } catch (err: any) {
    respond(false, undefined, { 
      code: "INTERNAL_ERROR", 
      message: err?.message ?? "activity fetch failed" 
    });
  }
});
```

### 2. Extend `vantage.poll` to Include Task Activity

Update the poll method to optionally include recent task activity:

```typescript
api.registerGatewayMethod("vantage.poll", async ({ params, respond, context }: any) => {
  captureBroadcast(context);
  try {
    const { channels, since, types, limit, includeTaskActivity = false, taskIds } = params ?? {};
    
    const messages = await store.getMessagesSince(since ?? 0, {
      channels,
      types,
      limit: limit ?? 100,
    });

    let taskActivity: Record<string, Array<{ id: string; content: string; createdAt: number }>> | undefined;
    
    if (includeTaskActivity && taskIds?.length) {
      taskActivity = {};
      for (const taskId of taskIds) {
        taskActivity[taskId] = await store.getTaskActivity(taskId, { since: since ?? 0, limit: 50 });
      }
    }

    respond(true, { 
      messages, 
      taskActivity,  // ← NEW: map of taskId → activity chunks
      serverTime: Date.now() 
    });
  } catch (err: any) {
    respond(false, undefined, { code: "INTERNAL_ERROR", message: err?.message ?? "poll failed" });
  }
});
```

### 3. Update `vantage.tasks.list` Response

The store changes already handle this, but ensure the response type is correct:

```typescript
api.registerGatewayMethod("vantage.tasks.list", async ({ params, respond }: any) => {
  try {
    const tasks = await store.listTasks(params ?? {});
    respond(true, { 
      tasks,  // Now includes isLive, lastActivityAt, activityCount
    });
  } catch (err: any) {
    respond(false, undefined, { code: "INTERNAL_ERROR", message: err?.message ?? "list failed" });
  }
});
```

---

## Wire Format Summary

### What the Client Receives

#### Via SSE (`/vantage/events`)

When a subagent produces output:

```json
{
  "type": "task_activity",
  "channel": "vantage-oc",
  "timestamp": 1710132456789,
  "payload": {
    "taskId": "agent:vantage-oc:subagent:abc123",
    "sessionKey": "agent:vantage-oc:subagent:abc123",
    "content": "Reading the source files to understand...",
    "streaming": true
  }
}
```

#### Via `vantage.poll` (with `includeTaskActivity: true`)

```json
{
  "messages": [...],
  "taskActivity": {
    "agent:vantage-oc:subagent:abc123": [
      { "id": "uuid1", "content": "Chunk 1...", "createdAt": 1710132456000 },
      { "id": "uuid2", "content": "Chunk 2...", "createdAt": 1710132457000 }
    ]
  },
  "serverTime": 1710132458000
}
```

#### Via `vantage.task.activity`

```json
{
  "taskId": "agent:vantage-oc:subagent:abc123",
  "activity": [
    { "id": "uuid1", "content": "Chunk 1...", "createdAt": 1710132456000 },
    { "id": "uuid2", "content": "Chunk 2...", "createdAt": 1710132457000 }
  ],
  "isLive": true,
  "serverTime": 1710132458000
}
```

#### Via `vantage.tasks.list`

```json
{
  "tasks": [
    {
      "taskId": "agent:vantage-oc:subagent:abc123",
      "name": "Architect spec for streaming",
      "status": "running",
      "isLive": true,
      "lastActivityAt": 1710132457000,
      "activityCount": 47,
      "createdAt": 1710132400000
    }
  ]
}
```

---

## Granularity Notes

LLM output arrives in small chunks (sometimes token-by-token). The `llm_output` hook receives coalesced chunks per turn (via `event.assistantTexts`), which is already reasonable granularity.

If DB write volume becomes a concern, consider:

1. **Debouncing in the hook:** Accumulate chunks in a Map, flush after 500ms idle or 1KB accumulated
2. **Memory-only ring buffer:** Skip DB entirely, keep last N chunks per task in memory

For V1, direct writes are fine — SQLite WAL handles concurrent writes well, and task activity is ephemeral anyway.

---

## Client Integration Notes

### Swift Client Changes

1. **TaskDetailView:** Add activity feed section that auto-updates when `isLive: true`
2. **WebSocket listener:** Handle `task_activity` message type
3. **Poll strategy:** When viewing a live task, poll `vantage.task.activity` every 500ms OR subscribe to SSE
4. **Display:** Show activity as streaming text, append new chunks, auto-scroll

### UI State Machine

```
Task spawned (task_spawn message)
    ↓
isLive: false, status: pending (waiting for activity)
    ↓
First activity chunk received
    ↓
isLive: true, status: running (show streaming indicator)
    ↓
Activity keeps streaming (append chunks)
    ↓
Task completes (task_complete message)
    ↓
isLive: false, status: completed (activity frozen, show summary)
```

---

## File Modification Summary

| File | Changes |
|------|---------|
| `src/types.ts` | Add `TaskActivityChunk`, `TaskActivityPayload`, update `MessageType`, `PayloadForType`, `TaskInfo` |
| `src/store.ts` | Add `task_activity` schema, `storeTaskActivity`, `getTaskActivity`, `getTaskActivityCount`, `getLastActivityTimestamp`, update `listTasks` |
| `src/subagent-hooks.ts` | Populate `taskId` in binding, add `getTaskIdForSession` export |
| `index.ts` | Extend `llm_output` hook to capture subagent output |
| `src/rpc.ts` | Add `vantage.task.activity` method, extend `vantage.poll` with `includeTaskActivity` option |

---

## Testing Checklist

1. [ ] Spawn a subagent from vantage-oc channel
2. [ ] Verify `SubagentBinding.taskId` is populated
3. [ ] Verify subagent LLM output appears in `task_activity` table
4. [ ] Call `vantage.task.activity` and verify response
5. [ ] Call `vantage.tasks.list` and verify `isLive`, `lastActivityAt`, `activityCount`
6. [ ] Verify SSE broadcasts `task_activity` events
7. [ ] Complete task, verify `isLive` becomes false
8. [ ] Delete task, verify activity is cascade-deleted

---

## Open Questions (for Aaron)

1. **Activity retention:** Should we auto-purge activity chunks when task completes? Or keep for audit?
2. **Activity size limit:** Cap per-task at N chunks or N MB?
3. **Streaming to main channel:** Should subagent activity also be mirrored to the channel message history, or just the task-specific feed?
