#!/usr/bin/env python3
"""
reconcile_scan.py — Hourly light-pass helper for memory reconciliation.

Scans an agent's transcript deltas since the last cursor, extracts candidate
memory-worthy moments using deterministic heuristics, and writes them as JSON.

Usage:
    python3 scripts/reconcile_scan.py --agent barnabas-coaching --out /tmp/candidates.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# ── Paths ────────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
OPENCLAW_STATE = Path(os.environ.get("OPENCLAW_STATE_DIR", "/Users/apollo/.openclaw"))

# ── Detection patterns (from rubric-v1 + scan.py) ────────────────────────────
DECISION_PATTERNS = [
    r"\blet's (?:pick|go with|skip|keep|drop|archive|stop|start)\b",
    r"\bdecided to\b",
    r"\bgoing with\b",
    r"\bskip it\b",
    r"\bnot doing\b",
    r"\bdropping\b",
    r"\barchiving\b",
]

COMMITMENT_PATTERNS = [
    r"\bwill (?:do|check|follow|rotate|set|schedule|book)\b",
    r"\bgoing to (?:do|check|follow)\b",
    r"\bneed to\b",
    r"\bshould (?:do|check|remember|set)\b",
    r"\bremember to\b",
    r"\btodo\b",
    r"\bfollow up\b",
    r"\bschedule\b",
    r"\bset a reminder\b",
]

STATE_CHANGE_PATTERNS = [
    r"\benabled\b",
    r"\bdisabled\b",
    r"\bstarted\b",
    r"\bstopped\b",
    r"\binstalled\b",
    r"\buninstalled\b",
    r"\bdeleted\b",
    r"\bremoved\b",
    r"\badded\b",
    r"\bcreated\b",
    r"\brenamed\b",
    r"\bmoved to\b",
    r"\bchanged to\b",
    r"\breset\b",
]

PREFERENCE_PATTERNS = [
    r"\bprefers?\b",
    r"\bdon't like\b",
    r"\blike\b",
    r"\bokay with\b",
    r"\bnot okay\b",
    r"\bavoid\b",
    r"\bskip\b",
    r"\bwant\b",
    r"\bdon't want\b",
]

CORRECTION_PATTERNS = [
    r"\bactually\b",
    r"\bno\b",
    r"\bnot quite\b",
    r"\bwrong\b",
    r"\bshould have\b",
    r"\binstead\b",
    r"\bmissed\b",
    r"\berror\b",
    r"\bbug\b",
    r"\bfix\b",
    r"\bthat's not\b",
]

# Fact detection
URL_PATTERN = r'https?://[^\s<>"\']+'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
VERSION_PATTERN = r'v[0-9]+\.[0-9]+(\.[0-9]+)?'
PRICE_PATTERN = r'\$\d+(?:,\d{3})*(?:\.\d+)?'
DATE_PATTERN = r'\d{4}-\d{2}-\d{2}'
PHONE_PATTERN = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
CREDENTIAL_PATTERN = r'(?:KEY|TOKEN|SECRET|PASSWORD|API_KEY)\w*'


# ── Transcript loading ───────────────────────────────────────────────────────

def load_transcript_sqlite(db_path: Path, session_id: Optional[str] = None) -> List[dict]:
    """Read transcript_events from the agent SQLite store."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        if session_id:
            rows = conn.execute(
                "SELECT event_json FROM transcript_events WHERE session_id = ? ORDER BY seq",
                (session_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT event_json FROM transcript_events ORDER BY seq"
            ).fetchall()
    finally:
        conn.close()

    messages = []
    for (event_json,) in rows:
        try:
            ev = json.loads(event_json)
        except json.JSONDecodeError:
            continue
        etype = ev.get("type")
        if etype == "message" and isinstance(ev.get("message"), dict):
            msg = ev["message"]
            role = msg.get("role")
            content = msg.get("content") or ""
            timestamp = msg.get("timestamp") or ev.get("timestamp")
            if isinstance(content, list):  # content blocks
                content = " ".join(
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content, "timestamp": timestamp})
        elif etype in ("thinking_level_change", "model_change", "custom"):
            # These are metadata, not对话内容; skip for candidate extraction
            pass
    return messages


