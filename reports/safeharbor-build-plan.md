# SafeHarbor: Unified Build Plan

**Version:** 1.0.0  
**Status:** Architecture Complete, Ready for Implementation  
**Date:** 2026-03-14  
**Supersedes:** `burrow-server-build-plan.md`, `vantageoc-standalone-architecture.md`

---

## Executive Summary

SafeHarbor is a standalone macOS application that embeds a complete multi-agent AI runtime inside an Alpine Linux virtual machine. It transforms VantageOC from a remote gateway client into a self-contained personal AI command center. No Docker, no external dependencies, direct distribution.

**The core transformation:** VantageOC today connects to a remote OpenClaw gateway over WebSocket. SafeHarbor replaces that remote gateway with a local Linux VM running the same agent runtime, communicating over Apple's Virtualization.framework vsock IPC.

**What ships:**
- A single `.app` bundle containing the Swift UI, Alpine Linux rootfs image, and Node.js agent runner
- ~150MB total (80MB rootfs + 40MB Swift app + 30MB bundled resources)
- macOS 13+, Apple Silicon primary (Intel supported)
- **Distribution: Mac App Store** (sandbox entitlements, App Store review, auto-updates via App Store)

**Key decisions validated:**
1. VM over sidecar: Full Linux environment enables the complete OpenClaw runtime without macOS/Node.js compatibility hacks
2. vsock over Unix socket: Native Virtualization.framework IPC, no network stack overhead
3. Embedded Node.js over rewrite: Claude Agent SDK is TypeScript; fighting this would waste months
4. Single VM multi-agent over container-per-agent: Personal tool doesn't need tenant isolation

---

## 1. Project Overview

### 1.1 What SafeHarbor Is

SafeHarbor is a macOS application for running personal AI agents locally. It's designed for power users who want:
- Full control over their AI assistants
- Privacy (agents run locally, API keys stay local)
- Reliability (no dependency on remote infrastructure)
- A polished native macOS experience

### 1.2 Target User

Technical individuals who:
- Currently use Claude via API
- Want persistent AI agents with memory
- Value local-first software
- Are comfortable with ~150MB app and ~1GB RAM usage

### 1.3 How SafeHarbor Differs from VantageOC + OpenClaw Plugin

| Aspect | VantageOC + OpenClaw | SafeHarbor |
|--------|---------------------|------------|
| Architecture | Thin client → remote gateway | Standalone app with embedded runtime |
| Dependency | Requires running OpenClaw server | None (self-contained) |
| Agent runtime | Runs on server | Runs inside local VM |
| Network | WebSocket/SSE to gateway | vsock IPC to local VM |
| Distribution | Client app + server setup | Single .app bundle |
| Setup complexity | High (server, API keys, networking) | Low (download, enter API key, go) |

### 1.4 What's Being Reused vs. Replaced vs. Removed

**Reused from VantageOC (≈70% of Swift code):**
- All UI views (chat, channels, tasks, safety alerts, files, settings)
- All observable stores (ChannelStore, TaskStore, SafetyStore, etc.)
- Database schema and GRDB infrastructure
- All models (Channel, Message, Task, etc.)
- Theme, design system, components

**Replaced:**
- `GatewayClient.swift` → `VMClient.swift` (vsock instead of WebSocket)
- `GatewaySSE.swift` → removed (VM pushes events directly)
- `WebSocketConnection.swift` → `VsockConnection.swift`
- `GatewayAPI.swift` → `VMCommands.swift` (same operations, different transport)
- Connection setup flow → First-launch wizard (API key, agent creation)

**Removed (dead code after transformation):**
- Device identity/pairing system (no remote server to pair with)
- Gateway authentication flow
- SSE reconnection logic
- Remote polling system (VM pushes events)
- Any references to OpenClaw gateway URLs

