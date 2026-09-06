# Behavioral RL for OpenClaw Agents
### A practical implementation of online reinforcement learning via memory

**Version:** 1.0  
**Date:** 2026-03-13  
**Author:** Aaron Williams + Dru (AI)

---

## What This Is

Princeton just published research proving that AI agents throw away the most valuable data they'll ever collect.

Every time an agent responds, the user's next message contains an implicit signal: did the agent succeed or fail? Did the recommendation land? Did the user have to re-ask? These signals are everywhere, they're free, and almost every agent in existence discards them the moment the conversation moves on.

This spec describes a system that captures those signals and uses them to make an OpenClaw agent measurably better over time — without retraining, without labeled datasets, without annotation pipelines.

The key insight: a frozen LLM can implement the same four loops as online RL — serve, collect, judge, update — by writing to memory instead of updating weights.

---

## The Theory

Princeton's team built what they call a "next-state signal" extractor. When an agent takes an action, the user's response *is* the reward signal. Specifically:

**Implicit scores (free, universal, currently ignored):**
- User re-asks the same question → agent failed. Score: -0.8
- User says "perfect" or "exactly" → agent succeeded. Score: +1.0
- Tool call had to be retried → partial failure. Score: -0.3
- User needed 3+ messages to clarify a single request → agent communication failure. Score: -0.5
- User accepted output and moved on → task success. Score: +0.5

**Correction direction (richer than scalar reward):**
When a user says "you should have checked the file first," they're not just saying the response was wrong. They're specifying which tokens should have been different and how. That's token-level supervision. Scalar rewards throw all of it away.

Their result: an agent started at 0.17 personalization score, hit 0.81 after 36 normal conversations. No new training data. No human annotations. Just running.

**The memory-layer translation:** Since we can't update model weights at inference time, we update behavioral priors stored in memory files. The effect is functionally equivalent — the agent behaves differently on future tasks because its loaded context (instincts, protocols) has been updated by observed signal.

---

## Architecture

Three systems, all running on OpenClaw's existing infrastructure:

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM 1: Dru's Behavioral RL            │
│                                                             │
│  Every session → extract_signals.py → signals.jsonl        │
│  Every session → track_orchestration.py → orchestration-   │
│                  log.jsonl                                  │
│  Weekly cron   → compress_signals.py → instincts.md        │
│                  track_orchestration.py --analyze           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 SYSTEM 2: Per-Client Coaching RL            │
│            (for agents running commercial services)         │
│                                                             │
│  Every session → client_signals.py --log <client-id>       │
│  Before session → client_signals.py --analyze <client-id>  │
│  Monthly       → client_signals.py --summary               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  SYSTEM 3: Weekly Compression Cron          │
│                                                             │
│  Schedule: 0 6 * * 1 UTC (Sunday 10pm PST)                 │
│  Compresses signals → promotes patterns → updates instincts │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
workspace/
├── memory/
│   ├── signals.jsonl              # append-only signal log
│   ├── orchestration-log.jsonl    # delegation decision log
│   └── instincts.md               # promoted behavioral patterns (existing)
├── scripts/
│   ├── extract_signals.py         # transcript analyzer
│   ├── compress_signals.py        # signal → instinct promotion
│   └── track_orchestration.py    # delegation tracker + analyzer
└── channels/<agent-name>/
    ├── client-profiles/
    │   ├── README.md
    │   ├── SCHEMA.md
    │   └── <client-id>.jsonl      # per-client signal log
    └── scripts/
        └── client_signals.py      # client signal tool
