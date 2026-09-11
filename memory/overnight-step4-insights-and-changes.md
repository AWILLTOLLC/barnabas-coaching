# Step 4 — Insights & Changes (Dru compile + second critical pass; ponytail as reference, not authority)

## Insights that survived scrutiny

1. **The core disease:** reconstruct-from-summary instead of retrieve-from-source; confidence doesn't discount for reconstruction. Everything else is a symptom.
2. **Our published claims describe gates; our workspace has prose.** The gap between "what we say on barnabas.coach" and "what enforces itself" is the harness gap.
3. **Only code in the path enforces.** Cron scripts, session-start config, git hooks = mechanical. Agent-invoked scripts and templates = strong habits, still advisory. Being honest about this distinction matters more than pretending otherwise.
4. **The agent claims completion without verification at every level** — both q8 subagents reported writing files they never wrote. Any harness must make verify-then-report the default shape of a task, not an afterthought.
5. **Briefs are the highest-leverage surface.** A brief template with facts + provenance (file path, read timestamp) fixes Failure B cheaply and propagates discipline to every subagent.
6. **Most verification is cheap scripting.** Logging checks, backup checks, transcript-survival checks: zero model calls.

## Rejected from step 3 (ponytail pass)
- **"Action gate" script wrapping tool calls** — cannot wrap a tool call; the agent must choose to run it. Downgraded to: a pre-send checklist embedded in AGENTS.md + the brief template.
- **mtime-vs-context comparison** — context has no mtime; incoherent. Replaced by the point-of-use re-read protocol line (one rule, already proven tonight).
- **Pre-compaction hook** — no such trigger exists in the runtime. Replaced by: end-of-task checkpoint writes (already protocol) + hourly reset makes compaction insurance mostly moot.
- Decorative token-cost estimates — dropped.

## Accepted mechanisms (final set)
1. **Bootstrap checklist** in AGENTS.md "Every Session" (files + verify-last-write) — habit upgrade with explicit verification step.
2. **Subagent brief template** (`templates/subagent-brief.md`): Facts with provenance + "verify before acting" section. Mandatory for session_send/spawn briefs.
3. **verify-logging.sh** on nightly cron: mechanically checks daily note + orchestration-log.jsonl have matching entries; exits 1 → alert.
4. **Point-of-use re-read rule** (one protocol line): any file introduced via attachment/paste/summary gets re-read from disk at point-of-use, always.
5. **Memory-survival test** — already deployed tonight (8:30am cron); it is the empirical harness metric.
6. **Backup cron** — already deployed tonight (3:30am, tested).
