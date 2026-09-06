# Burrow Server-Side Runtime: Complete Build Plan

**Document Version:** 1.0  
**Target:** Claude Code Implementation  
**Last Updated:** 2026-03-14

---

## Executive Summary

This document specifies the complete server-side runtime for Burrow — a macOS application that runs personal AI agents inside an isolated Linux VM. The runtime consists of:

1. An Alpine Linux rootfs image bundled in the .app
2. A Node.js agent runner (TypeScript → JS) that runs inside the VM
3. SQLite + filesystem persistence mounted from the host
4. vsock IPC between Swift host and Node.js guest

**The Swift client (VantageOC) is built separately.** This document defines the interface contract the client must implement, but focuses on everything that runs inside the VM.

---

## 1. Repository & Project Structure

### 1.1 Directory Layout

```
burrow/
├── server/                          # Everything that runs inside the VM
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts                 # Entry point
│   │   ├── vsock-server.ts          # vsock IPC handler
│   │   ├── agent-manager.ts         # Agent lifecycle management
│   │   ├── agent.ts                 # Agent class definition
│   │   ├── router.ts                # Message routing (user→agent, agent→agent)
│   │   ├── scheduler.ts             # Heartbeat & cron system
│   │   ├── db.ts                    # SQLite wrapper
│   │   ├── memory.ts                # Agent memory file operations
│   │   ├── tools/                   # Agent tools
│   │   │   ├── index.ts
│   │   │   ├── file-read.ts
│   │   │   ├── file-write.ts
│   │   │   ├── web-fetch.ts
│   │   │   └── shell-exec.ts
│   │   └── types.ts                 # Shared TypeScript types
│   ├── dist/                        # Compiled JS (gitignored, built for release)
│   └── scripts/
│       └── build.sh                 # TypeScript → JS build
│
├── vm/                              # VM image build infrastructure
│   ├── Dockerfile.rootfs            # Alpine rootfs builder
│   ├── build-rootfs.sh              # Builds rootfs on macOS via Docker
│   ├── init.sh                      # VM init script (runs at boot)
│   └── rootfs/                      # Output directory for rootfs.img
│
├── swift/                           # Swift client (separate agent's responsibility)
│   └── README.md                    # Handoff doc pointing to Section 3
│
├── scripts/
│   ├── package-app.sh               # Assembles final .app bundle
│   └── dev-server.sh                # Runs server locally for development
│
└── docs/
    └── ARCHITECTURE.md              # This document (copy for reference)
```

### 1.2 What Lives Where

| Location | Contents |
|----------|----------|
| `Burrow.app/Contents/Resources/rootfs.img` | Alpine Linux rootfs (read-only, ~80MB) |
| `Burrow.app/Contents/Resources/runner/` | Compiled JS agent runner code |
| `~/Library/Application Support/Burrow/agents/` | Agent directories (mounted into VM) |
| `~/Library/Application Support/Burrow/data/` | SQLite database, logs |
| `~/Library/Application Support/Burrow/config.json` | User config (API keys reference, settings) |

### 1.3 Bundle Script (`scripts/package-app.sh`)

```bash
#!/bin/bash
set -euo pipefail

APP_NAME="Burrow"
BUILD_DIR="build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"

# Clean
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/Resources"
mkdir -p "$APP_DIR/Contents/MacOS"

# Copy Swift binary (built separately)
cp "swift/build/Release/Burrow" "$APP_DIR/Contents/MacOS/"

# Copy rootfs image
cp "vm/rootfs/rootfs.img" "$APP_DIR/Contents/Resources/"

# Copy compiled JS runner
cp -r "server/dist" "$APP_DIR/Contents/Resources/runner"

# Copy VM init script
cp "vm/init.sh" "$APP_DIR/Contents/Resources/"

# Info.plist (create or copy)
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Burrow</string>
    <key>CFBundleIdentifier</key>
    <string>com.burrow.app</string>
    <key>CFBundleName</key>
    <string>Burrow</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

echo "Built $APP_DIR"
```

---

## 2. Linux VM / Rootfs

### 2.1 Rootfs Build Strategy

**Decision:** Use Docker buildx on macOS to create the Alpine rootfs. This works without a Linux host and produces a consistent, minimal image.

**Target size:** ~80MB uncompressed (Alpine base + Node.js 20 + essential libs)

### 2.2 Dockerfile.rootfs

```dockerfile
FROM alpine:3.19

# Essential packages
RUN apk add --no-cache \
    nodejs=20.11.1-r0 \
    npm \
    sqlite \
    curl \
    ca-certificates \
    tzdata \
    bash

# Create runtime directories
RUN mkdir -p /app /agents /data /logs

# Set timezone (configurable at runtime via env)
ENV TZ=UTC

# Copy runner code (done at image assembly time, not here)
# The init.sh script handles this

# Cleanup
RUN rm -rf /var/cache/apk/* /tmp/*

# Default command (overridden by init.sh)
CMD ["/bin/sh"]
```

### 2.3 Build Script (`vm/build-rootfs.sh`)

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/rootfs"
ROOTFS_IMG="$OUTPUT_DIR/rootfs.img"

# Ensure output directory
mkdir -p "$OUTPUT_DIR"

# Build for arm64 (Apple Silicon primary)
echo "Building Alpine rootfs for arm64..."
docker buildx build \
    --platform linux/arm64 \
    --file "$SCRIPT_DIR/Dockerfile.rootfs" \
    --output "type=local,dest=$OUTPUT_DIR/rootfs-arm64" \
    "$SCRIPT_DIR"

# Create disk image from rootfs
# Virtualization.framework needs a raw disk image, not a tarball
echo "Creating disk image..."

# Calculate size (add 20% headroom)
ROOTFS_SIZE=$(du -sm "$OUTPUT_DIR/rootfs-arm64" | cut -f1)
IMG_SIZE=$((ROOTFS_SIZE + ROOTFS_SIZE / 5 + 50))  # +20% + 50MB buffer

# Create ext4 image using hdiutil + mke2fs (requires e2fsprogs: brew install e2fsprogs)
dd if=/dev/zero of="$ROOTFS_IMG" bs=1M count="$IMG_SIZE"
$(brew --prefix e2fsprogs)/sbin/mke2fs -t ext4 -d "$OUTPUT_DIR/rootfs-arm64" "$ROOTFS_IMG"

# Cleanup intermediate
rm -rf "$OUTPUT_DIR/rootfs-arm64"

echo "Created $ROOTFS_IMG (${IMG_SIZE}MB)"
```

**Note:** Requires `brew install e2fsprogs` on macOS for `mke2fs`.

### 2.4 VM Init Script (`vm/init.sh`)

This script runs when the VM boots. It's copied into the rootfs and executed by the Virtualization.framework boot config.

```bash
#!/bin/bash
set -e

# Mount points are set up by Virtualization.framework before this runs:
# - /agents  → ~/Library/Application Support/Burrow/agents/ (9p mount, read-write)
# - /data    → ~/Library/Application Support/Burrow/data/ (9p mount, read-write)
# - /app     → Contents/Resources/runner/ (9p mount, read-only)

# Environment variables passed from host:
# - ANTHROPIC_API_KEY (required)
# - BURROW_LOG_LEVEL (optional, default: info)
# - TZ (optional, default: UTC)

