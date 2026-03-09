#!/usr/bin/env python3
"""
Index situational-awareness.pdf text into SQLite FTS5 for on-demand search.
Splits at actual chapter starts (2nd occurrence of headers, after TOC).
Chunks each section into ~1500 char pieces with 200 char overlap.
"""

import sqlite3
import re
import os

TEXT_FILE = "/root/.openclaw/workspace/data/situational-awareness.txt"
DB_FILE = "/root/.openclaw/workspace/data/situational-awareness.db"
CHUNK_SIZE = 1500
OVERLAP = 200

# Section headers as they appear in the text (in order)
SECTION_HEADERS = [
    ("Preface", None),  # Everything before Introduction
    ("Introduction", r"^You can see the future first in San Francisco"),
    ("I. From GPT-4 to AGI: Counting the OOMs", r"^I\. From GPT-4 to AGI"),
    ("II. From AGI to Superintelligence: The Intelligence Explosion", r"^II\. From AGI to Superintelligence"),
    ("IIIa. Racing to the Trillion-Dollar Cluster", r"^IIIa\."),
    ("IIIb. Lock Down the Labs", r"^IIIb\."),
    ("IIIc. Superalignment", r"^IIIc\."),
    ("IIId. The Free World Must Prevail", r"^IIId\."),
    ("IV. The Project", r"^IV\. The Project"),
    ("V. Parting Thoughts", r"^V\. Parting Thoughts"),
]

def find_section_boundaries(text):
    """
    Find character offsets for each section.
    For headers that appear twice (TOC + body), use the LAST occurrence.
    """
    lines = text.split("\n")
    # Build line→char_offset map
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1  # +1 for newline

    sections = []
    for name, pattern in SECTION_HEADERS[1:]:  # Skip "Preface" placeholder
        matches = []
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                matches.append(offsets[i])
        if matches:
            # Use last match (body content, not TOC)
            sections.append((name, matches[-1]))

    # Sort by offset
    sections.sort(key=lambda x: x[1])

    # Add Preface at start (char 0)
    sections.insert(0, ("Preface / Introduction", 0))

    return sections

def chunk_section(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks

def build_index():
    with open(TEXT_FILE, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    print(f"Total text: {len(text):,} chars")
    boundaries = find_section_boundaries(text)

    print(f"\nSection boundaries detected:")
    for name, offset in boundaries:
        print(f"  char {offset:>7,}  {name}")

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE VIRTUAL TABLE chunks USING fts5(
            chunk_id UNINDEXED,
            section,
            content,
            tokenize='porter unicode61'
        )
    """)

    chunk_id = 0
    total_chunks = 0
    for i, (section_name, start_offset) in enumerate(boundaries):
        end_offset = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
        section_text = text[start_offset:end_offset]
        chunks = chunk_section(section_text)
        for chunk in chunks:
            cur.execute(
                "INSERT INTO chunks (chunk_id, section, content) VALUES (?, ?, ?)",
                (chunk_id, section_name, chunk)
            )
            chunk_id += 1
        total_chunks += len(chunks)
        print(f"  [{section_name[:55]}] → {len(chunks)} chunks ({len(section_text):,} chars)")

    conn.commit()
    conn.close()

    size_kb = os.path.getsize(DB_FILE) / 1024
    print(f"\n✓ Done: {total_chunks} chunks indexed → {DB_FILE} ({size_kb:.1f} KB)")

    # Quick sanity check search
    conn2 = sqlite3.connect(DB_FILE)
    cur2 = conn2.cursor()
    rows = list(cur2.execute(
        "SELECT section, snippet(chunks, 3, '[', ']', '...', 10) FROM chunks WHERE chunks MATCH 'superintelligence' LIMIT 3"
    ))
    print(f"\nSanity check — 'superintelligence' hits: {len(rows)}")
    for r in rows:
        print(f"  [{r[0]}]: {r[1][:100]}")
    conn2.close()

if __name__ == "__main__":
    build_index()
