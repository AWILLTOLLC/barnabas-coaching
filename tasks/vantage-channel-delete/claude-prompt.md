# VantageOC: Implement Channel Delete (Client Side)

## Context

VantageOC is a macOS SwiftUI app that connects to an OpenClaw gateway via WebSocket (JSON-RPC). It has a channels sidebar where each channel has a settings panel accessible via a ⚙ icon in the channel header.

The settings panel currently has:
- Rename channel (display name only; slug is immutable)
- Change icon (emoji picker)
- Archive channel
- "Add Channel" button

## What to Add

Add a **Delete Channel** action to the channel settings panel. The server-side is already implemented. You just need the client side.

---

## Server-Side RPC (already live)

**Method:** `vantage.channels.delete`

**Request:**
```json
{
  "type": "req",
  "id": "<uuid>",
  "method": "vantage.channels.delete",
  "params": { "slug": "channel-slug" }
}
```

**Success response:**
```json
{
  "ok": true,
  "slug": "channel-slug",
  "dbDeleted": true,
  "message": "Channel deleted. Gateway restarting..."
}
```

**Error response (protected channel or bad slug):**
```json
{
  "ok": false,
  "error": "barnabas-coaching is a protected channel and cannot be deleted"
}
```

**Important:** After a successful delete, the **gateway will restart** (brief WebSocket disconnect ~1-2 seconds). The client should handle this gracefully via its existing reconnect logic — no special handling needed beyond what's already there for disconnects.

---

## UI/UX Requirements

1. **Delete button** in the channel settings panel — below Archive, styled destructively (red text, `role: .destructive`)

2. **Confirmation dialog** before sending the RPC:
   > **Delete "#channel-name"?**
   > All message history will be permanently deleted. This cannot be undone.
   > [Cancel] [Delete Channel ⚠️]

3. **On success:**
   - Remove the channel from the sidebar immediately (optimistic)
   - If the deleted channel was selected, navigate away (select the first available channel or show empty state)
   - The gateway will restart — let the existing reconnect logic handle the brief disconnect

4. **On error:**
   - Show an alert with the server's error message
   - Do NOT remove the channel from the sidebar

5. **Protected channels** (barnabas-coaching, morse-marketing, black-raven, glimmer-cards): the server will return an error. The UI can optionally hide the delete button for these, or just let the server error surface.

---

## Notes

- Use the same RPC send/receive pattern already in the codebase for other `vantage.channels.*` methods
- The `slug` is the channel's identifier (e.g. `test3`), not the display name
- No local SQLite changes needed — channel data and history live server-side only in this app
- Don't add delete to the right-click context menu unless it's trivially easy given existing patterns — the settings panel is sufficient
