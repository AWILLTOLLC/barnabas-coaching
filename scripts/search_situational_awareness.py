#!/usr/bin/env python3
"""
Search the Situational Awareness document via SQLite FTS5.

Usage:
  python3 search_situational_awareness.py "query terms" [--section "section name"] [--limit 5]

Returns matching chunks with section context.
"""

import sqlite3
import sys
import argparse

DB_FILE = "/root/.openclaw/workspace/data/situational-awareness.db"

def search(query, section_filter=None, limit=5):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    if section_filter:
        rows = list(cur.execute(
            """SELECT section, snippet(chunks, 2, '>>>', '<<<', '...', 25), rank
               FROM chunks
               WHERE chunks MATCH ? AND section LIKE ?
               ORDER BY rank LIMIT ?""",
            (query, f"%{section_filter}%", limit)
        ))
    else:
        rows = list(cur.execute(
            """SELECT section, snippet(chunks, 2, '>>>', '<<<', '...', 25), rank
               FROM chunks
               WHERE chunks MATCH ?
               ORDER BY rank LIMIT ?""",
            (query, limit)
        ))

    conn.close()
    return rows

def list_sections():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    rows = list(cur.execute(
        "SELECT section, count(*) as c FROM chunks GROUP BY section ORDER BY min(chunk_id)"
    ))
    conn.close()
    return rows

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="Search query (FTS5 syntax supported)")
    parser.add_argument("--section", help="Filter by section name (partial match)")
    parser.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--sections", action="store_true", help="List all sections")
    args = parser.parse_args()

    if args.sections:
        print("Sections in database:")
        for name, count in list_sections():
            print(f"  {count:3d} chunks  {name}")
        sys.exit(0)

    if not args.query:
        parser.print_help()
        sys.exit(1)

    results = search(args.query, args.section, args.limit)
    if not results:
        print(f"No results for: {args.query}")
        sys.exit(0)

    print(f"Results for '{args.query}' ({len(results)} hits):\n")
    for i, (section, snippet, rank) in enumerate(results, 1):
        print(f"[{i}] Section: {section}")
        print(f"     {snippet}")
        print()
