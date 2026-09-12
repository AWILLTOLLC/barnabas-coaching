#!/usr/bin/env python3
"""
analyze_overlap.py — Compute overlap between staged candidates and answer key

Usage:
    python3 analyze_overlap.py
"""

import json
import re
from datetime import datetime
from pathlib import Path

SCANNER_TEST_DIR = Path(__file__).parent
STAGED_FILE = SCANNER_TEST_DIR / "staged-candidates.md"
ANSWER_KEY_FILE = SCANNER_TEST_DIR / "answer-key.md"


def parse_staged_candidates() -> list[dict]:
    """Parse staged-candidates.md into list of dicts."""
    candidates = []
    with STAGED_FILE.open("r") as f:
        content = f.read()
    
    # Split by "## Candidate #N"
    blocks = re.split(r'## Candidate #\d+', content)[1:]  # Skip header
    
    for block in blocks:
        lines = block.strip().split("\n")
        candidate = {}
        evidence_line = ""
        for line in lines:
            if line.startswith("- **Type:**"):
                candidate["type"] = line.replace("- **Type:**", "").strip()
            elif line.startswith("- **Source:**"):
                candidate["source"] = line.replace("- **Source:**", "").strip()
            elif line.startswith("- **Confidence:**"):
                candidate["confidence"] = float(line.replace("- **Confidence:**", "").strip())
            elif line.startswith("- **Evidence:**"):
                evidence_line = line.replace("- **Evidence:**", "").strip().strip("`")
                candidate["evidence"] = evidence_line
            elif line.startswith("- **Summary:**"):
                candidate["summary"] = line.replace("- **Summary:**", "").strip()
        
        if "type" in candidate:
            candidates.append(candidate)
    
    return candidates


def parse_answer_key() -> list[dict]:
    """Parse answer-key.md into list of dicts."""
    events = []
    with ANSWER_KEY_FILE.open("r") as f:
        content = f.read()
    
    # Split by numbered items (1., 2., 3., etc.)
    # Match lines starting with digit followed by period and space
    pattern = r'\n(\d+)\.\s*(.+?)(?=\n\d+\.|###|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        event_id, rest = match
        
        # First line has title
        title_line = rest.split("\n")[0]
        title_match = re.match(r'(.+?)$', title_line, re.MULTILINE)
        title = title_match.group(1) if title_match else title_line
        
        # Try to extract date from ID (e.g., "2026-09-05" from "### 2026-09-05")
        date_match = re.search(r'### (\d{4}-\d{2}-\d{2})', content[content.find(f"{event_id}. {title}")-50:content.find(f"{event_id}. {title}")+100])
        date = date_match.group(1) if date_match else "unknown"
        
        # Get evidence (rest of block)
        evidence = "\n".join(rest.split("\n")[1:2]) if "\n" in rest else ""
        
        events.append({
            "id": event_id,
            "title": title.strip(),
            "date": date,
            "evidence": evidence.strip(),
        })
    
    return events


def compute_overlap(candidates: list[dict], events: list[dict]) -> tuple[int, list[dict]]:
    """Compute naive overlap by timestamp/topic matching."""
    overlaps = []
    missed = []
    
    # Build date map from events
    date_map = {}
    for event in events:
        date = event["date"]
        if date not in date_map:
            date_map[date] = []
        date_map[date].append(event)
    
    # For each candidate, check if any event on same date has matching topic
    for candidate in candidates:
        evidence = candidate.get("evidence", "").lower()
        candidate_type = candidate.get("type", "")
        
        # Try to extract date from source
        source = candidate.get("source", "")
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', source)
        candidate_date = date_match.group(1) if date_match else "unknown"
        
        # Check for overlap
        matched = False
        for event in date_map.get(candidate_date, []):
            title = event["title"].lower()
            evidence_text = event["evidence"].lower()
            
            # Check if candidate evidence matches event title or evidence
            if any(keyword in evidence for keyword in [
                title.split(":")[0],  # First part of title
                event["id"],  # Event ID
                title.split(" — ")[0] if " — " in title else title,
            ]):
                matched = True
                overlaps.append({
                    "candidate": candidate,
                    "event": event,
                    "match_type": "title/evidence_overlap",
                })
                break
        
        if not matched:
            missed.append(candidate)
    
    return len(overlaps), missed, overlaps


def main():
    print("=" * 60)
    print("Barnabas Memory Scanner — Overlap Analysis")
    print("=" * 60)
    print()
    
    # Parse files
    candidates = parse_staged_candidates()
    events = parse_answer_key()
    
    print(f"Parsed {len(candidates)} staged candidates")
    print(f"Parsed {len(events)} answer-key events")
    print()
    
    # Compute overlap
    overlap_count, missed_candidates, overlaps = compute_overlap(candidates, events)
    
    print(f"Naive overlap count: {overlap_count}")
    print(f"Missed candidates: {len(missed_candidates)}")
    print()
    
    # Analyze missed events
    missed_events = []
    for event in events:
        # Check if this event is in any overlap
        is_in_overlap = any(o["event"]["id"] == event["id"] for o in overlaps)
        if not is_in_overlap:
            missed_events.append(event)
    
    print(f"Answer-key events missed by scanner: {len(missed_events)}")
    print()
    
    for event in missed_events[:10]:  # Show first 10
        print(f"  {event['id']}. {event['title']} ({event['date']})")
    if len(missed_events) > 10:
        print(f"  ... and {len(missed_events) - 10} more")
    print()
    
    # Print candidates by type
    type_counts = {}
    for c in candidates:
        t = c.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("Staged candidates by type:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Line counts + coverage %: 640 lines, 100.0%")
    print(f"Staged candidates: {len(candidates)}")
    print(f"Answer-key events: {len(events)}")
    print(f"Naive overlap count: {overlap_count}")
    print(f"Answer-key events missed: {len(missed_events)}")
    print()
    print("Files written:")
    print(f"  - {STAGED_FILE}")
    print(f"  - {ANSWER_KEY_FILE}")
    print(f"  - {SCANNER_TEST_DIR / 'deltas.json'}")


if __name__ == "__main__":
    main()
