#!/usr/bin/env python3
"""
SafeHarbor Factory Orchestrator
Monitors Anthropic rate limit usage and decides parallel vs. serial agent spawning.
Usage: python3 scripts/factory_orchestrator.py
"""

import json
import time
import subprocess
import requests
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

POLL_INTERVAL_SECONDS = 300  # check every 5 min
STATE_FILE = Path(__file__).parent.parent / "tasks/safeharbor/factory-state.json"
AUTH_FILE = Path.home() / ".openclaw/agents/main/agent/auth-profiles.json"

# How long to stay conservative (serial) before switching to parallel.
# Set to however many hours until Aaron leaves. Default: 3 hours.
CONSERVATIVE_HOURS = float(os.environ.get("CONSERVATIVE_HOURS", "3"))
PARALLEL_AFTER_UTC = datetime.now(timezone.utc).replace(microsecond=0)  # set at import time, updated in main()

# ─── Rate Limit Check ─────────────────────────────────────────────────────────

def get_auth_token() -> str:
    """Read Anthropic token from OpenClaw auth profiles."""
    d = json.loads(AUTH_FILE.read_text())
    profiles = d.get("profiles", {})
    p = profiles.get("anthropic:default", {})
    token = p.get("token")
    if not token:
        raise RuntimeError("No Anthropic token found in auth-profiles.json")
    return token


def check_usage() -> dict:
    """
    Make a minimal Anthropic API call and read rate limit headers.
    Returns dict with: used_pct, remaining, limit, reset_at
    """
    token = get_auth_token()
    headers = {
        "x-api-key": token,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # Cheapest possible call — 1 input token, 1 output token
    payload = {
        "model": "claude-haiku-3-5",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}],
    }
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=15,
        )
        rl = r.headers

        limit   = int(rl.get("anthropic-ratelimit-tokens-limit", 0))
        remaining = int(rl.get("anthropic-ratelimit-tokens-remaining", 0))
        reset_at  = rl.get("anthropic-ratelimit-tokens-reset", "unknown")

        if limit == 0:
            # Headers not present (subscription auth may vary) — assume safe
            log("Rate limit headers not present — assuming below threshold")
            return {"used_pct": 0.0, "remaining": 999999, "limit": 0, "reset_at": reset_at, "status": r.status_code}

        used = limit - remaining
        used_pct = used / limit
        return {"used_pct": used_pct, "remaining": remaining, "limit": limit, "reset_at": reset_at, "status": r.status_code}

    except Exception as e:
        log(f"WARNING: Could not check rate limits: {e} — assuming safe")
        return {"used_pct": 0.0, "remaining": 999999, "limit": 0, "reset_at": "unknown", "status": 0}


def should_run_parallel() -> bool:
    """
    Subscription auth (sk-ant-oat-*) blocks direct API calls so we can't read
    Anthropic rate limit headers directly. Instead we use a time-based strategy:

    - Before PARALLEL_AFTER_UTC: serial (Aaron is actively using Claude)
    - After PARALLEL_AFTER_UTC: parallel (Aaron has left, full bandwidth)

    PARALLEL_AFTER_UTC is set at orchestrator start time + CONSERVATIVE_HOURS.
    """
    now = datetime.now(timezone.utc)
    if now < PARALLEL_AFTER_UTC:
        remaining_min = int((PARALLEL_AFTER_UTC - now).total_seconds() / 60)
        log(f"SERIAL mode — conservative window active for {remaining_min} more min (Aaron still online)")
        return False
    else:
        log(f"PARALLEL mode — conservative window passed, full bandwidth available")
        return True


# ─── State Management ─────────────────────────────────────────────────────────

def load_state() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "tasks": {
            "T1": {"name": "Alpine Rootfs",       "status": "pending", "session_key": None},
            "T2": {"name": "Node.js Runtime",     "status": "pending", "session_key": None},
            "T3": {"name": "Swift VM Infrastructure", "status": "pending", "session_key": None},
        },
        "mode": None,
        "started_at": None,
        "last_check": None,
    }


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def pending_tasks(state: dict) -> list:
    return [k for k, v in state["tasks"].items() if v["status"] == "pending"]


def running_tasks(state: dict) -> list:
    return [k for k, v in state["tasks"].items() if v["status"] == "running"]


def all_done(state: dict) -> bool:
    return all(v["status"] in ("done", "failed") for v in state["tasks"].values())


# ─── Logging ─────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


# ─── Agent Spawning ───────────────────────────────────────────────────────────