export NODE_ENV=production
export LOG_LEVEL="${BURROW_LOG_LEVEL:-info}"

# Start the agent runner
cd /app
exec node index.js
```

### 2.5 VM Configuration (for Swift implementation)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| vCPUs | 2 | Sufficient for Node.js + Claude API calls |
| RAM | 1024 MB | Node.js heap + SQLite, agents are I/O bound not memory bound |
| Disk | Read-only rootfs + mounted writable paths | Separation of concerns |
| Network | NAT (outbound only) | Agents need Claude API + web access |
| Boot time | ~2-3 seconds | Alpine is fast; Node.js startup adds ~1s |

### 2.6 Mount Configuration

The Swift client sets up these virtio-9p mounts before VM boot:

| Host Path | Guest Path | Mode |
|-----------|------------|------|
| `~/Library/Application Support/Burrow/agents/` | `/agents` | read-write |
| `~/Library/Application Support/Burrow/data/` | `/data` | read-write |
| `Burrow.app/Contents/Resources/runner/` | `/app` | read-only |

---

## 3. Virtualization.framework Interface Contract

**This section is the handoff document to the Swift client team.**

### 3.1 Swift API Surface

The Swift client must implement a `BurrowVM` class with this interface:

```swift
// MARK: - Types

struct MountPath {
    let hostPath: URL
    let guestPath: String
    let readOnly: Bool
}

struct VSockMessage: Codable {
    let jsonrpc: String  // Always "2.0"
    let id: Int?
    let method: String?
    let params: [String: AnyCodable]?
    let result: AnyCodable?
    let error: VSockError?
}

struct VSockError: Codable {
    let code: Int
    let message: String
    let data: AnyCodable?
}

enum VMStatus {
    case stopped
    case starting
    case running
    case stopping
    case error(String)
}

// MARK: - BurrowVM Class

class BurrowVM {
    
    /// Current VM status
    var status: VMStatus { get }
    
    /// Status change publisher (for SwiftUI observation)
    var statusPublisher: AnyPublisher<VMStatus, Never> { get }
    
    /// Start the VM with specified mount paths
    /// - Parameters:
    ///   - mounts: Array of host→guest mount configurations
    ///   - environment: Environment variables to pass to guest (ANTHROPIC_API_KEY, etc.)
    func start(mounts: [MountPath], environment: [String: String]) async throws
    
    /// Stop the VM gracefully (sends SIGTERM, waits 5s, then SIGKILL)
    func stop() async
    
    /// Send a JSON-RPC message and wait for response
    /// - Returns: The JSON-RPC response
    func send(message: VSockMessage) async throws -> VSockMessage
    
    /// Send a message and receive streaming responses
    /// - Returns: AsyncStream of partial responses
    func sendStreaming(message: VSockMessage) async throws -> AsyncStream<VSockMessage>
    
    /// Check if VM is healthy (vsock ping)
    func healthCheck() async -> Bool
}
```

### 3.2 vsock Configuration

| Parameter | Value |
|-----------|-------|
| Port | 5000 |
| Protocol | JSON-RPC 2.0 over newline-delimited JSON |
| Framing | Each message is a single JSON object followed by `\n` |
| Encoding | UTF-8 |

### 3.3 Connection Lifecycle

1. **VM Boot:** Swift starts VM with mounts and environment
2. **vsock Listen:** Node.js starts listening on vsock port 5000 within ~3s of boot
3. **Swift Connect:** Swift connects to vsock, sends `ping` to verify
4. **Normal Operation:** Swift sends JSON-RPC requests, Node.js responds
5. **Reconnection:** If connection drops, Swift retries every 1s for 30s before declaring VM unhealthy
6. **Shutdown:** Swift sends `shutdown` RPC, waits for ACK, then stops VM

### 3.4 Environment Variables (Host → Guest)

These are passed to the VM at boot time:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from host keychain |
| `BURROW_LOG_LEVEL` | No | `debug`, `info`, `warn`, `error` (default: `info`) |
| `TZ` | No | Timezone (default: `UTC`) |

**Security Decision:** Pass API key as environment variable at boot. This is simpler and secure enough for a single-user desktop app. A host-side proxy would add complexity without meaningful security benefit since the VM has network access anyway.

### 3.5 First-Launch Setup

On first launch, Swift must create these directories before starting the VM:

```
~/Library/Application Support/Burrow/
├── agents/           # Empty, user adds agents later
├── data/
│   └── burrow.db     # Created by Node.js on first run
└── config.json       # Created by Swift with defaults
```

---

## 4. Node.js Agent Runner Architecture

### 4.1 Entry Point (`src/index.ts`)

```typescript
import { VsockServer } from './vsock-server';
import { AgentManager } from './agent-manager';
import { Database } from './db';
import { Scheduler } from './scheduler';
import { Router } from './router';
import { logger } from './logger';

async function main() {
  logger.info('Burrow agent runner starting...');

  // Initialize database
  const db = new Database('/data/burrow.db');
  await db.initialize();

  // Initialize agent manager
  const agentManager = new AgentManager('/agents', db);
  await agentManager.loadAgents();

  // Initialize router
  const router = new Router(agentManager, db);

  // Initialize scheduler
  const scheduler = new Scheduler(agentManager, db);
  await scheduler.start();

  // Start vsock server
  const server = new VsockServer(router, agentManager, scheduler);
  await server.listen(5000);

  logger.info('Burrow agent runner ready');

  // Handle shutdown
  process.on('SIGTERM', async () => {
    logger.info('Shutting down...');
    await scheduler.stop();
    await server.close();
    await db.close();
    process.exit(0);
  });
}

main().catch((err) => {
  logger.error('Fatal error:', err);
  process.exit(1);
});
```

### 4.2 Agent Manager (`src/agent-manager.ts`)

```typescript
import { Agent, AgentConfig } from './agent';
import { Database } from './db';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
import { logger } from './logger';

export class AgentManager {
  private agents: Map<string, Agent> = new Map();
  private agentsDir: string;
  private db: Database;

  constructor(agentsDir: string, db: Database) {
    this.agentsDir = agentsDir;
    this.db = db;
  }

  async loadAgents(): Promise<void> {
    const dirs = readdirSync(this.agentsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const agentId of dirs) {
      try {
        await this.loadAgent(agentId);
      } catch (err) {
        logger.error(`Failed to load agent ${agentId}:`, err);
      }
    }

    logger.info(`Loaded ${this.agents.size} agents`);
  }

  private async loadAgent(agentId: string): Promise<void> {
    const agentDir = join(this.agentsDir, agentId);
    const soulPath = join(agentDir, 'SOUL.md');

    if (!existsSync(soulPath)) {
      throw new Error(`Agent ${agentId} missing SOUL.md`);
    }

    const soul = readFileSync(soulPath, 'utf-8');
    
    // Optional: AGENTS.md for operational rules
    const agentsPath = join(agentDir, 'AGENTS.md');
    const agentsMd = existsSync(agentsPath) 
      ? readFileSync(agentsPath, 'utf-8') 
      : null;

    // Load or create agent state from DB
    const state = await this.db.getAgentState(agentId);

    const config: AgentConfig = {
      id: agentId,
      name: this.extractName(soul) || agentId,
      soul,
      agentsMd,
      memoryPath: join(agentDir, 'memory'),
      workspacePath: join(agentDir, 'workspace'),
      heartbeatIntervalMs: state?.heartbeatIntervalMs || 30 * 60 * 1000, // 30 min default
    };

    const agent = new Agent(config, this.db);
    await agent.initialize();
    this.agents.set(agentId, agent);
  }

