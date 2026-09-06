# Heartbeat Feature — Client-Side Spec

## Overview

Display heartbeat schedule and history in the Vantage macOS/iOS client, giving the operator visibility into:
- When heartbeats last ran and their outcomes
- When the next heartbeat will fire
- The upcoming heartbeat schedule

---

## 1. UI Design

### Heartbeat Panel Location

Add a "Heartbeat" section to the system status view (alongside existing health checks). This could be:
- A collapsible card in the main dashboard
- Part of the settings/status screen
- A dedicated tab in system monitoring

### Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ♥ Heartbeat                                    [Healthy ●] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NEXT HEARTBEAT                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⏱ 2:00 PM PST                        in 47 minutes │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  RECENT                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ✓ 10:00 AM                  3 tasks    2 hours ago │   │
│  │  ✓ 6:00 AM                   1 task     6 hours ago │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  SCHEDULE (08:00–22:00 PST, every 4h)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Today     2:00 PM  •  6:00 PM  •  10:00 PM         │   │
│  │  Tomorrow  8:00 AM  •  12:00 PM                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Compact Mode (Widget / Sidebar)

For space-constrained views:

```
┌──────────────────────────────────┐
│  ♥ Next: 2:00 PM (in 47 min)    │
│     Last: ✓ 10:00 AM (3 tasks)  │
└──────────────────────────────────┘
```

---

## 2. Data Model (Swift)

```swift
import Foundation

// MARK: - RPC Response

struct HeartbeatStatusResponse: Codable {
    let status: HealthStatus
    let uptime: Int
    let checks: [HealthCheck]
    let schedule: HeartbeatSchedule?
    let serverTime: Int64
    
    enum HealthStatus: String, Codable {
        case ok, degraded, error
    }
    
    struct HealthCheck: Codable {
        let name: String
        let status: HealthStatus
        let lastRun: Int64
    }
}

struct HeartbeatSchedule: Codable {
    let config: HeartbeatConfig
    let recent: [HeartbeatOccurrence]
    let upcoming: [Int64]
    let next: Int64?
}

struct HeartbeatConfig: Codable {
    let every: String
    let activeHours: ActiveHours
    
    struct ActiveHours: Codable {
        let start: String  // "HH:mm"
        let end: String    // "HH:mm"
        let timezone: String
    }
}

struct HeartbeatOccurrence: Codable {
    let timestamp: Int64
    let success: Bool
    let tasksCompleted: Int
}

// MARK: - View Model

@Observable
final class HeartbeatViewModel {
    private(set) var schedule: HeartbeatSchedule?
    private(set) var lastUpdated: Date?
    private(set) var error: Error?
    private(set) var isLoading = false
    
    var nextHeartbeat: Date? {
        schedule?.next.map { Date(timeIntervalSince1970: TimeInterval($0) / 1000) }
    }
    
    var recentHeartbeats: [HeartbeatDisplayItem] {
        (schedule?.recent ?? []).map { occurrence in
            HeartbeatDisplayItem(
                timestamp: Date(timeIntervalSince1970: TimeInterval(occurrence.timestamp) / 1000),
                success: occurrence.success,
                tasksCompleted: occurrence.tasksCompleted
            )
        }
    }
    
    var upcomingHeartbeats: [Date] {
        (schedule?.upcoming ?? []).map {
            Date(timeIntervalSince1970: TimeInterval($0) / 1000)
        }
    }
    
    var scheduleDescription: String? {
        guard let config = schedule?.config else { return nil }
        let interval = config.every
        let start = config.activeHours.start
        let end = config.activeHours.end
        let tz = config.activeHours.timezone.components(separatedBy: "/").last ?? config.activeHours.timezone
        return "\(start)–\(end) \(tz), every \(interval)"
    }
    
    func refresh() async {
        // Implementation in section 3
    }
}

struct HeartbeatDisplayItem: Identifiable {
    let id = UUID()
    let timestamp: Date
    let success: Bool
    let tasksCompleted: Int
    
    var relativeTime: String {
        timestamp.formatted(.relative(presentation: .named))
    }
    
    var absoluteTime: String {
        timestamp.formatted(date: .omitted, time: .shortened)
    }
    
    var taskLabel: String {
        switch tasksCompleted {
        case 0: return "no tasks"
        case 1: return "1 task"
        default: return "\(tasksCompleted) tasks"
        }
    }
}
```

