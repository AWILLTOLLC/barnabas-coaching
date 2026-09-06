#!/usr/bin/env python3
"""
compress_signals.py — Behavioral RL Signal Compressor for Dru

Reads memory/signals.jsonl, groups signals by topic and type,
and promotes recurring patterns (2+ occurrences) into instinct entries
in memory/instincts.md.

Run weekly (or on demand) to surface actionable behavioral patterns.

Usage:
    python3 compress_signals.py [--dry-run] [--min-occurrences N]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

# ── Tunable constants ──────────────────────────────────────────────────────────
MIN_OCCURRENCES_DEFAULT = 2     # minimum hits to generate an instinct
HIGH_CONFIDENCE_THRESHOLD = 5   # occurrences for high confidence
MEDIUM_CONFIDENCE_THRESHOLD = 3 # occurrences for medium confidence

# ── Workspace paths ────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
SIGNALS_FILE = WORKSPACE / "memory" / "signals.jsonl"
INSTINCTS_FILE = WORKSPACE / "memory" / "instincts.md"


def load_signals() -> list[dict]:
    """Load all signals from signals.jsonl."""
    if not SIGNALS_FILE.exists():
        print(f"ERROR: signals.jsonl not found at {SIGNALS_FILE}", file=sys.stderr)
        sys.exit(1)

    signals = []
    with SIGNALS_FILE.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: Skipping malformed line {lineno}: {e}", file=sys.stderr)
    return signals


def load_instincts() -> str:
    """Load current instincts.md content."""
    if not INSTINCTS_FILE.exists():
        return ""
    return INSTINCTS_FILE.read_text()


def confidence_label(occurrences: int) -> str:
    if occurrences >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if occurrences >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def pattern_key(topic: str, signal_type: str) -> str:
    return f"{topic}::{signal_type}"


def generate_instinct_title(topic: str, signal_type: str) -> str:
    """Human-readable title for a topic+signal_type combination."""
    descriptions = {
        "correction":          f"{topic} — repeated corrections",
        "re_query":            f"{topic} — questions not answered on first try",
        "approval":            f"{topic} — consistently approved approach",
        "tool_failure":        f"{topic} — tool reliability issues",
        "clarification_spiral": f"{topic} — unclear initial responses",
        "task_success":        f"{topic} — clean task completion pattern",
    }
    return descriptions.get(signal_type, f"{topic} — {signal_type}")


def generate_pattern_advice(topic: str, signal_type: str, avg_score: float) -> str:
    """Generate actionable pattern text."""
    if signal_type == "correction":
        return f"Review approach for {topic} tasks — repeated corrections suggest a systematic gap. Re-read relevant docs or ask a clarifying question upfront."
    if signal_type == "re_query":
        return f"For {topic} topics, first answers are not landing. Provide more context, check for ambiguity, and confirm understanding before proceeding."
    if signal_type == "approval":
        return f"Current approach to {topic} consistently earns approval. Maintain this pattern — don't over-engineer or second-guess."
    if signal_type == "tool_failure":
        return f"Tool reliability issues in {topic} context. Add error handling, validate inputs, prefer defensive patterns."
    if signal_type == "clarification_spiral":
        return f"Responses on {topic} topics are triggering clarification loops. Be more explicit and complete in initial responses."
    if signal_type == "task_success":
        return f"Tasks in {topic} area complete cleanly and without re-work. This is the baseline — protect it."
    return f"Recurring {signal_type} pattern in {topic} context. Review and adjust approach."


def slugify(text: str) -> str:
    """Convert text to a simple slug for duplicate detection."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def pattern_already_documented(existing_content: str, title: str, confidence: str) -> bool:
    """Check if a pattern is already in instincts.md with equal or higher confidence."""
    title_slug = slugify(title)
    if title_slug not in slugify(existing_content):
        return False

    # Find the existing confidence level
    confidence_order = {"low": 0, "medium": 1, "high": 2}
    new_level = confidence_order.get(confidence, 0)

    # Look for the pattern block and its confidence line
    pattern = re.compile(
        r'### .+?' + re.escape(title[:30]) + r'.+?\n.*?\*\*Confidence:\*\*\s*(low|medium|high)',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(existing_content)
    if match:
        existing_confidence = match.group(1).lower()
        existing_level = confidence_order.get(existing_confidence, 0)
        return existing_level >= new_level

    return False


def build_instinct_entry(
    topic: str,
    signal_type: str,
    occurrences: int,
    session_count: int,
    avg_score: float,
    today: str,
) -> str:
    """Build a formatted instinct entry block."""
    title = generate_instinct_title(topic, signal_type)
    confidence = confidence_label(occurrences)
    advice = generate_pattern_advice(topic, signal_type, avg_score)
    context_when = f"When working on {topic}-related tasks" if topic != "general" else "In any session"

    return (
        f"\n### [{today}] Pattern: {title}\n"
        f"**Pattern:** {advice}\n"
        f"**Confidence:** {confidence}\n"
        f"**Evidence:** {occurrences} occurrences over {session_count} session(s), avg score: {avg_score:+.2f}\n"
        f"**Context:** {context_when}\n"
    )


def analyze_and_compress(signals: list[dict], min_occurrences: int) -> list[str]:
    """
    Group signals by (topic, signal_type), compute stats,
    and return a list of instinct entry strings for patterns
    that meet the threshold.
    """
    # Group by (topic, signal_type)
    groups: dict[str, list[dict]] = defaultdict(list)
    for s in signals:
        topic = s.get("topic", "general")
        signal_type = s.get("signal_type", "unknown")
        key = pattern_key(topic, signal_type)
        groups[key].append(s)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_entries = []

    for key, group in sorted(groups.items()):
        if len(group) < min_occurrences:
            continue

        topic, signal_type = key.split("::", 1)
        sessions = set(s.get("session_key", "") for s in group)
        scores = [s.get("implicit_score", 0.0) for s in group]
        avg_score = mean(scores)

        entry = build_instinct_entry(
            topic=topic,
            signal_type=signal_type,
            occurrences=len(group),
            session_count=len(sessions),
            avg_score=avg_score,
            today=today,
        )
        new_entries.append((topic, signal_type, entry, confidence_label(len(group))))

    return new_entries


def print_summary(signals: list[dict], new_entries: list) -> None:
    """Print a human-readable compression summary."""
    total = len(signals)
    by_type: dict[str, int] = defaultdict(int)
    for s in signals:
        by_type[s.get("signal_type", "unknown")] += 1

    print(f"\nSignal Compression Summary")
    print(f"  Total signals in log: {total}")
    print(f"  Breakdown by type:")
    for t, count in sorted(by_type.items()):
        print(f"    {t:25s} {count}")
    print(f"\n  New instinct entries generated: {len(new_entries)}")
    for topic, signal_type, _, confidence in new_entries:
        print(f"    [{confidence:6s}] {topic} :: {signal_type}")


def main():
    parser = argparse.ArgumentParser(
        description="Compress behavioral signals into instinct entries."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without modifying instincts.md",
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=MIN_OCCURRENCES_DEFAULT,
        help=f"Minimum signal occurrences to promote a pattern (default: {MIN_OCCURRENCES_DEFAULT})",
    )
    args = parser.parse_args()

    print(f"Loading signals from {SIGNALS_FILE}...")
    signals = load_signals()
    print(f"  {len(signals)} signals loaded")

    if not signals:
        print("No signals to compress.")
        return

    new_entries = analyze_and_compress(signals, args.min_occurrences)
    existing_content = load_instincts()

    # Filter out already-documented patterns
    to_append = []
    skipped = 0
    for topic, signal_type, entry_text, confidence in new_entries:
        title = generate_instinct_title(topic, signal_type)
        if pattern_already_documented(existing_content, title, confidence):
            skipped += 1
        else:
            to_append.append(entry_text)

    print_summary(signals, new_entries)
    print(f"\n  Patterns already documented (skipped): {skipped}")
    print(f"  New patterns to append: {len(to_append)}")

    if not to_append:
        print("Nothing new to write.")
        return

    if args.dry_run:
        print("\nDry run — would append to instincts.md:")
        for entry in to_append:
            print(entry)
        return

    # Append to instincts.md
    INSTINCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INSTINCTS_FILE.open("a") as f:
        for entry in to_append:
            f.write(entry)

    print(f"\nAppended {len(to_append)} new pattern(s) to {INSTINCTS_FILE}")


if __name__ == "__main__":
    main()