TASK_PROMPTS = {
    "T1": """
You are building and validating the Alpine Linux rootfs for SafeHarbor.

Project root: /root/.openclaw/workspace/projects/safeharbor/VantageSrc/VantageSrc/
VM files: vm/

ARCHITECTURE NOTE: This Ubuntu build container is x86_64. Build and validate for
x86_64 here. The production aarch64 rootfs is built by Aaron on his Apple Silicon
Mac using `ARCH=aarch64 bash vm/build-rootfs.sh` before T8. Document this clearly.

Your deliverables:

1. REFINE vm/build-rootfs.sh
   - Script already exists, review and harden it
   - Make sure it handles: download failures, mount failures, chroot failures
   - Add verification step at end: chroot into image and run `node --version`
   - Ensure ARCH auto-detection works correctly

2. REFINE vm/init.sh
   - Review existing script
   - Add SIGTERM handler for graceful shutdown (kill Node.js child, wait, exit 0)
   - Add vsock readiness check (wait up to 10s for port 5000 to bind before declaring ready)
   - Ensure all env var validation is clear with actionable error messages

3. RUN THE BUILD
   - Execute: cd vm && sudo bash build-rootfs.sh
   - This requires root (loop mount). You are running as root on this container.
   - If it succeeds, rootfs.img will be created in vm/
   - Log the output to vm/build.log
   - Report the final image size

4. CREATE vm/README.md
   - How to build rootfs (x86_64 on Ubuntu, aarch64 on Mac)
   - What's inside the image (Alpine version, Node.js version, packages)
   - Mount points (/agents, /data, /app)
   - Environment variables init.sh expects
   - How to debug: extracting and inspecting the image

5. CREATE vm/MAC-BUILD-SPEC.md
   A self-contained spec for a Claude Code agent running on Aaron's Apple Silicon Mac
   to build the production aarch64 rootfs. Must include:
   - Prerequisites (Xcode CLT, Homebrew, e2fsprogs: `brew install e2fsprogs`)
   - Exact commands to run (copy-pasteable, no assumptions)
   - How to verify the build succeeded (node --version inside chroot)
   - How to copy rootfs.img into the Xcode project bundle resources
     (SafeHarbor.app/Contents/Resources/rootfs.img)
   - Expected final image size (~200MB uncompressed)
   - How to confirm the Mac rootfs boots correctly in Virtualization.framework
     (pointer to T3's SafeHarborVM.swift test harness once available)
   - Any gotchas found during the x86_64 build that also apply to aarch64

CHECKPOINT RULE: Write/update each file before moving to the next step.

Read the full build plan first: /root/.openclaw/workspace/reports/safeharbor-build-plan.md

When done, write a summary to vm/T1-COMPLETE.md including the rootfs.img size and print "T1 COMPLETE".
""",

    "T2": """
You are building the Node.js agent runtime for SafeHarbor.

Project root: /root/.openclaw/workspace/projects/safeharbor/VantageSrc/VantageSrc/server/

You have:
- server/package.json (dependencies defined)
- server/tsconfig.json (TypeScript config)
- server/src/types.ts (full protocol contract — DO NOT modify)

Your deliverables (all in server/src/):
- index.ts — entry point, initialization, graceful shutdown
- vsock-server.ts — JSON-RPC 2.0 over vsock (port 5000), newline-delimited
- agent-manager.ts — load agents from /agents/, manage lifecycle
- agent.ts — Agent class integrating @anthropic-ai/sdk, handles chat + streaming
- router.ts — inter-agent messaging
- scheduler.ts — heartbeats and cron via node-cron
- db.ts — SQLite wrapper using better-sqlite3, schema from build plan Appendix A
- memory.ts — agent memory file operations (read/write SOUL.md, MEMORY.md, daily files)
- logger.ts — structured JSON logging, respects SAFEHARBOR_LOG_LEVEL env var
- tools/index.ts — tool registry
- tools/file-read.ts — read files within /agents/ mount
- tools/file-write.ts — write files within /agents/ mount
- tools/web-fetch.ts — HTTP fetch for agents
- tools/shell-exec.ts — execute shell commands inside VM (with timeout + size limits)

Auth: read ANTHROPIC_AUTH_TOKEN env var. If ANTHROPIC_AUTH_MODE=setup-token, the token is sk-ant-oat-*. Pass directly as apiKey to Anthropic SDK — it accepts both formats.

NATIVE MODULE: better-sqlite3 is pre-compiled inside the Alpine rootfs at /app/node_modules/better-sqlite3/
Do NOT npm install it again. Reference it directly:
  const Database = require('/app/node_modules/better-sqlite3');
The compiled .node binary is architecture-matched to the rootfs (x86_64 for testing, aarch64 for production).

CHECKPOINT RULE: Write each file as soon as it's complete. Never hold multiple files in memory.

Read the full build plan first: /root/.openclaw/workspace/reports/safeharbor-build-plan.md
Read server/src/types.ts to understand the full protocol contract before writing anything.

When done, write a summary to server/T2-COMPLETE.md and print "T2 COMPLETE".
""",

    "T3": """
You are building the Swift VM infrastructure layer for SafeHarbor.

Project root: /root/.openclaw/workspace/projects/safeharbor/VantageSrc/VantageSrc/

Existing source is in SafeHarbor/ (renamed from VantageOC). Read the existing code structure before writing anything.

Your deliverables (all new files in SafeHarbor/VM/):
- SafeHarborVM.swift — Virtualization.framework wrapper (VM lifecycle: configure, start, stop, crash detection)
- VsockConnection.swift — low-level vsock read/write, newline-delimited framing
- VMClient.swift — JSON-RPC 2.0 client over vsock, async/await, request/response matching by ID
- VMCommands.swift — typed RPC methods (chat, status, agents.list, channels.list, messages.history, broadcast, shutdown)
- VMEventRouter.swift — routes VM push events to the appropriate ObservableObject stores

Also modify (do NOT rewrite — surgical edits only):
- SafeHarbor/App/AppCoordinator.swift (or equivalent) — replace GatewayClient references with VMClient
- SafeHarbor/Services/ — stub out or remove GatewayClient.swift, GatewaySSE.swift, WebSocketConnection.swift

VERIFICATION: After writing each Swift file, run:
  export PATH=/usr/local/swift/usr/bin:$PATH
  # Type-check pure Swift files (will fail on Apple framework imports — that's expected)
  swiftc -typecheck SafeHarbor/VM/<file>.swift 2>&1 || true
  # Lint the whole VM directory after each new file
  swiftlint lint SafeHarbor/VM/ 2>&1 || true
Note: typecheck failures on Virtualization/Combine imports are expected on Linux.
Log them but do not stop. Fix any pure-Swift type errors.
Add a comment at the top of each Apple-framework file: // COMPILE-CHECK: requires macOS + Xcode

CHECKPOINT RULE: Write each file as soon as it's complete. Verify before moving on.

Read these before writing anything:
1. /root/.openclaw/workspace/reports/safeharbor-build-plan.md (full build plan)
2. server/src/types.ts (protocol contract — Swift must match this exactly)
3. .claude/skills/swiftui-pro/ (SwiftUI patterns and conventions for this project)
4. SafeHarbor/Services/GatewayClient.swift (interface you are replacing)
5. SafeHarbor/Services/GatewaySSE.swift and WebSocketConnection.swift (also being replaced)
6. SafeHarbor/App/AppCoordinator.swift (wiring you need to update)

When done, write a summary to SafeHarbor/VM/T3-COMPLETE.md listing:
- Files created
- Files modified
- Any typecheck errors that need Mac verification
- Any design decisions made
Then print "T3 COMPLETE".
""",
}


