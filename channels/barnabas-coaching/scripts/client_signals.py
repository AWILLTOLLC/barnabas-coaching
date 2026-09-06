#!/usr/bin/env python3
"""
client_signals.py — Per-Client Behavioral RL Signal Tracker for Barnabas Coaching

Logs coaching session signals per client, enables per-client analysis, and
surfaces cross-client patterns to improve Barrett's coaching recommendations.

Usage:
    # Log a session signal (JSON via stdin):
    echo '<signal-json>' | python3 client_signals.py --log <client-id>

    # Analyze a specific client's history:
    python3 client_signals.py --analyze <client-id>

    # Cross-client summary (run monthly):
    python3 client_signals.py --summary
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

# ── Tunable scoring constants ──────────────────────────────────────────────────
SCORE_IMPLEMENTATION  = +1.0   # client reported implementing a recommendation
SCORE_WIN             = +1.0   # client came back with a concrete success
SCORE_RE_QUERY        = -0.8   # client re-asked something from a prior session
SCORE_RESISTANCE      = -0.3   # client pushed back on a recommendation
SCORE_CHURN_RISK      = -1.5   # cancellation mention, frustration, lack of engagement

# ── Workspace paths ────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
COACHING_DIR = SCRIPTS_DIR.parent
PROFILES_DIR = COACHING_DIR / "client-profiles"


def get_profile_path(client_id: str) -> Path:
    """Return the JSONL path for a given client ID."""
    slug = client_id.lower().replace(" ", "-")
    return PROFILES_DIR / f"{slug}.jsonl"


def load_profile(client_id: str) -> list[dict]:
    """Load all signal entries for a client."""
    path = get_profile_path(client_id)
    if not path.exists():
        return []

    entries = []
    with path.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: Skipping malformed line {lineno}: {e}", file=sys.stderr)
    return entries


def compute_implicit_score(entry: dict) -> float:
    """
    Compute implicit_score from signal arrays if not already set.
    Combines individual signal counts into a composite score.
    """
    score = 0.0
    score += len(entry.get("implementations_reported", [])) * SCORE_IMPLEMENTATION
    score += len(entry.get("wins_reported", [])) * SCORE_WIN
    score += len(entry.get("re_questions", [])) * SCORE_RE_QUERY
    score += len(entry.get("resistance_patterns", [])) * SCORE_RESISTANCE
    # churn_risk: check notes or signal_type
    if entry.get("signal_type") == "churn_risk":
        score += SCORE_CHURN_RISK
    return round(score, 2)


def make_entry(raw: dict, client_id: str) -> dict:
    """Build a normalized signal entry with defaults."""
    now = datetime.now(timezone.utc).isoformat()

    # Compute implicit_score if not provided
    implicit_score = raw.get("implicit_score")
    if implicit_score is None:
        implicit_score = compute_implicit_score(raw)

    return {
        "timestamp": raw.get("timestamp", now),
        "session_number": int(raw.get("session_number", 1)),
        "client_id": client_id,
        "client_type": raw.get("client_type", ""),
        "industry": raw.get("industry", ""),
        "company_size": raw.get("company_size", ""),
        "session_type": raw.get("session_type", ""),
        "recommendations_given": raw.get("recommendations_given", []),
        "implementations_reported": raw.get("implementations_reported", []),
        "re_questions": raw.get("re_questions", []),
        "resistance_patterns": raw.get("resistance_patterns", []),
        "wins_reported": raw.get("wins_reported", []),
        "implicit_score": implicit_score,
        "signal_type": raw.get("signal_type", ""),
        "notes": raw.get("notes", ""),
    }


def append_entry(client_id: str, entry: dict) -> None:
    """Append a signal entry to the client's JSONL file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    path = get_profile_path(client_id)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_log(args):
    """Handle --log <client-id> mode."""
    client_id = args.log
    print(f"Reading signal JSON for client '{client_id}' from stdin...")
    try:
        raw = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    entry = make_entry(raw, client_id)

    if args.dry_run:
        print("Dry run — would append:")
        print(json.dumps(entry, indent=2))
        return

    append_entry(client_id, entry)
    path = get_profile_path(client_id)
    print(f"Logged signal for '{client_id}' → {path}")
    print(f"  Session #{entry['session_number']} | Score: {entry['implicit_score']:+.2f} | Type: {entry['signal_type']}")


def cmd_analyze(args):
    """Handle --analyze <client-id> mode."""
    client_id = args.analyze
    entries = load_profile(client_id)

    if not entries:
        print(f"No signals found for client '{client_id}'")
        print(f"  Expected at: {get_profile_path(client_id)}")
        return

    print(f"\n{'='*60}")
    print(f"Client Analysis: {client_id}")
    print(f"{'='*60}")
    print(f"Sessions logged: {len(entries)}")

    scores = [e.get("implicit_score", 0.0) for e in entries]
    if scores:
        print(f"Score trend:     {scores[0]:+.2f} → {scores[-1]:+.2f} (avg: {mean(scores):+.2f})")

    # Implementation rate
    total_recs = sum(len(e.get("recommendations_given", [])) for e in entries)
    total_impl = sum(len(e.get("implementations_reported", [])) for e in entries)
    impl_rate = (total_impl / total_recs * 100) if total_recs else 0
    print(f"Implementation:  {total_impl}/{total_recs} recommendations ({impl_rate:.0f}%)")

    # Wins
    all_wins = [w for e in entries for w in e.get("wins_reported", [])]
    print(f"Wins reported:   {len(all_wins)}")
    for win in all_wins[:3]:
        print(f"  ✦ {win[:80]}")
    if len(all_wins) > 3:
        print(f"  ... and {len(all_wins) - 3} more")

    # Re-questions
    all_reqs = [q for e in entries for q in e.get("re_questions", [])]
    if all_reqs:
        print(f"\nRe-questions ({len(all_reqs)} — areas where advice didn't land):")
        for q in all_reqs[:5]:
            print(f"  ✗ {q[:80]}")

    # Resistance patterns
    all_resist = [r for e in entries for r in e.get("resistance_patterns", [])]
    if all_resist:
        print(f"\nResistance patterns ({len(all_resist)}):")
        for r in all_resist[:5]:
            print(f"  ⚡ {r[:80]}")

    # Churn risk check
    churn_entries = [e for e in entries if e.get("signal_type") == "churn_risk"]
    if churn_entries:
        print(f"\n⚠️  CHURN RISK SIGNALS: {len(churn_entries)} entry/entries flagged")
        for e in churn_entries:
            print(f"  Session #{e.get('session_number')} — {e.get('notes', '')[:100]}")

    # Recent session summary
    if entries:
        last = entries[-1]
        print(f"\nLast session (#{last.get('session_number')}):")
        print(f"  Type: {last.get('session_type')} | Score: {last.get('implicit_score', 0):+.2f}")
        if last.get("notes"):
            print(f"  Notes: {last['notes'][:150]}")

    print()


