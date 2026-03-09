# VantageOC — Channels Feature Spec

**Status:** Ready for implementation  
**Target:** macOS desktop app (SwiftUI), existing Vantage codebase  
**Feature:** Persistent, named channels for agent activity organized by business/function

---

## Overview

Channels replaces Discord for private, self-hosted agent activity tracking. Each business or task type gets a named channel. Agents post updates, drafts, and alerts into channels. The operator browses async, approves drafts, and reviews activity logs — all encrypted end-to-end, stored locally.

---

## UI Layout

### Sidebar Addition
Insert a **Channels** section in the left sidebar, below existing navigation items.

```
Sidebar
├── Chat
├── Dashboard
├── Activity Feed
├── Work Panel
├── ── ── ── ── ── (divider)
├── CHANNELS
│   ├── 📣  daily-briefing       (unread badge)
│   ├── 🏢  barnabas-coaching
│   ├── 🎵  morse-marketing      (unread badge)
│   ├── 🪓  black-raven
│   └── ✨  glimmer-cards
├── ── ── ── ── ── (divider)
├── Tokens
├── Heartbeat
├── Logs
└── Sessions
```

Channel names show:
- Icon (emoji, configurable)
- Channel name
- Unread count badge (blue pill) when there are unread messages
- Subtle dot indicator for pending approvals (orange)

### Channel View (main content area when a channel is selected)

```
┌─────────────────────────────────────────────────────┐
│  🎵 morse-marketing                    [Search] [⚙]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  📋 STATUS  · Dru · 9:03 AM                  │   │
│  │  Influencer research complete. Found 12       │   │
│  │  targets above 50k subs in ham radio niche.   │   │
│  │  Full list in tasks/morse-marketing/          │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  📝 DRAFT  · Dru · 9:05 AM      [PENDING]    │   │
│  │                                              │   │
│  │  Platform: X Thread                          │   │
│  │  ─────────────────────────────────────────   │   │
│  │  "Hear this sound. What letter is it?"       │   │
│  │                                              │   │
│  │  [Full draft content here...]                │   │
│  │                                              │   │
│  │  [✅ Approve & Queue]  [✏️ Edit]  [❌ Reject] │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  📊 REPORT  · Dru · 7:00 AM                  │   │
│  │  Daily KPIs — Mar 6                          │   │
│  │  Downloads: 47  Revenue: $23.10              │   │
│  │  Top source: Organic search                  │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Data Models

```swift
// Channel definition
struct Channel: Identifiable, Codable {
    let id: String           // UUID
    var name: String         // "morse-marketing"
    var displayName: String  // "Morse Marketing"
    var icon: String         // emoji or SF Symbol name
    var businessTag: BusinessTag
    var sortOrder: Int
    var createdAt: Date
    var updatedAt: Date
}

enum BusinessTag: String, Codable {
    case barnabas = "barnabas"
    case morse = "morse"
    case blackRaven = "black-raven"
    case glimmer = "glimmer"
    case system = "system"
}

// Message posted to a channel
struct ChannelMessage: Identifiable, Codable {
    let id: String           // UUID
    let channelId: String
    let agentId: String      // which agent posted it
    let agentName: String    // "Dru", "subagent-marketing", etc.
    let type: MessageType
    var content: String      // Markdown
    var attachments: [Attachment]?
    var metadata: [String: String]?  // platform, target, etc.
    var status: MessageStatus?
    let createdAt: Date
    var resolvedAt: Date?
    var isRead: Bool
}

enum MessageType: String, Codable {
    case post      // standard update/log
    case draft     // content draft awaiting operator approval
    case report    // structured data/KPI output
    case alert     // something needs attention
    case status    // short status update (agent started/completed task)
}

enum MessageStatus: String, Codable {
    case pending   // awaiting operator action (drafts)
    case approved  // operator approved
    case rejected  // operator rejected
    case posted    // content was published externally
}

struct Attachment: Codable {
    let filename: String
    let mimeType: String
    let data: Data        // base64-encoded in transit
}
```

---

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS channels (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    icon        TEXT NOT NULL DEFAULT '📋',
    business_tag TEXT NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_messages (
    id          TEXT PRIMARY KEY,
    channel_id  TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    agent_id    TEXT NOT NULL,
    agent_name  TEXT NOT NULL,
    type        TEXT NOT NULL CHECK(type IN ('post','draft','report','alert','status')),
    content     TEXT NOT NULL,
    attachments TEXT,              -- JSON array
    metadata    TEXT,              -- JSON object
    status      TEXT CHECK(status IN ('pending','approved','rejected','posted')),
    created_at  INTEGER NOT NULL,
    resolved_at INTEGER,
    is_read     INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_channel_messages_channel_id
    ON channel_messages(channel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_channel_messages_unread
    ON channel_messages(channel_id, is_read)
    WHERE is_read = 0;
```

