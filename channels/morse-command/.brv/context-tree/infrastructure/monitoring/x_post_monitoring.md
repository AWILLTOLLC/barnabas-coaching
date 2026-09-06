---
title: X Post Monitoring
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-25T19:41:54.161Z'
updatedAt: '2026-03-25T19:41:54.161Z'
---
## Raw Concept
**Task:**
Monitor X posts for Morse/CW related content

**Files:**
- scripts/monitor_x_posts.py
- scripts/seen_posts.json
- scripts/monitor_x_posts.log

**Flow:**
Nitter RSS (no auth) -> monitor_x_posts.py -> relevance check (score >= 8) -> FastMail JMAP -> Email to Aaron

**Timestamp:** 2026-03-25

**Author:** meowso

**Patterns:**
- `score >= 8` - Relevance threshold for Morse/CW keywords

## Narrative
### Structure
Uses Nitter RSS as a workaround for X API limitations. Monitoring script runs via cron daily at 7am PT.

### Dependencies
Requires Nitter RSS availability, FastMail JMAP access

### Highlights
Avoids X API free tier costs (402 errors). @Ham_Radio_World is currently unresolvable on Nitter.

### Rules
Rule 1: Only notify if relevance score >= 8
Rule 2: Daily monitoring schedule at 7am PT

## Facts
- **monitoring_strategy**: Monitoring script uses Nitter RSS instead of X API [project]
- **monitoring_schedule**: Cron schedule is daily at 7am PT [convention]
- **relevance_threshold**: Relevance threshold is score >= 8 [preference]