---

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SafeHarbor.app (macOS)                              │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Dashboard  │  │  Channels   │  │    Tasks    │  │   Safety Alerts     │ │
│  │    View     │  │    View     │  │    View     │  │       View          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                │                     │           │
│         └────────────────┴────────────────┴─────────────────────┘           │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │   AppCoordinator  │◄──── REUSED (modified)       │
│                          └─────────┬─────────┘                              │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │     VMClient      │◄──── NEW (replaces Gateway)  │
│                          │  (vsock JSON-RPC) │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │   SafeHarborVM    │◄──── NEW                     │
│                          │(Virtualization.fw)│                              │
│                          └─────────┬─────────┘                              │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │ vsock port 5000
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                        Alpine Linux VM (arm64)                              │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │  vsock-server.ts  │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                        │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                        Node.js Agent Runner                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │  │
│  │  │  agent   │  │  router  │  │scheduler │  │  tools   │  │   db    │  │  │
│  │  │manager.ts│  │   .ts    │  │   .ts    │  │  /*.ts   │  │   .ts   │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │  │
│  │       │             │             │             │             │       │  │
│  │       └─────────────┴─────────────┴─────────────┴─────────────┘       │  │
│  │                                   │                                   │  │
│  │                    ┌──────────────┴──────────────┐                    │  │
│  │                    │     Claude Agent SDK        │                    │  │
│  │                    │    (@anthropic-ai/sdk)      │                    │  │
│  │                    └─────────────────────────────┘                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Mounts (9p virtio):                                                        │
│    /agents  ← ~/Library/Application Support/SafeHarbor/agents/ (rw)         │
│    /data    ← ~/Library/Application Support/SafeHarbor/data/ (rw)           │
│    /app     ← SafeHarbor.app/Contents/Resources/runner/ (ro)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 VM Layer

**Alpine Linux rootfs (~80MB):**
- Alpine 3.19 base
- Node.js 20 LTS
- SQLite
- curl, ca-certificates, tzdata

**Virtualization.framework configuration:**
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| vCPUs | 2 | Sufficient for Node.js + Claude API |
| RAM | 1024 MB | Node.js heap + SQLite, agents are I/O-bound |
| Boot time | 2-3 seconds | Alpine fast boot + Node.js startup |
| Disk | Read-only rootfs + 9p mounts | Separation of concerns |
| Network | NAT (outbound only) | Claude API + web access |

**Why Virtualization.framework, not a sidecar:**
1. Full Linux environment — no Node.js/macOS compatibility issues
2. Clean isolation — VM crashes don't affect host app
3. Consistent environment — same runtime on every Mac
4. Future-proof — can add more Linux tooling without macOS constraints

### 2.3 Host Application Layer

The Swift/SwiftUI app keeps its existing structure with surgical replacements:

**Services (modified):**
```
VantageOC/Services/
├── GatewayClient.swift      → VMClient.swift
├── GatewaySSE.swift         → REMOVED
├── GatewayAPI.swift         → VMCommands.swift (extension on VMClient)
├── GatewayEventRouter.swift → VMEventRouter.swift
├── DeviceIdentityService.swift → REMOVED (no pairing needed)
├── KeychainService.swift    → KEPT (for API key storage)
└── NotificationService.swift → KEPT
```

**New files:**
```
VantageOC/VM/
├── SafeHarborVM.swift       # Virtualization.framework wrapper
├── VMClient.swift           # vsock JSON-RPC client
├── VMCommands.swift         # RPC method implementations
├── VMEventRouter.swift      # Event → store routing
└── VsockConnection.swift    # Low-level vsock wrapper
```

### 2.4 Runtime Layer (Node.js in VM)

**Directory structure:**
```
server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts             # Entry point
│   ├── vsock-server.ts      # JSON-RPC over vsock
│   ├── agent-manager.ts     # Agent lifecycle
│   ├── agent.ts             # Agent class (Claude SDK integration)
│   ├── router.ts            # Inter-agent messaging
│   ├── scheduler.ts         # Heartbeats and cron
│   ├── db.ts                # SQLite wrapper (better-sqlite3)
│   ├── memory.ts            # Agent memory file operations
│   ├── logger.ts            # Logging utility
│   ├── types.ts             # TypeScript types
│   └── tools/               # Agent tools
│       ├── index.ts
│       ├── file-read.ts
│       ├── file-write.ts
│       ├── web-fetch.ts
│       └── shell-exec.ts
└── dist/                    # Compiled JS (bundled into app)
```

### 2.5 Storage Architecture

**Dual-database approach:**

| Database | Location | Runtime | Purpose |
|----------|----------|---------|---------|
| Host SQLite | `~/Library/.../SafeHarbor/safeharbor.db` | GRDB (Swift) | UI cache, offline access |
| VM SQLite | `/data/runtime.db` (9p mount) | better-sqlite3 (Node.js) | Agent state, messages |

**Sync strategy:**
- VM database is source of truth for agent data
- Host database is a read-through cache for UI responsiveness
- On VM boot, host syncs from VM database
- Real-time events update both (VM writes, pushes to Swift, Swift caches)

**Why dual databases (not shared):**
- GRDB and better-sqlite3 have different locking semantics
- Concurrent writes from different processes risk corruption
- Cache-aside pattern is proven reliable
- UI can show stale data while VM is booting

### 2.6 Gaps and Risks in Current Architecture

**Gap 1: Rootfs build pipeline**
- The build script assumes Docker buildx on macOS
- **Risk:** Developer needs Docker installed for builds
- **Mitigation:** Pre-build rootfs and commit to repo, only rebuild for Node.js version changes

**Gap 2: VM crash recovery**
- Current plan doesn't specify behavior when VM crashes mid-conversation
- **Suggestion:** VMClient should buffer unacknowledged requests and retry on VM restart

**Gap 3: First-launch UX**
- No design for auth onboarding flow
- **Suggestion:** ConnectionSetupView → FirstLaunchView with two paths: setup-token (default, subscription) and API key (fallback). See Appendix C for full flow design.

**Gap 4: Agent SOUL.md creation**
- No UI for creating new agents with custom personalities
- **Suggestion:** Defer to v1.1, ship with default agent

**Gap 5: Background heartbeats when app closed**
- launchd not available in App Store sandbox
- **Decision:** Deferred indefinitely. Agents run only while app is open. v1 ships without background operation.

---

## 3. Interface Contract

### 3.1 vsock Configuration

| Parameter | Value |
|-----------|-------|
| Port | 5000 |
| Protocol | JSON-RPC 2.0 |
| Framing | Newline-delimited JSON (`\n`) |
| Encoding | UTF-8 |

### 3.2 JSON-RPC Message Format

**Request (Swift → VM):**
```json
{
  "jsonrpc": "2.0",
  "id": "uuid-string",
  "method": "chat",
  "params": {
    "agentId": "main",
    "message": "Hello, how are you?"
  }
}
```

**Response (VM → Swift):**
```json
{
  "jsonrpc": "2.0",
  "id": "uuid-string",
  "result": {
    "content": "I'm doing well, thank you!"
  }
}
```

**Streaming response (multiple messages, same ID):**
```json
{"jsonrpc": "2.0", "id": "uuid", "result": {"chunk": "I'm ", "done": false}}
{"jsonrpc": "2.0", "id": "uuid", "result": {"chunk": "doing well!", "done": false}}
{"jsonrpc": "2.0", "id": "uuid", "result": {"chunk": "", "done": true, "fullContent": "I'm doing well!"}}
```

**Push event (VM → Swift, no request ID):**
```json
{
  "jsonrpc": "2.0",
  "method": "event",
  "params": {
    "type": "agent_status",
    "agentId": "main",
    "status": "idle"
  }
}
```

**Error:**
```json
{
  "jsonrpc": "2.0",
  "id": "uuid-string",
  "error": {
    "code": -32000,
    "message": "Agent not found",
    "data": { "agentId": "unknown" }
  }
}
```

### 3.3 RPC Method Reference

| Method | Params | Returns | Direction |
|--------|--------|---------|-----------|
| `ping` | `{}` | `{ pong: true }` | Swift → VM |
| `chat` | `{ agentId, message, stream? }` | `{ content }` or streaming | Swift → VM |
| `heartbeat` | `{ agentId? }` | `{ responses: [...] }` | Swift → VM |
| `status` | `{}` | `{ agents: [...], vmUptime: N }` | Swift → VM |
| `agents.list` | `{}` | `{ agents: [...] }` | Swift → VM |
| `agents.reload` | `{ agentId }` | `{ success: true }` | Swift → VM |
| `channels.list` | `{}` | `{ channels: [...] }` | Swift → VM |
| `channels.create` | `{ slug, name, soul? }` | `{ channel }` | Swift → VM |
| `channels.delete` | `{ slug }` | `{ success: true }` | Swift → VM |
| `messages.history` | `{ channel, limit?, before? }` | `{ messages: [...] }` | Swift → VM |
| `broadcast` | `{ message, from? }` | `{ delivered: N }` | Swift → VM |
| `shutdown` | `{}` | `{ ack: true }` | Swift → VM |
| `event` | `{ type, ... }` | N/A (push) | VM → Swift |

### 3.4 Event Types (VM → Swift push)

| Event Type | Payload | Triggers |
|------------|---------|----------|
| `agent_status` | `{ agentId, status, currentTask? }` | Agent state change |
| `message` | `{ channel, message }` | New message (user or agent) |
| `stream_chunk` | `{ channel, agentId, chunk }` | Agent streaming response |
| `stream_end` | `{ channel, agentId, fullContent }` | Stream complete |
| `safety_alert` | `{ alertId, severity, ... }` | Agent requests approval |
| `task_spawn` | `{ taskId, name, channel }` | Subagent started |
| `task_update` | `{ taskId, status, progress? }` | Task progress |
| `task_complete` | `{ taskId, summary? }` | Task finished |
| `heartbeat_result` | `{ agentId, response }` | Heartbeat completed |
| `error` | `{ code, message }` | Runtime error |

### 3.5 Mount Paths

| Host Path | Guest Path | Mode |
|-----------|------------|------|
| `~/Library/Application Support/SafeHarbor/agents/` | `/agents` | read-write |
| `~/Library/Application Support/SafeHarbor/data/` | `/data` | read-write |
| `SafeHarbor.app/Contents/Resources/runner/` | `/app` | read-only |

### 3.6 VM Lifecycle

**Start sequence:**
1. Swift creates SafeHarborVM instance
2. SafeHarborVM configures Virtualization.framework (mounts, RAM, vCPUs)
3. SafeHarborVM boots Alpine from rootfs.img
4. VM runs `/init.sh` which starts Node.js runner
5. Node.js binds to vsock port 5000
6. Swift connects to vsock, sends `ping`
7. On `pong`, Swift fires `.connected` event

**Stop sequence:**
1. Swift sends `shutdown` RPC
2. VM acknowledges, begins graceful shutdown
3. Node.js persists state, closes DB
4. Swift waits 5s, then force-kills VM if still running
5. Swift fires `.disconnected` event

**Crash recovery:**
1. Swift detects vsock disconnect
2. Swift fires `.disconnected(error)` event
3. VMClient buffers any pending requests
4. SafeHarborVM attempts restart (max 3 attempts)
5. On successful restart, VMClient reconnects and replays buffered requests
6. If restart fails 3x, show error UI, offer manual retry

### 3.7 Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error (invalid JSON) |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Agent not found |
| -32001 | Agent busy |
| -32002 | Agent error |
| -32003 | Channel not found |
| -32004 | Database error |
| -32010 | VM not ready |

---

## 4. What's No Longer Needed

### 4.1 Dead Code in VantageOC

**Services to remove:**
| File | Reason |
|------|--------|
| `GatewayClient.swift` | Replaced by VMClient |
| `GatewaySSE.swift` | VM pushes events, no SSE needed |
| `WebSocketConnection.swift` | Replaced by VsockConnection |
| `DeviceIdentityService.swift` | No remote pairing |
| `GatewayAPI.swift` | Replaced by VMCommands |
| `GatewayEventRouter.swift` | Replaced by VMEventRouter |

**Model changes:**
| Model | Change |
|-------|--------|
| `ConnectionState` | Remove `gatewayURL`, add `vmStatus` |
| `GatewayError` | Rename to `SafeHarborError`, remove auth errors |
| `GatewayEvent` | Rename to `VMEvent`, simplify cases |

**View changes:**
| View | Change |
|------|--------|
| `ConnectionSetupView` | Replace with `FirstLaunchView` (setup-token default, API key fallback) |
| `SettingsView` | Remove gateway URL field, add VM status |

### 4.2 OpenClaw-Specific Assumptions

**Hardcoded patterns to update:**
- Session key format `agent:main:main` — keep but generate locally
- Channel slugs `general`, `vantage` — replace with user-defined
- Gateway URL validation — remove entirely
- Device pairing flow — remove entirely
- SSE connection status — replace with VM health check

### 4.3 Plugin System (Entire Directory)

The entire `plugin/` directory in VantageSrc becomes dead code:
```
plugin/
├── index.ts              # DELETE
├── openclaw.plugin.json  # DELETE
├── package.json          # DELETE
├── src/
│   ├── channel.ts        # DELETE
│   ├── runtime.ts        # DELETE
│   ├── rpc.ts            # DELETE
│   ├── store.ts          # MIGRATE to server/src/db.ts
│   ├── subagent-hooks.ts # MIGRATE to server/src/router.ts
│   └── types.ts          # MIGRATE to server/src/types.ts
└── tsconfig.json         # DELETE
```

The useful logic from the plugin (store, subagent hooks) is ported to the SafeHarbor server, but the plugin registration machinery is gone.

---

## 5. Task DAG

### 5.1 Visual Overview

```
                    ┌─────────────────────┐
                    │ Phase 0: Foundation │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌────────────────┐
│ T1: Rootfs    │    │ T2: Node Runner │    │ T3: Swift VM   │
│ (Alpine build)│    │ (TypeScript)    │    │ (Virt.framework)│
│     [M]       │    │     [L]         │    │     [L]        │
└───────┬───────┘    └────────┬────────┘    └────────┬───────┘
        │                     │                      │
        └──────────┬──────────┴──────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ T4: Integration │
         │ (vsock IPC)     │
         │     [M]         │
         └────────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ T5: Swift UI  │   │ T6: Agent     │
│ Adaptation    │   │ Features      │
│     [L]       │   │     [L]       │
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ T7: Testing &   │
         │ Polish          │
         │     [M]         │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ T8: Packaging   │
         │ & Distribution  │
         │     [S]         │
         └─────────────────┘
```

### 5.2 Detailed Task Breakdown

#### Phase 0: Foundation (T0) — [S]
**Description:** Project setup, directory structure, dependencies
**Deliverables:**
- [ ] Create `safeharbor/` repo structure
- [ ] Set up `server/package.json` with dependencies
- [ ] Set up `server/tsconfig.json`
- [ ] Create Xcode project or xcodegen config
- [ ] Add Virtualization.framework entitlements
**Dependencies:** None
**Complexity:** S (1-2 days)

---

#### T1: Alpine Rootfs Build — [M]
**Description:** Create minimal Alpine Linux rootfs with Node.js 20
**Deliverables:**
- [ ] `vm/Dockerfile.rootfs` — Alpine 3.19 + Node.js 20 + SQLite
- [ ] `vm/build-rootfs.sh` — Docker buildx → ext4 image
- [ ] `vm/init.sh` — Boot script that starts Node.js runner
- [ ] Output: `rootfs.img` (~80MB)
**Dependencies:** T0
**Complexity:** M (3-5 days)
**Notes:**
- Requires `brew install e2fsprogs` for `mke2fs`
- Build for both arm64 (primary) and x86_64 (Intel support)

---

#### T2: Node.js Agent Runner — [L]
**Description:** Core runtime that executes agents inside the VM
**Deliverables:**
- [ ] `src/index.ts` — Entry point, initialization
- [ ] `src/vsock-server.ts` — JSON-RPC over vsock
- [ ] `src/agent-manager.ts` — Load agents from /agents
- [ ] `src/agent.ts` — Agent class with Claude SDK integration
- [ ] `src/router.ts` — Inter-agent messaging
- [ ] `src/scheduler.ts` — Heartbeats and cron
- [ ] `src/db.ts` — SQLite wrapper (better-sqlite3)
- [ ] `src/memory.ts` — Agent memory file operations
- [ ] `src/tools/*.ts` — File, web, shell tools
- [ ] Build script producing bundled JS
**Dependencies:** T0
**Complexity:** L (1-2 weeks)
**Parallel:** Can run alongside T1 and T3

---

#### T3: Swift VM Infrastructure — [L]
**Description:** Virtualization.framework wrapper and vsock client
**Deliverables:**
- [ ] `SafeHarborVM.swift` — VM lifecycle (start, stop, configure)
- [ ] `VsockConnection.swift` — Low-level vsock read/write
- [ ] `VMClient.swift` — JSON-RPC client over vsock
- [ ] `VMCommands.swift` — Typed RPC methods (chat, status, etc.)
- [ ] `VMEventRouter.swift` — Push events → stores
- [ ] Entitlements for Virtualization.framework
**Dependencies:** T0
**Complexity:** L (1-2 weeks)
**Parallel:** Can run alongside T1 and T2

---

#### T4: Integration Layer — [M]
**Description:** Wire VM to Swift app, end-to-end message flow
**Deliverables:**
- [ ] VMClient ↔ VsockServer handshake working
- [ ] Chat message round-trip (Swift → VM → Claude → VM → Swift)
- [ ] Streaming response displayed in UI
- [ ] Push events updating stores
- [ ] VM crash detection and auto-restart
**Dependencies:** T1, T2, T3
**Complexity:** M (3-5 days)

---

#### T5: Swift UI Adaptation — [L]
**Description:** Modify VantageOC UI for SafeHarbor
**Deliverables:**
- [ ] Remove GatewayClient references from AppCoordinator
- [ ] Replace GatewayClient with VMClient
- [ ] Create `FirstLaunchView` (API key entry)
- [ ] Update `SettingsView` (VM status, not gateway URL)
- [ ] Update `ConnectionIndicatorView` for VM state
- [ ] Remove dead code (SSE, device pairing)
- [ ] Rename app → SafeHarbor throughout
**Dependencies:** T4
**Complexity:** L (1-2 weeks)

---

#### T6: Agent Features — [L]
**Description:** Full agent functionality (memory, tools, inter-agent)
**Deliverables:**
- [ ] Memory system (SOUL.md, MEMORY.md, daily files)
- [ ] All tools implemented and tested
- [ ] Inter-agent messaging via router
- [ ] Heartbeat system running
- [ ] Channel creation/deletion
- [ ] Task tracking (subagent spawning)
**Dependencies:** T4
**Complexity:** L (1-2 weeks)
**Parallel:** Can run alongside T5

---

#### T7: Testing & Polish — [M]
**Description:** End-to-end testing, edge cases, UX polish
**Deliverables:**
- [ ] Unit tests for Node.js runner
- [ ] Integration tests for vsock protocol
- [ ] UI tests for critical flows
- [ ] Error handling polish (user-friendly messages)
- [ ] Performance testing (VM boot time, response latency)
- [ ] Memory leak testing (long-running conversations)
**Dependencies:** T5, T6
**Complexity:** M (3-5 days)

---

#### T8: Packaging & Distribution — [S]
**Description:** Prepare app for Mac App Store submission (handled by Aaron)
**Deliverables:**
- [ ] Xcode Archive configuration (Release scheme)
- [ ] App Store Connect metadata prep (description, screenshots, keywords)
- [ ] Privacy manifest (`PrivacyInfo.xcprivacy`) — required by App Store
- [ ] App Review notes (explain Virtualization.framework usage)
- [ ] README for internal reference
**Dependencies:** T7
**Complexity:** S (1-2 days)
**Note:** Aaron handles final archive, upload to App Store Connect, and submission.

### 5.3 Parallelization Opportunities

```
Week 1-2:   [T0] ──► [T1] [T2] [T3] (all parallel after T0)
Week 2-3:   [T1, T2, T3 continue]
Week 3:     [T4] (blocks on T1, T2, T3)
Week 4-5:   [T5] [T6] (parallel)
Week 5:     [T7] (blocks on T5, T6)
Week 6:     [T8]
```

**Total estimated timeline:** 5-6 weeks for one engineer
**Critical path:** T0 → T2 → T4 → T5 → T7 → T8

### 5.4 Task Groupings

| Group | Tasks | Owner Focus |
|-------|-------|-------------|
| VM Infrastructure | T1, T3 | Low-level systems, Virtualization.framework |
| Node.js Runtime | T2, T6 | TypeScript, Claude SDK, agent logic |
| Swift Integration | T4, T5 | AppCoordinator, stores, views |
| Quality & Ship | T7, T8 | Testing, packaging, distribution |

---

## 6. Risks & Suggestions

### 6.1 Architectural Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| vsock complexity on Intel Macs | Medium | Medium | Test early on Intel hardware; have TCP fallback ready |
| App Store review rejection for Virtualization.framework | Low | Low | Apple allows Virtualization.framework on App Store; include clear review notes |
| Node.js native module issues in VM | Medium | Low | Use pure-JS SQLite wrapper if better-sqlite3 fails |
| VM boot time >5s | Medium | Medium | Profile init.sh, defer non-critical initialization |
| Memory pressure from VM + Swift app | Medium | Medium | Target 1GB total; test on 8GB Macs |

### 6.2 Missing Pieces in Current Plans

**1. Error telemetry:**
- No plan for crash reporting or error telemetry
- **Suggestion:** Add optional Sentry integration, disabled by default

**2. Update mechanism:**
- No plan for app updates
- **Suggestion:** Sparkle framework for direct distribution updates

**3. Agent migration:**
- No plan for migrating agents from VantageOC/OpenClaw
- **Suggestion:** Export/import via zip file; v1.1 feature

**4. Multi-model support:**
- Current plan is Claude-only
- **Suggestion:** Abstract provider interface now, add OpenAI/local later

**5. Backup/restore:**
- No plan for backing up agent data
- **Suggestion:** `~/Library/Application Support/SafeHarbor/` is Time Machine friendly; document this

### 6.3 Over-Engineered Elements

**1. Dual database approach:**
- Adds complexity; sync bugs likely
- **Alternative:** Single VM database, Swift reads via vsock RPC
- **Verdict:** Keep dual for now (UI responsiveness), but document sync carefully

**2. Full JSON-RPC 2.0 compliance:**
- May be more ceremony than needed for local IPC
- **Alternative:** Simpler line protocol
- **Verdict:** Keep JSON-RPC (good tooling, debuggability)

### 6.4 Under-Engineered Elements

**1. Agent tool sandboxing:**
- Current plan has basic path checks
- **Suggestion:** Add rate limiting, size limits, execution timeouts

**2. API key security:**
- Passing via environment variable is simple but visible
- **Suggestion:** Consider vsock-based key injection after VM boot

**3. Logging strategy:**
- No unified logging across Swift/Node.js
- **Suggestion:** Structure logs as JSON, aggregate in Swift for display

### 6.5 Concrete Improvement Suggestions

1. **Add health check endpoint:** `/health` HTTP endpoint inside VM for debugging (disabled in production)

2. **Implement request timeout:** VMClient should timeout requests after 60s (configurable per method)

3. **Add VM metrics:** Track boot time, memory usage, message latency; display in Settings

4. **Graceful degradation:** If VM fails to start, offer "debug mode" showing VM console output

5. **Agent reload without VM restart:** Hot-reload SOUL.md changes via `agents.reload` RPC

---

## 7. Agent Instructions

### 7.1 Server-Side Build Agent (Node.js Runtime)

**Your scope:** Everything inside `server/` directory
**Primary files:** `src/*.ts`
**Key dependencies:** `@anthropic-ai/sdk`, `better-sqlite3`, `node-cron`

**Critical constraints:**
- Must work inside Alpine Linux ARM64
- vsock is the only communication channel (no HTTP server needed)
- All file operations must respect mount boundaries
- Agent instances must be isolated (no shared mutable state except router)

**Testing approach:**
- Run locally on macOS with TCP socket mock before VM testing
- Use `tsx watch` for development iteration
- Integration tests run against real vsock in CI

**What the Swift agent needs from you:**
- JSON-RPC protocol implementation exactly as specified
- Push events for all state changes
- Graceful shutdown on SIGTERM
- Deterministic boot sequence (ready signal after initialization)

### 7.2 Swift Client Build Agent

**Your scope:** Everything in the Swift/Xcode project except VM internals
**Primary files:** `VantageOC/VM/*.swift`, `VantageOC/Services/*.swift`, `VantageOC/App/*.swift`

**Critical constraints:**
- macOS 13+ only (Virtualization.framework requirement)
- Must work on both Apple Silicon and Intel
- UI must remain responsive during VM operations (async/await)
- GRDB operations on background thread

**Testing approach:**
- Unit tests for VMClient protocol handling
- UI tests for critical user flows
- Manual testing on both ARM64 and x86_64 Macs

**What the Node.js agent needs from you:**
- Correct vsock connection handling
- Environment variables passed at VM boot
- 9p mount configuration exactly as specified
- Graceful handling of VM crashes

**Code to reuse vs. rewrite:**
- **Reuse:** All views, all stores, all models, database schema
- **Rewrite:** GatewayClient → VMClient (similar structure, different transport)
- **Remove:** SSE, device identity, pairing flow

### 7.3 Integration/Testing Agent

**Your scope:** End-to-end flows, edge cases, release readiness

**Critical test scenarios:**
1. First launch flow (no agents, no API key)
2. Normal chat conversation with streaming
3. VM crash mid-conversation → recovery
4. Agent heartbeat execution
5. Inter-agent message routing
6. Safety alert flow (agent requests approval)
7. Long-running conversation (memory handling)
8. Network offline → Claude API failure handling
9. App backgrounded → foregrounded
10. macOS sleep → wake

**Performance benchmarks:**
- VM boot: <5 seconds
- First message latency: <2 seconds (excluding Claude API)
- Streaming chunk latency: <100ms
- Memory usage: <1GB total

**Release checklist:**
- [ ] All tests pass on ARM64
- [ ] All tests pass on Intel
- [ ] Notarization succeeds
- [ ] DMG installs cleanly
- [ ] First-launch flow works
- [ ] Existing agents migrate (if applicable)

---

## Appendix A: SQLite Schema (VM-side)

```sql
-- Agent state
CREATE TABLE agent_state (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    heartbeat_interval_ms INTEGER NOT NULL DEFAULT 1800000,
    last_heartbeat INTEGER,
    last_activity INTEGER,
    status TEXT NOT NULL DEFAULT 'idle',
    error_message TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Messages
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    metadata TEXT,
    FOREIGN KEY (agent_id) REFERENCES agent_state(agent_id)
);

CREATE INDEX idx_messages_channel_time ON messages(channel, timestamp DESC);

-- Channels
CREATE TABLE channels (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    soul TEXT,
    agent_id TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agent_state(agent_id)
);

-- Scheduled tasks
CREATE TABLE scheduled_tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_type TEXT NOT NULL CHECK (task_type IN ('heartbeat', 'cron', 'once')),
    cron_expression TEXT,
    run_at INTEGER,
    last_run INTEGER,
    next_run INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1,
    payload TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    FOREIGN KEY (agent_id) REFERENCES agent_state(agent_id)
);

-- Schema version
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

INSERT INTO schema_version (version) VALUES (1);
```

---

## Appendix B: File Manifest

```
SafeHarbor.app/
├── Contents/
│   ├── MacOS/
│   │   └── SafeHarbor           # Swift binary
│   ├── Resources/
│   │   ├── rootfs.img           # Alpine Linux (~80MB)
│   │   ├── runner/              # Node.js bundle (~20MB)
│   │   │   ├── index.js
│   │   │   └── better_sqlite3.node
│   │   └── Assets.xcassets/
│   ├── Info.plist
│   └── Entitlements.plist

~/Library/Application Support/SafeHarbor/
├── safeharbor.db                # Swift-side cache (GRDB)
├── config.json                  # App settings
├── agents/
│   └── {agent-id}/
│       ├── SOUL.md
│       ├── AGENTS.md
│       ├── HEARTBEAT.md
│       ├── memory/
│       │   ├── MEMORY-L0.md
│       │   ├── MEMORY.md
│       │   ├── topics/
│       │   └── {YYYY-MM-DD}.md
│       └── workspace/
└── data/
    ├── runtime.db               # VM-side SQLite
    └── runner.log               # VM stdout/stderr
```

---

## Appendix C: Authentication

### Auth Modes

SafeHarbor supports two auth modes. **Setup-token is the default and recommended path.**

| Mode | Token format | Source | Cost model |
|------|-------------|--------|------------|
| **Setup-token (default)** | `sk-ant-oat-*` | `claude setup-token` CLI | Claude subscription (~$20/mo flat) |
| **API key (fallback)** | `sk-ant-api*` | Anthropic Console | Pay-per-token (can be expensive at scale) |

### First-Launch Auth Flow

**Step 1 — detect auth mode:**
The first-launch wizard presents two options:
1. "I have a Claude subscription" → setup-token path (recommended, highlighted)
2. "I have an Anthropic API key" → API key path (advanced)

**Setup-token path:**
```
1. Show instruction: "Open Terminal and run: claude setup-token"
2. User pastes the resulting token (sk-ant-oat-*)
3. App validates token with a test ping to Anthropic
4. Token stored in macOS Keychain under key "com.safeharbor.auth.setup-token"
5. Auth mode saved to config.json: { "authMode": "setup-token" }
```

**API key path:**
```
1. Show text field: "Paste your Anthropic API key"
2. User pastes key (sk-ant-api*)
3. App validates with test ping
4. Key stored in Keychain under key "com.safeharbor.auth.api-key"
5. Auth mode saved to config.json: { "authMode": "api-key" }
```

### Keychain Storage

Both credentials stored in macOS Keychain (not in files, not in config.json).

```swift
// KeychainService additions
func storeAuthToken(_ token: String, mode: AuthMode) throws
func loadAuthToken(mode: AuthMode) throws -> String?
func clearAuthToken(mode: AuthMode) throws
```

### Token Validation

Before accepting either token type, SafeHarbor makes a minimal test call:
- Endpoint: `POST https://api.anthropic.com/v1/messages`
- Model: `claude-haiku-3-5` (cheapest, fastest)
- Message: `{ role: "user", content: "ping" }`, `max_tokens: 1`
- Success: HTTP 200 → proceed
- Failure: show specific error (expired, invalid, no subscription, etc.)

### VM Environment Variables

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `ANTHROPIC_AUTH_TOKEN` | Yes | Keychain → VM env | Either setup-token or API key |
| `ANTHROPIC_AUTH_MODE` | Yes | config.json | `setup-token` or `api-key` |
| `SAFEHARBOR_LOG_LEVEL` | No | Swift config | `debug`, `info`, `warn`, `error` |
| `TZ` | No | Swift system | Timezone for agent timestamps |
| `NODE_ENV` | No | Hardcoded | `production` |

### Node.js SDK Auth

The Node.js runtime detects auth mode at startup:

```typescript
const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_AUTH_TOKEN,
  // SDK accepts both sk-ant-oat-* and sk-ant-api* in the apiKey field
  defaultHeaders: process.env.ANTHROPIC_AUTH_MODE === 'setup-token'
    ? { 'anthropic-beta': 'oauth-2025-04-20' }  // required for subscription auth
    : {}
});
```

### Caveats

- **Setup-token / subscription auth:** Anthropic has intermittently restricted subscription use outside Claude Code. This is a user-choice risk; SafeHarbor documents it in the onboarding flow.
- **Prompt caching:** Not available with setup-token auth (`sk-ant-oat-*`). API key users get caching; subscription users don't. Note this in Settings.
- **1M context:** Rejected with subscription tokens. API key only.
- **Token expiry:** Setup-tokens can expire. SafeHarbor detects 401 errors and prompts re-auth via a non-blocking banner (not a modal interrupt).

---

*End of SafeHarbor Build Plan. This document supersedes all prior planning artifacts.*
