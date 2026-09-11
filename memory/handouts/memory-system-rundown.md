# Dru's Memory System — Full Rundown

Handout for an LLM-agent presentation. Describes the memory architecture of "Dru," a personal AI assistant (OpenClaw agent) working for a single principal, Aaron. Written so another agent or writer can accurately present how it works.

---

## Design philosophy

The system assumes **every session starts from zero**. Nothing survives in context; everything survives in files. Three principles drive the design:

1. **Text beats brain.** If it's worth remembering, it's written to a file. "Mental notes" don't survive restarts.
2. **Load less, on demand.** A tiered structure means each session reads a tiny index first and expands only what's relevant.
3. **Facts get stale; structure must expose that.** New information supersedes old visibly — never silently.

---

## The layers

### Tier 0 — Always-loaded context (injected into every session)
- **SOUL.md** — persona, tone, operating rules (internal-and-reversible → act; external/costly → ask).
- **USER.md** — the principal's durable profile: identity, preferences, relationships, businesses, addresses. This is the authoritative place for "who is my human." (Lesson learned: when Aaron's email was buried in operational config notes instead of here, an agent failed to recall it and asked a question it should never have needed to ask.)
- **AGENTS.md** — the operating manual: memory protocol, delegation rules, orchestration policy.

### Tier 1 — The index layer
- **memory/MEMORY-L0.md** — one-liner per topic, ~20 lines, plus a **"Right now" header**: 3–6 lines of current focus (active projects, awaiting decisions) refreshed by the agent in-session and by a nightly cron as a safety net. Every main session reads this first, so it gets recent-state grounding before any search happens.
- **MEMORY.md (L1)** — key operational facts per topic: channel configs, credentials *locations* (never values), project states, hardware notes.

### Tier 2 — Deep detail, loaded on demand
- **memory/topics/&lt;name&gt;.md** — full context per topic. Opened only when doing real work on that subject.
- **memory/YYYY-MM-DD.md** — daily raw logs: what happened, what was decided, verbatim-worthy corrections.
- **DECISIONS.md** — meaningful decisions with alternatives considered and trade-offs accepted, so settled questions aren't re-litigated.
- **ERRORS.md** — one entry per mistake with root cause and prevention rule. No repeats allowed.
- **memory/instincts.md** — extracted behavioral patterns in an atomic format: Trigger → Action → Confidence (0.0–1.0) → Evidence.

### Parallel system — structured knowledge
- **ByteRover (`brv`)** — a separate long-term structured store for project patterns and architectural rules, queried before work and curated after tasks.

### Machine layer — semantic search
- **OpenClaw memory search** — local embedding model (300M, quantized, on-device) indexes all memory markdown into a local sqlite vector + FTS store. Agents query it semantically before answering questions about prior work. ~120 files / 600+ chunks currently indexed; runs fully locally.

---

## How memory flows

**Session start (main session):** read L0 index + "Right now" header → expand L1/L2 only for relevant topics → check today's and yesterday's daily files → retrieval protocol: `memory_search` before answering anything about past work.

**During the session:** learned something important? Write it to the right file *immediately*, not at the end. Corrected on a mistake? It goes in ERRORS.md or the protocol gets updated.

**Session end (the discipline layer):**
1. Log the session to the daily file.
2. Promote anything durable into L1/L2; supersede-mark whatever it replaces.
3. Refresh the L0 "Right now" header.
4. **Instinct extraction:** scan for reusable patterns. New instinct → instincts.md at confidence ≤ 0.6. **Promotion to hard rules is gated:** `high` confidence requires the pattern in 2+ distinct sessions with citable evidence; never promote the same night it's first observed. Wrong instincts get deleted.
5. **Signal extraction:** verbatim corrections, re-queries (same question asked twice = an earlier failure), approvals → `signals.jsonl`. A weekly cron compresses these into instinct candidates.

**Nightly cron (11pm):** safety net that consolidates anything the session missed and refreshes the "Right now" header.

---

## The supersede rule (newest addition)

When new information replaces an existing memory entry, the agent **edits the old entry** to prepend:

```
> superseded 2026-09-08 by: <new fact / pointer>
```

Old facts stay visible with their replacement noted — the system never lets stale and current information sit side by side looking equally true. This closes the classic memory-system failure where an agent "remembers" an outdated fact with full confidence.

---

## What makes this design work (presentation takeaways)

- **Memory is a liability as much as an asset.** The expiry/supersede mechanics and the instinct-deletion rule treat forgetting stale facts as a first-class operation.
- **Behavioral learning is evidence-gated.** One incident earns an instinct at low confidence; two sessions earn medium; only repeated, citable patterns become hard rules. This prevents overfitting to a single conversation.
- **The human's profile is sacred and centralized.** Anything an agent might need to know about the person belongs in one always-loaded file — not scattered in operational notes.
- **Mistakes are data.** ERRORS.md (root cause + prevention) and signals.jsonl (quantified, compressed weekly) turn failures into protocol changes.
- **Everything is plain markdown in files.** Human-readable, greppable, version-controllable, no proprietary store. The vector index is a *convenience layer* over the files, never the source of truth.
- **Costs almost nothing to run.** Local embeddings, local LLM fallback (a 27B Q8_0 model on an M5 Max measured at ~90 tok/s), hosted model for main work — the memory system itself adds negligible spend.
