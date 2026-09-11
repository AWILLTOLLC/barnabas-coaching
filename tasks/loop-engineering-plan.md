# Plan: Adopting the "Loop That Edits the Loop" Pattern in OpenClaw

*Source: @polydao article "300 Agents, One Graph, and a Loop That Edits the Loop" (Sept 5, 2026). Prepared by Dru for Aaron, 2026-09-07.*

## Why this matters for us

The article's core claim: an agent system improves between runs when two things are true — **something carries forward** (memory) and **something rejects work before it carries forward** (gates). We already have half of this: memory tiers, ERRORS.md, instincts.md, signal extraction, cron jobs, subagent delegation. What we *don't* have is the closed loop: **corrections flowing back into the files that govern every future run, on a schedule, with compounding effect.**

The goal of this plan is not to add new machinery. It's to wire the machinery we have into a cycle that gets measurably better every week.

## Design principles (from the article, adopted as rules)

1. **Corrections get a permanent home, not a chat message.** Every correction Aaron gives or a gate catches becomes a line in a loaded-every-run constraints file.
2. **Stop conditions are machine-evaluable, written before the prompt.** Counts and verifiable facts, never "be thorough."
3. **Gates are agent-independent.** A script/validator rejects before any LLM verification tokens are spent.
4. **The meta-loop proposes; Aaron approves.** Agents never edit their own constraints without review. The article's warning is our policy: an unreviewed agent will eventually edit away the inconvenient constraint and explain why it was reasonable.
5. **Automate by frequency × reversibility.** First targets recur weekly, verify fast, and are cheap when wrong.

---

## Phase 0 — CONSTRAINTS.md as first-class memory (Week 1)

**Problem today:** corrections live in ERRORS.md and instincts.md, which are read *sometimes* — end of session, or when a relevant skill runs. They are not loaded at the top of every launch.

**Plan:**
- Create `shared/CONSTRAINTS.md` — a compact, append-mostly file of hard-won rules ("never merge companies without checking aliases.csv", "always cite a source line on graph edges"). Three lines at week one, thirty by month three. Each line is a mistake no future agent makes again.
- **Load it everywhere:** every agent's AGENTS.md gains one line: read `shared/CONSTRAINTS.md` at session start; every subagent spawn includes its current contents (or the relevant subset) in the task prompt. Keep it under a hard size cap (the article's file stays three lines → thirty; we cap at ~50 lines, forcing consolidation — old lines merge or graduate into skills).
- **Write path:** any correction (from Aaron, a gate, or an ERROR) must land here *in the same session it happens*. Amend the existing "When corrected on a mistake" protocol to name CONSTRAINTS.md as the always-loaded destination, with ERRORS.md as the detailed record.

**Compounding effect:** every future run of every agent inherits every past correction, with zero retrieval cost.

## Phase 1 — Stop conditions and gates on subagent work (Weeks 2–3)

**Plan:**
- **Task template change.** Subagent task prompts get a mandatory section: *Stop condition* (machine-checkable: "report ≤900 words", "every claim cites a file line", "return structured JSON with fields X/Y/Z") written *before* the prompt body.
- **Return schema for parallel work.** When spawning multiple subagents, they return a fixed shape; the parent merges deterministically. No prose merges.
- **Cheap gate first.** Wherever feasible, a script validates subagent output (word count, schema, required citations, forbidden phrases) before the parent spends tokens reviewing. The gate script rejects mechanically; only survivors get judgment.
- **Gate the agent doesn't control:** the validating script is never run by the subagent itself — the parent or the harness runs it. (An agent reviewing its own output approves it.)

**Compounding effect:** failed gate events are a new *source* of corrections — they flow into CONSTRAINTS.md (Phase 0) and the meta-loop (Phase 3).

## Phase 2 — Entity hygiene above the memory graph (Weeks 3–4)

**Plan:**
- Create `shared/aliases.md` (or `aliases.csv`): canonical names for the entities we deal with repeatedly — agent names, projects, clients, tools — and their known variants ("Merkle & Bloom" / "Merkle and Bloom" / "merkle-bloom").
- Rule: dedup/alias checks happen **above** memory, as an input to every memory write and every research dispatch — not by re-editing memory files after the fact.
- When a duplicate slips through (it will), the fix happens once in the alias table, never as a per-file patch.