def spawn_task(task_id: str, state: dict):
    prompt = TASK_PROMPTS[task_id]
    name = state["tasks"][task_id]["name"]
    log(f"Spawning agent for {task_id}: {name}")

    result = subprocess.run(
        ["python3", "-c", f"""
import json, subprocess, sys
payload = {{
    "task": {json.dumps(prompt)},
    "mode": "run",
    "model": "claude-sonnet-4-6",
    "runTimeoutSeconds": 21600
}}
print(json.dumps(payload))
"""],
        capture_output=True, text=True
    )
    # In practice this would call sessions_spawn via the OpenClaw API
    # For now, log the intent and record it in state
    state["tasks"][task_id]["status"] = "running"
    state["tasks"][task_id]["spawned_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    log(f"  → {task_id} marked as running (manual spawn needed via sessions_spawn)")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    global PARALLEL_AFTER_UTC
    hours = CONSERVATIVE_HOURS
    PARALLEL_AFTER_UTC = datetime.now(timezone.utc).replace(microsecond=0)
    from datetime import timedelta
    PARALLEL_AFTER_UTC = PARALLEL_AFTER_UTC + timedelta(hours=hours)

    log("SafeHarbor Factory Orchestrator starting")
    log(f"Conservative window: {hours}h → parallel mode after {PARALLEL_AFTER_UTC.strftime('%H:%M UTC')}")
    log(f"State file: {STATE_FILE}")

    state = load_state()
    if state["started_at"] is None:
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)

    while not all_done(state):
        state = load_state()
        state["last_check"] = datetime.now(timezone.utc).isoformat()

        pending = pending_tasks(state)
        running = running_tasks(state)

        log(f"Status — pending: {pending}, running: {running}")

        if not pending:
            log("No pending tasks. Waiting for running tasks to complete...")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        parallel = should_run_parallel()
        state["mode"] = "parallel" if parallel else "serial"
        save_state(state)

        if parallel:
            # Spawn all pending tasks at once
            for task_id in pending:
                spawn_task(task_id, state)
            log(f"Parallel mode: spawned {len(pending)} agents")
        else:
            # Only spawn one if nothing is running
            if not running:
                task_id = pending[0]
                spawn_task(task_id, state)
                log(f"Serial mode: spawned {task_id}, waiting...")
            else:
                log(f"Serial mode: {running} still running, waiting...")

        log(f"Sleeping {POLL_INTERVAL_SECONDS}s before next check...")
        time.sleep(POLL_INTERVAL_SECONDS)

    log("All tasks complete!")
    log(json.dumps(load_state(), indent=2))


if __name__ == "__main__":
    main()
