# Topic: safe_harbor

## Overview
SafeHarbor: run AI agents in isolated macOS VMs. Long-term replacement for VantageOC gateway layer.

## Architecture (finalized 2026-03-14)
- **VM:** Alpine Linux via Virtualization.framework (macOS 13+, no Docker)
- **Runtime:** Single Node.js sidecar (TypeScript → JS via esbuild)
- **IPC:** vsock JSON-RPC 2.0 on port 5000 (Swift host ↔ Node.js guest)
- **Persistence:** SQLite via GRDB + 9p filesystem mounts
- **App Support:** `~/Library/Application Support/SafeHarbor/`
- **Guest mounts:** `/agents/` (configs), `/data/burrow.db` (SQLite)
- **API key:** passed as env var at VM boot
- Working title: "Burrow" (rename pending)
- Naming theme: lobster/crustacean

## Files
- Build plan: `reports/burrow-server-build-plan.md`
- Project dir: `projects/safeharbor/`