**Compounding effect:** prevents the class of errors that silently fork our memory and poison future retrieval — the article's "three nodes where there should be one" problem.

## Phase 3 — The meta-loop: scheduled self-improvement (Month 2) — *the focus*

This is where the environment pushes itself forward. We already run weekly signal compression and a nightly memory cron; the upgrade is making the loop **close**: run history → proposed file edits → human approval → files change → next runs improve.

**Plan:**
- **Weekly Review Agent (cron, Sunday evening, after signal compression):** one agent reads the week's raw material — daily notes, ERRORS.md, new instincts, signals.jsonl, orchestration-log.jsonl, gate failures — and produces a **proposal packet**:
  1. CONSTRAINTS.md additions/mergers (dedup overlapping lines)
  2. Skill/protocol edits (small diffs, per the one-bounded-edit rule)
  3. Repeals: rules that evidence shows are wrong or obsolete
  4. Orchestration calibration notes (what should delegate vs. inline)
  5. Automation candidates scored by *frequency × reversibility*
- **Approval gate is human, always.** The packet lands as a pending proposal (skill_workshop proposals for skill changes; a review document for AGENTS.md/SOUL.md edits). Aaron approves or rejects in one pass. Nothing self-edits directly.
- **Explicit anti-drift rule (from the article):** the Review Agent may propose edits to constraints but **may not edit its own approval step** or any safety protocol. Those changes only ever come from Aaron directly.
- **Effect measurement:** each packet includes a short "what improved / what regressed" scorecard — re-query counts, gate failure rates, correction counts week-over-week. This gives us the feedback that the loop is actually compounding, not just churning.
- **Escalation path:** patterns confirmed in 2+ weeks with high confidence get promoted (instincts → protocol file) through the existing evidence-gating rules, as bounded edits.

**Why this compounds:** every week the system's *rules* improve, not just its memory. Week 12's agents run under week 12's rules — which encode 11 weeks of corrections no one had to re-explain.

## Phase 4 — Graph-query-driven dispatch (Month 2–3, selective)

**Plan:**
- Convert the highest-value recurring jobs from **static lists to state queries**: instead of "check these 40 things daily," the launch block reads current state (which topics are stale, which leads moved, which files were touched) and dispatches on structural importance.
- **Route by node state:** skip settled work — "skipping settled work is the entire economics of the setup." A daily cron on monthly-changing data is waste; match interval to data velocity.
- Apply this first to one job (recommend: Barnabas coaching content pipeline or inbox triage), prove the pattern, then generalize.

## Phase 5 — Facts before edges (standing rule, Month 3)

- For research/multi-subagent runs: **materialize the complete fact set before drawing connections.** Sequential research tilts toward what was read first. Standing rule in CONSTRAINTS.md: parallel breadth-first fact collection, then one synthesis pass over all of it.
- Every claim/edge in research output carries a **source line** — walkable, not just trusted.

---

## Sequencing and effort

| Phase | Effort | Compounding value | Dependency |
|---|---|---|---|
| 0. CONSTRAINTS.md | ~1 afternoon | Immediate, universal | None — do first |
| 1. Stop conditions + gates | Per-task habit + small harness work | High on subagent quality | Phase 0 |
| 2. Alias table | Low | Prevents silent corruption | Phase 0 |
| 3. Weekly meta-loop | One cron + review template | **The engine — highest** | Phases 0–1 |
| 4. State-driven dispatch | Per-job migration | Cost/perf | Phase 3 |
| 5. Facts-before-edges | One rule + habit | Research quality | Phase 0 |

## Success metrics (check monthly)

- **Corrections per week trending down** on repeated error classes (the article's original symptom: "the same instruction retyped on Monday that I had already typed on Friday")
- Gate rejection rate falling (agents internalize past rejections via CONSTRAINTS.md)
- Re-query/correction signal counts week-over-week (we already track these — now they close the loop)
- Proposal packets: % accepted, and rules repealed (a loop that never repeals is hoarding, not improving)

## What we deliberately do NOT adopt

- **300-agent swarms.** Our delegation patterns (one-to-few subagents, domain owners) fit our workload; massive parallelism is a cost without a use case yet.
- **Kimi K3 specifically.** Model-agnostic pattern; we keep our model routing.
- **Unreviewed self-editing.** Non-negotiable: the approval step stays human.
