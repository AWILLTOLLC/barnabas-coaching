# Agent Config Sheet — Client-Side Implementation

## What's Ready (Gateway)

Two new RPC methods are live:

### `vantage.agent.config.get`
**Request:**
```json
{ "slug": "glimmer", "filename": "SOUL.md" }
```
**Response:**
```json
{ "slug": "glimmer", "filename": "SOUL.md", "content": "# SOUL.md\n..." }
```
- `slug: "main"` → reads from `~/.openclaw/workspace/{filename}`
- Any other slug → reads from `~/.openclaw/workspace/channels/{slug}/{filename}`
- Returns `content: ""` if file doesn't exist yet (safe to display as empty)

### `vantage.agent.config.set`
**Request:**
```json
{ "slug": "glimmer", "filename": "SOUL.md", "content": "# SOUL.md\n..." }
```
**Response:**
```json
{ "slug": "glimmer", "filename": "SOUL.md", "saved": true }
```
- Creates the file if it doesn't exist
- Overwrites if it does
- Only these filenames are allowed (allowlisted server-side):
  `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, `AGENTS.md`

---

## What Claude Needs to Implement

### 1. Add methods to `GatewayClient.swift`

```swift
func getAgentConfig(slug: String, filename: String) async throws -> String {
    let result = try await rpc("vantage.agent.config.get", params: [
        "slug": slug,
        "filename": filename
    ])
    return result["content"] as? String ?? ""
}

func setAgentConfig(slug: String, filename: String, content: String) async throws {
    _ = try await rpc("vantage.agent.config.set", params: [
        "slug": slug,
        "filename": filename,
        "content": content
    ])
}
```

Use whatever RPC call pattern is already established in GatewayClient (match existing style).

---

### 2. Wire `AgentConfigSheet`

The sheet has 6 tabs: SOUL, IDENTITY, USER, TOOLS, HEARTBEAT, AGENTS.

Each tab maps to a filename:
```
SOUL      → SOUL.md
IDENTITY  → IDENTITY.md
USER      → USER.md
TOOLS     → TOOLS.md
HEARTBEAT → HEARTBEAT.md
AGENTS    → AGENTS.md
```

**On appear:** Call `getAgentConfig(slug:filename:)` for each tab. Populate the TextEditor. Show a loading state while fetching.

**On save (per tab):** Call `setAgentConfig(slug:filename:content:)` with the current tab's content. Only save tabs that have changed (the sheet already tracks unsaved changes per tab via dot indicators — only call `set` for dirty tabs).

**The `slug`** to pass: this should come from whichever channel/agent the sheet was opened for. For the main agent, pass `"main"`. For a channel agent, pass the channel slug (e.g. `"glimmer"`).

---

### 3. Error handling

- If `get` fails: show an inline error in the tab, allow the user to retry
- If `set` fails: show an alert, do NOT clear the unsaved changes indicator (let them try again)
- Network errors should not discard edits

---

### 4. Notes

- The gateway writes files immediately on `set` — no debounce needed server-side
- Changes take effect on the agent's **next turn** (no restart required for SOUL.md etc.)
- AGENTS.md changes that affect tool behavior may need a gateway restart — not a client concern, just FYI
- The allowlist is enforced server-side; the client doesn't need to validate filenames
