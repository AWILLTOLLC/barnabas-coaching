---
title: Local LLM Timeout Bug
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-24T16:01:17.608Z'
updatedAt: '2026-03-24T16:01:17.608Z'
---
## Raw Concept
**Task:**
Document Ollama local LLM timeout issues

**Changes:**
- Identified hardcoded 30s timeout in OpenClaw gateway
- Identified num_ctx override issue in Ollama Modelfile

**Timestamp:** 2026-03-24

## Narrative
### Structure
OpenClaw gateway has a hardcoded 30-second timeout that causes issues with local LLM models when they consume excessive memory.

### Dependencies
Ollama models, OpenClaw gateway

### Highlights
Discord 401 errors were a red herring. The root cause is the model context window (num_ctx) being overridden to 262144 instead of 32768, causing memory pressure and >30s inference times.

### Rules
Ensure Modelfile explicitly caps num_ctx at 32768 and the model is pre-warmed.

## Facts
- **timeout_config**: OpenClaw gateway has a hardcoded 30-second LLM call timeout. [project]
- **ollama_context_window**: Ollama models can override num_ctx to 262144, exceeding intended 32768 limit. [project]
