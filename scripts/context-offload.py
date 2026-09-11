#!/usr/bin/env python3
"""Context offload monitor: compact agent sessions above the context threshold.

Rebuilt 2026-09-10 after the original file was found truncated to the 7-byte
text "pending" (see ERRORS.md 2026-09-10 entry). Contract per the
auto-context-offload cron job: offload (compact) sessions over 80K tokens and
record each action in memory/context-offloads/.

Pattern from scripts/nightly-auto-compact.py: gateway token read from
openclaw.json at runtime (never hardcoded), 45m idle guard, skip-list.
Stdlib only. Exit 1 on any failed compaction so the cron's failureAlert fires.
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

CONTEXT_THRESHOLD = 80_000
IDLE_SECONDS = 45 * 60
SKIP_AGENTS = {"forge", "spark", "barrett"}
CONFIG = Path.home() / ".openclaw" / "openclaw.json"
OFFLOAD_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "context-offloads"
TAIL_EVENTS = 80
TAIL_MAX_CHARS = 20_000


def gw(method: str, params: dict, timeout: int = 360) -> dict:
    token = json.loads(CONFIG.read_text())["gateway"]["auth"]["token"]
    cmd = [
        "openclaw", "gateway", "call", method,
        "--params", json.dumps(params), "--json",
        "--timeout", "300000",
        "--token", token,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "error": {"message": "empty gateway response"}}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"ok": False, "error": {"message": str(e)}}


def save_pre_tail(key: str, stamp: str) -> Optional[Path]:
    """Snapshot the session trajectory before compacting (post-mortem trail)."""
    try:
        r = subprocess.run(
            ["openclaw", "sessions", "tail", "--session-key", key, "--tail", str(TAIL_EVENTS)],
            capture_output=True, text=True, timeout=60,
        )
        text = (r.stdout or r.stderr or "")[:TAIL_MAX_CHARS]
        if not text.strip():
            return None
        OFFLOAD_DIR.mkdir(parents=True, exist_ok=True)
        p = OFFLOAD_DIR / f"{stamp}-pre.md"
        p.write_text(f"# Context Offload pre-tail - {stamp}\n\nSession: {key}\n\n{text}\n")
        return p
    except Exception:
        return None


def main():
    now = time.time()
    data = gw("sessions.list", {"configuredAgentsOnly": True})
    sessions = data.get("sessions", data.get("result", {}).get("sessions", []))
    if not sessions:
        print(json.dumps({"status": "error", "error": "sessions.list returned no data"}))
        return 1

    usages = [((s.get("contextBudgetStatus") or {}).get("estimatedPromptTokens") or 0) for s in sessions]
    if not any(u > 0 for u in usages):
        print(json.dumps({"status": "error", "error": "no session reported usage (schema drift?)"}))
        return 1

    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    done, failed, guarded = [], [], []
    for s, usage in zip(sessions, usages):
        agent = s.get("agentId", "")
        key = s.get("key") or f"agent:{agent}:main"
        updated = (s.get("updatedAt") or 0) / 1000

        if agent in SKIP_AGENTS or usage <= CONTEXT_THRESHOLD:
            continue
        if now - updated < IDLE_SECONDS:
            guarded.append(f"{key}: {usage:,} tok, active {int((now - updated) / 60)}m ago")
            continue

        save_pre_tail(key, stamp)
        res = gw("sessions.compact", {"key": key})
        reason = (res.get("reason") or "")
        if not res.get("ok", False) and "already compacted" in reason.lower():
            continue  # benign no-op
        if res.get("ok", False):
            r = res.get("result") or {}
            after = r.get("contextTokens", r.get("estimatedPromptTokens", "?"))
            done.append((key, usage, after))
        else:
            failed.append(f"{key}: {(res.get('error') or {}).get('message', 'unknown')}")

    if done:
        OFFLOAD_DIR.mkdir(parents=True, exist_ok=True)
        lines = "\n".join(f"Compacted session {k} ({u:,} → {a} tokens)." for k, u, a in done)
        record = f"# Context Offload - {stamp}\n\n## Summary\n\n{lines}\n"
        if guarded:
            record += "\nGuarded (active, skipped): " + "; ".join(guarded) + "\n"
        (OFFLOAD_DIR / f"{stamp}.md").write_text(record)

    print(json.dumps({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "scanned": len(sessions),
        "compacted": [f"{k}: {u:,}→{a}" for k, u, a in done],
        "guarded_active": guarded,
        "failed": failed,
    }))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())