def load_jsonl(path: Path) -> List[dict]:
    messages = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return messages


def decompress_zst(path: Path) -> List[dict]:
    try:
        import zstandard as zstd
    except ImportError:
        # Fall back to zstd CLI
        import subprocess
        result = subprocess.run(
            ["zstd", "-d", "-c", str(path)],
            capture_output=True,
            text=True,
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(f"zstd decompress failed: {result.stderr}")
        lines = result.stdout.splitlines()
        messages = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return messages

    cctx = zstd.ZstdDecompressor()
    with path.open("rb") as f:
        with cctx.stream_reader(f) as reader:
            data = reader.read()
    text = data.decode("utf-8", errors="replace")
    messages = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return messages


def normalize_messages(raw: List[dict]) -> List[dict]:
    """Normalize raw transcript entries to {role, content, timestamp}."""
    out = []
    for ev in raw:
        if isinstance(ev, dict) and "message" in ev and isinstance(ev["message"], dict):
            msg = ev["message"]
            role = msg.get("role")
            content = msg.get("content") or ""
            ts = msg.get("timestamp") or ev.get("timestamp")
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if role in ("user", "assistant") and content:
                out.append({"role": role, "content": content, "timestamp": ts})
        elif isinstance(ev, dict) and ev.get("role") in ("user", "assistant"):
            content = ev.get("content") or ""
            if isinstance(content, str) and content:
                out.append({
                    "role": ev["role"],
                    "content": content,
                    "timestamp": ev.get("timestamp"),
                })
    return out


# ── Candidate extraction ─────────────────────────────────────────────────────

def classify_line(text: str) -> List[Tuple[str, float, str]]:
    """Classify a line against rubric criteria."""
    results: List[Tuple[str, float, str]] = []
    line_lower = text.lower()

    for pattern in DECISION_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("decision", 0.85, pattern))

    for pattern in COMMITMENT_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("commitment", 0.8, pattern))

    for pattern in STATE_CHANGE_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("state_change", 0.85, pattern))

    for pattern in PREFERENCE_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("preference", 0.75, pattern))

    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("correction", 0.7, pattern))

    if re.search(URL_PATTERN, text):
        results.append(("new_fact", 0.9, "URL"))
    if re.search(EMAIL_PATTERN, text):
        results.append(("new_fact", 0.9, "email"))
    if re.search(VERSION_PATTERN, text):
        results.append(("new_fact", 0.7, "version"))
    if re.search(PRICE_PATTERN, text):
        results.append(("new_fact", 0.7, "price"))
    if re.search(DATE_PATTERN, text):
        results.append(("new_fact", 0.6, "date"))
    if re.search(PHONE_PATTERN, text):
        results.append(("new_fact", 0.7, "phone"))
    if re.search(CREDENTIAL_PATTERN, text, re.IGNORECASE):
        results.append(("new_fact", 0.8, "credential"))

    return results


def extract_candidates(messages: List[dict], source_ref: str) -> List[dict]:
    """Extract candidate moments from normalized messages."""
    candidates = []
    for idx, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")
        ts = msg.get("timestamp")
        if not isinstance(content, str) or not content.strip():
            continue

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            classifications = classify_line(line)
            if not classifications:
                continue
            best = max(classifications, key=lambda x: x[1])
            candidate_type, confidence, match = best

            candidate = {
                "id": f"{source_ref}:{idx}:{candidate_type}:{hash(line) & 0xFFFFFFFF}",
                "type": candidate_type,
                "evidence": line[:500],
                "source_ref": source_ref,
                "ts": ts if ts else datetime.now(timezone.utc).isoformat(),
                "confidence": confidence,
                "role": role,
            }
            candidates.append(candidate)

    return candidates


# ── Main ─────────────────────────────────────────────────────────────────────

def get_cursor_path(agent: str) -> Path:
    return MEMORY_DIR / f"reconcile-cursor-{agent}.json"


