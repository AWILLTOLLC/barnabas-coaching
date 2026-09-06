# instincts.md — Learned Patterns

_Extracted from sessions. Promote high-confidence ones into SOUL.md / AGENTS.md / skills over time._

---

### [2026-03-05] Never write narration + closing summary — pick one
**Pattern:** After tool use, write ONE reply. If the result is self-evident, a single sentence or nothing. Never re-state what was just said.
**Confidence:** high — PROMOTED TO SOUL.md
**Evidence:** Double-posted 4+ times this session across different task types. Root cause: writing narration before tools AND summary after = two sends.
**Context:** Every turn that uses tools. Fix: never write text on both sides of a tool call.

### [2026-03-05] Emoji pillars on business sites look cheap
**Pattern:** Replace emoji section icons with inline SVGs on any professional/services site. Emojis render inconsistently across OS and read as "weekend project."
**Confidence:** high
**Evidence:** Barnabas Coaching had 3 emoji pillar icons — replaced with Heroicons in brand color. Clear improvement.
**Context:** Any site where credibility matters. Casual/consumer brands may be different.

### [2026-03-05] Sub-environments may not have sessions_spawn
**Pattern:** When spawning agents with instructions to spawn sub-agents, note that `sessions_spawn` may not be available in the child runtime. Design tasks to degrade gracefully (run inline if spawn unavailable).
**Confidence:** medium
**Evidence:** Agent test 2/3 — both Alpha and Beta handled their 3 tasks inline because `sessions_spawn` wasn't available in their sub-environment.
**Context:** Nested agent spawning for VantageOC tests and any multi-level orchestration.

### [2026-03-05] Log structured heartbeat data for dashboard visibility
**Pattern:** Write a JSONL heartbeat log (`memory/heartbeat-log.jsonl`) on every heartbeat with ts, status, checked[], tasks[], and summary. VantageOC can read this file directly.
**Confidence:** medium
**Evidence:** Aaron asked about VantageOC heartbeat visibility — JSONL file approach was the agreed solution.
**Context:** Every heartbeat response should append one line.
### [2026-09-05] show_widget unavailable → board.widget.put RPC
**Pattern:** When show_widget isn't exposed (no inline-widgets client), author dashboard widgets directly via `openclaw gateway call board.widget.put` with declared capabilities; grants resolve through the normal board flow.
**Confidence:** medium
**Evidence:** Fleet recency widget built and granted end-to-end without the agent tool.
**Context:** Any Control UI dashboard widget request where the tool is missing.
### [2026-09-05] Verify spawn liveness before yielding
**Pattern:** sessions_spawn "accepted" ≠ running. Check `subagents list` for status=running before ending the turn; crash-before-boot children only surface later (or not at all).
**Confidence:** high
**Evidence:** Two spawns died in <110ms on workspace-migration validation while I waited on a completion event.
**Context:** Any spawn from worktree sessions or workspaces with legacy setup state.
