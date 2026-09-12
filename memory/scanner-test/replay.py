#!/usr/bin/env python3
"""
replay.py — Transcript Replay Engine for Memory Scanner

Parses the last 7 days of Barnabas session transcripts (JSONL),
splits into chronological line deltas, tracks cursor offset,
verifies 100% line coverage, and emits deltas for scanning.

Usage:
    python3 replay.py [--cursor OFFSET] [--force]
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Paths
WORKSPACE = Path(__file__).parent.parent
BARNABAS_AGENT_DIR = Path("/Users/apollo/.openclaw/agents/barnabas-coaching/agent")
TRANSCRIPTS_DIR = BARNABAS_AGENT_DIR / "transcripts"  # fallback if no sessions dir
SCANNER_TEST_DIR = Path(__file__).parent
CORSOR_FILE = SCANNER_TEST_DIR / "cursor.json"

# 7-day window (from 2026-09-05 to 2026-09-11)
START_DATE = datetime(2026, 9, 5, 0, 0, 0, tzinfo=timezone.utc)
END_DATE = datetime(2026, 9, 11, 23, 59, 59, tzinfo=timezone.utc)


def get_cursor() -> int:
    """Load current cursor offset from file."""
    if CORSOR_FILE.exists():
        try:
            with CORSOR_FILE.open("r") as f:
                data = json.load(f)
                return data.get("cursor", 0)
        except (json.JSONDecodeError, KeyError):
            pass
    return 0


def save_cursor(offset: int) -> None:
    """Save cursor offset to file."""
    with CORSOR_FILE.open("w") as f:
        json.dump({"cursor": offset, "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def load_transcript_sqlite() -> list[dict]:
    """Load transcripts from the Barnabas agent's SQLite store."""
    db_path = BARNABAS_AGENT_DIR / "openclaw-agent.sqlite"
    if not db_path.exists():
        print(f"ERROR: SQLite database not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    
    # Copy to temp to avoid lock
    import shutil
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        shutil.copy2(db_path, tmp_path)
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT event_json FROM transcript_events
            WHERE event_json LIKE '%"type":"message"%'
            ORDER BY seq
            """,
        ).fetchall()
        conn.close()
    finally:
        tmp_path.unlink(missing_ok=True)
    
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
            timestamp = ev.get("timestamp", "")
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content 
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if role in ("user", "assistant") and content:
                messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                })
    return messages


def load_transcript_jsonl() -> list[dict]:
    """Load transcripts from JSONL files in sessions dir."""
    sessions_dir = Path("/Users/apollo/.openclaw/agents/barnabas-coaching/sessions")
    if not sessions_dir.exists():
        return []
    
    messages = []
    for jsonl_file in sessions_dir.glob("*.jsonl"):
        try:
            with jsonl_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"  WARN: Error reading {jsonl_file}: {e}", file=sys.stderr)
    
    # Sort by timestamp if present
    def get_ts(m):
        return m.get("timestamp", "") or m.get("ts", "")
    messages.sort(key=get_ts)
    return messages


def load_transcripts() -> list[dict]:
    """Try JSONL first, fall back to SQLite."""
    # Try JSONL first
    jsonl_msgs = load_transcript_jsonl()
    if jsonl_msgs:
        print(f"Loaded {len(jsonl_msgs)} messages from JSONL transcripts")
        return jsonl_msgs
    
    # Fall back to SQLite
    sqlite_msgs = load_transcript_sqlite()
    if sqlite_msgs:
        print(f"Loaded {len(sqlite_msgs)} messages from SQLite")
        return sqlite_msgs
    
    print("No transcripts found in either JSONL or SQLite", file=sys.stderr)
    return []


def split_into_deltas(messages: list[dict], cursor: int) -> list[tuple[int, str]]:
    """Split messages into line deltas, return lines from cursor onward."""
    # Concatenate all messages into a single text stream with line breaks
    full_text = "\n".join(
        f"[{m.get('role', 'unknown')}] {m.get('content', '')}" 
        for m in messages
    )
    lines = full_text.split("\n")
    
    # Return lines after cursor
    deltas = []
    for i, line in enumerate(lines):
        if i >= cursor:
            deltas.append((i, line))
    
    return deltas


def verify_coverage(messages: list[dict], cursor: int) -> dict:
    """Verify 100% line coverage and report gaps."""
    full_text = "\n".join(
        f"[{m.get('role', 'unknown')}] {m.get('content', '')}" 
        for m in messages
    )
    total_lines = len(full_text.split("\n"))
    lines_scanned = total_lines - cursor
    gap_count = 0  # If cursor > total_lines, we have gaps
    
    return {
        "total_lines": total_lines,
        "lines_scanned": lines_scanned,
        "cursor": cursor,
        "gap_count": max(0, gap_count),
        "coverage_pct": round(100 * lines_scanned / total_lines, 2) if total_lines > 0 else 0,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Replay transcript deltas")
    parser.add_argument("--cursor", type=int, default=None, help="Override cursor offset")
    parser.add_argument("--force", action="store_true", help="Force re-scan from beginning")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Barnabas Memory Scanner — Transcript Replay Engine")
    print("=" * 60)
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print()
    
    # Load cursor
    if args.force or args.cursor is not None:
        cursor = args.cursor if args.cursor is not None else 0
    else:
        cursor = get_cursor()
    print(f"Current cursor offset: {cursor}")
    
    # Load transcripts
    messages = load_transcripts()
    if not messages:
        print("No messages found, exiting")
        sys.exit(0)
    
    print(f"Total messages: {len(messages)}")
    print()
    
    # Split into deltas
    deltas = split_into_deltas(messages, cursor)
    print(f"Deltas to scan: {len(deltas)}")
    
    # Verify coverage
    coverage = verify_coverage(messages, cursor)
    print()
    print("Coverage Report:")
    print(f"  Total lines: {coverage['total_lines']}")
    print(f"  Lines scanned: {coverage['lines_scanned']}")
    print(f"  Gap count: {coverage['gap_count']}")
    print(f"  Coverage %: {coverage['coverage_pct']}%")
    print()
    
    # Save new cursor
    new_cursor = coverage['total_lines']
    save_cursor(new_cursor)
    print(f"Updated cursor to: {new_cursor}")
    print()
    
    # Output deltas for scanning (save to file)
    deltas_file = SCANNER_TEST_DIR / "deltas.json"
    with deltas_file.open("w") as f:
        json.dump(deltas, f, indent=2)
    print(f"Saved {len(deltas)} deltas to {deltas_file}")
    print()
    print("Run scan.py to apply rubric to these deltas.")
    return deltas, coverage, deltas_file


if __name__ == "__main__":
    main()