  private extractName(soul: string): string | null {
    // Extract name from SOUL.md front matter or first heading
    const nameMatch = soul.match(/^#\s+(.+?)(?:\s*[-—]|$)/m) 
      || soul.match(/\*\*Name:\*\*\s*(.+)/);
    return nameMatch ? nameMatch[1].trim() : null;
  }

  getAgent(id: string): Agent | undefined {
    return this.agents.get(id);
  }

  getAllAgents(): Agent[] {
    return Array.from(this.agents.values());
  }

  async reloadAgent(id: string): Promise<void> {
    const existing = this.agents.get(id);
    if (existing) {
      await existing.shutdown();
    }
    await this.loadAgent(id);
  }
}
```

### 4.3 Agent Class (`src/agent.ts`)

```typescript
import Anthropic from '@anthropic-ai/sdk';
import { Database } from './db';
import { MemoryManager } from './memory';
import { createTools } from './tools';
import { logger } from './logger';

export interface AgentConfig {
  id: string;
  name: string;
  soul: string;
  agentsMd: string | null;
  memoryPath: string;
  workspacePath: string;
  heartbeatIntervalMs: number;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'busy' | 'error';
  lastActivity: number;
  lastHeartbeat: number | null;
  currentTask: string | null;
  errorMessage: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export class Agent {
  private config: AgentConfig;
  private db: Database;
  private memory: MemoryManager;
  private anthropic: Anthropic;
  private conversationHistory: ChatMessage[] = [];
  private status: AgentStatus['status'] = 'idle';
  private currentTask: string | null = null;
  private lastActivity: number = Date.now();
  private lastHeartbeat: number | null = null;
  private errorMessage: string | null = null;

  constructor(config: AgentConfig, db: Database) {
    this.config = config;
    this.db = db;
    this.memory = new MemoryManager(config.memoryPath);
    this.anthropic = new Anthropic(); // Uses ANTHROPIC_API_KEY env var
  }

  async initialize(): Promise<void> {
    // Load recent conversation history from DB
    const history = await this.db.getRecentMessages(this.config.id, 20);
    this.conversationHistory = history;

    // Load last heartbeat time
    const state = await this.db.getAgentState(this.config.id);
    this.lastHeartbeat = state?.lastHeartbeat || null;
  }

  async chat(message: string, userId: string = 'user'): Promise<AsyncGenerator<string>> {
    this.status = 'busy';
    this.currentTask = 'Processing chat message';
    this.lastActivity = Date.now();

    try {
      // Build system prompt
      const systemPrompt = this.buildSystemPrompt();

      // Add user message to history
      this.conversationHistory.push({ role: 'user', content: message });

      // Persist user message
      await this.db.insertMessage({
        agentId: this.config.id,
        role: 'user',
        content: message,
        userId,
        timestamp: Date.now(),
      });

      // Create streaming response
      const stream = await this.anthropic.messages.stream({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8192,
        system: systemPrompt,
        messages: this.conversationHistory.map(m => ({
          role: m.role,
          content: m.content,
        })),
        tools: createTools(this.config.workspacePath),
      });

      // Return async generator that yields chunks
      return this.processStream(stream);

    } catch (err) {
      this.status = 'error';
      this.errorMessage = err instanceof Error ? err.message : String(err);
      throw err;
    }
  }

  private async *processStream(stream: any): AsyncGenerator<string> {
    let fullResponse = '';

    for await (const event of stream) {
      if (event.type === 'content_block_delta') {
        const text = event.delta?.text || '';
        fullResponse += text;
        yield text;
      }
    }

    // Get final message for tool use handling
    const finalMessage = await stream.finalMessage();

    // Handle tool use if present
    if (finalMessage.stop_reason === 'tool_use') {
      // Process tool calls and continue conversation
      // (Simplified - full implementation would loop until no more tool calls)
      const toolResults = await this.executeToolCalls(finalMessage.content);
      // Continue conversation with tool results...
    }

    // Add assistant response to history
    this.conversationHistory.push({ role: 'assistant', content: fullResponse });

    // Persist assistant message
    await this.db.insertMessage({
      agentId: this.config.id,
      role: 'assistant',
      content: fullResponse,
      timestamp: Date.now(),
    });

    // Trim history if too long (keep last 50 messages)
    if (this.conversationHistory.length > 50) {
      this.conversationHistory = this.conversationHistory.slice(-50);
    }

    this.status = 'idle';
    this.currentTask = null;
  }

  private async executeToolCalls(content: any[]): Promise<any[]> {
    // Implementation for tool execution
    // Returns array of tool results to feed back to Claude
    return [];
  }

  private buildSystemPrompt(): string {
    const parts: string[] = [];

    // Core identity from SOUL.md
    parts.push(this.config.soul);

    // Operational rules from AGENTS.md if present
    if (this.config.agentsMd) {
      parts.push('\n---\n## Operational Rules\n' + this.config.agentsMd);
    }

    // Memory context (L0 index + today's notes)
    const memoryContext = this.memory.getContextForPrompt();
    if (memoryContext) {
      parts.push('\n---\n## Memory Context\n' + memoryContext);
    }

    // Current date/time
    parts.push(`\n---\nCurrent time: ${new Date().toISOString()}`);

    return parts.join('\n');
  }

  async heartbeat(): Promise<string> {
    this.status = 'busy';
    this.currentTask = 'Running heartbeat';
    this.lastActivity = Date.now();

    try {
      // Read HEARTBEAT.md if it exists
      const heartbeatPrompt = this.memory.getHeartbeatPrompt() 
        || 'Check if anything needs attention. If not, respond with HEARTBEAT_OK.';

      // Run a chat turn with heartbeat prompt
      let response = '';
      for await (const chunk of await this.chat(heartbeatPrompt, 'system')) {
        response += chunk;
      }

      // Update heartbeat timestamp
      this.lastHeartbeat = Date.now();
      await this.db.updateAgentState(this.config.id, {
        lastHeartbeat: this.lastHeartbeat,
      });

      this.status = 'idle';
      this.currentTask = null;
      return response;

    } catch (err) {
      this.status = 'error';
      this.errorMessage = err instanceof Error ? err.message : String(err);
      throw err;
    }
  }

  getStatus(): AgentStatus {
    return {
      id: this.config.id,
      name: this.config.name,
      status: this.status,
      lastActivity: this.lastActivity,
      lastHeartbeat: this.lastHeartbeat,
      currentTask: this.currentTask,
      errorMessage: this.errorMessage,
    };
  }

  async shutdown(): Promise<void> {
    // Save any pending state
    await this.db.updateAgentState(this.config.id, {
      lastHeartbeat: this.lastHeartbeat,
    });
  }
}
```

### 4.4 Tools Available to Agents

Agents inside the VM have access to these tools:

| Tool | Description | Scope |
|------|-------------|-------|
| `file_read` | Read files from agent's workspace | `/agents/{id}/workspace/` only |
| `file_write` | Write files to agent's workspace | `/agents/{id}/workspace/` only |
| `memory_read` | Read memory files | `/agents/{id}/memory/` only |
| `memory_write` | Write memory files | `/agents/{id}/memory/` only |
| `web_fetch` | HTTP GET with content extraction | Any URL (outbound network) |
| `shell_exec` | Execute shell commands | Limited to safe commands |

**Security:** Tools are sandboxed to the agent's own directories. No cross-agent file access.

---

## 5. Inter-Agent Communication

### 5.1 Router Design (`src/router.ts`)

```typescript
import { EventEmitter } from 'events';
import { AgentManager } from './agent-manager';
import { Database } from './db';
import { logger } from './logger';

export interface AgentMessage {
  id: string;
  from: string;           // Agent ID or 'user'
  to: string[];           // Agent IDs, or ['*'] for broadcast
  content: string;
  timestamp: number;
  inReplyTo?: string;     // Parent message ID for threading
}

export class Router extends EventEmitter {
  private agentManager: AgentManager;
  private db: Database;
  private messageQueue: Map<string, AgentMessage[]> = new Map();

