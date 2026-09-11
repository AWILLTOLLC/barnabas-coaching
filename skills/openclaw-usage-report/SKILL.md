---
name: "openclaw-usage-report"
description: "Answer OpenClaw token/cost questions by querying per-agent transcript SQLite; use when asked how many tokens or cost were used by the instance, agent, or model."
---

# OpenClaw Usage Report

Procedures for answering "how many tokens did we use" questions from OpenClaw's local data.

## Instance/agent totals for a date

1. Read transcripts from `/Users/apollo/.openclaw/agents/<agent>/agent/openclaw-agent.sqlite` (one DB per agent). Do NOT parse `.jsonl` files — transcripts live in SQLite now.
2. Copy each DB to /tmp before querying (read-only originals untouched).
3. Query `transcript_events` (`event_json`, `created_at` ms epoch UTC). Keep events where `type == "message"` and `message.role == "assistant"`; usage lives at `message.usage` (`input`, `output`, `cacheRead`, `cacheWrite`, `cost.total`), model at `message.model`.
4. Date window: convert the target local day (America/Los_Angeles) to UTC epoch ms bounds; filter `created_at` between them. Per-message filtering splits midnight-spanning sessions exactly.
5. Sum per agent; grand total across agents. Cost = sum of `usage.cost.total` (provider-billed; local Ollama models cost $0). Report cached `cacheRead` separately from input.
6. Known quirk: `json_each`-style key probing fails on these DBs — parse `event_json` in Python instead.

## Per-model totals (e.g. q8, glm)

Same query as above, but filter on `message.model` matching the model name substring (lowercase compare; e.g. `quinn` for quinn-q8, `qwen`+`distill` for the GGUF distill). Fallback models appear inside main-agent transcripts.

## What NOT to try

- Ollama CLI has no usage/stats command and `~/.ollama/logs/server.log` logs only request timings, not tokens. Source token counts from OpenClaw transcripts, never Ollama logs.
- `openclaw` CLI has no `usage` command; `openclaw telemetry` is anonymous feature stats only.
- `session_status` shows only the current session's running totals — fine for "this conversation", not for a date range.

## Heavy sweeps

For whole-instance sweeps across all agent DBs with decompression of archived sessions, spawn a subagent (multi-directory work exceeds inline budget). For a single model or date, inline Python is enough.