```

---

## System 1: Agent Behavioral RL

### Signal Collection (`extract_signals.py`)

Reads a session transcript (OpenClaw JSONL format) and extracts implicit reward signals.

**Usage:**
```bash
python3 scripts/extract_signals.py /path/to/session.jsonl
# or
python3 scripts/extract_signals.py --session-key agent:main:main
```

**What it detects:**

| Pattern | Detection Method | Score |
|---|---|---|
| Explicit correction | Keywords: "you should have", "no, actually", "that's wrong", "not quite" | -1.0 |
| Re-query | Semantic similarity between user messages in same session | -0.8 |
| Clarification spiral | >3 user messages to resolve one request | -0.5 |
| Tool failure / retry | Tool error followed by same tool call | -0.3 |
| Task success | Task completed, no re-ask in next 2 messages | +0.5 |
| Approval signal | Keywords: "perfect", "great", "exactly", "that's it", "love it" | +1.0 |

**Output format (`signals.jsonl`):**
```json
{
  "timestamp": "2026-03-13T21:00:00Z",
  "session_key": "agent:main:main",
  "topic": "git operations",
  "implicit_score": -1.0,
  "signal_type": "correction",
  "correction_verbatim": "you should have checked the branch name first",
  "context": "Agent pushed to wrong branch, user corrected",
  "topics_covered": ["git", "deployment"]
}
```

### Pattern Compression (`compress_signals.py`)

Reads `signals.jsonl`, groups by topic and signal type, promotes recurring patterns (2+ occurrences) to `instincts.md`.

**Usage:**
```bash
python3 scripts/compress_signals.py
```

**Logic:**
1. Group signals by topic tags
2. For each group with 2+ negative signals: surface as an instinct to avoid
3. For each group with 2+ positive signals: surface as an instinct to reinforce
4. Duplicate detection: skip if pattern already exists in `instincts.md` at equal or higher confidence
5. Confidence scaling: 2 occurrences = low, 4 = medium, 7+ = high

**Output (appended to `instincts.md`):**
```markdown
### [2026-03-20] Pattern: Check branch before git push
**Pattern:** Always verify current branch name before any push operation
**Confidence:** medium
**Evidence:** 3 occurrences over 2 sessions, avg score: -0.93
**Context:** Applies to all git push operations, especially in multi-branch repos
```

### Orchestration Tracking (`track_orchestration.py`)

Logs delegation decisions (inline vs subagent) and analyzes which task types perform better under which approach.

**Log an entry:**
```bash
echo '{"task_type": "file_analysis", "decision": "subagent", "rationale": "3+ files to read", "outcome": "success", "turns_needed": 1, "corrections_needed": 0}' | python3 scripts/track_orchestration.py --log
```

**Analyze patterns:**
```bash
python3 scripts/track_orchestration.py --analyze
```

**What it surfaces:**
- Task types where subagent outperforms inline (fewer corrections, higher success rate)
- Task types where inline is faster (< 2 turns, no correction)
- Common failure modes in delegated tasks
- Recommended delegation rules based on observed data

---

## System 2: Per-Client Coaching RL

Built for commercial use cases where an agent runs sessions with end-users or clients over time. The same signal-capture logic, but applied per-client instead of per-session.

The core principle: every coaching interaction is training data. A client re-asking a question you answered last month means your recommendation didn't land. A client reporting implementation means it did. Capture both.

### Signal Logging (`client_signals.py --log`)

```bash
echo '{
  "session_number": 2,
  "client_id": "acme-landscaping",
  "client_type": "retainer",
  "industry": "landscaping",
  "company_size": "11-50",
  "session_type": "retainer",
  "recommendations_given": ["automate invoice generation", "use Calendly for booking"],
  "implementations_reported": ["set up Calendly"],
  "re_questions": ["how do I connect my CRM again?"],
  "resistance_patterns": ["doesn't want to touch invoicing software"],
  "wins_reported": [],
  "notes": "CRM question was answered session 1 — explanation didn't stick"
}' | python3 scripts/client_signals.py --log acme-landscaping
```

### Client Review Before Sessions (`client_signals.py --analyze`)

Run before a coaching session to load context on what's worked and what hasn't:

```bash
python3 scripts/client_signals.py --analyze acme-landscaping
```

**Output:**
```
Client: acme-landscaping (retainer, landscaping, 11-50 employees)
Sessions: 2 | Avg score: 0.1 | Trend: flat

IMPLEMENTATIONS (worked):
  + Calendly setup (session 2)

