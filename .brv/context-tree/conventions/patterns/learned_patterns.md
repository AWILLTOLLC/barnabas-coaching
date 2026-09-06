---
title: Learned Patterns
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-20T16:02:43.608Z'
updatedAt: '2026-03-20T16:02:43.608Z'
---
## Raw Concept
**Task:**
Document agent interaction and writing patterns

**Timestamp:** 2026-03-20

## Narrative
### Structure
Guidelines for agent behavior and content style.

### Highlights
ByteRover setup requires npm install and provider connection.

### Rules
Rule 1: Write ONE reply after tool use (no narration + summary).
Rule 2: Use inline SVGs (Heroicons) instead of emojis for icons.
Rule 3: No em dashes in writing.
Rule 4: Heartbeat log must be written to JSONL.

## Facts
- **writing_patterns**: After tool use, write exactly one reply and avoid providing both narration and a closing summary.
- **writing_patterns**: Never use em dashes in writing; use commas, periods, colons, semicolons, or parentheses instead.