def get_transcript_sources(agent: str) -> List[Tuple[str, List[dict]]]:
    """Find all transcript sources for an agent. Returns [(source_label, messages), ...]."""
    sources: List[Tuple[str, List[dict]]] = []
    agent_dir = OPENCLAW_STATE / "agents" / agent
    sessions_dir = agent_dir / "sessions"

    # 1. Plain .jsonl files
    if sessions_dir.exists():
        for jsonl_path in sorted(sessions_dir.glob("*.jsonl")):
            label = f"file:{jsonl_path.name}"
            messages = load_jsonl(jsonl_path)
            if messages:
                sources.append((label, normalize_messages(messages)))

        # 2. .zst compressed files
        for zst_path in sorted(sessions_dir.glob("*.zst")):
            label = f"file:{zst_path.name}"
            try:
                messages = decompress_zst(zst_path)
                if messages:
                    sources.append((label, normalize_messages(messages)))
            except Exception as e:
                print(f"WARN: Failed to decompress {zst_path}: {e}", file=sys.stderr)

    # 3. SQLite fallback — always check, even if files exist
    db_path = agent_dir / "agent" / "openclaw-agent.sqlite"
    if db_path.exists():
        messages = load_transcript_sqlite(db_path)
        if messages:
            sources.append((f"sqlite:{db_path.name}", messages))

    return sources


def main():
    parser = argparse.ArgumentParser(description="Memory reconcile scanner")
    parser.add_argument("--agent", default="barnabas-coaching", help="Agent ID to scan")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    parser.add_argument("--since", help="ISO timestamp or cursor file path")
    args = parser.parse_args()

    cursor_path = get_cursor_path(args.agent)
    cursor = {}
    if args.since:
        since_path = Path(args.since)
        if since_path.exists():
            try:
                cursor = json.loads(since_path.read_text())
            except Exception:
                cursor = {}
        elif args.since.endswith(".json"):
            # Likely a cursor file path that doesn't exist yet — start fresh
            cursor = {}
        else:
            cursor = {"last_ts": args.since}
    elif cursor_path.exists():
        try:
            cursor = json.loads(cursor_path.read_text())
        except Exception as e:
            print(f"WARN: Corrupt cursor file, starting fresh: {e}", file=sys.stderr)
            cursor = {}

    last_ts = cursor.get("last_ts")
    last_seq = cursor.get("last_seq", 0)

    sources = get_transcript_sources(args.agent)
    if not sources:
        print(f"ERROR: No transcript sources found for agent {args.agent}", file=sys.stderr)
        sys.exit(1)

    all_candidates = []
    latest_ts = last_ts
    latest_seq = last_seq

    for source_label, messages in sources:
        # Filter by timestamp if available
        filtered = []
        for msg in messages:
            ts = msg.get("timestamp")
            if last_ts and ts:
                # Normalize ts for comparison
                ts_cmp = ts
                if isinstance(ts, int):
                    ts_cmp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
                if isinstance(ts_cmp, str) and ts_cmp <= last_ts:
                    continue
            filtered.append(msg)

        if not filtered:
            continue

        candidates = extract_candidates(filtered, source_label)
        all_candidates.extend(candidates)

        # Update cursor tracking
        for msg in filtered:
            ts = msg.get("timestamp")
            if ts:
                if isinstance(ts, int):
                    ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
                else:
                    ts_iso = ts
                if latest_ts is None or ts_iso > latest_ts:
                    latest_ts = ts_iso

    # Write output
    try:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            json.dump(all_candidates, f, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to write output: {e}", file=sys.stderr)
        sys.exit(1)

    # Update cursor only after successful write
    new_cursor = {}
    if latest_ts:
        new_cursor["last_ts"] = latest_ts
    if latest_seq:
        new_cursor["last_seq"] = latest_seq

    try:
        cursor_path.parent.mkdir(parents=True, exist_ok=True)
        with cursor_path.open("w") as f:
            json.dump(new_cursor, f, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to update cursor: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanned {len(all_candidates)} candidate(s) from {len(sources)} source(s)")
    print(f"Cursor updated: {cursor_path}")


if __name__ == "__main__":
    main()