RE-QUESTIONS (didn't land):
  - CRM connection (re-asked session 2, originally answered session 1)
    → Try a different explanation approach or provide written steps

RESISTANCE:
  - Invoicing software (consistent resistance — avoid pushing this angle)

RECOMMENDATIONS:
  → Address CRM connection with step-by-step guide before next session
  → Invoicing automation: find a lighter-touch entry point or drop it
```

### Cross-Client Pattern Analysis (`client_signals.py --summary`)

Run monthly to identify what's working across the whole practice:

```bash
python3 scripts/client_signals.py --summary
```

**What it surfaces:**
- Which recommendation types have highest implementation rates across all clients
- Which industries show the most resistance to specific recommendation categories
- Clients showing churn risk signals (score declining over sessions)
- Coaching approaches that consistently land vs. ones that consistently miss

---

## System 3: Weekly Compression Cron

Runs automatically every Sunday at 10pm PST (Monday 6am UTC).

**What it does:**
1. Runs `compress_signals.py` — takes the week's behavioral signals and promotes patterns to `instincts.md`
2. Runs `track_orchestration.py --analyze` — surfaces delegation patterns

**Setup (OpenClaw cron tool):**
```json
{
  "name": "Weekly Signal Compression",
  "schedule": { "kind": "cron", "expr": "0 6 * * 1", "tz": "UTC" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run weekly signal compression: python3 /path/to/compress_signals.py and python3 /path/to/track_orchestration.py --analyze. Summarize what patterns emerged and any instincts updated."
  },
  "sessionTarget": "isolated"
}
```

---

## AGENTS.md Protocol Updates

Add these sections to your agent's `AGENTS.md` to make signal capture part of standard operating procedure:

### Signal Extraction Protocol

```markdown
## Signal Extraction Protocol (Behavioral RL)

At end of every main session, in addition to memory logging:
1. Note any corrections the user gave you verbatim — append to memory/signals.jsonl via:
   python3 scripts/extract_signals.py <session_transcript_path>
2. Note any re-queries (same question asked again = you failed it the first time)
3. Note any explicit approvals ("perfect", "exactly", etc.)
4. The weekly cron automatically runs compress_signals.py to promote patterns to instincts.md

Signal types tracked: re_query (-0.8), correction (-1.0), approval (+1.0),
tool_failure (-0.3), clarification_spiral (-0.5), task_success (+0.5)
```

### Orchestration Tracking Protocol

```markdown
## Orchestration Tracking Protocol

When making a delegation decision (inline vs subagent), log it to memory/orchestration-log.jsonl:
- Before: note task_type, decision, rationale
- After: update with outcome, turns_needed, corrections_needed
- Use: python3 scripts/track_orchestration.py --log

Weekly compression runs --analyze and surfaces delegation patterns to instincts.md.
Goal: build a calibrated model over time of what to delegate vs handle inline.
```

---

## The Four Loops

To make explicit how this maps to the Princeton architecture:

| Princeton Loop | This Implementation |
|---|---|
| **Policy serving** | Agent answering messages (unchanged) |
| **Rollout collection** | `extract_signals.py` running on session transcripts |
| **Reward judging** | Scoring heuristics + pattern grouping in `compress_signals.py` |
| **Weight updates** | Writing promoted patterns to `instincts.md` (loaded next session) |

The loops are fully decoupled. The agent serves live requests while transcripts are being analyzed, while signals are being compressed, while instincts are being updated. Nothing blocks anything.

---

## Why It Compounds

The standard paradigm: collect data offline → train in batches → deploy → hope it works.

This paradigm: deploy → extract signal from every interaction → update continuously → improve automatically.

The gap widens with usage. An agent running this system for 3 months will be measurably more calibrated to its user than one that isn't. The more interactions, the more signal. The more signal, the more accurate the instincts. The more accurate the instincts, the fewer corrections, which in turn improves the signal quality (fewer negative signals from correctable mistakes).

It's a flywheel. And it costs nothing to run.

---

## Commercial Application (Barnabas Pattern)

For agents running commercial services — coaching, consulting, support — the per-client signal system creates a differentiated product:

**Pitch:** "Our system learns from every client interaction. The longer you work with us, the more calibrated our advice becomes to your specific business context."

No other AI consulting firm is building this. They're all deploy-and-hope. You're compounding.

---

## Implementation Notes

- All scripts use `Path(__file__).parent.parent` for workspace root — no hardcoded paths
- Signal scoring constants are tunable at top of each script
- `compress_signals.py` includes duplicate detection — won't re-add patterns already in `instincts.md`
- `client_signals.py` auto-computes `implicit_score` from signal arrays if not provided
- All JSONL files are append-only — never overwrite, always append

---

## Reference

Princeton research: online RL for AI agents  
OpenClaw docs: `/usr/lib/node_modules/openclaw/docs`  
Scripts: `/Users/apollo/.openclaw/workspace/scripts/`  
Barrett (Barnabas coaching agent) implementation: `/Users/apollo/.openclaw/workspace/channels/barnabas-coaching/`
