# Per-Agent Session↔Disk Memory Reconcile Cron (design draft, 2026-09-11)

Aaron's goal: reset sessions more often with less loss. A per-agent cron that forces each
agent to close the gap between its live session memory and what's on disk — recursively,
so the gap shrinks over time instead of growing.

## How it differs from what exists
- **Nightly consolidation (main, 11pm):** one agent, extracts signals + refreshes indexes. Reads transcripts; doesn't verify disk state.
- **Context-guard:** protects context size, doesn't reconcile.
- **This cron:** per-agent, bidirectional reconcile — compare *session's belief state* vs *disk state*, close gaps both ways, prove closure.

## Design sketch

**Trigger:** per-agent cron (staggered overnight, e.g. main 11pm, channels 11:15–11:45 by offset).

**Per-agent pass:**
1. **Extract** — agent summarizes its current session's working state: active tasks, decisions made, open threads, facts learned. Output: `reconcile-report` (bounded, structured).
2. **Diff** — compare report against its memory files (MEMORY.md topic lines, memory/YYYY-MM-DD.md, topics/*.md). Three gap classes:
   - *Session-newer:* in session, not on disk → write to disk.
   - *Disk-newer:* on disk, not in session context → flag for next-session bootstrap (don't force context reload).
   - *Contradictory:* both exist, conflict → apply supersede rule (mark old, keep new, log).
3. **Write** — bounded edits only (the one-bounded-edit-per-pass rule). Session-newer gaps land in daily note + topic files.
4. **Verify** — closure check: re-diff; if any session-newer gap remains unwritten, retry once, then log a residual. Residuals feed the next night (the recursive part).
5. **Score** — append `gap_closed / gap_total` to a shared ledger (`memory/reconcile-ledger.jsonl`). Trend visible across nights; a rising trend = agent's memory hygiene improving, a flat one = systemic problem worth a rule change.

**Loop closure (why the gap shrinks over time):**
- Nightly diffs are cumulative: tonight's residuals are tomorrow's must-fix items.
- Repeated *contradictory* gaps indicate a rule drift → surface to weekly consolidation as an AGENTS.md/skill fix (goes upstream, prevents the class, not the instance).
- Repeated *disk-newer* misses indicate the agent isn't reading its files at session start → bootstrap fix, not more cron.

**Failure modes to design against:**
- Infinite retry loops → max 2 attempts, residual-then-move-on (lesson: 2-attempt rule from ERRORS.md).
- Bloat from nightly appends → consolidation prunes; ledger is append-only JSONL, small.
- Agents writing while consolidation reads → staggered schedule, per-agent lock file.

## Open questions for the discussion
1. Scope: all channel agents, or main + a pilot first (suggest: pilot on Barnabas or Scout — real workloads, low stakes)?
2. Reset policy: does a "clean reconcile" unlock auto-session-reset, or is reset still always manual?
3. Should extraction live in the agent itself (self-report) or in an external watcher comparing session transcript to disk (tamper-proof, more plumbing)? Suggest self-report + spot-check audits.
4. Where do residuals from a dead session (agent reset before reconcile) go? Suggest: reconcile runs at reset time too — a "checkout" step before a session dies, not just overnight.