  constructor(agentManager: AgentManager, db: Database) {
    super();
    this.agentManager = agentManager;
    this.db = db;
  }

  async routeToAgent(agentId: string, message: string, from: string = 'user'): Promise<AsyncGenerator<string>> {
    const agent = this.agentManager.getAgent(agentId);
    if (!agent) {
      throw new Error(`Agent not found: ${agentId}`);
    }

    // Persist the message
    const msgRecord: AgentMessage = {
      id: crypto.randomUUID(),
      from,
      to: [agentId],
      content: message,
      timestamp: Date.now(),
    };
    await this.db.insertChannelMessage(msgRecord);

    // Route to agent
    return agent.chat(message, from);
  }

  async broadcast(message: string, from: string, excludeAgentIds: string[] = []): Promise<void> {
    const agents = this.agentManager.getAllAgents()
      .filter(a => !excludeAgentIds.includes(a.getStatus().id));

    const msgRecord: AgentMessage = {
      id: crypto.randomUUID(),
      from,
      to: ['*'],
      content: message,
      timestamp: Date.now(),
    };
    await this.db.insertChannelMessage(msgRecord);

    // Queue message for each agent (they process on next heartbeat or activity)
    for (const agent of agents) {
      const agentId = agent.getStatus().id;
      if (!this.messageQueue.has(agentId)) {
        this.messageQueue.set(agentId, []);
      }
      this.messageQueue.get(agentId)!.push(msgRecord);
    }

    // Emit event for real-time listeners
    this.emit('broadcast', msgRecord);
  }

  async sendToAgents(toAgentIds: string[], message: string, from: string): Promise<void> {
    const msgRecord: AgentMessage = {
      id: crypto.randomUUID(),
      from,
      to: toAgentIds,
      content: message,
      timestamp: Date.now(),
    };
    await this.db.insertChannelMessage(msgRecord);

    for (const agentId of toAgentIds) {
      if (!this.messageQueue.has(agentId)) {
        this.messageQueue.set(agentId, []);
      }
      this.messageQueue.get(agentId)!.push(msgRecord);
    }

    this.emit('message', msgRecord);
  }

  getPendingMessages(agentId: string): AgentMessage[] {
    const messages = this.messageQueue.get(agentId) || [];
    this.messageQueue.set(agentId, []); // Clear after retrieval
    return messages;
  }
}
```

### 5.2 Message Flow

1. **User → Agent:** Direct via `router.routeToAgent(agentId, message)`
2. **Agent → Agent (targeted):** Agent calls tool that invokes `router.sendToAgents([targetId], message, fromId)`
3. **Agent → All (broadcast):** Agent calls tool that invokes `router.broadcast(message, fromId)`
4. **Pending delivery:** Messages queue until agent's next activity or heartbeat

### 5.3 SQLite Message Schema

See Section 7 for complete DDL. Key table: `channel_messages`.

---

## 6. vsock IPC Protocol

### 6.1 JSON-RPC 2.0 Message Format

All messages are JSON-RPC 2.0, newline-delimited.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "chat",
  "params": {
    "agentId": "assistant",
    "message": "Hello, how are you?"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": "I'm doing well, thank you for asking!"
  }
}
```

**Streaming Response (multiple messages with same ID):**
```json
{"jsonrpc": "2.0", "id": 1, "result": {"chunk": "I'm ", "done": false}}
{"jsonrpc": "2.0", "id": 1, "result": {"chunk": "doing well!", "done": false}}
{"jsonrpc": "2.0", "id": 1, "result": {"chunk": "", "done": true, "fullContent": "I'm doing well!"}}
```

**Error:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Agent not found",
    "data": { "agentId": "unknown" }
  }
}
```

### 6.2 Method Reference

| Method | Params | Returns | Description |
|--------|--------|---------|-------------|
| `ping` | none | `{ "pong": true }` | Health check |
| `chat` | `{ agentId, message, stream? }` | `{ content }` or stream | Send message to agent |
| `heartbeat` | `{ agentId? }` | `{ responses: [...] }` | Trigger heartbeat (one or all) |
| `status` | none | `{ agents: [...] }` | Get all agent statuses |
| `agents.list` | none | `{ agents: [...] }` | List agents with metadata |
| `agents.reload` | `{ agentId }` | `{ success: true }` | Hot-reload an agent |
| `broadcast` | `{ message, from? }` | `{ delivered: number }` | Broadcast to all agents |
| `shutdown` | none | `{ ack: true }` | Graceful shutdown |

### 6.3 Error Codes

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

### 6.4 vsock Server (`src/vsock-server.ts`)

```typescript
import { createServer, Socket } from 'net';
import { Router } from './router';
import { AgentManager } from './agent-manager';
import { Scheduler } from './scheduler';
import { logger } from './logger';

interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: number | string | null;
  method: string;
  params?: Record<string, any>;
}

interface JsonRpcResponse {
  jsonrpc: '2.0';
  id: number | string | null;
  result?: any;
  error?: { code: number; message: string; data?: any };
}

export class VsockServer {
  private router: Router;
  private agentManager: AgentManager;
  private scheduler: Scheduler;
  private server: ReturnType<typeof createServer> | null = null;
  private connections: Set<Socket> = new Set();

  constructor(router: Router, agentManager: AgentManager, scheduler: Scheduler) {
    this.router = router;
    this.agentManager = agentManager;
    this.scheduler = scheduler;
  }

  async listen(port: number): Promise<void> {
    return new Promise((resolve) => {
      // In actual VM, this would use vsock. For development, use TCP.
      // The vsock binding is handled by the VM's virtio-vsock device.
      this.server = createServer((socket) => this.handleConnection(socket));
      
      // vsock uses AF_VSOCK but Node.js net module abstracts this
      // The VM kernel maps vsock port to TCP-like interface
      this.server.listen(port, () => {
        logger.info(`vsock server listening on port ${port}`);
        resolve();
      });
    });
  }