---

## 3. RPC Call

### Method

```
vantage.heartbeat.status
```

### Parameters

None required. Future enhancement: add `{ recentCount: Int, upcomingCount: Int }` params.

### Request

```swift
func fetchHeartbeatStatus() async throws -> HeartbeatStatusResponse {
    let request = RPCRequest(
        method: "vantage.heartbeat.status",
        params: [:]  // No params needed
    )
    
    return try await rpcClient.call(request)
}
```

### Response Shape

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

### Null Schedule

If `schedule` is `null`, the gateway has no heartbeat configuration. Display:
- "Heartbeat not configured" message
- Or hide the heartbeat panel entirely

---

## 4. Refresh Strategy

### Initial Load

Fetch immediately when the heartbeat view becomes visible.

### Polling

| Situation | Refresh Interval |
|-----------|------------------|
| Panel visible, app in foreground | Every 60 seconds |
| Panel visible, next heartbeat < 5 minutes | Every 30 seconds |
| App in background | No polling (wait for foreground) |

### Smart Refresh

Calculate time until next heartbeat. If < 2 minutes, start 15-second polling to capture the transition.

```swift
func scheduleNextRefresh() {
    guard let next = nextHeartbeat else {
        scheduleRefresh(after: 60)
        return
    }
    
    let timeUntilNext = next.timeIntervalSinceNow
    
    switch timeUntilNext {
    case ..<0:
        // Heartbeat should have fired — refresh now to see result
        Task { await refresh() }
    case 0..<120:
        // Within 2 minutes — poll frequently
        scheduleRefresh(after: 15)
    case 120..<300:
        // 2-5 minutes — poll every 30 seconds
        scheduleRefresh(after: 30)
    default:
        // > 5 minutes — standard polling
        scheduleRefresh(after: 60)
    }
}
```

### Push Updates (Future)

If Vantage implements WebSocket push, subscribe to `vantage.event` type `heartbeat_fired` to get instant updates.

---

## 5. State Representations

### Heartbeat Status Colors

