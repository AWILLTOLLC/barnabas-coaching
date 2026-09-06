# Heartbeat Schedule Feature — Implementation Notes

**Date:** 2026-03-14
**Status:** Implemented, build clean

---

## Files Changed

### New Files

1. **`src/heartbeat-schedule.ts`**
   - `parseIntervalMs(every: string)` — parse "4h", "30m", etc. to milliseconds
   - `getNextHeartbeats(config, count, fromMs?)` — compute next N heartbeat timestamps
   - `readHeartbeatConfig()` — read heartbeat config from `openclaw.json`
   - Uses `Intl.DateTimeFormat` for timezone handling (no luxon dependency)

2. **`src/heartbeat-capture.ts`**
   - Polls the gateway's `last-heartbeat` RPC method every 5 minutes
   - Stores new heartbeat events in the `messages` table (type = "heartbeat")
   - Started on `gateway_start`, stopped on `gateway_stop`
   - Creates its own WS connection (replicates loopback.ts pattern since that file was not to be modified)

### Modified Files

3. **`src/types.ts`**
   - Added `HeartbeatScheduleConfig` interface
   - Added `HeartbeatOccurrence` interface
   - Added `HeartbeatSchedule` interface
   - Added `HeartbeatStatusExtended` interface

4. **`src/store.ts`**
   - Added `storeHeartbeatEvent(event)` — stores heartbeat as message with type="heartbeat"
   - Added `getRecentHeartbeats(limit)` — retrieves recent heartbeat messages
   - Added `getTasksCompletedInWindow(startTs, endTs)` — counts tasks completed in window

5. **`src/rpc.ts`**
   - Updated `vantage.heartbeat.status` handler to include:
     - `schedule.config` — heartbeat config (every, activeHours)
     - `schedule.recent` — last 2 heartbeats with tasksCompleted counts
     - `schedule.upcoming` — next 5 heartbeat timestamps
     - `schedule.next` — convenience field for next heartbeat
     - `serverTime` — current server epoch ms

6. **`index.ts`**
   - Added import for `startHeartbeatCapture`, `stopHeartbeatCapture`
   - Added `gateway_start` hook to start heartbeat capture
   - Added `gateway_stop` hook to stop heartbeat capture

---

## Response Shape

The updated `vantage.heartbeat.status` response:

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

---

## Deviations from Spec

1. **Timezone handling**: Used `Intl.DateTimeFormat` with custom epoch conversion instead of luxon. The spec recommended luxon but the task explicitly said "no luxon in dependencies."

2. **Heartbeat capture approach**: The spec mentioned checking for a `heartbeat` SDK hook, which doesn't exist. Implemented polling approach as specified in the task instructions.

3. **WS connection duplication**: Had to replicate the WS connection pattern from `loopback.ts` in `heartbeat-capture.ts` since we were told not to modify `loopback.ts`.

---

## Testing Notes

- Build compiles clean (`npm run build`)
- Gateway restart NOT performed (per instructions)
- To test: call `vantage.heartbeat.status` RPC method after gateway restart

---

## Open Items

1. **Initial heartbeat history**: Until heartbeats actually fire and get captured, `schedule.recent` will be empty.

2. **Polling efficiency**: Heartbeat capture polls every 5 minutes. If heartbeats fire more frequently than that, we might miss some. However, the spec indicates typical intervals are 4h, so 5-minute polling is sufficient.

3. **DST handling**: The timezone conversion logic handles basic cases but may have edge cases around DST transitions. Would benefit from real-world testing in PST during DST changes.
