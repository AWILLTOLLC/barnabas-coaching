#!/usr/bin/env python3
"""
track_orchestration.py — Orchestration Decision Tracker for Dru

Logs inline vs subagent delegation decisions and analyzes patterns over time
to surface which task types are best handled inline vs delegated.

Usage:
    # Log a new delegation decision (JSON via stdin):
    echo '{"task_type": "research", "decision": "subagent", ...}' | \\
        python3 track_orchestration.py --log

    # Log with inline JSON arg:
    python3 track_orchestration.py --log --entry '{"task_type": "edit", ...}'

    # Analyze patterns in the log:
    python3 track_orchestration.py --analyze [--min-samples N]
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

# ── Tunable constants ──────────────────────────────────────────────────────────
MIN_SAMPLES_DEFAULT = 3          # minimum entries per task_type to surface a pattern
HIGH_CONFIDENCE_THRESHOLD = 10   # entries for high confidence
MEDIUM_CONFIDENCE_THRESHOLD = 5  # entries for medium confidence

# ── Workspace paths ────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
ORCH_LOG = WORKSPACE / "memory" / "orchestration-log.jsonl"
INSTINCTS_FILE = WORKSPACE / "memory" / "instincts.md"

# ── Valid field values (for basic validation) ──────────────────────────────────
VALID_DECISIONS = {"inline", "subagent"}
VALID_OUTCOMES = {"success", "partial", "failure", "pending"}


def load_log() -> list[dict]:
    """Load all entries from orchestration-log.jsonl."""
    if not ORCH_LOG.exists():
        return []

    entries = []
    with ORCH_LOG.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: Skipping malformed line {lineno}: {e}", file=sys.stderr)
    return entries


def make_entry(raw: dict) -> dict:
    """Build a normalized log entry with defaults and a timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": raw.get("timestamp", now),
        "task_type": raw.get("task_type", "unknown"),
        "task_description": raw.get("task_description", ""),
        "decision": raw.get("decision", "inline"),
        "rationale": raw.get("rationale", ""),
        "outcome": raw.get("outcome", "pending"),
        "turns_needed": int(raw.get("turns_needed", 0)),
        "corrections_needed": int(raw.get("corrections_needed", 0)),
        "notes": raw.get("notes", ""),
    }


def validate_entry(entry: dict) -> list[str]:
    """Return a list of validation warnings (not fatal)."""
    warnings = []
    if entry["decision"] not in VALID_DECISIONS:
        warnings.append(f"Unknown decision '{entry['decision']}' — expected: {VALID_DECISIONS}")
    if entry["outcome"] not in VALID_OUTCOMES:
        warnings.append(f"Unknown outcome '{entry['outcome']}' — expected: {VALID_OUTCOMES}")
    return warnings


