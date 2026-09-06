# VantageOC Standalone Architecture
## Technical Report for Aaron

**Date:** 2026-03-14  
**Author:** Systems Architecture Analysis  
**Status:** Recommendation Ready

---

## Executive Summary

VantageOC can absolutely become a standalone macOS app. The cleanest path is **embedding a lightweight Node.js sidecar** inside the app bundle that runs the Claude Agent SDK, with agents communicating via a **shared SQLite database** and scheduled work handled by **NSBackgroundActivityScheduler** (while the app is open) plus an optional **launchd agent** for background heartbeats.

Apple's new Containerization framework is interesting but overkill for this use case. Full container isolation per agent adds complexity without proportional benefit for a personal tool.

The NanoClaw architecture is a useful reference point, but VantageOC doesn't need to replicate its container-per-agent model. A simpler single-process multi-agent runner is more appropriate.

---

## 1. Architecture Options

### Option A: Embedded Node.js Sidecar (Recommended)

**How it works:**
- Bundle a stripped-down Node.js binary inside `VantageOC.app/Contents/Resources/`
- Include the Claude Agent SDK and a minimal agent runner as JavaScript
- Swift app spawns the Node process on launch via `Process()` / `NSTask`
- Communication via Unix domain socket or stdin/stdout JSON-RPC

**Pros:**
- Claude Agent SDK is TypeScript/Node.js. This is the path of least resistance.
- Sidecar pattern is battle-tested (Tauri, Electron, many production apps)
- Full access to npm ecosystem
- Single process can run multiple agents (no container overhead)
- Easy to debug, update, and maintain

**Cons:**
- Adds ~50-80MB to app bundle (Node.js binary + node_modules)
- Two runtimes in one app (Swift + Node)

**Verdict:** This is the right answer. The Claude Agent SDK is Node.js-only, and fighting that would be wasted effort.

---

### Option B: Native Swift Agent Runner (HTTP API Only)

**How it works:**
- Write a pure Swift agent runner that calls Claude API directly via HTTP
- Reimplement tool execution, memory management, etc. in Swift

**Pros:**
- Single runtime, cleaner bundle
- Fully native, no sidecar complexity

**Cons:**
- Claude Agent SDK doesn't exist for Swift. You'd be rebuilding it from scratch.
- Tool execution (shell commands, file operations, browser automation) would need Swift implementations
- Massive engineering effort for marginal benefit
- You'd be maintaining your own agent SDK forever

**Verdict:** Don't do this. The Claude Agent SDK does heavy lifting (tool parsing, sandboxing, conversation management) that isn't worth reimplementing in Swift.

---

### Option C: Apple Containerization (Container per Agent)

**How it works:**
- Use Apple's new `Containerization` Swift package
- Each agent runs in its own lightweight Linux VM
- VMs boot in sub-second, full isolation

**Pros:**
- Maximum isolation between agents
- macOS-native, fast boot times
- Could run untrusted code safely

**Cons:**
- Requires **macOS 26** (not yet released as of this writing)
- Each container spins up a Linux kernel. Overkill for running Claude agents.
- Adds significant complexity: OCI images, rootfs management, vsock communication
- Your agents aren't running untrusted code; they're your personal assistants. Container-level isolation is solving a problem you don't have.

**Verdict:** Interesting for the future, but not the right primitive today. NanoClaw uses containers because it's designed for multi-tenant/security-critical scenarios. VantageOC is a personal tool.

---

### Option D: Docker Sidecar

**How it works:**
- Require Docker Desktop installed on the Mac
- Spawn agent containers via Docker API

**Pros:**
- Well-understood technology
- Strong isolation

**Cons:**
- External dependency (Docker must be running)
- Heavyweight for a personal app
- Friction for non-developer users
- Licensing considerations for Docker Desktop

**Verdict:** No. This defeats the "standalone app" goal.

---

### Option E: Python Sidecar

**How it works:**
- Bundle Python + Anthropic SDK instead of Node.js

**Pros:**
- Anthropic has a Python SDK too

**Cons:**
- Python packaging is notoriously painful (venvs, dependencies, etc.)
- Larger bundle size than Node
- Claude Agent SDK (the full agent framework, not just the API client) is TypeScript-first

**Verdict:** Node.js sidecar is cleaner. Don't do Python unless you have a specific reason.

---

