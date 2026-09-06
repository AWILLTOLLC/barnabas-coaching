---
title: Dru Agent Hard Rules
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-26T16:02:40.672Z'
updatedAt: '2026-03-26T16:02:40.672Z'
---
## Raw Concept
**Task:**
Define hard rules for Dru agent operations

**Timestamp:** 2026-03-26

**Author:** Aaron

## Narrative
### Structure
Hard constraints for autonomous operations.

### Highlights
Safety constraints for gateway stability and git integrity.

### Rules
Rule 1: Never restart gateway without Aaron's explicit permission.
Rule 2: Always verify subagent API claims before acting on them.
Rule 3: No ghost-writing public posts for Aaron without approval.
Rule 4: scrapling is default web fetcher (not web_fetch) — undici TLS bugs can crash gateway.
Rule 5: Never force-push, delete branches, or rewrite git history.
Rule 6: Never push env variables to codebases without permission.

## Facts
- **gateway_restart**: Never restart gateway without Aaron's explicit permission [convention]
- **subagent_verification**: Always verify subagent API claims before acting on them [convention]
- **public_posts**: No ghost-writing public posts for Aaron without approval [convention]
- **web_fetcher**: scrapling is default web fetcher (not web_fetch) [project]
- **git_safety**: Never force-push, delete branches, or rewrite git history [convention]
- **env_security**: Never push env variables to codebases without permission [convention]
