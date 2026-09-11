#!/usr/bin/env python3
"""
reconcile_instincts.py — Instinct Reconciliation Loop for Dru

Cross-references instincts.md against corrections in signals.jsonl
and mistakes in ERRORS.md. Demotes or deletes instincts contradicted
by external evidence. Flags high-confidence instincts with zero
external validation.

Run weekly (alongside compress_signals.py) to close the self-scoring
bias loop identified in the memory system review.

Usage:
    python3 reconcile_instincts.py [--dry-run] [--report-only]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Workspace paths ────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
SIGNALS_FILE = WORKSPACE / "memory" / "signals.jsonl"
ERRORS_FILE = WORKSPACE / "ERRORS.md"
INSTINCTS_FILE = WORKSPACE / "memory" / "instincts.md"
REPORT_FILE = WORKSPACE / "memory" / "reconciliation-report.md"

# ── Confidence order ───────────────────────────────────────────────────────────
CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}
CONFIDENCE_NAMES = {0: "low", 1: "medium", 2: "high"}

# ── Demotion thresholds ────────────────────────────────────────────────────────
# Number of contradictions before demotion
FIRST_CONTRADICTION_DEMOTE = True   # high → medium
SECOND_CONTRADICTION_DEMOTE = True  # medium → low
THIRD_CONTRADICTION_DELETE = True   # low → delete


def load_signals() -> list[dict]:
    """Load all signals from signals.jsonl."""
    if not SIGNALS_FILE.exists():
        return []
    signals = []
    with SIGNALS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return signals


def load_errors() -> list[dict]:
    """Parse ERRORS.md into structured entries."""
    if not ERRORS_FILE.exists():
        return []
    content = ERRORS_FILE.read_text()
    entries = []
    # Match error blocks: ### [YYYY-MM-DD] Title ... Prevention rule: ...
    pattern = re.compile(
        r'###\s*\[(\d{4}-\d{2}-\d{2})\]\s*(.+?)\n'
        r'(?:.*?\n)*?'
        r'\*\*Prevention rule:\*\*\s*(.+?)(?:\n|$)',
        re.DOTALL,
    )
    for match in pattern.finditer(content):
        entries.append({
            "date": match.group(1),
            "title": match.group(2).strip(),
            "prevention_rule": match.group(3).strip(),
        })
    return entries


def parse_instincts(content: str) -> list[dict]:
    """Parse instincts.md into structured entries.

    Supports two block formats:
    - Legacy:  **Pattern:** / **Confidence:** low|medium|high / **Evidence:** / **Context:**
    - Atomic:  **Trigger:** / **Action:** / **Confidence:** 0.0-1.0 or low|medium|high / **Evidence:** / **Project:** (optional)
    """
    instincts = []
    legacy = re.compile(
        r'###\s*\[(\d{4}-\d{2}-\d{2})\]\s*(.+?)\n'
        r'\*\*Pattern:\*\*\s*(.+?)\n'
        r'\*\*Confidence:\*\*\s*([^\n]+?)\n'
        r'(?:.*?\n)*?'
        r'\*\*Evidence:\*\*\s*(.+?)\n'
        r'\*\*Context:\*\*\s*(.+?)(?:\n|$)',
        re.DOTALL,
    )
    atomic = re.compile(
        r'###\s*\[(\d{4}-\d{2}-\d{2})\]\s*(.+?)\n'
        r'\*\*Trigger:\*\*\s*(.+?)\n'
        r'\*\*Action:\*\*\s*(.+?)\n'
        r'\*\*Confidence:\*\*\s*([^\n]+?)\n'
        r'(?:.*?\n)*?'
        r'\*\*Evidence:\*\*\s*(.+?)(?:\n|$)',
        re.DOTALL,
    )
    for match in legacy.finditer(content):
        instinct = _instinct_from_match(match, pattern_text=match.group(3), is_atomic=False)
        instinct["start"], instinct["end"] = match.start(), match.end()
        instinct["raw_block"] = match.group(0)
        instincts.append(instinct)
    for match in atomic.finditer(content):
        instinct = _instinct_from_match(match, pattern_text=f"{match.group(3)} → {match.group(4)}", is_atomic=True)
        instinct["start"], instinct["end"] = match.start(), match.end()
        instinct["raw_block"] = match.group(0)
        instincts.append(instinct)
    instincts.sort(key=lambda i: i["start"])
    return instincts


def _parse_confidence(raw: str) -> float:
    """Numeric confidence 0.0-1.0. low=0.35, medium=0.6, high=0.85 baseline."""
    raw = raw.strip().lower()
    baseline = {"low": 0.35, "medium": 0.6, "high": 0.85}
    if raw in baseline:
        return baseline[raw]
    try:
        v = float(raw.split()[0])
        return max(0.0, min(1.0, v))
    except (ValueError, IndexError):
        return 0.35


def _instinct_from_match(match: re.Match, pattern_text: str, is_atomic: bool) -> dict:
    confidence_str = (match.group(4) if is_atomic else match.group(4)).strip()
    note_text = ""
    promoted = "promoted" in confidence_str.lower()
    evidence = match.group(5).strip() if not is_atomic else match.group(5).strip()
    context = match.group(6).strip() if not is_atomic else evidence
    if is_atomic:
        context = match.group(3).strip()  # trigger doubles as context for matching
        evidence = match.group(5).strip()
    return {
        "date": match.group(1),
        "title": match.group(2).strip(),
        "pattern": pattern_text,
        "confidence_raw": confidence_str,
        "confidence": confidence_str.split()[0] if confidence_str else "low",
        "score": _parse_confidence(confidence_str),
        "promoted": promoted,
        "evidence": evidence,
        "context": context,
    }


# ── Staleness decay ────────────────────────────────────────────────────────────
# Instincts uncorroborated (no approval/task_success signals) for this many
# weeks lose one confidence step at reconcile time.
STALENESS_WEEKS = 8



def compute_contradictions(
    instinct: dict,
    correction_signals: list[dict],
    errors: list[dict],
) -> list[dict]:
    """
    Check if corrections or errors contradict this instinct.
    Returns a list of contradiction records.
    """
    contradictions = []
    title_lower = instinct["title"].lower()
    pattern_lower = instinct["pattern"].lower()
    context_lower = instinct["context"].lower()
    
    # Combine all text for keyword matching
    instinct_text = f"{title_lower} {pattern_lower} {context_lower}"
    
    # Check correction signals
    for signal in correction_signals:
        topic = signal.get("topic", "").lower()
        text = signal.get("text", "").lower()
        signal_text = f"{topic} {text}"
        
        # Simple overlap: if the signal topic overlaps with instinct context
        topic_words = set(topic.split())
        context_words = set(context_lower.split())
        overlap = topic_words & context_words - {
            "the", "a", "an", "in", "on", "for", "to", "and", "or", "of",
            "with", "is", "are", "was", "be", "it", "this", "that",
        }
        
        if len(overlap) >= 2:  # at least 2 meaningful word overlap
            contradictions.append({
                "source": "signal",
                "type": signal.get("signal_type", "correction"),
                "date": signal.get("date", ""),
                "topic": signal.get("topic", ""),
                "overlap_words": list(overlap),
            })
    
    # Check errors
    for error in errors:
        title = error.get("title", "").lower()
        rule = error.get("prevention_rule", "").lower()
        error_text = f"{title} {rule}"
        
        # Check if the error's prevention rule contradicts the instinct's pattern
        title_words = set(title.split())
        context_words = set(context_lower.split())
        overlap = title_words & context_words - {
            "the", "a", "an", "in", "on", "for", "to", "and", "or", "of",
            "with", "is", "are", "was", "be", "it", "this", "that",
        }
        
        if len(overlap) >= 2:
            contradictions.append({
                "source": "error",
                "type": "prevention_rule",
                "date": error.get("date", ""),
                "title": error.get("title", ""),
                "overlap_words": list(overlap),
            })
    
    return contradictions


def demote_confidence(current: str, n_contradictions: int) -> tuple[str, bool]:
    level = CONFIDENCE_ORDER.get(current, 0)
    
    if n_contradictions >= 3 and THIRD_CONTRADICTION_DELETE:
        return current, True  # delete
    
    if n_contradictions >= 2 and SECOND_CONTRADICTION_DEMOTE:
        return "low", False
    
    if n_contradictions >= 1 and FIRST_CONTRADICTION_DEMOTE:
        new_level = max(0, level - 1)
        return CONFIDENCE_NAMES[new_level], False
    
    return current, False


def has_external_validation(instinct: dict, all_signals: list[dict]) -> bool:
    """Check if an instinct has any supporting external signal (approval or task_success)."""
    context_lower = instinct["context"].lower()
    
    for signal in all_signals:
        if signal.get("signal_type") not in ("approval", "task_success"):
            continue
        topic = signal.get("topic", "").lower()
        topic_words = set(topic.split())
        context_words = set(context_lower.split())
        overlap = topic_words & context_words - {
            "the", "a", "an", "in", "on", "for", "to", "and", "or", "of",
        }
        if len(overlap) >= 2:
            return True
    return False


def build_report(
    instincts: list[dict],
    results: list[dict],
    today: str,
) -> str:
    """Build the reconciliation report."""
    lines = [
        f"# Instinct Reconciliation Report — {today}",
        "",
        f"_Cross-referenced {len(instincts)} instincts against corrections and errors._",
        "",
    ]
    
    demoted = [r for r in results if r["action"] == "demoted"]
    deleted = [r for r in results if r["action"] == "deleted"]
    flagged = [r for r in results if r["action"] == "flagged"]
    clean = [r for r in results if r["action"] == "clean"]
    
    lines.append(f"**Summary:** {len(clean)} clean, {len(demoted)} demoted, {len(deleted)} deleted, {len(flagged)} flagged (zero external validation)")
    lines.append("")
    
    if demoted:
        lines.append("## Demoted")
        for r in demoted:
            lines.append(f"- **{r['title']}** — {r['old_confidence']} → {r['new_confidence']} ({r['n_contradictions']} contradiction(s))")
        lines.append("")
    
    if deleted:
        lines.append("## Deleted")
        for r in deleted:
            lines.append(f"- **{r['title']}** — {r['old_confidence']} → DELETED ({r['n_contradictions']} contradiction(s))")
        lines.append("")
    
    if flagged:
        lines.append("## Flagged (zero external validation)")
        for r in flagged:
            lines.append(f"- **{r['title']}** — {r['old_confidence']} confidence, no approval/task_success signals found")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile instincts against corrections and errors."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without modifying instincts.md",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate the report, don't modify instincts.md",
    )
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Load data
    print("Loading data...")
    all_signals = load_signals()
    correction_signals = [s for s in all_signals if s.get("signal_type") == "correction"]
    errors = load_errors()
    
    if not INSTINCTS_FILE.exists():
        print(f"ERROR: instincts.md not found at {INSTINCTS_FILE}", file=sys.stderr)
        sys.exit(1)
    
    instincts_content = INSTINCTS_FILE.read_text()
    instincts = parse_instincts(instincts_content)
    print(f"  {len(all_signals)} signals ({len(correction_signals)} corrections)")
    print(f"  {len(errors)} errors")
    print(f"  {len(instincts)} instincts")
    
    # Analyze each instinct
    results = []
    modifications = []
    
    for instinct in instincts:
        contradictions = compute_contradictions(instinct, correction_signals, errors)
        n_contradictions = len(contradictions)
        
        if n_contradictions > 0:
            new_confidence, should_delete = demote_confidence(
                instinct["confidence"], n_contradictions
            )
            
            if should_delete:
                results.append({
                    "title": instinct["title"],
                    "action": "deleted",
                    "old_confidence": instinct["confidence"],
                    "new_confidence": "deleted",
                    "n_contradictions": n_contradictions,
                })
                modifications.append(("delete", instinct))
            elif new_confidence != instinct["confidence"]:
                results.append({
                    "title": instinct["title"],
                    "action": "demoted",
                    "old_confidence": instinct["confidence"],
                    "new_confidence": new_confidence,
                    "n_contradictions": n_contradictions,
                })
                modifications.append(("demote", instinct, new_confidence))
            else:
                results.append({
                    "title": instinct["title"],
                    "action": "clean",
                    "old_confidence": instinct["confidence"],
                    "new_confidence": instinct["confidence"],
                    "n_contradictions": 0,
                })
        elif not instinct.get("promoted") and not has_external_validation(instinct, all_signals):
            # Staleness decay: uncorroborated for STALENESS_WEEKS → demote one step
            try:
                from datetime import datetime as _dt
                age_days = (_dt.now() - _dt.strptime(instinct["date"], "%Y-%m-%d")).days
            except ValueError:
                age_days = 0
            if age_days >= STALENESS_WEEKS * 7 and instinct["score"] < 0.85:
                new_level = max(0, CONFIDENCE_ORDER.get(instinct["confidence"], 0) - 1)
                new_confidence = CONFIDENCE_NAMES[new_level]
                if new_confidence != instinct["confidence"]:
                    results.append({
                        "title": instinct["title"],
                        "action": "demoted",
                        "old_confidence": instinct["confidence"],
                        "new_confidence": new_confidence,
                        "n_contradictions": 0,
                    })
                    modifications.append(("demote", instinct, new_confidence))
                    continue
            results.append({
                "title": instinct["title"],
                "action": "flagged" if instinct["confidence"] == "high" else "clean",
                "old_confidence": instinct["confidence"],
                "new_confidence": instinct["confidence"],
                "n_contradictions": 0,
            })
        else:
            results.append({
                "title": instinct["title"],
                "action": "clean",
                "old_confidence": instinct["confidence"],
                "new_confidence": instinct["confidence"],
                "n_contradictions": 0,
            })
    
    # Print summary
    demoted = sum(1 for r in results if r["action"] == "demoted")
    deleted = sum(1 for r in results if r["action"] == "deleted")
    flagged = sum(1 for r in results if r["action"] == "flagged")
    clean = sum(1 for r in results if r["action"] == "clean")
    
    print(f"\nReconciliation Results:")
    print(f"  Clean:   {clean}")
    print(f"  Demoted: {demoted}")
    print(f"  Deleted: {deleted}")
    print(f"  Flagged: {flagged}")
    
    # Build report
    report = build_report(instincts, results, today)
    if not args.dry_run:
        REPORT_FILE.write_text(report)
        print(f"\nReport written to {REPORT_FILE}")
    else:
        print(f"\nDry run — report preview:")
        print(report)
    
    # Apply modifications
    if not modifications:
        print("\nNo modifications needed.")
        return
    
    if args.dry_run or args.report_only:
        print(f"\nWould modify {len(modifications)} instinct(s):")
        for mod in modifications:
            if mod[0] == "delete":
                print(f"  DELETE: {mod[1]['title']}")
            elif mod[0] == "demote":
                print(f"  DEMOTE: {mod[1]['title']} → {mod[2]}")
        return
    
    # Apply changes to instincts.md
    new_content = instincts_content
    for mod in reversed(modifications):  # reverse to preserve positions
        if mod[0] == "delete":
            new_content = new_content.replace(mod[1]["raw_block"], "")
        elif mod[0] == "demote":
            old_conf = mod[1]["confidence"]
            new_conf = mod[2]
            old_line = f"**Confidence:** {old_conf}"
            new_line = f"**Confidence:** {new_conf}"
            # Only replace in the specific block
            block = mod[1]["raw_block"]
            new_block = block.replace(old_line, new_line, 1)
            new_content = new_content.replace(block, new_block, 1)
    
    INSTINCTS_FILE.write_text(new_content)
    print(f"\nApplied {len(modifications)} modification(s) to {INSTINCTS_FILE}")


if __name__ == "__main__":
    main()
