# VantageOC — Operator Control Center for Dru

VantageOC is a macOS desktop app that serves as Dru's operator dashboard. It connects to the OpenClaw gateway via WebSocket and gives the operator real-time visibility and control over sessions.

---

## Views

### Chat
Real-time conversation with Dru. Messages stream token-by-token. Operator can send instructions, files (as base64 attachments), and safety responses. Stock ticker across the top shows all active agents.

### Dashboard
Overview cards: active agent count, total sessions, today's token usage, cron job status. Plus live "thinking columns" showing what Dru and subagents are currently working on, and a recent events feed.

### Activity Feed
Scrolling log of everything Dru does: tool calls, file reads/writes, subagent spawns/completions, and thinking events. Filterable by type and searchable.

### Work Panel
Card-based view of Dru and all subagents in a hierarchy. Shows which agents are running/idle/complete, what they're working on, elapsed time, and output. Main agent always expanded; subagents auto-expand when running.

### Tokens
Per-session breakdown of input/output token usage with aggregate totals.

### Heartbeat
Timeline of health checks from the gateway with status indicators (ok / alert / error).

### Logs
System-level log viewer capturing all events: connections, chat, agent activity, safety alerts. Filterable by level (info / warning / error / debug) and source.

### Sessions
List of all sessions with search, rename, archive. Operator can switch between sessions.

---

## Safety Alert Protocol

How blocking works when Dru is about to do something requiring operator approval:

### Dru sends (blocking):
```
[SAFETY:RED:r-TIMESTAMP] About to run: COMMAND_DESCRIPTION — blocked, awaiting approval.
```
- `RED` = blocks until operator approves or denies
- `r-TIMESTAMP` = unique action ID
- Vantage displays a red overlay card with the command in a monospaced code block + Approve/Deny buttons
- System notification fires with critical sound

### Dru sends (informational):
```
[SAFETY:YELLOW] Notice text
```
- `YELLOW` = informational, no action needed

### Operator responds:
```
[SAFETY:APPROVED:r-TIMESTAMP]   → Dru proceeds
[SAFETY:DENIED:r-TIMESTAMP]     → Dru does not execute
```

All alerts and resolutions are recorded in Logs.

---

## Connection Details

- WebSocket with JSON-RPC protocol (req/res/event)
- Auto-reconnect with exponential backoff
- Device identity via Ed25519 signatures
- Credentials stored in macOS Keychain

---

## Status
- Spec defined: 2026-03-06
- Build status: TBD
