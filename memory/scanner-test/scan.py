#!/usr/bin/env python3
"""
scan.py — Deterministic Rubric Scanner

Applies rubric-v1 criteria via keyword/structure-based detection (NOT LLM),
stages candidates to memory/scanner-test/staged-candidates.md.

Usage:
    python3 scan.py <deltas_file.json> [--rubric rubric-v1.md]
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple

# Paths
SCANNER_TEST_DIR = Path(__file__).parent
STAGED_FILE = SCANNER_TEST_DIR / "staged-candidates.md"

# Detection patterns (from rubric)
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

# Fact detection patterns
URL_PATTERN = r'https?://[^\s<>"\']+'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
VERSION_PATTERN = r'v[0-9]+\.[0-9]+(\.[0-9]+)?'
PRICE_PATTERN = r'\$\d+(?:,\d{3})*(?:\.\d+)?'
DATE_PATTERN = r'\d{4}-\d{2}-\d{2}'
CREDENTIAL_PATTERN = r'(?:KEY|TOKEN|SECRET|PASSWORD|API_KEY)\w*'


def classify_line(line: str) -> List[Tuple[str, float, str]]:
    """Classify a line against rubric criteria, return list of (type, confidence, match)."""
    results: List[Tuple[str, float, str]] = []
    line_lower = line.lower()
    
    # Decision detection
    for pattern in DECISION_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("decision", 0.85, pattern))
    
    # Commitment detection
    for pattern in COMMITMENT_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("commitment", 0.8, pattern))
    
    # State change detection
    for pattern in STATE_CHANGE_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("state_change", 0.85, pattern))
    
    # Preference detection
    for pattern in PREFERENCE_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("preference", 0.75, pattern))
    
    # Correction detection
    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            results.append(("correction", 0.7, pattern))
    
    # Fact detection (URLs, emails, versions, prices, dates, credentials)
    if re.search(URL_PATTERN, line):
        results.append(("new_fact", 0.9, "URL"))
    if re.search(EMAIL_PATTERN, line):
        results.append(("new_fact", 0.9, "email"))
    if re.search(VERSION_PATTERN, line):
        results.append(("new_fact", 0.7, "version"))
    if re.search(PRICE_PATTERN, line):
        results.append(("new_fact", 0.7, "price"))
    if re.search(DATE_PATTERN, line):
        results.append(("new_fact", 0.6, "date"))
    if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', line):  # phone pattern
        results.append(("new_fact", 0.7, "phone"))
    if re.search(r'\b\d{3}-\d{3}-\d{4}\b', line):  # phone pattern
        results.append(("new_fact", 0.7, "phone"))
    if re.search(r'\b\d{3}\.\d{3}\.\d{4}\b', line):  # phone pattern
        results.append(("new_fact", 0.7, "phone"))
    
    return results


def summarize_line(line: str) -> str:
    """Generate a 1-2 sentence summary."""
    # Extract key entities
    entities = []
    if url := re.search(URL_PATTERN, line):
        entities.append(f"URL: {url.group()}")
    if email := re.search(EMAIL_PATTERN, line):
        entities.append(f"email: {email.group()}")
    if price := re.search(PRICE_PATTERN, line):
        entities.append(f"price: {price.group()}")
    
    summary_parts = [line.strip()[:100]]
    if entities:
        summary_parts.append(f" [{', '.join(entities[:3])}]")
    return "".join(summary_parts)


def scan_delta(line_idx: int, line: str, source_file: str) -> Optional[dict]:
    """Scan a single delta line, return candidate dict or None."""
    classifications = classify_line(line)
    
    if not classifications:
        return None
    
    # Get highest confidence classification
    best = max(classifications, key=lambda x: x[1])
    candidate_type, confidence, match = best
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": f"{source_file}:line{line_idx}",
        "candidate_type": candidate_type,
        "evidence_line": line.strip(),
        "confidence": confidence,
        "summary": summarize_line(line),
    }


def main():
    print("=" * 60)
    print("Barnabas Memory Scanner — Deterministic Rubric Scanner")
    print("=" * 60)
    print()
    
    # Load deltas from replay.py output
    if len(sys.argv) < 2:
        print("Usage: python3 scan.py <deltas_file.json>")
        sys.exit(1)
    
    deltas_file = Path(sys.argv[1])
    if not deltas_file.exists():
        print(f"ERROR: {deltas_file} not found")
        sys.exit(1)
    
    with deltas_file.open("r") as f:
        deltas = json.load(f)
    
    print(f"Loaded {len(deltas)} deltas")
    print()
    
    # Scan each delta
    candidates: List[dict] = []
    for line_idx, line in deltas:
        candidate = scan_delta(line_idx, line, str(deltas_file))
        if candidate:
            candidates.append(candidate)
    
    print(f"Found {len(candidates)} candidates")
    print()
    
    # Group by type
    type_counts = {}
    for c in candidates:
        t = c["candidate_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("Candidates by type:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")
    print()
    
    # Write staged candidates
    with STAGED_FILE.open("w") as f:
        f.write("# Staged Candidates for Barnabas Memory Scanner\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"Total candidates: {len(candidates)}\n\n")
        
        for i, c in enumerate(candidates, 1):
            f.write(f"## Candidate #{i}\n")
            f.write(f"- **Type:** {c['candidate_type']}\n")
            f.write(f"- **Source:** {c['source']}\n")
            f.write(f"- **Confidence:** {c['confidence']}\n")
            f.write(f"- **Evidence:** `{c['evidence_line']}`\n")
            f.write(f"- **Summary:** {c['summary']}\n")
            f.write("\n")
    
    print(f"Staged {len(candidates)} candidates to {STAGED_FILE}")
    print()
    print("Run with answer key to compute overlap.")
    
    return candidates


if __name__ == "__main__":
    main()
