#!/usr/bin/env python3
"""
extract_signals.py — Behavioral RL Signal Extractor for Dru

Analyzes a session transcript (JSONL) and extracts implicit reward signals:
re-queries, corrections, approvals, tool failures, clarification spirals,
and task completions. Appends results to memory/signals.jsonl.

Usage:
    python3 extract_signals.py <session_id_or_path>

The session transcript is JSONL with fields: role, content, timestamp.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Tunable scoring constants ──────────────────────────────────────────────────
SCORE_RE_QUERY        = -0.8
SCORE_CORRECTION      = -1.0
SCORE_APPROVAL        = +1.0
SCORE_TOOL_FAILURE    = -0.3
SCORE_CLARIF_SPIRAL   = -0.5
SCORE_TASK_SUCCESS    = +0.5

# ── Keyword patterns ──────────────────────────────────────────────────────────
CORRECTION_PHRASES = [
    r"\byou should have\b",
    r"\bno,?\s+actually\b",
    r"\bthat'?s?\s+wrong\b",
    r"\bnot quite\b",
    r"\bthat'?s?\s+not\s+(right|correct|what I meant)\b",
    r"\bwrong approach\b",
    r"\byou missed\b",
    r"\bactually,?\s+(no|that'?s?\s+not)\b",
]

APPROVAL_PHRASES = [
    r"\bperfect\b",
    r"\bgreat\b",
    r"\bexactly\b",
    r"\bthat'?s?\s+it\b",
    r"\blove\s+it\b",
    r"\bawesome\b",
    r"\bspot\s+on\b",
    r"\bjust\s+what\s+I\s+(needed|wanted)\b",
    r"\bnailed\s+it\b",
    r"\bwell\s+done\b",
]

# ── Workspace paths ────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
SIGNALS_FILE = WORKSPACE / "memory" / "signals.jsonl"
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")


def load_transcript(session_arg: str) -> list[dict]:
    """Load a session transcript from a path or session ID."""
    candidate = Path(session_arg)
    if not candidate.exists():
        candidate = SESSIONS_DIR / f"{session_arg}.jsonl"
    if not candidate.exists():
        print(f"ERROR: Transcript not found: {session_arg}", file=sys.stderr)
        sys.exit(1)

    messages = []
    with candidate.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: Skipping malformed line {lineno}: {e}", file=sys.stderr)
    return messages


def extract_session_key(session_arg: str) -> str:
    """Derive a stable session key from the argument."""
    return Path(session_arg).stem if Path(session_arg).exists() else session_arg


def extract_topics(messages: list[dict]) -> list[str]:
    """Heuristically extract topic tags from a conversation."""
    topics: set[str] = set()
    topic_keywords = {
        "code": ["code", "script", "python", "function", "bug", "error", "debug"],
        "memory": ["memory", "remember", "recall", "forget", "session"],
        "writing": ["write", "draft", "blog", "post", "email", "content"],
        "research": ["search", "find", "look up", "research", "web"],
        "file": ["file", "folder", "directory", "path", "read", "write"],
        "cron": ["cron", "schedule", "job", "automation"],
        "git": ["git", "commit", "push", "branch", "repo"],
        "coaching": ["coaching", "client", "barnabas", "barrett"],
        "planning": ["plan", "todo", "task", "next steps"],
        "tools": ["tool", "script", "install", "setup"],
    }
    user_text = " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    ).lower()
    for tag, keywords in topic_keywords.items():
        if any(kw in user_text for kw in keywords):
            topics.add(tag)
    return sorted(topics) or ["general"]


def check_correction(text: str) -> str | None:
    """Return the matched correction phrase if found, else None."""
    for pattern in CORRECTION_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            return text[:300]  # capture verbatim up to 300 chars
    return None


def check_approval(text: str) -> bool:
    for pattern in APPROVAL_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def analyze_transcript(messages: list[dict], session_key: str) -> list[dict]:
    """Run all signal detectors over a transcript and return signal entries."""
    signals = []
    now = datetime.now(timezone.utc).isoformat()
    topics = extract_topics(messages)

    user_msgs = [m for m in messages if m.get("role") == "user"]
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
    tool_msgs = [m for m in messages if m.get("role") == "tool"]

    def make_signal(signal_type, score, context, correction_verbatim=""):
        return {
            "timestamp": now,
            "session_key": session_key,
            "topic": topics[0] if topics else "general",
            "implicit_score": score,
            "signal_type": signal_type,
            "correction_verbatim": correction_verbatim,
            "context": context,
            "topics_covered": topics,
        }

    # ── Corrections ──────────────────────────────────────────────────────────
    for msg in user_msgs:
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        verbatim = check_correction(content)
        if verbatim:
            signals.append(make_signal(
                "correction",
                SCORE_CORRECTION,
                "User issued an explicit correction",
                correction_verbatim=verbatim,
            ))

    # ── Approvals ─────────────────────────────────────────────────────────────
    for msg in user_msgs:
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        if check_approval(content):
            signals.append(make_signal(
                "approval",
                SCORE_APPROVAL,
                f"User expressed approval: {content[:100]}",
            ))

    # ── Re-queries (semantic similarity via simple overlap) ───────────────────
    # Simple heuristic: same meaningful noun/verb appears in user messages 8+ words apart
    user_texts = [m.get("content", "") for m in user_msgs if isinstance(m.get("content"), str)]
    if len(user_texts) >= 2:
        # Extract "content words" (>4 chars) from each user message
        def content_words(text):
            return set(w.lower() for w in re.findall(r'\b[a-z]{5,}\b', text, re.IGNORECASE))

        seen_topics: list[set] = []
        for text in user_texts:
            cw = content_words(text)
            for prior in seen_topics:
                overlap = len(cw & prior)
                if overlap >= 3 and cw != prior:
                    signals.append(make_signal(
                        "re_query",
                        SCORE_RE_QUERY,
                        "User re-asked a semantically similar question (word overlap ≥ 3)",
                    ))
                    break
            seen_topics.append(cw)

    # ── Tool failures (tool messages containing error indicators) ─────────────
    retry_count = 0
    for i, msg in enumerate(tool_msgs):
        content = msg.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content)
        if re.search(r'\b(error|failed|exception|traceback|not found|permission denied)\b',
                     content, re.IGNORECASE):
            retry_count += 1

    if retry_count > 0:
        signals.append(make_signal(
            "tool_failure",
            SCORE_TOOL_FAILURE * retry_count,
            f"Tool failures detected: {retry_count} error(s) in tool responses",
        ))

    # ── Clarification spirals (>3 user messages before resolution) ────────────
    # Heuristic: runs of 4+ short user messages (<50 chars) indicate back-and-forth
    short_run = 0
    max_run = 0
    for msg in user_msgs:
        content = msg.get("content", "")
        if isinstance(content, str) and len(content.strip()) < 80:
            short_run += 1
            max_run = max(max_run, short_run)
        else:
            short_run = 0

    if max_run >= 4:
        signals.append(make_signal(
            "clarification_spiral",
            SCORE_CLARIF_SPIRAL,
            f"Clarification spiral detected: {max_run} short consecutive messages",
        ))

    # ── Task success (assistant produced output, user didn't re-ask) ──────────
    # Heuristic: session ends with assistant message and no final correction/re-query
    if assistant_msgs and user_msgs:
        last_user = user_msgs[-1].get("content", "")
        if isinstance(last_user, str):
            no_correction = not any(re.search(p, last_user, re.IGNORECASE) for p in CORRECTION_PHRASES)
            no_reask_keywords = not re.search(r'\b(again|still|didn\'t|wrong|not working)\b',
                                               last_user, re.IGNORECASE)
            if no_correction and no_reask_keywords and len(last_user.strip()) > 10:
                signals.append(make_signal(
                    "task_success",
                    SCORE_TASK_SUCCESS,
                    "Session ended cleanly — no correction or re-ask on final message",
                ))

    return signals


def append_signals(signals: list[dict]) -> None:
    """Append signals to the JSONL log."""
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SIGNALS_FILE.open("a") as f:
        for signal in signals:
            f.write(json.dumps(signal) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract behavioral RL signals from a session transcript."
    )
    parser.add_argument(
        "session",
        help="Session ID (looked up in /root/.openclaw/agents/main/sessions/) or full path to transcript",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print signals without writing to signals.jsonl",
    )
    args = parser.parse_args()

    print(f"Loading transcript: {args.session}")
    messages = load_transcript(args.session)
    print(f"  {len(messages)} messages loaded")

    session_key = extract_session_key(args.session)
    signals = analyze_transcript(messages, session_key)

    if not signals:
        print("No signals extracted.")
        return

    print(f"\nExtracted {len(signals)} signal(s):")
    counts = {}
    for s in signals:
        t = s["signal_type"]
        counts[t] = counts.get(t, 0) + 1
        print(f"  [{s['signal_type']:22s}] score={s['implicit_score']:+.1f}  {s['context'][:80]}")

    if args.dry_run:
        print("\nDry run — not writing to signals.jsonl")
        return

    append_signals(signals)
    print(f"\nAppended to {SIGNALS_FILE}")
    print("Summary:", ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