def append_entry(entry: dict) -> None:
    """Append a single entry to the orchestration log."""
    ORCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ORCH_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def confidence_label(n: int) -> str:
    if n >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if n >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def analyze(entries: list[dict], min_samples: int) -> None:
    """Analyze orchestration patterns and print findings + instinct recommendations."""
    if not entries:
        print("No entries to analyze.")
        return

    # Group by task_type × decision
    by_task: dict[str, dict] = defaultdict(lambda: {"inline": [], "subagent": []})
    for e in entries:
        tt = e.get("task_type", "unknown")
        dec = e.get("decision", "inline")
        if dec not in ("inline", "subagent"):
            dec = "inline"
        by_task[tt][dec].append(e)

    print(f"\n{'='*60}")
    print(f"Orchestration Pattern Analysis ({len(entries)} total entries)")
    print(f"{'='*60}\n")

    instinct_entries = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for task_type in sorted(by_task.keys()):
        inline_entries = by_task[task_type]["inline"]
        sub_entries = by_task[task_type]["subagent"]
        total = len(inline_entries) + len(sub_entries)

        if total < min_samples:
            continue

        print(f"Task type: {task_type}  ({total} entries)")

        def stats(group):
            if not group:
                return None
            outcomes = [e.get("outcome", "pending") for e in group]
            success_rate = outcomes.count("success") / len(outcomes)
            turns = [e.get("turns_needed", 0) for e in group]
            corrections = [e.get("corrections_needed", 0) for e in group]
            return {
                "n": len(group),
                "success_rate": success_rate,
                "avg_turns": mean(turns) if turns else 0,
                "avg_corrections": mean(corrections) if corrections else 0,
            }

        i_stats = stats(inline_entries)
        s_stats = stats(sub_entries)

        if i_stats:
            print(f"  Inline   ({i_stats['n']:2d}):  success={i_stats['success_rate']:.0%}  "
                  f"avg_turns={i_stats['avg_turns']:.1f}  avg_corrections={i_stats['avg_corrections']:.1f}")
        if s_stats:
            print(f"  Subagent ({s_stats['n']:2d}):  success={s_stats['success_rate']:.0%}  "
                  f"avg_turns={s_stats['avg_turns']:.1f}  avg_corrections={s_stats['avg_corrections']:.1f}")

        # Generate recommendation
        if i_stats and s_stats:
            if s_stats["success_rate"] > i_stats["success_rate"] + 0.15:
                rec = f"Delegate '{task_type}' tasks to subagent — subagent success rate is significantly higher ({s_stats['success_rate']:.0%} vs {i_stats['success_rate']:.0%})"
                pattern = f"Use subagent for {task_type}"
            elif i_stats["avg_turns"] < s_stats["avg_turns"] * 0.7:
                rec = f"Handle '{task_type}' inline — faster resolution with fewer turns ({i_stats['avg_turns']:.1f} vs {s_stats['avg_turns']:.1f})"
                pattern = f"Handle {task_type} inline for speed"
            elif s_stats["avg_corrections"] < i_stats["avg_corrections"] * 0.7:
                rec = f"Delegate '{task_type}' to subagent — fewer corrections when delegated"
                pattern = f"Use subagent for {task_type} to reduce corrections"
            else:
                rec = None
                pattern = None

            if rec:
                print(f"  ✦ Recommendation: {rec}")
                confidence = confidence_label(total)
                instinct_entries.append(
                    f"\n### [{today}] Pattern: Orchestration — {pattern}\n"
                    f"**Pattern:** {rec}\n"
                    f"**Confidence:** {confidence}\n"
                    f"**Evidence:** {total} entries, inline n={i_stats['n']}, subagent n={s_stats['n']}\n"
                    f"**Context:** When deciding whether to delegate {task_type} tasks\n"
                )
        elif sub_entries and not inline_entries:
            if s_stats and s_stats["success_rate"] >= 0.8:
                print(f"  ✦ Note: '{task_type}' always delegated, {s_stats['success_rate']:.0%} success")
        elif inline_entries and not sub_entries:
            if i_stats and i_stats["success_rate"] >= 0.8:
                print(f"  ✦ Note: '{task_type}' always inline, {i_stats['success_rate']:.0%} success")

        print()

    # Failure mode analysis
    failed = [e for e in entries if e.get("outcome") == "failure"]
    if failed:
        print(f"Common failure modes ({len(failed)} failures):")
        fail_by_type: dict[str, int] = defaultdict(int)
        for e in failed:
            fail_by_type[f"{e.get('task_type','?')} ({e.get('decision','?')})"] += 1
        for combo, count in sorted(fail_by_type.items(), key=lambda x: -x[1]):
            print(f"  {combo}: {count} failure(s)")
        print()

    # Write instinct entries if any
    if instinct_entries:
        print(f"Generated {len(instinct_entries)} orchestration instinct(s)")
        if INSTINCTS_FILE.exists() or True:
            INSTINCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with INSTINCTS_FILE.open("a") as f:
                for entry in instinct_entries:
                    f.write(entry)
            print(f"Appended to {INSTINCTS_FILE}")
    else:
        print("No new orchestration instincts to generate.")


def cmd_log(args):
    """Handle --log mode."""
    if args.entry:
        try:
            raw = json.loads(args.entry)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in --entry: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Reading JSON from stdin... (Ctrl+D to end)", file=sys.stderr)
        try:
            raw = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    entry = make_entry(raw)
    warnings = validate_entry(entry)
    for w in warnings:
        print(f"  WARN: {w}", file=sys.stderr)

    if args.dry_run:
        print("Dry run — would append:")
        print(json.dumps(entry, indent=2))
        return

    append_entry(entry)
    print(f"Logged: [{entry['decision']}] {entry['task_type']} — {entry['outcome']}")
    print(f"Appended to {ORCH_LOG}")


def cmd_analyze(args):
    """Handle --analyze mode."""
    entries = load_log()
    print(f"Loaded {len(entries)} entries from {ORCH_LOG}")
    analyze(entries, args.min_samples)


def main():
    parser = argparse.ArgumentParser(
        description="Track and analyze orchestration decisions (inline vs subagent)."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--log",
        action="store_true",
        help="Append a new delegation decision entry (JSON via stdin or --entry)",
    )
    mode.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing orchestration patterns",
    )
    parser.add_argument(
        "--entry",
        help="JSON string for the log entry (alternative to stdin for --log)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=MIN_SAMPLES_DEFAULT,
        help=f"Minimum entries per task_type to surface a pattern (default: {MIN_SAMPLES_DEFAULT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print without writing (for --log mode)",
    )
    args = parser.parse_args()

    if args.log:
        cmd_log(args)
    elif args.analyze:
        cmd_analyze(args)


if __name__ == "__main__":
    main()
