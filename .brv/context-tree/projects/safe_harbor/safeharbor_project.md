---
title: SafeHarbor Project
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-21T20:08:30.172Z'
updatedAt: '2026-03-21T20:08:30.172Z'
---
## Raw Concept
**Task:**
Document SafeHarbor architecture and build plan

**Changes:**
- Finalized architecture 2026-03-14
- Replaced GatewayClient/WebSocket/SSE with SafeHarborVM/VSockConnection

**Files:**
- reports/burrow-server-build-plan.md

**Flow:**
Swift host -> vsock JSON-RPC -> Node.js guest -> SQLite/9p

**Timestamp:** 2026-03-14

**Author:** Aaron

## Narrative
### Structure
Isolated macOS VM running Alpine Linux. Host-guest communication via vsock. SQLite persistence with 9p mounts for shared data.

### Dependencies
macOS 13+, Virtualization.framework, Node.js, GRDB (Swift), esbuild (TypeScript compilation)

### Highlights
No Docker dependency. Direct vsock communication. Clean integration with existing VantageOC GRDB stack.

### Rules
Rule 1: Use vsock for all host-guest communication
Rule 2: Compile TypeScript to JS via esbuild for guest runtime
Rule 3: Pass API keys ONLY via env vars at boot

### Examples
Guest mount /data/burrow.db maps to host SQLite database via 9p.

## Facts
- **safe_harbor_description**: SafeHarbor is Aaron's project to run AI agents in an isolated macOS VM [project]
- **architecture_finalized_date**: SafeHarbor architecture was finalized on 2026-03-14 [project]
- **vm_os**: Uses Alpine Linux via Virtualization.framework on macOS 13+ [project]
- **runtime**: Runtime is a single Node.js sidecar with TypeScript compiled via esbuild [project]
- **ipc_mechanism**: IPC uses vsock JSON-RPC 2.0 on port 5000 (Swift host <-> Node.js guest) [project]
- **persistence**: Persistence uses SQLite via GRDB and 9p filesystem mounts [project]
- **app_support_dir**: Application Support directory: ~/Library/Application Support/SafeHarbor/ [project]
- **guest_mounts**: Guest mounts: /agents/ (configs), /data/burrow.db (SQLite) [project]
- **api_key_passing**: API keys are passed as environment variables at VM boot [project]
