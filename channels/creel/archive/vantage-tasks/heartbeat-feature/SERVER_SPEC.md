# Heartbeat Feature — Server-Side Spec

## Overview

Expose gateway heartbeat schedule and history through the VantageOC plugin so the Vantage client can display:
- Last 2 heartbeats (when they fired, success/failure, tasks completed)
- Next heartbeat (absolute + relative time)
- Next 5 upcoming heartbeat times

---

## 1. Architecture

### Data Sources

| Data | Source | Access Method |
|------|--------|---------------|
| Heartbeat config (interval, active hours) | Gateway config | `context.config` in RPC handlers |
| Heartbeat history (when they actually fired) | `messages` table, `type = "heartbeat"` | `store.getMessagesSince()` or new query |
| Task completions per window | `tasks` table with `completed_at` timestamps | New store query |

### Key Insight

The gateway's heartbeat mechanism fires an event that gets injected into the main session. **Currently, there is NO Vantage hook capturing these events.** 

Two options:
1. **Query-based (recommended)**: Compute schedule from config + query message history for `type: "heartbeat"` messages
2. **Hook-based**: Add `api.on("heartbeat_fired", ...)` hook (requires SDK support verification)

**Recommendation**: Use the query-based approach. The heartbeat config gives us the schedule rules, and any stored messages of `type: "heartbeat"` give us the history.

### NEEDS VERIFICATION

Does the gateway actually store a message with `type: "heartbeat"` when the heartbeat fires? Check:
```sql
SELECT * FROM messages WHERE type = 'heartbeat' ORDER BY timestamp DESC LIMIT 5;
```

If no heartbeat messages exist, we may need to:
1. Add a hook in `subagent-hooks.ts` or a new file to capture heartbeat events
2. Or rely purely on config-based schedule computation (no history available)

---

## 2. Heartbeat History

### Option A: Query Existing Messages (if they exist)

```typescript
async getRecentHeartbeats(limit: number = 2): Promise<HeartbeatRecord[]> {
  const rows = this.db.prepare(`
    SELECT id, channel, content, timestamp, metadata
    FROM messages 
    WHERE type = 'heartbeat'
    ORDER BY timestamp DESC 
    LIMIT ?
  `).all(limit);
  
  return rows.map(r => ({
    id: r.id,
    timestamp: r.timestamp,
    success: parseHeartbeatSuccess(r.content, r.metadata),
    tasksCompleted: 0, // computed separately
  }));
}
```

### Option B: Track Heartbeats Ourselves (if no existing messages)

If heartbeat events aren't being stored, add a new hook in a `heartbeat-hooks.ts` file:

```typescript
// In register() function
api.on("heartbeat", async (event) => {
  await store.storeMessage({
    channel: "main",
    type: "heartbeat",
    content: JSON.stringify({ status: "fired", event }),
    role: "system",
    timestamp: Date.now(),
    metadata: { success: true },
  });
});
```

**NEEDS VERIFICATION**: Does `api.on("heartbeat", ...)` exist as an SDK hook?

---

## 3. Task Completion Counting

Count tasks completed between two heartbeat timestamps:

```typescript
async getTasksCompletedInWindow(startTs: number, endTs: number): Promise<number> {
  const result = this.db.prepare(`
    SELECT COUNT(*) as count
    FROM tasks
    WHERE completed_at IS NOT NULL
      AND completed_at >= ?
      AND completed_at < ?
  `).get(startTs, endTs) as { count: number };
  
  return result.count;
}
```

For the "last heartbeat window", we need:
- `startTs` = timestamp of the heartbeat that just fired
- `endTs` = timestamp of the previous heartbeat (or current time if computing "since last")

---

## 4. Schedule Computation Algorithm

Given config:
```json
{
  "every": "4h",
  "activeHours": { "start": "08:00", "end": "22:00", "timezone": "America/Los_Angeles" }
}
```

### Algorithm: Next N Heartbeats

