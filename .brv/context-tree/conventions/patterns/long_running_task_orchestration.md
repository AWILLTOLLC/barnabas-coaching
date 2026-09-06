---
title: Long Running Task Orchestration
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-23T16:08:44.886Z'
updatedAt: '2026-03-23T16:08:44.886Z'
---
## Raw Concept
**Task:**
Orchestrate long-running (6-8 hour) compute jobs

**Flow:**
Decompose jobs into DAG -> Estimate token costs -> Track budget via rate limit headers -> Stagger subagent launches -> Persist state to tasks/<project>/todo.json

**Timestamp:** 2026-03-14

## Narrative
### Structure
Uses a Directed Acyclic Graph (DAG) for task decomposition and a state persistence file at tasks/<project>/todo.json to survive session restarts.

### Dependencies
Requires reading Anthropic rate limit response headers for budget tracking and rolling window management.

### Highlights
Enables stable 6-8 hour overnight compute jobs by staggering launches and persisting state.

### Rules
Rule 1: Decompose into DAG with per-node token cost estimates
Rule 2: Use budget tracker with rate limit headers
Rule 3: Persist state to todo.json