def cmd_summary(args):
    """Handle --summary mode: cross-client analysis."""
    if not PROFILES_DIR.exists():
        print("No client profiles directory found.")
        return

    profiles = sorted(PROFILES_DIR.glob("*.jsonl"))
    if not profiles:
        print("No client profile files found.")
        return

    print(f"\n{'='*60}")
    print(f"Cross-Client Summary ({len(profiles)} client(s))")
    print(f"{'='*60}\n")

    # Aggregate data across all clients
    all_entries: list[dict] = []
    client_summaries: list[dict] = []

    for profile_path in profiles:
        client_id = profile_path.stem
        entries = load_profile(client_id)
        if not entries:
            continue
        all_entries.extend(entries)

        scores = [e.get("implicit_score", 0.0) for e in entries]
        total_recs = sum(len(e.get("recommendations_given", [])) for e in entries)
        total_impl = sum(len(e.get("implementations_reported", [])) for e in entries)
        impl_rate = (total_impl / total_recs) if total_recs else 0
        churn_signals = sum(1 for e in entries if e.get("signal_type") == "churn_risk")

        client_summaries.append({
            "client_id": client_id,
            "sessions": len(entries),
            "avg_score": mean(scores) if scores else 0.0,
            "impl_rate": impl_rate,
            "churn_signals": churn_signals,
            "industry": entries[-1].get("industry", "unknown") if entries else "unknown",
            "client_type": entries[-1].get("client_type", "unknown") if entries else "unknown",
        })

    if not client_summaries:
        print("No data to summarize.")
        return

    # Per-client overview
    print("Client Overview:")
    print(f"  {'Client':30s} {'Sessions':>8} {'Avg Score':>10} {'Impl Rate':>10} {'Churn':>6}")
    print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*10} {'-'*6}")
    for c in sorted(client_summaries, key=lambda x: x["avg_score"], reverse=True):
        churn_flag = "⚠️" if c["churn_signals"] > 0 else ""
        print(f"  {c['client_id']:30s} {c['sessions']:>8} {c['avg_score']:>+10.2f} "
              f"{c['impl_rate']:>10.0%} {churn_flag:>6}")

    # Recommendation type analysis
    all_recs: list[str] = [r for e in all_entries for r in e.get("recommendations_given", [])]
    all_impl: list[str] = [r for e in all_entries for r in e.get("implementations_reported", [])]

    if all_recs:
        print(f"\nTop recommendations given ({len(all_recs)} total):")
        rec_counts: dict[str, int] = defaultdict(int)
        for r in all_recs:
            rec_counts[r[:60]] += 1
        for rec, count in sorted(rec_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {count}x  {rec}")

    # Industry resistance patterns
    industry_resist: dict[str, list[str]] = defaultdict(list)
    for e in all_entries:
        industry = e.get("industry", "unknown")
        for r in e.get("resistance_patterns", []):
            industry_resist[industry].append(r)

    if industry_resist:
        print("\nResistance by industry:")
        for industry, patterns in sorted(industry_resist.items()):
            print(f"  {industry}: {len(patterns)} resistance signal(s)")
            for p in patterns[:2]:
                print(f"    ✗ {p[:70]}")

    # Churn risk summary
    churn_clients = [c for c in client_summaries if c["churn_signals"] > 0]
    if churn_clients:
        print(f"\n⚠️  Churn Risk Clients ({len(churn_clients)}):")
        for c in churn_clients:
            print(f"  {c['client_id']} — {c['churn_signals']} churn signal(s), avg score {c['avg_score']:+.2f}")

    # Client type performance
    by_type: dict[str, list[dict]] = defaultdict(list)
    for c in client_summaries:
        by_type[c["client_type"]].append(c)

    if len(by_type) > 1:
        print("\nPerformance by client type:")
        for ctype, clients in sorted(by_type.items()):
            avg = mean(c["avg_score"] for c in clients)
            avg_impl = mean(c["impl_rate"] for c in clients)
            print(f"  {ctype:15s}: n={len(clients)}, avg_score={avg:+.2f}, impl_rate={avg_impl:.0%}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Per-client coaching signal tracker for Barnabas Coaching."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--log",
        metavar="CLIENT_ID",
        help="Append a session signal (JSON via stdin) for this client",
    )
    mode.add_argument(
        "--analyze",
        metavar="CLIENT_ID",
        help="Analyze signal history for a specific client",
    )
    mode.add_argument(
        "--summary",
        action="store_true",
        help="Cross-client summary of patterns and performance",
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
    elif args.summary:
        cmd_summary(args)


if __name__ == "__main__":
    main()