```typescript
import { DateTime } from "luxon"; // or manual timezone handling

interface HeartbeatConfig {
  every: string; // e.g., "4h", "30m"
  activeHours: {
    start: string; // "HH:mm"
    end: string;   // "HH:mm"
    timezone: string;
  };
}

function parseInterval(every: string): number {
  const match = every.match(/^(\d+)(h|m|s)$/);
  if (!match) throw new Error(`Invalid interval: ${every}`);
  const [, value, unit] = match;
  const ms = { h: 3600000, m: 60000, s: 1000 }[unit];
  return parseInt(value) * ms;
}

function getNextHeartbeats(config: HeartbeatConfig, count: number): number[] {
  const intervalMs = parseInterval(config.every);
  const tz = config.activeHours.timezone;
  const [startHour, startMin] = config.activeHours.start.split(":").map(Number);
  const [endHour, endMin] = config.activeHours.end.split(":").map(Number);
  
  const results: number[] = [];
  let now = DateTime.now().setZone(tz);
  
  // Find the next valid heartbeat time
  let candidate = now;
  
  while (results.length < count) {
    // Move to next interval boundary
    const dayStart = candidate.startOf("day").plus({ hours: startHour, minutes: startMin });
    const dayEnd = candidate.startOf("day").plus({ hours: endHour, minutes: endMin });
    
    // If before active hours, jump to start
    if (candidate < dayStart) {
      candidate = dayStart;
    }
    // If after active hours, jump to next day's start
    else if (candidate >= dayEnd) {
      candidate = dayStart.plus({ days: 1 });
      continue;
    }
    
    // Calculate next interval within active hours
    const msSinceDayStart = candidate.diff(dayStart).as("milliseconds");
    const intervalsElapsed = Math.floor(msSinceDayStart / intervalMs);
    const nextIntervalTime = dayStart.plus({ milliseconds: (intervalsElapsed + 1) * intervalMs });
    
    // If next interval is still within active hours, add it
    if (nextIntervalTime < dayEnd) {
      results.push(nextIntervalTime.toMillis());
      candidate = nextIntervalTime;
    } else {
      // Jump to next day's start
      candidate = dayStart.plus({ days: 1 });
    }
  }
  
  return results;
}
```

### Edge Cases

1. **Current time is within active hours**: Next heartbeat = next interval boundary
2. **Current time is before active hours**: Next heartbeat = start of active hours
3. **Current time is after active hours**: Next heartbeat = start of next day's active hours
4. **Interval doesn't divide evenly into active hours**: Last heartbeat of day may be partial interval from previous

---

## 5. RPC Method Design

### Option A: Extend `vantage.heartbeat.status` (Recommended)

The current method is a misnomer — it returns health checks, not heartbeat schedule. Extend it to include schedule data:

```typescript
api.registerGatewayMethod("vantage.heartbeat.status", async ({ respond, context }: any) => {
  try {
    const healthy = store.isHealthy();
    const heartbeatConfig = context?.config?.agents?.defaults?.heartbeat;
    
    // Get last 2 heartbeats from message history
    const recentHeartbeats = await store.getRecentHeartbeats(2);
    
    // Compute tasks completed per heartbeat window
    for (let i = 0; i < recentHeartbeats.length; i++) {
      const hb = recentHeartbeats[i];
      const windowEnd = i === 0 ? Date.now() : recentHeartbeats[i - 1].timestamp;
      hb.tasksCompleted = await store.getTasksCompletedInWindow(hb.timestamp, windowEnd);
    }
    
    // Compute next heartbeats
    const nextHeartbeats = heartbeatConfig 
      ? getNextHeartbeats(heartbeatConfig, 5)
      : [];
    
    respond(true, {
      // Existing health check data
      status: healthy ? "ok" : "error",
      uptime: process.uptime() * 1000,
      checks: [
        { name: "database", status: healthy ? "ok" : "error", lastRun: Date.now() },
      ],
      
      // NEW: Schedule data
      schedule: heartbeatConfig ? {
        config: {
          every: heartbeatConfig.every,
          activeHours: heartbeatConfig.activeHours,
        },
        recent: recentHeartbeats.map(hb => ({
          timestamp: hb.timestamp,
          success: hb.success,
          tasksCompleted: hb.tasksCompleted,
        })),
        upcoming: nextHeartbeats,
        next: nextHeartbeats[0] ?? null,
      } : null,
      
      serverTime: Date.now(),
    });
  } catch (err: any) {
    respond(false, undefined, { code: "INTERNAL_ERROR", message: err?.message ?? "status failed" });
  }
});
```

### Option B: New `vantage.heartbeat.schedule` Method

Keep health checks separate from schedule data:

```typescript
api.registerGatewayMethod("vantage.heartbeat.schedule", async ({ respond, context }: any) => {
  // ... schedule-only response
});
```

**Recommendation**: Option A (extend existing). The current `vantage.heartbeat.status` name already implies heartbeat information — clients calling it expect heartbeat data. Adding schedule info makes sense.

---

## 6. New Types (types.ts)

```typescript
// ── Heartbeat Schedule Types ────────────────────────────────────────────────

/** Configuration for heartbeat scheduling */
export interface HeartbeatScheduleConfig {
  every: string;  // e.g., "4h"
  activeHours: {
    start: string;    // "HH:mm"
    end: string;      // "HH:mm"
    timezone: string; // e.g., "America/Los_Angeles"
  };
}

/** A single heartbeat occurrence (past) */
export interface HeartbeatOccurrence {
  timestamp: number;
  success: boolean;
  tasksCompleted: number;
}

/** Full heartbeat schedule data */
export interface HeartbeatSchedule {
  config: HeartbeatScheduleConfig;
  recent: HeartbeatOccurrence[];  // Last N heartbeats (most recent first)
  upcoming: number[];              // Next N heartbeat timestamps
  next: number | null;             // Next heartbeat timestamp (convenience)
}

/** Extended heartbeat status response (replaces current) */
export interface HeartbeatStatusResponse {
  status: "ok" | "degraded" | "error";
  uptime: number;
  checks: HeartbeatCheck[];
  schedule: HeartbeatSchedule | null;  // null if no heartbeat config
  serverTime: number;
}
```