## 2. Inter-Agent Communication

Your agents need to talk to each other. The "agents channel" pattern from OpenClaw is essential. Here are the options:

### Option A: Shared SQLite Database (Recommended)

**How it works:**
- Single SQLite file at `~/Library/Application Support/VantageOC/agents.db`
- Table: `agent_messages (id, from_agent, to_agents, message, timestamp, read_by)`
- Agents poll for new messages or use SQLite's `NOTIFY` mechanism
- Swift app can also read/write to coordinate

**Pros:**
- Dead simple
- ACID transactions, no race conditions
- Both Swift and Node can access SQLite natively
- Easy to inspect and debug (it's just a file)
- Survives app restarts
- Already how NanoClaw handles memory

**Cons:**
- Polling adds slight latency (acceptable for agent messages)
- Not real-time push (but you don't need sub-second agent-to-agent delivery)

**Verdict:** This is the right answer for VantageOC. SQLite is the lingua franca both runtimes speak.

---

### Option B: Unix Domain Socket + JSON-RPC

**How it works:**
- Node sidecar listens on `/tmp/vantageoc.sock`
- Agents send messages through the socket
- Router in the sidecar dispatches to recipients

**Pros:**
- Real-time, low latency
- Standard IPC pattern

**Cons:**
- Socket disappears on restart; need reconnection logic
- More complex than SQLite
- Only works while both processes are running

**Verdict:** Good for Swift ↔ Node communication, but use SQLite for agent-to-agent messages that need persistence.

---

### Option C: Named Pipes / FIFO

**Cons:** Same as Unix sockets but worse. No benefit over sockets.

**Verdict:** Skip.

---

### Option D: In-Process Event Bus

**How it works:**
- All agents run in the same Node process
- Use EventEmitter or similar for pub/sub

**Pros:**
- Zero serialization overhead
- Instant delivery

**Cons:**
- Crashes affect all agents
- Harder to isolate misbehaving agents
- Still need persistence for messages across restarts

**Verdict:** Fine for runtime communication, but pair with SQLite for persistence.

---

### Recommended IPC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VantageOC.app (Swift)                    │
│  ┌──────────────┐                      ┌─────────────────┐  │
│  │   Chat UI    │◄────────────────────►│  SQLite (R/W)   │  │
│  └──────────────┘                      └────────┬────────┘  │
│         │                                       │           │
│         │ Unix Socket (JSON-RPC)                │           │
│         ▼                                       ▼           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                Node.js Sidecar Process                  ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       ││
│  │  │Glimmer  │ │ Black   │ │Barnabas │ │ Morse   │       ││
│  │  │ Agent   │ │ Raven   │ │Coaching │ │Command  │ ...   ││
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       ││
│  │       │           │           │           │             ││
│  │       └───────────┴─────┬─────┴───────────┘             ││
│  │                         │                               ││
│  │                   Agent Router                          ││
│  │                   (EventEmitter)                        ││
│  │                         │                               ││
│  │                   SQLite (R/W)                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Swift ↔ Node:** Unix socket for real-time UI updates and command dispatch  
**Agent ↔ Agent:** In-memory EventEmitter for live messages, SQLite for persistence  
**All agents:** Read/write to shared SQLite for messages and memory

---

## 3. Heartbeats / Scheduler

Agents need to wake up periodically for background work. Here are the options:

### Option A: NSBackgroundActivityScheduler (While App Running)

**How it works:**
- Swift app schedules periodic activities via `NSBackgroundActivityScheduler`
- On trigger, sends message to Node sidecar to wake specific agents

**Pros:**
- macOS-native, energy-efficient
- System-managed scheduling (deferred during low power, etc.)

**Cons:**
- Only works while app is running
- Minimum interval is ~10 minutes for background
- System may defer activities

**Verdict:** Good for heartbeats while the app is open. Simple to implement.

---

### Option B: launchd Agent (Background, App Closed)

**How it works:**
- Install a LaunchAgent plist to `~/Library/LaunchAgents/`
- launchd runs a lightweight script/binary on schedule
- That process can spawn the Node sidecar briefly for heartbeat work

**Pros:**
- Works even when app is closed
- Survives reboots
- Standard macOS pattern

**Cons:**
- Requires writing a plist to user's Library (installer step)
- More complex than in-app scheduling
- Not needed if users keep the app open

**Verdict:** Optional but valuable. Implement this as a "keep agents working in background" preference.

---

### Option C: Embedded Cron (node-cron)

**How it works:**
- Use `node-cron` or similar in the Node sidecar
- Schedule heartbeats as cron expressions

**Pros:**
- Simple, familiar pattern
- Works while sidecar is running

**Cons:**
- Dies when app closes
- Another dependency

**Verdict:** Simpler than NSBackgroundActivityScheduler for most cases. Use this as the primary mechanism while the app is open.

---

### Option D: Timer Thread in Node

**How it works:**
- Simple `setInterval()` for each agent's heartbeat

**Pros:**
- Zero dependencies
- Full control

**Cons:**
- Basic, no cron syntax

**Verdict:** This is probably fine. Keep it simple.

---

### Recommended Scheduler Architecture

**While app is running:**
- Node sidecar uses `setInterval()` or `node-cron` for heartbeats
- Each agent gets its configured interval (e.g., 30 minutes)
- Heartbeat triggers agent with heartbeat prompt, agent does its checks

**While app is closed (optional):**
- LaunchAgent plist installed to `~/Library/LaunchAgents/com.vantageoc.heartbeat.plist`
- Runs every N minutes (configurable)
- Spawns a minimal Node script that does heartbeat checks
- Results written to SQLite; app displays on next open

**For direct distribution (outside App Store):** No restrictions. launchd works fine.

**If you ever want App Store:** LaunchAgents are prohibited. You'd need to rely on app being open or use App Groups + background app refresh (limited on macOS).

---

## 4. Agent Isolation

### The Question: Separate Process/Container per Agent?

**Short answer:** No. Run all agents in the same Node process.

**Why:**
- Your agents are trusted. They're your personal assistants, not untrusted code.
- Container isolation adds ~100ms+ startup per agent and significant complexity.
- A misbehaving agent (infinite loop, memory leak) can be killed by restarting the sidecar. The Swift app remains stable.
- Process isolation would mean N Node processes running simultaneously. Memory overhead scales linearly.

**The NanoClaw Difference:**
NanoClaw uses containers because it's designed for:
- Multi-tenant scenarios (different users, different trust levels)
- Security-critical operations (agents running arbitrary code)
- Clean auditability (each container is isolated)

VantageOC is a personal tool. You trust your agents. Container isolation is solving a problem you don't have.

### Recommended Isolation Model

```
┌──────────────────────────────────────────┐
│           Node.js Process (1)            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │Agent1│ │Agent2│ │Agent3│ │Agent4│    │
│  └──────┘ └──────┘ └──────┘ └──────┘    │
│                                          │
│  - Separate AsyncLocalStorage context    │
│  - Separate memory/workspace paths       │
│  - Shared Claude API client (reuse conn) │
│  - Shared SQLite connection              │
└──────────────────────────────────────────┘
```

**Per-agent isolation (without containers):**
- Each agent gets its own `AsyncLocalStorage` context (Node.js)
- Each agent has its own directory for SOUL.md, memory, workspace
- Agent crashes are caught with try/catch; don't kill the whole process
- If the Node process dies, Swift app restarts it

**Upgrading to process isolation later:**
If you find you need stronger isolation (e.g., an agent running untrusted tool code), you can spawn separate Node processes per agent. This is a future optimization, not a launch requirement.

---

## 5. State and Memory

### Where Does Agent Data Live?

**Recommended:** `~/Library/Application Support/VantageOC/`

```
~/Library/Application Support/VantageOC/
├── agents.db                    # Shared SQLite (messages, state)
├── config.json                  # App configuration
├── agents/
│   ├── glimmer-cards/
│   │   ├── SOUL.md
│   │   ├── memory/
│   │   │   ├── 2026-03-14.md
│   │   │   └── MEMORY.md
│   │   └── workspace/
│   ├── black-raven/
│   │   ├── SOUL.md
│   │   ├── memory/
│   │   └── workspace/
│   ├── barnabas-coaching/
│   │   └── ...
│   └── morse-command/
│       └── ...
└── logs/
    └── vantageoc.log
```

**Why this structure:**
- Standard macOS location for app data
- Each agent has complete isolation at the filesystem level
- Easy to backup, inspect, or migrate
- Swift app can read SOUL.md to display agent identity in UI
- Node sidecar has full access for agent operations

### SQLite Schema

```sql
-- Agent messages (inter-agent + user chat)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL,           -- 'glimmer-cards', 'agents', etc.
    from_agent TEXT,                 -- null if from user
    to_agents TEXT,                  -- JSON array or null for broadcast
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    metadata TEXT                    -- JSON blob for extra data
);

-- Agent state
CREATE TABLE agent_state (
    agent_id TEXT PRIMARY KEY,
    last_heartbeat INTEGER,
    status TEXT,                     -- 'idle', 'working', 'error'
    current_task TEXT
);

-- Scheduled tasks
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    cron_expression TEXT,            -- or interval_ms for simple timers
    next_run INTEGER,
    last_run INTEGER,
    task_type TEXT,                  -- 'heartbeat', 'cron', etc.
    task_config TEXT                 -- JSON
);
```

### Memory Format

Follow the existing OpenClaw pattern:
- `SOUL.md`: Agent identity, personality, instructions
- `memory/YYYY-MM-DD.md`: Daily logs
- `memory/MEMORY.md`: Long-term curated memory
- `workspace/`: Agent's working directory for projects

This is already well-designed in OpenClaw. Don't reinvent it.

---

## 6. NanoClaw as a Template

NanoClaw solves a similar problem in ~3,900 lines. What can VantageOC borrow?

### What NanoClaw Does Well

1. **Clean agent abstraction**: Each agent is a directory with identity + memory + config
2. **Minimal dependencies**: Claude SDK + SQLite + filesystem. No massive frameworks.
3. **Per-session isolation**: Clean separation between conversation contexts
4. **Skills system**: Loadable capabilities per agent
5. **Scheduled tasks**: Cron-like scheduling built-in

### What VantageOC Should Borrow

| NanoClaw Concept | VantageOC Adaptation |
|------------------|---------------------|
| Agent directory structure | Copy directly: `agents/{name}/SOUL.md`, `memory/`, `workspace/` |
| SQLite for state | Copy directly: messages, state, schedules |
| Claude SDK usage | Copy the interaction pattern, simplify if needed |
| Skills loading | Implement if needed; start without for MVP |
| Group memory | Adapt for multi-channel (each channel = group) |

### What VantageOC Should NOT Copy

| NanoClaw Concept | Why Skip It |
|------------------|-------------|
| Container isolation | Overkill for personal tool; adds complexity |
| Docker dependency | Defeats standalone goal |
| Multi-tenant design | You're the only user |
| Heavy security model | You trust your own agents |

### Code Reuse Estimate

If NanoClaw is ~15 source files:
- ~5-6 files are container/isolation machinery: skip
- ~3-4 files are Claude SDK interaction: adapt for VantageOC
- ~3-4 files are memory/state management: port directly
- ~2-3 files are scheduling: simplify and port

You could probably get the core agent runner working in **~500-800 lines of TypeScript**, borrowing patterns from NanoClaw but stripping the container layer.

---

## 7. Recommendation

### The Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI** | Swift (existing VantageOC) | Already built |
| **Agent Runtime** | Node.js sidecar (embedded) | Claude Agent SDK is Node.js |
| **IPC (Swift ↔ Node)** | Unix domain socket + JSON-RPC | Real-time, bidirectional |
| **Agent ↔ Agent** | In-memory EventEmitter + SQLite | Fast runtime, persistent history |
| **State/Memory** | SQLite + filesystem | Simple, inspectable, robust |
| **Scheduler (app open)** | `setInterval()` or `node-cron` | Keep it simple |
| **Scheduler (app closed)** | launchd agent (optional) | Standard macOS pattern |
| **Agent Isolation** | Per-agent directories, shared process | No containers needed |

### Implementation Order

**Phase 1: Core (MVP)**
1. Create Node.js sidecar with embedded agent runner
2. Bundle Node binary in app (use `pkg` or similar to create single executable)
3. Swift spawns sidecar on app launch, kills on quit
4. Unix socket for Swift ↔ Node communication
5. Single agent (e.g., Dru) running, responding to chat

**Phase 2: Multi-Agent**
6. Agent registry: load multiple agents from `agents/` directory
7. Agent router: dispatch messages to correct agent
8. Inter-agent messaging via EventEmitter + SQLite
9. Each agent has own SOUL.md and memory

**Phase 3: Scheduling**
10. Heartbeat system: `setInterval()` for periodic agent wake-ups
11. Agent state tracking in SQLite
12. UI shows agent status (idle, working, last heartbeat)

**Phase 4: Background (Optional)**
13. LaunchAgent plist for background heartbeats
14. Installer/preference to enable background mode
15. Notification support for important agent findings

### Bundle Size Estimate

| Component | Size |
|-----------|------|
| VantageOC Swift app | ~10-20 MB |
| Node.js binary (stripped) | ~40-50 MB |
| Claude Agent SDK + deps | ~20-30 MB |
| Agent runner code | ~1 MB |
| **Total** | **~80-100 MB** |

This is acceptable for a macOS app. Comparable to Electron apps but leaner.

### Single-Person Maintainability

This architecture is maintainable by one person because:
- Two clear layers: Swift UI, Node backend
- No container orchestration to manage
- SQLite is the only database (no external dependencies)
- Agent code is just TypeScript files
- Debugging: `console.log` and SQLite queries
- No Kubernetes, no Docker, no cloud services

---

## Trade-offs Accepted

1. **Two runtimes (Swift + Node)**: Accepted because Claude Agent SDK is Node.js-only. Fighting this would be worse.

2. **No container isolation**: Accepted because this is a personal tool with trusted agents. Security through obscurity (your machine, your agents).

3. **Sidecar process management**: Accepted because it's simpler than embedding Node into Swift or rewriting the Agent SDK.

4. **SQLite for everything**: Accepted because it's simple, robust, and both runtimes can use it. No need for Redis/Postgres/etc.

5. **Background heartbeats require launchd setup**: Accepted as optional feature. Most users will keep the app open.

---

## Appendix: Quick Start Pseudocode

### Swift: Spawn Sidecar

```swift
class AgentSidecar {
    private var process: Process?
    private var socketConnection: UnixSocketConnection?
    
    func start() {
        let nodePath = Bundle.main.path(forResource: "node", ofType: nil, inDirectory: "Resources")!
        let runnerPath = Bundle.main.path(forResource: "agent-runner", ofType: "js", inDirectory: "Resources")!
        
        process = Process()
        process?.executableURL = URL(fileURLWithPath: nodePath)
        process?.arguments = [runnerPath]
        process?.launch()
        
        // Connect via Unix socket
        socketConnection = UnixSocketConnection(path: "/tmp/vantageoc.sock")
        socketConnection?.connect()
    }
    
    func sendMessage(to agent: String, content: String) async -> String {
        let request = JSONRPCRequest(method: "chat", params: ["agent": agent, "content": content])
        return await socketConnection?.send(request)
    }
}
```

### Node: Agent Runner

```typescript
import { createServer } from 'net';
import { Claude } from '@anthropic-ai/claude-agent-sdk';
import Database from 'better-sqlite3';

const db = new Database('~/Library/Application Support/VantageOC/agents.db');
const agents = new Map<string, AgentInstance>();

// Load agents from filesystem
for (const dir of fs.readdirSync(agentsPath)) {
    const soul = fs.readFileSync(`${agentsPath}/${dir}/SOUL.md`, 'utf-8');
    agents.set(dir, new AgentInstance(dir, soul, db));
}

// Unix socket server
const server = createServer((socket) => {
    socket.on('data', async (data) => {
        const { method, params } = JSON.parse(data.toString());
        
        if (method === 'chat') {
            const agent = agents.get(params.agent);
            const response = await agent.chat(params.content);
            socket.write(JSON.stringify({ result: response }));
        }
    });
});

server.listen('/tmp/vantageoc.sock');

// Heartbeats
setInterval(() => {
    for (const [name, agent] of agents) {
        agent.heartbeat();
    }
}, 30 * 60 * 1000); // 30 minutes
```

---

## Conclusion

VantageOC can ship as a standalone macOS app. The path is clear:

1. Embed Node.js + Claude Agent SDK as a sidecar
2. Communicate via Unix socket (Swift ↔ Node) and SQLite (persistence)
3. Run all agents in a single Node process with filesystem-level isolation
4. Use simple timers for heartbeats, optional launchd for background

Don't over-engineer. Start with one agent working end-to-end, then add multi-agent, then scheduling. NanoClaw's patterns are useful, but skip the container layer.

This is buildable by one person. Ship it.

---

*Report generated 2026-03-14*