  private handleConnection(socket: Socket): void {
    this.connections.add(socket);
    let buffer = '';

    socket.on('data', async (data) => {
      buffer += data.toString();
      
      // Process complete lines (newline-delimited JSON)
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
          const request: JsonRpcRequest = JSON.parse(line);
          await this.handleRequest(socket, request);
        } catch (err) {
          this.sendError(socket, null, -32700, 'Parse error');
        }
      }
    });

    socket.on('close', () => {
      this.connections.delete(socket);
    });

    socket.on('error', (err) => {
      logger.error('Socket error:', err);
      this.connections.delete(socket);
    });
  }

  private async handleRequest(socket: Socket, request: JsonRpcRequest): Promise<void> {
    const { id, method, params } = request;

    try {
      switch (method) {
        case 'ping':
          this.sendResult(socket, id, { pong: true });
          break;

        case 'chat':
          await this.handleChat(socket, id, params);
          break;

        case 'heartbeat':
          await this.handleHeartbeat(socket, id, params);
          break;

        case 'status':
          this.handleStatus(socket, id);
          break;

        case 'agents.list':
          this.handleAgentsList(socket, id);
          break;

        case 'agents.reload':
          await this.handleAgentsReload(socket, id, params);
          break;

        case 'broadcast':
          await this.handleBroadcast(socket, id, params);
          break;

        case 'shutdown':
          this.sendResult(socket, id, { ack: true });
          process.emit('SIGTERM');
          break;

        default:
          this.sendError(socket, id, -32601, `Method not found: ${method}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.sendError(socket, id, -32603, message);
    }
  }

  private async handleChat(socket: Socket, id: any, params: any): Promise<void> {
    const { agentId, message, stream = true } = params || {};

    if (!agentId || !message) {
      this.sendError(socket, id, -32602, 'Missing agentId or message');
      return;
    }

    const agent = this.agentManager.getAgent(agentId);
    if (!agent) {
      this.sendError(socket, id, -32000, 'Agent not found', { agentId });
      return;
    }

    if (stream) {
      // Streaming response
      const generator = await agent.chat(message);
      for await (const chunk of generator) {
        this.sendResult(socket, id, { chunk, done: false });
      }
      // Final message
      this.sendResult(socket, id, { chunk: '', done: true });
    } else {
      // Collect full response
      let content = '';
      const generator = await agent.chat(message);
      for await (const chunk of generator) {
        content += chunk;
      }
      this.sendResult(socket, id, { content });
    }
  }

  private async handleHeartbeat(socket: Socket, id: any, params: any): Promise<void> {
    const { agentId } = params || {};
    const responses: Array<{ agentId: string; response: string }> = [];

    if (agentId) {
      const agent = this.agentManager.getAgent(agentId);
      if (!agent) {
        this.sendError(socket, id, -32000, 'Agent not found', { agentId });
        return;
      }
      const response = await agent.heartbeat();
      responses.push({ agentId, response });
    } else {
      // All agents
      for (const agent of this.agentManager.getAllAgents()) {
        try {
          const response = await agent.heartbeat();
          responses.push({ agentId: agent.getStatus().id, response });
        } catch (err) {
          responses.push({ 
            agentId: agent.getStatus().id, 
            response: `Error: ${err instanceof Error ? err.message : String(err)}` 
          });
        }
      }
    }

    this.sendResult(socket, id, { responses });
  }

  private handleStatus(socket: Socket, id: any): void {
    const agents = this.agentManager.getAllAgents().map(a => a.getStatus());
    this.sendResult(socket, id, { agents });
  }

  private handleAgentsList(socket: Socket, id: any): void {
    const agents = this.agentManager.getAllAgents().map(a => {
      const status = a.getStatus();
      return {
        id: status.id,
        name: status.name,
        status: status.status,
      };
    });
    this.sendResult(socket, id, { agents });
  }

  private async handleAgentsReload(socket: Socket, id: any, params: any): Promise<void> {
    const { agentId } = params || {};
    if (!agentId) {
      this.sendError(socket, id, -32602, 'Missing agentId');
      return;
    }
    await this.agentManager.reloadAgent(agentId);
    this.sendResult(socket, id, { success: true });
  }

  private async handleBroadcast(socket: Socket, id: any, params: any): Promise<void> {
    const { message, from = 'user' } = params || {};
    if (!message) {
      this.sendError(socket, id, -32602, 'Missing message');
      return;
    }
    await this.router.broadcast(message, from);
    this.sendResult(socket, id, { delivered: this.agentManager.getAllAgents().length });
  }

  private sendResult(socket: Socket, id: any, result: any): void {
    const response: JsonRpcResponse = { jsonrpc: '2.0', id, result };
    socket.write(JSON.stringify(response) + '\n');
  }

  private sendError(socket: Socket, id: any, code: number, message: string, data?: any): void {
    const response: JsonRpcResponse = { 
      jsonrpc: '2.0', 
      id, 
      error: { code, message, data } 
    };
    socket.write(JSON.stringify(response) + '\n');
  }

  async close(): Promise<void> {
    for (const socket of this.connections) {
      socket.end();
    }
    this.connections.clear();
    
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => resolve());
      } else {
        resolve();
      }
    });
  }
}
```

---

## 7. SQLite Schema

### 7.1 Complete DDL

```sql
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Agent state
CREATE TABLE IF NOT EXISTS agent_state (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    heartbeat_interval_ms INTEGER NOT NULL DEFAULT 1800000,  -- 30 min
    last_heartbeat INTEGER,
    last_activity INTEGER,
    status TEXT NOT NULL DEFAULT 'idle',
    error_message TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Message history (user ↔ agent conversations)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    user_id TEXT,  -- 'user', 'system', or another agent_id
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agent_state(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_agent_time ON messages(agent_id, timestamp DESC);

-- Channel messages (inter-agent communication)
CREATE TABLE IF NOT EXISTS channel_messages (
    id TEXT PRIMARY KEY,
    from_id TEXT NOT NULL,
    to_ids TEXT NOT NULL,  -- JSON array: ["agent1", "agent2"] or ["*"]
    content TEXT NOT NULL,
    in_reply_to TEXT,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (in_reply_to) REFERENCES channel_messages(id)
);

CREATE INDEX IF NOT EXISTS idx_channel_messages_time ON channel_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_channel_messages_from ON channel_messages(from_id);

-- Scheduled tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_type TEXT NOT NULL CHECK (task_type IN ('heartbeat', 'cron', 'once')),
    cron_expression TEXT,  -- For cron type: "0 */30 * * * *"
    run_at INTEGER,        -- For once type: specific timestamp
    last_run INTEGER,
    next_run INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1,
    payload TEXT,          -- JSON payload for task
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    FOREIGN KEY (agent_id) REFERENCES agent_state(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next ON scheduled_tasks(next_run) WHERE enabled = 1;
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_agent ON scheduled_tasks(agent_id);

-- Task execution log
CREATE TABLE IF NOT EXISTS task_log (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    completed_at INTEGER,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'error')),
    error_message TEXT,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_log_task ON task_log(task_id, started_at DESC);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version) VALUES (1);
```

### 7.2 Migration Strategy

```typescript
// src/db.ts (migration section)

const MIGRATIONS: { version: number; sql: string }[] = [
  {
    version: 1,
    sql: `-- Initial schema (see above)`,
  },
  {
    version: 2,
    sql: `
      -- Example future migration
      ALTER TABLE agent_state ADD COLUMN config_json TEXT;
    `,
  },
];

async function migrate(db: BetterSqlite3.Database): Promise<void> {
  const currentVersion = db.prepare(
    'SELECT MAX(version) as v FROM schema_version'
  ).get() as { v: number } | undefined;
  
  const version = currentVersion?.v || 0;

  for (const migration of MIGRATIONS) {
    if (migration.version > version) {
      db.exec(migration.sql);
      db.prepare('INSERT INTO schema_version (version) VALUES (?)').run(migration.version);
      logger.info(`Applied migration ${migration.version}`);
    }
  }
}
```

---

## 8. Agent Memory & Workspace Layout

### 8.1 Directory Structure

Each agent has this structure under `/agents/{agent-id}/`:

```
/agents/
└── {agent-id}/
    ├── SOUL.md              # Required: agent identity & personality
    ├── AGENTS.md            # Optional: operational rules
    ├── HEARTBEAT.md         # Optional: heartbeat instructions
    ├── memory/
    │   ├── MEMORY-L0.md     # L0: one-liner index (~20 lines max)
    │   ├── MEMORY.md        # L1: key facts per topic
    │   ├── topics/          # L2: detailed topic files
    │   │   └── {topic}.md
    │   └── {YYYY-MM-DD}.md  # Daily notes
    └── workspace/
        └── (agent working files, sandboxed)
```

### 8.2 Memory Manager (`src/memory.ts`)

```typescript
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from 'fs';
import { join, dirname } from 'path';

export class MemoryManager {
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
    this.ensureDirectories();
  }

  private ensureDirectories(): void {
    const dirs = [this.basePath, join(this.basePath, 'topics')];
    for (const dir of dirs) {
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
    }
  }

  // Read file if exists, return null otherwise
  private readIfExists(path: string): string | null {
    if (existsSync(path)) {
      return readFileSync(path, 'utf-8');
    }
    return null;
  }

  // Build context string for system prompt injection
  getContextForPrompt(): string | null {
    const parts: string[] = [];

    // L0: always load (tiny)
    const l0 = this.readIfExists(join(this.basePath, 'MEMORY-L0.md'));
    if (l0) {
      parts.push('### Memory Index (L0)\n' + l0);
    }

    // Today's daily notes
    const today = new Date().toISOString().split('T')[0];
    const dailyPath = join(this.basePath, `${today}.md`);
    const daily = this.readIfExists(dailyPath);
    if (daily) {
      parts.push(`### Today's Notes (${today})\n` + daily);
    }

    // Yesterday's notes (for continuity)
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
    const yesterdayPath = join(this.basePath, `${yesterday}.md`);
    const yesterdayNotes = this.readIfExists(yesterdayPath);
    if (yesterdayNotes) {
      parts.push(`### Yesterday's Notes (${yesterday})\n` + yesterdayNotes);
    }

    return parts.length > 0 ? parts.join('\n\n') : null;
  }

  // Get heartbeat instructions
  getHeartbeatPrompt(): string | null {
    const heartbeatPath = join(dirname(this.basePath), 'HEARTBEAT.md');
    return this.readIfExists(heartbeatPath);
  }

  // Write to daily notes
  appendToDaily(content: string): void {
    const today = new Date().toISOString().split('T')[0];
    const dailyPath = join(this.basePath, `${today}.md`);
    
    const existing = this.readIfExists(dailyPath) || '';
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const entry = `\n## ${timestamp}\n${content}\n`;
    
    writeFileSync(dailyPath, existing + entry);
  }

  // Write to specific memory file
  writeMemory(filename: string, content: string): void {
    const fullPath = join(this.basePath, filename);
    mkdirSync(dirname(fullPath), { recursive: true });
    writeFileSync(fullPath, content);
  }

  // Read specific memory file
  readMemory(filename: string): string | null {
    return this.readIfExists(join(this.basePath, filename));
  }

  // List all daily note files
  listDailyNotes(): string[] {
    const files = readdirSync(this.basePath);
    return files.filter(f => /^\d{4}-\d{2}-\d{2}\.md$/.test(f)).sort().reverse();
  }
}
```

### 8.3 SOUL.md Loading

SOUL.md is loaded once at agent initialization and injected as the first part of the system prompt. It's re-read on `agents.reload` RPC call, allowing hot-reload of agent personality without VM restart.

---

## 9. Heartbeat / Scheduler System

### 9.1 Scheduler (`src/scheduler.ts`)

```typescript
import { AgentManager } from './agent-manager';
import { Database } from './db';
import { logger } from './logger';
import * as cron from 'node-cron';

interface ScheduledTask {
  id: string;
  agentId: string;
  taskType: 'heartbeat' | 'cron' | 'once';
  cronExpression?: string;
  runAt?: number;
  lastRun?: number;
  nextRun?: number;
  enabled: boolean;
  payload?: string;
}

export class Scheduler {
  private agentManager: AgentManager;
  private db: Database;
  private cronJobs: Map<string, cron.ScheduledTask> = new Map();
  private heartbeatTimers: Map<string, NodeJS.Timeout> = new Map();
  private running: boolean = false;
  private runningTasks: Set<string> = new Set(); // Prevents concurrent runs

  constructor(agentManager: AgentManager, db: Database) {
    this.agentManager = agentManager;
    this.db = db;
  }

  async start(): Promise<void> {
    this.running = true;
    
    // Load scheduled tasks from DB
    const tasks = await this.db.getScheduledTasks();
    
    for (const task of tasks) {
      this.scheduleTask(task);
    }

    // Set up heartbeats for all agents
    for (const agent of this.agentManager.getAllAgents()) {
      const status = agent.getStatus();
      this.setupHeartbeat(status.id);
    }

    // Check for one-time tasks every minute
    setInterval(() => this.checkOnceTasks(), 60000);

    logger.info('Scheduler started');
  }

  async stop(): Promise<void> {
    this.running = false;

    // Stop all cron jobs
    for (const [id, job] of this.cronJobs) {
      job.stop();
    }
    this.cronJobs.clear();

    // Clear all heartbeat timers
    for (const [id, timer] of this.heartbeatTimers) {
      clearInterval(timer);
    }
    this.heartbeatTimers.clear();

    logger.info('Scheduler stopped');
  }

  private setupHeartbeat(agentId: string): void {
    const agent = this.agentManager.getAgent(agentId);
    if (!agent) return;

    // Default: 30 minutes
    const intervalMs = 30 * 60 * 1000;

    const timer = setInterval(async () => {
      if (!this.running) return;
      if (this.runningTasks.has(`heartbeat:${agentId}`)) {
        logger.debug(`Skipping heartbeat for ${agentId} - already running`);
        return;
      }

      try {
        this.runningTasks.add(`heartbeat:${agentId}`);
        await agent.heartbeat();
        logger.debug(`Heartbeat completed for ${agentId}`);
      } catch (err) {
        logger.error(`Heartbeat failed for ${agentId}:`, err);
      } finally {
        this.runningTasks.delete(`heartbeat:${agentId}`);
      }
    }, intervalMs);

    this.heartbeatTimers.set(agentId, timer);
  }

  private scheduleTask(task: ScheduledTask): void {
    if (!task.enabled) return;

    if (task.taskType === 'cron' && task.cronExpression) {
      const job = cron.schedule(task.cronExpression, async () => {
        await this.runTask(task);
      });
      this.cronJobs.set(task.id, job);
    }
  }

  private async runTask(task: ScheduledTask): Promise<void> {
    if (this.runningTasks.has(task.id)) {
      logger.debug(`Skipping task ${task.id} - already running`);
      return;
    }

    const agent = this.agentManager.getAgent(task.agentId);
    if (!agent) {
      logger.warn(`Agent not found for task ${task.id}: ${task.agentId}`);
      return;
    }

    this.runningTasks.add(task.id);
    const logId = crypto.randomUUID();

    try {
      await this.db.insertTaskLog({
        id: logId,
        taskId: task.id,
        agentId: task.agentId,
        startedAt: Date.now(),
        status: 'running',
      });

      // Execute based on task type
      if (task.taskType === 'heartbeat') {
        await agent.heartbeat();
      } else if (task.payload) {
        // Custom task - send payload as message
        const generator = await agent.chat(task.payload, 'scheduler');
        let response = '';
        for await (const chunk of generator) {
          response += chunk;
        }
      }

      await this.db.updateTaskLog(logId, {
        completedAt: Date.now(),
        status: 'success',
      });

      await this.db.updateScheduledTask(task.id, {
        lastRun: Date.now(),
      });

    } catch (err) {
      await this.db.updateTaskLog(logId, {
        completedAt: Date.now(),
        status: 'error',
        errorMessage: err instanceof Error ? err.message : String(err),
      });
    } finally {
      this.runningTasks.delete(task.id);
    }
  }

  private async checkOnceTasks(): Promise<void> {
    const now = Date.now();
    const tasks = await this.db.getDueOnceTasks(now);
    
    for (const task of tasks) {
      await this.runTask(task);
      await this.db.updateScheduledTask(task.id, { enabled: false });
    }
  }

  // API for adding new scheduled tasks
  async addTask(task: Omit<ScheduledTask, 'id'>): Promise<string> {
    const id = crypto.randomUUID();
    await this.db.insertScheduledTask({ ...task, id });
    this.scheduleTask({ ...task, id });
    return id;
  }

  async removeTask(taskId: string): Promise<void> {
    const job = this.cronJobs.get(taskId);
    if (job) {
      job.stop();
      this.cronJobs.delete(taskId);
    }
    await this.db.deleteScheduledTask(taskId);
  }
}
```

### 9.2 Background Mode (Optional launchd)

For running heartbeats when the app is closed, define a launchd plist:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.burrow.heartbeat</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Burrow.app/Contents/MacOS/Burrow</string>
        <string>--headless</string>
        <string>--heartbeat-only</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer><!-- 30 minutes -->
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/burrow-heartbeat.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/burrow-heartbeat.log</string>
</dict>
</plist>
```

**Installation:** The Swift app can install/remove this plist to `~/Library/LaunchAgents/` based on user preference.

---

## 10. Build & Packaging

### 10.1 TypeScript Build (`server/scripts/build.sh`)

```bash
#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Installing dependencies..."
npm ci

echo "Building TypeScript..."
npx tsc

echo "Bundling with esbuild..."
npx esbuild dist/index.js \
    --bundle \
    --platform=node \
    --target=node20 \
    --outfile=dist/bundle.js \
    --external:better-sqlite3 \
    --minify

# Copy native modules
cp node_modules/better-sqlite3/build/Release/better_sqlite3.node dist/

echo "Build complete: dist/"
```

### 10.2 package.json

```json
{
  "name": "burrow-runner",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "./scripts/build.sh",
    "dev": "tsx watch src/index.ts",
    "test": "vitest"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.30.0",
    "better-sqlite3": "^11.0.0",
    "node-cron": "^3.0.3"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.8",
    "@types/node": "^20.0.0",
    "esbuild": "^0.20.0",
    "tsx": "^4.0.0",
    "typescript": "^5.4.0",
    "vitest": "^1.0.0"
  }
}
```

### 10.3 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 10.4 First-Launch Setup

The Swift client handles first-launch:

1. Create `~/Library/Application Support/Burrow/` directory
2. Create `agents/` and `data/` subdirectories
3. Create default `config.json`
4. Copy a sample agent (optional, or start empty)

The Node.js runner handles:

1. Create SQLite database if not exists
2. Run migrations
3. Load any agents present in `/agents/`

### 10.5 Update Strategy

**Runner code updates:** Ship new JS in `Contents/Resources/runner/`. Since it's mounted read-only into the VM, the next VM boot picks up new code. No rootfs rebuild needed.

**Rootfs updates:** Only needed for Node.js version changes or new system packages. Rare. Ship new rootfs.img, replace in app bundle.

**Agent updates:** User modifies files in `~/Library/Application Support/Burrow/agents/`. Call `agents.reload` RPC to pick up changes without VM restart.

---

## 11. Security Model

### 11.1 VM Isolation

| Access | Allowed | Notes |
|--------|---------|-------|
| Host filesystem | Only mounted paths | `/agents`, `/data`, `/app` |
| Network | Outbound only | NAT via Virtualization.framework |
| Host processes | None | No access to host PIDs |
| Host memory | None | VM is isolated |

### 11.2 Agent Sandboxing

Each agent's tools are restricted to their own directories:

- `file_read`/`file_write` → `/agents/{agent-id}/workspace/` only
- `memory_read`/`memory_write` → `/agents/{agent-id}/memory/` only
- `web_fetch` → any URL (outbound)
- `shell_exec` → allowlist of safe commands (ls, cat, head, tail, grep, wc)

**No cross-agent file access.** Enforced in tool implementations.

### 11.3 API Key Handling

**Decision:** Pass `ANTHROPIC_API_KEY` as environment variable at VM boot.

**Rationale:** 
- Simple to implement
- Secure enough for single-user desktop app
- VM isolation means key isn't exposed to host processes
- Alternative (host-side proxy) adds complexity without meaningful security benefit since VM has outbound network access anyway

**Key retrieval flow:**
1. Swift reads API key from macOS Keychain (stored by user on first setup)
2. Swift passes key as environment variable when starting VM
3. Node.js reads `process.env.ANTHROPIC_API_KEY`
4. Key never written to disk inside VM

### 11.4 Network Policy

Virtualization.framework's NAT mode provides outbound-only access by default. The VM cannot accept incoming connections from the network. vsock is the only inbound path, and it's only accessible from the host.

---

## 12. Development & Testing Setup

### 12.1 Local Development (No VM)

For rapid iteration, run the Node.js runner directly on macOS:

```bash
# scripts/dev-server.sh
#!/bin/bash
cd "$(dirname "$0")/../server"

export ANTHROPIC_API_KEY="your-key-here"
export BURROW_LOG_LEVEL="debug"

# Create local agent directory
mkdir -p ../dev-agents/test-agent/memory ../dev-agents/test-agent/workspace

# Run with tsx for hot reloading
npx tsx watch src/index.ts --agents-dir=../dev-agents --data-dir=../dev-data --port=5000
```

Then test with:

```bash
# In another terminal
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | nc localhost 5000
```

### 12.2 VM Development

To test inside the VM without rebuilding rootfs every time:

1. Mount the `server/dist/` directory directly into the VM (instead of copying to rootfs)
2. Run `npm run build` on host
3. Restart VM to pick up changes

### 12.3 Logging Strategy

```typescript
// src/logger.ts
const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const currentLevel = LOG_LEVELS[process.env.LOG_LEVEL || 'info'];

export const logger = {
  debug: (...args: any[]) => {
    if (currentLevel <= 0) console.log('[DEBUG]', new Date().toISOString(), ...args);
  },
  info: (...args: any[]) => {
    if (currentLevel <= 1) console.log('[INFO]', new Date().toISOString(), ...args);
  },
  warn: (...args: any[]) => {
    if (currentLevel <= 2) console.warn('[WARN]', new Date().toISOString(), ...args);
  },
  error: (...args: any[]) => {
    if (currentLevel <= 3) console.error('[ERROR]', new Date().toISOString(), ...args);
  },
};
```

**Log access:** VM stdout goes to Virtualization.framework's serial console. Swift can capture and display logs in app UI, or write to `~/Library/Application Support/Burrow/data/runner.log`.

---

## 13. Phased Implementation Plan

### Phase 1: Minimal Viable VM + Chat

**Goal:** VM boots, Node.js starts, single agent responds to a chat message via vsock.

**Completion criteria:** 
- Send `{"jsonrpc":"2.0","id":1,"method":"chat","params":{"agentId":"test","message":"Hello"}}` via vsock
- Receive streaming response from Claude

**Files to create:**

| File | Purpose |
|------|---------|
| `server/package.json` | Dependencies |
| `server/tsconfig.json` | TypeScript config |
| `server/src/index.ts` | Entry point (minimal) |
| `server/src/vsock-server.ts` | vsock handler (ping + chat only) |
| `server/src/agent.ts` | Agent class (chat method only) |
| `server/src/logger.ts` | Logging utility |
| `server/src/types.ts` | Type definitions |
| `vm/Dockerfile.rootfs` | Alpine rootfs |
| `vm/build-rootfs.sh` | Build script |
| `vm/init.sh` | VM init |

**Test agent:**
```
dev-agents/test-agent/
├── SOUL.md  # "You are a helpful test agent. Keep responses brief."
└── memory/  # Empty
```

### Phase 2: Multiple Agents + Inter-Agent + SQLite

**Goal:** Multiple agents load, inter-agent messaging works, SQLite persists state.

**Completion criteria:**
- Two agents loaded from `/agents/`
- Agent A can send message to Agent B via router
- Messages persisted to SQLite
- `agents.list` returns both agents

**Files to create:**

| File | Purpose |
|------|---------|
| `server/src/agent-manager.ts` | Agent loading & lifecycle |
| `server/src/router.ts` | Message routing |
| `server/src/db.ts` | SQLite wrapper |
| `server/src/memory.ts` | Memory file operations |

**Add to vsock-server.ts:** `agents.list`, `status`, `broadcast` methods

### Phase 3: Heartbeat + Scheduler + Memory

**Goal:** Heartbeat system running, scheduler works, agent memory persists across restarts.

**Completion criteria:**
- Agents run heartbeats every 30 minutes
- Custom cron tasks can be scheduled
- Memory files created/updated during heartbeat
- Task execution logged to SQLite

**Files to create:**

| File | Purpose |
|------|---------|
| `server/src/scheduler.ts` | Heartbeat & cron |

**Add to agent.ts:** `heartbeat()` method, memory integration

### Phase 4: Tools + Polish + Packaging

**Goal:** Full tool suite, error recovery, logging, first-launch setup, packaged .app.

**Completion criteria:**
- All tools implemented (file_read, file_write, web_fetch, shell_exec)
- Graceful error recovery (agent crashes don't kill runner)
- Comprehensive logging
- `scripts/package-app.sh` produces working .app
- First-launch creates necessary directories

**Files to create:**

| File | Purpose |
|------|---------|
| `server/src/tools/index.ts` | Tool registry |
| `server/src/tools/file-read.ts` | File read tool |
| `server/src/tools/file-write.ts` | File write tool |
| `server/src/tools/web-fetch.ts` | HTTP fetch tool |
| `server/src/tools/shell-exec.ts` | Shell exec tool |
| `scripts/package-app.sh` | App bundling |

---

## Appendix A: Tool Implementations

### file_read

```typescript
// server/src/tools/file-read.ts
import { readFileSync, existsSync } from 'fs';
import { join, resolve, relative } from 'path';

export function createFileReadTool(workspacePath: string) {
  return {
    name: 'file_read',
    description: 'Read a file from the agent workspace',
    input_schema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Relative path within workspace',
        },
      },
      required: ['path'],
    },
    execute: async (input: { path: string }) => {
      // Resolve and validate path stays within workspace
      const fullPath = resolve(workspacePath, input.path);
      const rel = relative(workspacePath, fullPath);
      
      if (rel.startsWith('..') || rel.startsWith('/')) {
        throw new Error('Path escapes workspace');
      }
      
      if (!existsSync(fullPath)) {
        throw new Error(`File not found: ${input.path}`);
      }
      
      return readFileSync(fullPath, 'utf-8');
    },
  };
}
```

### web_fetch

```typescript
// server/src/tools/web-fetch.ts
export function createWebFetchTool() {
  return {
    name: 'web_fetch',
    description: 'Fetch content from a URL',
    input_schema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'URL to fetch',
        },
        extractMode: {
          type: 'string',
          enum: ['text', 'html'],
          default: 'text',
        },
      },
      required: ['url'],
    },
    execute: async (input: { url: string; extractMode?: string }) => {
      const response = await fetch(input.url);
      const html = await response.text();
      
      if (input.extractMode === 'html') {
        return html;
      }
      
      // Basic text extraction (strip tags)
      return html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    },
  };
}
```

---

## Appendix B: Swift Integration Checklist

For the Swift team implementing the client side:

- [ ] Implement `BurrowVM` class per Section 3.1 interface
- [ ] Set up virtio-9p mounts per Section 2.6
- [ ] Pass environment variables per Section 3.4
- [ ] Implement JSON-RPC client for vsock per Section 6
- [ ] Handle streaming responses (multiple JSON lines with same ID)
- [ ] Implement reconnection logic (1s retry, 30s timeout)
- [ ] Create first-launch directory structure per Section 3.5
- [ ] UI for displaying agent list, chat, status
- [ ] Settings UI for API key (store in Keychain)
- [ ] Optional: launchd plist installation for background heartbeats

---

## Appendix C: Quick Reference

### JSON-RPC Methods

```
ping                    → { pong: true }
chat(agentId, message)  → streaming { chunk, done } or { content }
heartbeat(agentId?)     → { responses: [...] }
status                  → { agents: [...] }
agents.list             → { agents: [...] }
agents.reload(agentId)  → { success: true }
broadcast(message)      → { delivered: number }
shutdown                → { ack: true }
```

### Directory Paths

```
App Bundle:
  Contents/Resources/rootfs.img
  Contents/Resources/runner/

Application Support:
  ~/Library/Application Support/Burrow/
  ├── agents/{agent-id}/
  │   ├── SOUL.md
  │   ├── memory/
  │   └── workspace/
  ├── data/
  │   └── burrow.db
  └── config.json
```

### VM Mounts

```
Host                                          Guest
~/Library/.../Burrow/agents/              →   /agents   (rw)
~/Library/.../Burrow/data/                →   /data     (rw)
Burrow.app/Contents/Resources/runner/     →   /app      (ro)
```

---

*End of document. This plan is ready for Claude Code implementation.*