| State | Color | Icon | Description |
|-------|-------|------|-------------|
| `ok` | Green (#34C759) | ✓ checkmark.circle.fill | Heartbeat succeeded |
| `missed` | Orange (#FF9500) | ⚠ exclamationmark.triangle.fill | Heartbeat was due but didn't fire |
| `error` | Red (#FF3B30) | ✕ xmark.circle.fill | Heartbeat fired but reported error |
| `upcoming` | Blue (#007AFF) | ⏱ clock.fill | Future heartbeat |
| `pending` | Gray (#8E8E93) | ○ circle | Waiting (within expected window) |

### Panel Header Status

The overall heartbeat health indicator in the panel header:

```swift
var overallStatus: HeartbeatHealth {
    guard let recent = recentHeartbeats.first else {
        return .unknown
    }
    
    if !recent.success {
        return .error
    }
    
    // Check if we missed a heartbeat
    if let expectedInterval = parseInterval(schedule?.config.every),
       Date().timeIntervalSince(recent.timestamp) > expectedInterval * 1.5 {
        return .missed
    }
    
    return .healthy
}

enum HeartbeatHealth {
    case healthy    // Green dot
    case missed     // Orange dot
    case error      // Red dot
    case unknown    // Gray dot
}
```

### Next Heartbeat State

```swift
var nextHeartbeatState: NextHeartbeatState {
    guard let next = nextHeartbeat else {
        return .unknown
    }
    
    let timeUntil = next.timeIntervalSinceNow
    
    switch timeUntil {
    case ..<(-60):
        // More than 1 minute overdue
        return .overdue
    case (-60)..<0:
        // Just passed, likely in progress
        return .inProgress
    case 0..<300:
        // Within 5 minutes
        return .imminent
    default:
        return .scheduled
    }
}

enum NextHeartbeatState {
    case scheduled   // Normal — show time
    case imminent    // < 5 min — emphasize
    case inProgress  // Just fired — show spinner?
    case overdue     // Should have fired — show warning
    case unknown     // No data
}
```

---

## 6. Relative Time Display

### Formatting Rules

| Time Difference | Display |
|-----------------|---------|
| < 1 minute ago | "just now" |
| 1-59 minutes ago | "X minutes ago" |
| 1-23 hours ago | "X hours ago" |
| 1-6 days ago | "X days ago" |
| > 6 days | Date format (Mar 8) |

| Time Until | Display |
|------------|---------|
| < 1 minute | "now" or "< 1 minute" |
| 1-59 minutes | "in X minutes" |
| 1-23 hours | "in X hours" |
| Tomorrow | "tomorrow at HH:mm" |
| > 1 day | Day + time |

### Implementation

```swift
extension Date {
    var heartbeatRelativeString: String {
        let now = Date()
        let interval = self.timeIntervalSince(now)
        
        if interval < 0 {
            // Past
            return self.formatted(.relative(presentation: .named))
        } else {
            // Future
            let minutes = Int(interval / 60)
            let hours = Int(interval / 3600)
            
            switch interval {
            case ..<60:
                return "in < 1 minute"
            case 60..<3600:
                return "in \(minutes) minute\(minutes == 1 ? "" : "s")"
            case 3600..<86400:
                return "in \(hours) hour\(hours == 1 ? "" : "s")"
            default:
                let formatter = DateFormatter()
                formatter.dateFormat = "EEEE 'at' h:mm a"
                return formatter.string(from: self)
            }
        }
    }
}
```

### Combined Display

For the "Next Heartbeat" prominent display:

```
┌────────────────────────────────────────────────┐
│  ⏱ 2:00 PM PST                  in 47 minutes │
└────────────────────────────────────────────────┘
```

Left side: Absolute time with timezone
Right side: Relative time

---

## 7. SwiftUI View Structure

```swift
struct HeartbeatPanelView: View {
    @StateObject var viewModel: HeartbeatViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HeartbeatHeaderView(status: viewModel.overallStatus)
            
            // Next heartbeat (prominent)
            if let next = viewModel.nextHeartbeat {
                NextHeartbeatCard(date: next, state: viewModel.nextHeartbeatState)
            }
            
            // Recent heartbeats
            RecentHeartbeatsSection(items: viewModel.recentHeartbeats)
            
            // Upcoming schedule
            if !viewModel.upcomingHeartbeats.isEmpty {
                UpcomingScheduleSection(
                    dates: viewModel.upcomingHeartbeats,
                    description: viewModel.scheduleDescription
                )
            }
        }
        .task {
            await viewModel.refresh()
        }
    }
}

struct HeartbeatHeaderView: View {
    let status: HeartbeatHealth
    
    var body: some View {
        HStack {
            Image(systemName: "heart.fill")
                .foregroundColor(.pink)
            Text("Heartbeat")
                .font(.headline)
            Spacer()
            StatusIndicator(status: status)
        }
    }
}

struct NextHeartbeatCard: View {
    let date: Date
    let state: NextHeartbeatState
    
    var body: some View {
        HStack {
            Image(systemName: "clock.fill")
                .foregroundColor(.blue)
            Text(date, format: .dateTime.hour().minute())
                .font(.title2.bold())
            Spacer()
            Text(date.heartbeatRelativeString)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
}

struct RecentHeartbeatsSection: View {
    let items: [HeartbeatDisplayItem]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("RECENT")
                .font(.caption)
                .foregroundColor(.secondary)
            
            ForEach(items) { item in
                HStack {
                    Image(systemName: item.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundColor(item.success ? .green : .red)
                    Text(item.absoluteTime)
                    Spacer()
                    Text(item.taskLabel)
                        .foregroundColor(.secondary)
                    Text(item.relativeTime)
                        .foregroundColor(.secondary)
                }
                .font(.subheadline)
            }
        }
    }
}
```

---

## 8. Error Handling

### No Schedule Data

```swift
if viewModel.schedule == nil {
    ContentUnavailableView {
        Label("No Heartbeat", systemImage: "heart.slash")
    } description: {
        Text("Heartbeat monitoring is not configured for this gateway.")
    }
}
```

### Fetch Error

```swift
if let error = viewModel.error {
    ContentUnavailableView {
        Label("Unable to Load", systemImage: "exclamationmark.triangle")
    } description: {
        Text(error.localizedDescription)
    } actions: {
        Button("Retry") {
            Task { await viewModel.refresh() }
        }
    }
}
```

### Clock Skew

Use `serverTime` from response to detect significant clock skew between client and server:

```swift
func adjustForClockSkew(_ serverTime: Int64) -> TimeInterval {
    let serverDate = Date(timeIntervalSince1970: TimeInterval(serverTime) / 1000)
    let skew = serverDate.timeIntervalSinceNow
    
    // Warn if skew > 30 seconds
    if abs(skew) > 30 {
        logger.warning("Clock skew detected: \(skew) seconds")
    }
    
    return skew
}
```

---

## 9. Accessibility

```swift
struct NextHeartbeatCard: View {
    // ...
    
    var body: some View {
        HStack { /* ... */ }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("Next heartbeat at \(date.formatted(date: .omitted, time: .shortened))")
            .accessibilityHint(date.heartbeatRelativeString)
    }
}

struct RecentHeartbeatRow: View {
    let item: HeartbeatDisplayItem
    
    var body: some View {
        HStack { /* ... */ }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("""
                Heartbeat at \(item.absoluteTime), \
                \(item.success ? "successful" : "failed"), \
                \(item.taskLabel)
                """)
    }
}
```

---

## 10. Localization Notes

- Use `Date.FormatStyle` for dates (auto-localizes)
- Use `String(localized:)` for static text
- Pluralization: Use `String.LocalizationValue` with `%lld` for counts
- Timezone display: Consider showing user's local timezone vs. gateway timezone

```swift
// Plural-aware task count
Text("^[\(tasksCompleted) task](inflect: true)")
```

---

## Implementation Checklist

### Phase 1: Data Layer
- [ ] Add `HeartbeatStatusResponse` Codable struct
- [ ] Add `HeartbeatSchedule` and nested types
- [ ] Add RPC call method to API client
- [ ] Add basic error handling

### Phase 2: ViewModel
- [ ] Create `HeartbeatViewModel` with refresh logic
- [ ] Add computed properties for display items
- [ ] Implement polling timer with smart intervals
- [ ] Add state tracking (loading, error)

### Phase 3: UI — Core
- [ ] Build `HeartbeatPanelView` skeleton
- [ ] Build `NextHeartbeatCard` component
- [ ] Build `RecentHeartbeatsSection` component
- [ ] Add to existing system status view

### Phase 4: UI — Polish
- [ ] Add status indicators (colors, icons)
- [ ] Add relative time formatting
- [ ] Add accessibility labels
- [ ] Add loading/error states
- [ ] Add empty state for missing config

### Phase 5: Testing
- [ ] Test with mock data (happy path)
- [ ] Test null schedule handling
- [ ] Test error state
- [ ] Test timezone edge cases
- [ ] Test relative time formatting
