# VantageOC Client — Subagent Activity Streaming
## Feature Spec for Swift Client Implementation

**Date:** 2026-03-11  
**Status:** Server implementation complete, build verified clean.

---

## Overview

Subagent tasks now stream real-time LLM output back to the client while a task is running. Previously, the Tasks pane showed a task appear and then go silent until completion. Now the server captures the subagent's LLM output chunk-by-chunk and exposes it via two mechanisms:

1. **SSE push** — a `task_activity` event fires on the SSE channel each time a chunk arrives
2. **Poll pull** — `vantage.poll` and `vantage.task.activity` can return activity on demand

The `TaskInfo` model now includes `isLive`, `lastActivityAt`, and `activityCount` so the client knows whether a task is actively streaming without fetching the activity itself.

---

## Updated Data Models

### `TaskInfo` (extended)

```swift
struct TaskInfo: Codable {
    let taskId: String
    let sessionKey: String?
    let name: String
    let description: String?
    let channel: String?
    let status: TaskStatus          // "pending" | "running" | "completed" | "failed"
    let progress: Double?
    let createdAt: Int64            // Unix ms
    let completedAt: Int64?
    let isLive: Bool?               // true = subagent currently streaming output
    let lastActivityAt: Int64?      // Unix ms of most recent activity chunk
    let activityCount: Int?         // total chunks stored
}
```

### `TaskActivityChunk` (new)

```swift
struct TaskActivityChunk: Codable {
    let id: String
    let taskId: String
    let sessionKey: String
    let content: String
    let createdAt: Int64            // Unix ms
}
```

### `TaskActivityPayload` (SSE event payload)

```swift
struct TaskActivityPayload: Codable {
    let taskId: String
    let sessionKey: String
    let content: String
    let streaming: Bool             // always true for live chunks
    let chunkIndex: Int?
}
```

---

## RPC Methods

### `vantage.task.activity` — Fetch activity for a task

**Request:**
```json
{
  "type": "req",
  "id": "<unique>",
  "method": "vantage.task.activity",
  "params": {
    "taskId": "forge-smoke-1234567890",
    "since": 0,
    "limit": 100
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `taskId` | string | ✅ | The task to fetch activity for |
| `since` | number | ❌ | Unix ms cursor — only return chunks after this timestamp. Default: 0 (all) |
| `limit` | number | ❌ | Max chunks to return. Default: 100 |

**Response (ok):**
```json
{
  "type": "res",
  "id": "<same>",
  "ok": true,
  "payload": {
    "taskId": "forge-smoke-1234567890",
    "activity": [
      {
        "id": "abc123",
        "taskId": "forge-smoke-1234567890",
        "sessionKey": "agent:vantage-oc:subagent:fe2eae36-...",
        "content": "Analyzing the input data...",
        "createdAt": 1773204500000
      }
    ],
    "isLive": true,
    "serverTime": 1773204501234
  }
}
```

**Response (error):**
```json
{ "ok": false, "error": { "code": "INVALID_REQUEST", "message": "taskId is required" } }
```

---

### `vantage.poll` — Extended with task activity

Existing poll method, extended with two new optional params.

**Request additions:**
```json
{
  "method": "vantage.poll",
  "params": {
    "since": 1773200000000,
    "includeTaskActivity": true,
    "taskIds": ["forge-smoke-1234", "haiku-forge-5678"]
  }
}
```

| New Param | Type | Description |
|-----------|------|-------------|
| `includeTaskActivity` | boolean | If true, include activity for the requested taskIds |
| `taskIds` | string[] | Which tasks to fetch activity for (only used when includeTaskActivity is true) |

**Response additions:**
```json
{
  "payload": {
    "messages": [...],
    "taskActivity": {
      "forge-smoke-1234": [
        { "id": "abc", "content": "Starting analysis...", "createdAt": 1773204500000 }
      ],
      "haiku-forge-5678": []
    },
    "serverTime": 1773204501234
  }
}
```

`taskActivity` is a dictionary keyed by taskId. Each value is an array of activity chunks (same shape as `TaskActivityChunk`, minus `taskId` which is the key).

---

### `vantage.tasks.list` — Updated response

No param changes. The response now includes the new fields on each task:

```json
{
  "tasks": [
    {
      "taskId": "forge-smoke-1234",
      "name": "Smoke Test Task",
      "status": "running",
      "channel": "vantage-oc",
      "isLive": true,
      "lastActivityAt": 1773204500000,
      "activityCount": 12
    }
  ]
}
```

Use `isLive: true` to show a live indicator on the task row. Use `activityCount > 0` to know whether there's history worth fetching.

---

## SSE Event: `task_activity`

When a subagent LLM output chunk arrives, the server broadcasts a `task_activity` event over SSE.

**Event shape** (same envelope format as other SSE events):
```json
{
  "event": "task_activity",
  "payload": {
    "taskId": "forge-smoke-1234",
    "sessionKey": "agent:vantage-oc:subagent:fe2eae36-...",
    "content": "Computing the result...",
    "streaming": true,
    "chunkIndex": 7
  }
}
```

If the client has an active SSE connection, this is the lowest-latency path — append the chunk to the in-memory activity buffer for that task immediately without polling.

---

## Recommended Client Implementation

### Task row in Tasks pane

- If `isLive == true`: show a pulsing indicator (e.g. green dot, activity spinner)
- If `activityCount > 0 && !isLive`: show a "view log" affordance
- If `isLive == false && activityCount == 0`: no indicator

### Activity view (tapped from task row)

1. On open: call `vantage.task.activity` with `since: 0` to load full history
2. Store `lastActivityAt` from the most recent chunk as your cursor
3. If `isLive` is true: subscribe to SSE `task_activity` events filtered by `taskId`, appending chunks to the view as they arrive
4. On SSE disconnect or fallback: poll `vantage.task.activity` with `since: <cursor>` every ~2s while `isLive`
5. On `vantage.tasks.list` update where `isLive` flips false: stop polling, mark stream closed

### Poll integration

If you're already polling `vantage.poll` for message updates, you can piggyback:

```json
{
  "method": "vantage.poll",
  "params": {
    "since": <cursor>,
    "includeTaskActivity": true,
    "taskIds": ["<currently-visible-task-ids>"]
  }
}
```

Only pass `taskIds` for tasks currently visible to the user — don't fetch activity for all tasks.

---

## Cursor Strategy

Activity chunks have `createdAt` (Unix ms). Use this as your poll cursor:

```swift
var activityCursor: Int64 = 0  // per task

// On fetch response:
if let last = activity.last {
    activityCursor = last.createdAt
}

// Next poll:
params["since"] = activityCursor
```

The server returns chunks where `createdAt > since`, so you won't get duplicates.

---

## What Changed Server-Side (for context only)

- New SQLite table: `task_activity` (id, task_id, session_key, content, created_at)
- `llm_output` hook now captures subagent sessions (`:subagent:` in session key) and writes chunks to `task_activity`
- `SubagentBinding` now tracks `taskId`, populated from spawn event metadata
- New RPC: `vantage.task.activity`
- Extended: `vantage.poll`, `vantage.tasks.list`

**No gateway restart is required on the client side.** The server changes are live after the next gateway restart (pending Aaron's approval).