---

## 7. Store Methods to Add (store.ts)

```typescript
// ── Heartbeat Queries ───────────────────────────────────────────────────────

async getRecentHeartbeats(limit: number = 2): Promise<Array<{
  id: string;
  timestamp: number;
  success: boolean;
  metadata?: Record<string, unknown>;
}>> {
  const rows = this.db.prepare(`
    SELECT id, timestamp, content, metadata
    FROM messages 
    WHERE type = 'heartbeat'
    ORDER BY timestamp DESC 
    LIMIT ?
  `).all(limit) as Array<{
    id: string;
    timestamp: number;
    content: string;
    metadata: string | null;
  }>;
  
  return rows.map(r => {
    const meta = r.metadata ? JSON.parse(r.metadata) : {};
    return {
      id: r.id,
      timestamp: r.timestamp,
      success: meta.success !== false, // default to true if not specified
      metadata: meta,
    };
  });
}

async getTasksCompletedInWindow(startTs: number, endTs: number): Promise<number> {
  const result = this.db.prepare(`
    SELECT COUNT(*) as count
    FROM tasks
    WHERE completed_at IS NOT NULL
      AND completed_at >= ?
      AND completed_at < ?
  `).get(startTs, endTs) as { count: number };
  
  return result.count;
}
```

---

## 8. Implementation Checklist

### Phase 1: Verify Data Availability
- [ ] Check if `messages` table has `type = 'heartbeat'` entries
- [ ] Check if `api.on("heartbeat", ...)` hook exists in SDK
- [ ] Verify `context.config.agents.defaults.heartbeat` structure

### Phase 2: Store Layer
- [ ] Add `getRecentHeartbeats(limit)` method to `store.ts`
- [ ] Add `getTasksCompletedInWindow(start, end)` method to `store.ts`
- [ ] Test both methods with actual data

### Phase 3: Schedule Computation
- [ ] Create `src/heartbeat-schedule.ts` with `getNextHeartbeats()` function
- [ ] Add `parseInterval()` helper
- [ ] Handle timezone conversion (decide: luxon vs manual)
- [ ] Unit test edge cases (before/after active hours, day boundaries)

### Phase 4: Types
- [ ] Add `HeartbeatScheduleConfig` interface to `types.ts`
- [ ] Add `HeartbeatOccurrence` interface to `types.ts`
- [ ] Add `HeartbeatSchedule` interface to `types.ts`
- [ ] Update `HeartbeatStatusResponse` type (or add new one)

### Phase 5: RPC Method
- [ ] Update `vantage.heartbeat.status` handler in `rpc.ts`
- [ ] Import schedule computation function
- [ ] Wire up store queries
- [ ] Add `serverTime` field for client clock sync

### Phase 6: Hook (if needed)
- [ ] If no heartbeat messages exist, add `api.on("heartbeat", ...)` hook
- [ ] Store heartbeat events to `messages` table
- [ ] Test by waiting for next heartbeat or triggering manually

### Phase 7: Build & Test
- [ ] `npm run build` — verify no type errors
- [ ] Test RPC method via WebSocket
- [ ] Verify response shape matches spec

---

## Dependencies

| Package | Purpose | Required? |
|---------|---------|-----------|
| `luxon` | Timezone-aware date handling | **Recommended** — avoids DST bugs |
| Built-in `Date` | Basic timestamps | Works but timezone handling is error-prone |

**Recommendation**: Add `luxon` to dependencies. The active hours config uses timezone names ("America/Los_Angeles"), and correctly handling DST transitions requires proper timezone library support.

```bash
cd ~/.openclaw/extensions/vantage
npm install luxon
npm install -D @types/luxon
```

---

## Open Questions

1. **Does `type = 'heartbeat'` already exist in messages table?** — Need to query DB to verify
2. **What hook fires when gateway sends heartbeat?** — May need to check OpenClaw SDK docs or source
3. **How is success/failure determined for a heartbeat?** — Agent responds to HEARTBEAT.md; is there an error path?
4. **Should we track "skipped" heartbeats?** — When heartbeat would fire but it's outside active hours

---

## Response Shape (Final)

```json
{
  "status": "ok",
  "uptime": 3847293,
  "checks": [
    { "name": "database", "status": "ok", "lastRun": 1710385200000 }
  ],
  "schedule": {
    "config": {
      "every": "4h",
      "activeHours": {
        "start": "08:00",
        "end": "22:00",
        "timezone": "America/Los_Angeles"
      }
    },
    "recent": [
      { "timestamp": 1710381600000, "success": true, "tasksCompleted": 3 },
      { "timestamp": 1710367200000, "success": true, "tasksCompleted": 1 }
    ],
    "upcoming": [
      1710396000000,
      1710410400000,
      1710424800000,
      1710482400000,
      1710496800000
    ],
    "next": 1710396000000
  },
  "serverTime": 1710385247832
}
```
