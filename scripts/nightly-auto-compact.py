#!/usr/bin/env python3
"""Nightly auto-compact: compact agent sessions above a context threshold.

Guardrails: 6h idle guard (never compact an active session) + skip-list.
Dry-run by default; pass --apply to actually compact.
Reads the gateway token from openclaw.json at runtime; never hardcodes it.
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CONTEXT_THRESHOLD = 150_000
IDLE_SECONDS = 45 * 60
SKIP_AGENTS = {"forge", "spark", "barrett"}
CONFIG = Path.home() / ".openclaw" / "openclaw.json"
DRY_RUN = "--apply" not in sys.argv


def gw(method: str, params: dict, timeout: int = 300) -> dict:
    token = json.loads(CONFIG.read_text())["gateway"]["auth"]["token"]
    cmd = [
        "openclaw", "gateway", "call", method,
        "--params", json.dumps(params), "--json",
        "--timeout", "180000",
        "--token", token,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"ok": False, "error": {"message": str(e)}}


def main():
    now = time.time()
    data = gw("sessions.list", {"configuredAgentsOnly": True})
    sessions = data.get("sessions", data.get("result", {}).get("sessions", []))

    would, done, skipped, guarded = [], [], [], []
    for s in sessions:
        agent = s.get("agentId", "")
        key = s.get("key") or f"agent:{agent}:main"
        budget = s.get("contextBudgetStatus") or {}
        usage = budget.get("estimatedPromptTokens") or 0
        updated = (s.get("updatedAt") or 0) / 1000

        if agent in SKIP_AGENTS:
            skipped.append(f"{agent} (skip-list)")
            continue
        if usage <= CONTEXT_THRESHOLD:
            continue
        if now - updated < IDLE_SECONDS:
            guarded.append(f"{agent}: {usage:,} tok in use, active {int((now-updated)/60)}m ago")
            continue

        label = f"{key} ({usage:,} tok in use, idle {int((now-updated)/3600)}h)"
        if DRY_RUN:
            would.append(label)
        else:
            res = gw("sessions.compact", {"key": key})
            if res.get("ok", False):
                after = (res.get("result") or {}).get("contextTokens", (res.get("result") or {}).get("estimatedPromptTokens", "?"))
                done.append(f"{key}: {usage:,}→{after}")
            else:
                err = (res.get("error") or {}).get("message", "unknown")
                done.append(f"{key} FAILED: {err}")

    out = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "dry-run" if DRY_RUN else "apply",
        "scanned": len(sessions),
        "compacted": done or would,
        "guarded_active": guarded,
        "skipped": skipped,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