**Seed default channels on first launch:**
```sql
INSERT OR IGNORE INTO channels VALUES
    ('ch-briefing',  'daily-briefing',  'Daily Briefing',    '📣', 'system',     0, unixepoch(), unixepoch()),
    ('ch-barnabas',  'barnabas-coaching','Barnabas Coaching', '🏢', 'barnabas',   1, unixepoch(), unixepoch()),
    ('ch-morse',     'morse-marketing', 'Morse Marketing',   '🎵', 'morse',       2, unixepoch(), unixepoch()),
    ('ch-blackraven','black-raven',     'Black Raven',       '🪓', 'black-raven', 3, unixepoch(), unixepoch()),
    ('ch-glimmer',   'glimmer-cards',   'Glimmer Cards',     '✨', 'glimmer',     4, unixepoch(), unixepoch());
```

---

## WebSocket Protocol (JSON-RPC additions)

Add these message types to the existing JSON-RPC protocol.

### Agent → Vantage (inbound events)

**Post to channel:**
```json
{
  "jsonrpc": "2.0",
  "method": "channel.post",
  "params": {
    "channelSlug": "morse-marketing",
    "agentId": "agent:main:main",
    "agentName": "Dru",
    "type": "post",
    "content": "Influencer research complete. Found 12 targets.",
    "metadata": {}
  }
}
```

**Post draft for approval:**
```json
{
  "jsonrpc": "2.0",
  "method": "channel.draft",
  "params": {
    "channelSlug": "morse-marketing",
    "agentId": "agent:main:main",
    "agentName": "Dru",
    "content": "X Thread draft:\n\n\"Hear this sound...\"\n\n[full content]",
    "metadata": {
      "platform": "x-thread",
      "scheduledFor": "2026-03-06T17:00:00Z"
    },
    "draftId": "draft-r1741234567"
  }
}
```

### Vantage → Agent (outbound commands)

**Approve a draft:**
```json
{
  "jsonrpc": "2.0",
  "method": "channel.approve",
  "params": {
    "messageId": "msg-uuid",
    "draftId": "draft-r1741234567"
  }
}
```

**Reject a draft:**
```json
{
  "jsonrpc": "2.0",
  "method": "channel.reject",
  "params": {
    "messageId": "msg-uuid",
    "draftId": "draft-r1741234567",
    "reason": "Optional operator note"
  }
}
```

**Fetch channel list:**
```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "channel.list",
  "params": {}
}
```

**Fetch channel history:**
```json
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "method": "channel.history",
  "params": {
    "channelSlug": "morse-marketing",
    "limit": 50,
    "before": "2026-03-06T10:00:00Z"   // optional, for pagination
  }
}
```

---

## Agent Posting Convention

Agents (Dru and subagents) post to channels using a message prefix that Vantage intercepts from the gateway stream, OR by direct WebSocket call if the agent has gateway access.

**Prefix convention** (fallback if direct WS not available):
```
[CHANNEL:morse-marketing] Content here...
[CHANNEL:morse-marketing][DRAFT] X Thread draft content...
[CHANNEL:barnabas-coaching][REPORT] Weekly KPI data...
```

Vantage parses the prefix, strips it, routes to the correct channel, and does NOT display the message in the main Chat view.

**Type detection from prefix:**
- `[CHANNEL:slug]` → type: `post`
- `[CHANNEL:slug][DRAFT]` → type: `draft`, status: `pending`
- `[CHANNEL:slug][REPORT]` → type: `report`
- `[CHANNEL:slug][ALERT]` → type: `alert`

---

## Notification Behavior

| Event | Notification |
|-------|-------------|
| New `post` in any channel | None (silent, update unread count) |
| New `draft` awaiting approval | Banner notification: "Draft pending in #channel-name" |
| New `alert` | Banner + sound (same as SAFETY:YELLOW) |
| Approval/rejection confirmation | None |

Unread counts reset when the operator opens the channel and scrolls to bottom.

---

## Operator Interactions on Draft Messages

Draft messages render with three action buttons:

1. **Approve & Queue** — marks status `approved`, sends `channel.approve` back to agent, updates message to show green "APPROVED" badge
2. **Edit** — opens an inline text editor pre-filled with the draft content. Operator can modify and re-approve. Modified content is sent back with the approval.
3. **Reject** — shows a small text input for an optional note, marks status `rejected`, sends `channel.reject` back to agent, shows red "REJECTED" badge

After resolution, the buttons disappear and are replaced by the badge + resolved timestamp.

---

## Settings Panel (Channel Management)

Accessible via ⚙ icon in channel header.

- Rename channel (display name only; slug is immutable)
- Change icon (emoji picker)
- Archive channel (hides from sidebar, preserves history)
- View archived channels toggle
- "Add Channel" button → modal with name, icon, business tag

---

## Implementation Notes

- Channel data and message history are stored in the existing SQLite database (add tables to current migration system)
- The Channels sidebar section should collapse/expand (user preference stored in UserDefaults)
- Messages use `AttributedString` / markdown rendering — same renderer as existing Chat view if one exists
- Pagination: load last 50 messages on channel open, infinite scroll upward for history
- The `channel.post` WebSocket method should be handled by the gateway server, which persists the message and pushes an event to all connected Vantage clients (supports multi-device in future)
- If gateway connection is offline, queue outbound approval/rejection events and flush on reconnect
