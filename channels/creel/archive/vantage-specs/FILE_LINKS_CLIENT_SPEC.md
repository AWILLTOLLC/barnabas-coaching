# VantageOC File Links — Client Implementation Spec

**Version:** 1.0  
**Date:** 2026-03-12  
**Status:** Server-side complete. Client implementation required.

---

## Overview

Agents embed file references in their messages using a `vantage-file://` URI scheme inside standard Markdown link syntax. The client must detect these links, render them as tappable, and fetch/display the file content when tapped.

---

## URI Scheme

```
vantage-file://~/.openclaw/workspace/<relative-path>
```

### Examples

```markdown
[todo.md](vantage-file://~/.openclaw/workspace/channels/barnabas-coaching/tasks/todo.md)
[MEMORY.md](vantage-file://~/.openclaw/workspace/channels/morse-command/MEMORY.md)
[spec.md](vantage-file://~/.openclaw/workspace/channels/vantage-oc/specs/spec.md)
```

The tilde (`~`) is expanded server-side to `/root`. Clients should treat the URI as opaque and pass it directly to `vantage.files.read`.

---

## Server-Side RPC: `vantage.files.read`

### Request

```json
{
  "type": "req",
  "id": "<uuid>",
  "method": "vantage.files.read",
  "params": {
    "path": "vantage-file://~/.openclaw/workspace/channels/barnabas-coaching/tasks/todo.md"
  }
}
```

`params.path` accepts any of:
- `vantage-file://~/.openclaw/workspace/...` ← preferred, pass the URI verbatim
- `~/.openclaw/workspace/...` ← tilde path without scheme
- `/Users/apollo/.openclaw/workspace/...` ← absolute path

### Success Response

```json
{
  "type": "res",
  "id": "<uuid>",
  "ok": true,
  "result": {
    "path": "channels/barnabas-coaching/tasks/todo.md",
    "absolutePath": "/Users/apollo/.openclaw/workspace/channels/barnabas-coaching/tasks/todo.md",
    "filename": "todo.md",
    "content": "# Tasks\n\n- [ ] Item one\n- [ ] Item two\n",
    "encoding": "utf8",
    "size": 42,
    "mimeType": "text/markdown"
  }
}
```

### Error Responses

| `code` | Meaning |
|--------|---------|
| `INVALID_REQUEST` | Missing `path`, not absolute/tilde, or path is a directory |
| `FORBIDDEN` | Path is outside the workspace (security rejection) |
| `NOT_FOUND` | File does not exist |
| `FILE_TOO_LARGE` | File exceeds 10MB server limit |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Encoding

| File type | `encoding` | How to use |
|-----------|------------|------------|
| Text (`.md`, `.txt`, `.ts`, `.json`, etc.) | `"utf8"` | Use `content` as a string directly |
| Binary (images, PDFs, etc.) | `"base64"` | Decode from base64 before use |

The `mimeType` field tells you what the content is — use it to decide the renderer.

---

## Client Implementation Requirements

### 1. Link Detection

When rendering a message, detect Markdown links where the `href` starts with `vantage-file://`:

```swift
// Swift regex
let pattern = #"\[([^\]]+)\]\((vantage-file://[^)]+)\)"#
```

Extract:
- Display label: captured group 1 (e.g. `"todo.md"`)
- URI: captured group 2 (e.g. `"vantage-file://~/.openclaw/workspace/..."`)

Render the link as a tappable inline element (not a plain URL).

### 2. Tap Handler

On tap, call `vantage.files.read` with the full URI as `params.path`. Show a loading indicator while the request is in flight.

### 3. Display

On success:

- **`text/markdown`** — render as a Markdown sheet/panel (in-app). Preferred: a modal or slide-over with a title bar showing `filename`.
- **`text/plain`, `text/typescript`, `text/javascript`, etc.** — render as monospaced code view with appropriate syntax highlighting if available.
- **`application/json`** — render as pretty-printed code view.
- **Binary / unknown mimeType** — show filename + size + "Cannot preview this file type."

### 4. Error Handling

| Error code | User-facing message |
|------------|---------------------|
| `NOT_FOUND` | "File not found on the server." |
| `FORBIDDEN` | "Access denied." |
| `FILE_TOO_LARGE` | "File is too large to preview (> 10MB)." |
| `INTERNAL_ERROR` | "Could not load file. Try again." |

---

## Supported File Types (Text — `encoding: "utf8"`)

`.md` `.txt` `.ts` `.js` `.jsx` `.tsx` `.json` `.py` `.sh` `.yaml` `.yml` `.toml` `.csv` `.html` `.css` `.swift` `.env` `.mjs` `.cjs` `.rs` `.go` `.rb` `.php` `.sql` `.xml` `.ini` `.cfg` `.conf` `.log`

All others are returned as base64.

---

## Message Storage Note

File link markdown is stored verbatim in the `messages` table. No server-side transformation is applied. The `vantage-file://` syntax passes through the LLM output → `llm_output` hook → `storeMessage()` pipeline unchanged. Parse it at render time on the client.

---

## Security

- Server rejects all paths outside `~/.openclaw/workspace/`
- Symlink escape is checked via `fs.realpathSync`
- Credentials directory is not accessible (it's outside workspace root)
- Client should not attempt to construct or modify URIs — pass them through verbatim as received in message content

---

## Example Full Flow

1. Agent message arrives via `vantage.poll` or SSE:
   ```
   "I've drafted the outreach template. Review it here: [outreach.md](vantage-file://~/.openclaw/workspace/channels/black-raven/drafts/outreach.md)"
   ```

2. Client markdown renderer detects `vantage-file://` href → renders `outreach.md` as tappable link instead of plain text.

3. User taps. Client calls:
   ```json
   { "method": "vantage.files.read", "params": { "path": "vantage-file://~/.openclaw/workspace/channels/black-raven/drafts/outreach.md" } }
   ```

4. Server responds with `mimeType: "text/markdown"`, `content: "# Outreach Template\n..."`.

5. Client presents a Markdown sheet showing the file content.
