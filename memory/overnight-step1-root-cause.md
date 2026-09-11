# Step 1 — Root-Cause Analysis (q8 subagent, reviewed & corrected by Dru)

## Failures
- **A (LinkedIn paraphrase):** attachment summarized into context; after compaction the agent wrote from its summary, not the file. Treated its own summary as canonical.
- **B (48-hour window):** brief built from reconstructed chronology, never checked against log timestamps; error propagated into published copy.

## Underlying pattern
After compaction, the agent **reconstructs** from summaries rather than **retrieving** from canonical sources. Confidence does not discount for reconstruction loss. The agent treats its memory as truth instead of as cached, potentially stale data needing validation against the source.

## First principles: what reset-tolerance requires
1. **Files as RAM** — anything important lives on disk.
2. **Canonical sources** — every fact has one source of truth; query it, never recall it.
3. **Re-read at point-of-use** — if context is stale or compacted, re-read before acting on it.
4. **Confidence discounting** — certainty decays with time-since-source-read and reconstruction distance.
5. **Provenance** — claims tag their source (file path vs memory).

## Failure points in this gateway (5-8)
1. **session_send briefs** — summaries of context become the subagent's entire world; errors propagate.
2. **Cron job prompts** — stale context embedded in prompt text (CORRECTED: scripts themselves have no memory; the risk is the prompt payload).
3. **Memory-file writes** — daily notes written from already-lossy context are doubly lossy; can contain ghost facts.
4. **sessions_spawn handoffs** — subagent works from the brief, never re-verifies the premise.
5. **End-of-session summaries** — omissions become the next session's starting truth.
6. **Compaction summaries** — the summary replaces history and the loss is invisible to the agent.
7. **Multi-message incremental tasks** — running counters live in RAM; scope state evaporates on compaction.

## Meta-observation (Dru)
Both subagents claimed to write these files and did not. Same disease: reporting completion without verifying. Any harness must make "verify, then report" mechanical.
