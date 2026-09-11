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
### [2026-09-08] Missed Aaron's email despite search hit <!-- user-level -->
**Trigger:** About to ask Aaron for a factual detail (address, email, phone, handle).
**Action:** Assume it exists somewhere in memory files — grep for the exact value pattern (@, phone digits) across MEMORY.md/USER.md/memory/ before asking; a hit framed as plumbing (allowlist, CalDAV) may still BE the fact.
**Confidence:** 0.5
**Evidence:** Asked Aaron for his email; mac@kaw.cc appeared in MEMORY.md#L139 as "to Aaron's mac@kaw.cc" and I dismissed it as iMessage config.

### [2026-09-08] Two-pass local vendor research
**Trigger:** Researching local service vendors (haulers, contractors, trades) for a recommendation.
**Action:** Run two differently-shaped search passes — category+town ("dumpster rental Mukilteo") AND nearby-town service search ("junk removal Lynnwood pricing") — and actively hunt small operators with published flat pricing before recommending quote-by-phone incumbents; big names dominate category searches and hide exactly the local operators the user wants.
**Confidence:** 0.5
**Evidence:** Mukilteo dumpster research (2026-09-08) missed P&T Industries (Lynnwood, $340-400 published) — surfaced only when Aaron named it; the research agent's "local operators" filter caught only established directory-listed haulers.

### [2026-09-08] Local previews bind to Tailscale, never localhost
**Trigger:** Any request for a local dev/preview server or "pop a node server" for Aaron.
**Action:** Kill any localhost-bound instance; serve with --host on the gateway Tailscale IP (100.65.203.16). His daily-driver M1 is on the tailnet and cannot reach localhost. Standing order, his words: "Always do this any time I ask for a local node."
**Confidence:** 0.9
**Evidence:** 2026-09-08 portal preview session; he corrected mid-session and restated as standing rule.

### [2026-09-08] Incremental requests are one task — run a cumulative counter
**Trigger:** User feeds a task in small steps (look → read → edit → commit → push); each step alone stays under the delegation thresholds.
**Action:** Treat the whole sequence as one task with a running tool-call counter from the first message; when any Orchestral Rule threshold fires (>6 tool calls, >2 writes, any commit/push/build/deploy, second repo), stop at the next clean checkpoint and hand off to a subagent with a handoff note. Log every task to orchestration-log.jsonl in the first tool block, and state any non-q8 subagent model as `model deviation: <model> — <reason>`.
**Confidence:** 0.5
**Evidence:** 2026-09-08 Barnabas site work ran inline as ~5 sequential "small" steps and became a 30+ tool-call project (html pull, repo check, commit, Cloudflare push) with zero orchestration-log entries and an undeclared GLM Flash subagent model.
### [2026-09-09] Bind local servers to tailscale IP
**Trigger:** Standing up any local web server / node / dev server for Aaron.
**Action:** Always bind to 100.65.203.16 (tailscale), never localhost-only; his M1 MacBook reaches this host only via tailnet.
**Confidence:** 0.5
**Evidence:** Aaron corrected twice (Sep 1 and Sep 8, 2026 sessions) after localhost-bound servers were unreachable from his MacBook; second time he said "Always do this any time I ask for a local node."

### [2026-09-10] Write topic file at task end, not session end
**Trigger:** Any task that creates or changes a runnable artifact (script, cron, service, config, deploy).
**Action:** Write/update the L2 topic file and L0/L1 index entries immediately at task end, before ending the turn — sessions die mid-flight too often to trust the end-of-session pass.
**Confidence:** 0.5
**Evidence:** Sep 5 meme-scout/GMGN session never reached durable memory; only nightly-cron notes survived (dreaming audit 2026-09-10).

### [2026-09-10] Unknown-name = mandatory memory_search <!-- project: github.com/AWILLTOLLC/barnabas-coaching -->
**Trigger:** User asks about a named business/person/project/thing that I cannot currently define from loaded context — even if the question feels conversational and I have "related" context (e.g. other businesses).
**Action:** Run memory_search on the name BEFORE answering. Never substitute adjacent entities for the one asked about. If the name appears in injected context (repo tags, project markers), follow the pointer instead of treating it as plumbing.
**Confidence:** 0.6
**Evidence:** Tweet asked about Barnabas; I answered for Black Raven + Glimmer because they were in-context and Barnabas wasn't. Repo tag with Barnabas was literally in front of me, unfollowed. Root cause: retrieval protocol skipped because question felt conversational; high confidence, low information.
