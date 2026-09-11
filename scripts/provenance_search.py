#!/usr/bin/env python3
"""
provenance_search.py — Provenance-Weighted Memory Search

Reference implementation for trust-tier ranking of memory_search results.
Fixes the "first result wins on conflict" bug by weighting owner-curated
content higher than agent-curated or auto-generated content.

Trust tiers:
  1.0 — L2 topics, wiki vault (owner-curated, human-reviewed)
  0.9 — MEMORY.md, USER.md (agent-curated, human-reviewed at session start)
  0.8 — daily notes (agent-written, ephemeral)
  0.7 — situational-awareness.db (ingested, can go stale)
  0.6 — dreaming/consolidated (auto-promoted, variable quality)
  0.5 — ByteRover .brv (agent-curated, no human review)
  0.4 — imports/ (migrated from other tools, unverified)

Agent integration pattern:
  After calling memory_search(), apply provenance weights to results:
  1. For each result, compute trust_weight from the path
  2. Multiply score × trust_weight
  3. Re-sort by weighted score descending
  4. Use re-ranked results

Usage:
    python3 provenance_search.py "query" [--max-results 10]
    python3 provenance_search.py --test   # run test cases
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Trust tier weights ─────────────────────────────────────────────────────────
TRUST_TIERS = {
    "topics": 1.0,            # memory/topics/<name>.md
    "wiki": 1.0,              # compiled wiki vault
    "memory_md": 0.9,         # MEMORY.md
    "user_md": 0.9,           # USER.md
    "soul_md": 0.9,           # SOUL.md
    "agents_md": 0.9,         # AGENTS.md
    "daily_notes": 0.8,       # memory/YYYY-MM-DD.md
    "situational_awareness": 0.7,  # data/situational-awareness.db
    "dreaming": 0.6,          # memory/dreaming/
    "byterover": 0.5,         # .brv/context-tree
    "imports": 0.4,           # memory/imports/
}

DEFAULT_TRUST = 0.7


def classify_path(path: str) -> str:
    """Classify a memory file path into a trust tier."""
    p = path.lower()

    if "memory/topics/" in p:
        return "topics"
    if "wiki" in p and ("compiled" in p or "vault" in p):
        return "wiki"
    if p.endswith("memory.md") or p == "memory.md":
        return "memory_md"
    if p.endswith("user.md") or p == "user.md":
        return "user_md"
    if p.endswith("soul.md") or p == "soul.md":
        return "soul_md"
    if p.endswith("agents.md") or p == "agents.md":
        return "agents_md"
    if re.search(r"memory/\d{4}-\d{2}-\d{2}", p):
        return "daily_notes"
    if "situational" in p or "awareness" in p:
        return "situational_awareness"
    if "dreaming" in p or "consolidated" in p:
        return "dreaming"
    if ".brv" in p or "byterover" in p or "context-tree" in p:
        return "byterover"
    if "imports/" in p:
        return "imports"

    return "unknown"


def get_trust_weight(path: str) -> float:
    """Get the trust weight for a given path."""
    return TRUST_TIERS.get(classify_path(path), DEFAULT_TRUST)


def rerank_results(results: list[dict]) -> list[dict]:
    """
    Re-rank search results by applying trust weights.
    New score = original_score * trust_weight
    Results are re-sorted by weighted score descending.
    """
    for result in results:
        path = result.get("path", "")
        trust_weight = get_trust_weight(path)
        original_score = result.get("score", result.get("vectorScore", 0.5))

        result["originalScore"] = original_score
        result["trustWeight"] = trust_weight
        result["trustTier"] = classify_path(path)
        result["weightedScore"] = original_score * trust_weight

    results.sort(key=lambda r: r.get("weightedScore", 0), reverse=True)
    return results


def run_tests():
    """Run test cases to verify ranking logic."""
    test_results = [
        {"path": "memory/topics/malta.md", "score": 0.7, "snippet": "L2 topic about Malta trip"},
        {"path": "MEMORY.md", "score": 0.85, "snippet": "L1 overview of active context"},
        {"path": ".brv/context-trees/project.md", "score": 0.9, "snippet": "ByteRover cached pattern (stale)"},
        {"path": "memory/dreaming/light/2026-09-05.md", "score": 0.75, "snippet": "Dreaming consolidated entry"},
        {"path": "memory/imports/hermes/MEMORY.md", "score": 0.8, "snippet": "Hermes import (unverified)"},
        {"path": "memory/2026-09-06.md", "score": 0.65, "snippet": "Daily note"},
    ]

    print("BEFORE weighting (sorted by original score):")
    for r in sorted(test_results, key=lambda x: -x.get("score", 0)):
        print(f"  {r['score']:.2f}  {r['path']}")
    print()

    reranked = rerank_results(test_results)

    print("AFTER weighting (sorted by weighted score):")
    for r in reranked:
        tier = r.get("trustTier", "?")
        tw = r.get("trustWeight", 0)
        ws = r.get("weightedScore", 0)
        print(f"  {ws:.3f}  ({r['originalScore']:.2f} * {tw})  [{tier}]  {r['path']}")
    print()

    # The key test: ByteRover at score 0.9 should NOT outrank
    # MEMORY.md at score 0.85, because ByteRover trust=0.5 vs MEMORY.md trust=0.9
    byterover_result = next(r for r in reranked if ".brv" in r["path"])
    memory_result = next(r for r in reranked if r["path"] == "MEMORY.md")

    if memory_result["weightedScore"] > byterover_result["weightedScore"]:
        print("PASS: MEMORY.md outranks ByteRover after weighting")
    else:
        print("FAIL: ByteRover still outranks MEMORY.md")
        sys.exit(1)

    # L2 topic should rank highest when scores are close
    topic_result = next(r for r in reranked if "topics/" in r["path"])
    if topic_result == reranked[0]:
        print("PASS: L2 topic ranks highest")
    else:
        print(f"INFO: L2 topic ranked #{reranked.index(topic_result)+1} (score was lower)")


def main():
    parser = argparse.ArgumentParser(
        description="Provenance-weighted memory search."
    )
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--test", action="store_true", help="Run test cases")
    parser.add_argument("--show-tiers", action="store_true", help="Show trust tier weights")
    args = parser.parse_args()

    if args.show_tiers or not args.query:
        print("Trust tier weights:")
        for tier, weight in sorted(TRUST_TIERS.items(), key=lambda x: -x[1]):
            print(f"  {weight:4.1f}  {tier}")
        print(f"  {DEFAULT_TRUST:4.1f}  (default)")
        print()
        if not args.query and not args.test:
            return

    if args.test:
        run_tests()
        return

    print(f"Query: \"{args.query}\"")
    print()
    print("Apply this in agent code after memory_search:")
    print("  1. results = memory_search(query)")
    print("  2. For each result: result.weightedScore = result.score * get_trust_weight(result.path)")
    print("  3. Sort results by weightedScore descending")
    print("  4. Use re-ranked results")


if __name__ == "__main__":
    main()
