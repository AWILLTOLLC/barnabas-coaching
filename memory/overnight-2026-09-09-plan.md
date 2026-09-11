# Overnight Plan — 2026-09-08 → 09-09 (Aaron's brief, 22:23 PDT)

**North star:** "A harness where I can hit /reset on main once an hour and never miss a beat." Fast, efficient, smart Dru that lives in files, not RAM. Token-spend aware; offload to q8 wherever possible.

## Lessons from tonight (raw material)
1. Aaron's LinkedIn rewrite arrived as pasted-text attachment. After compaction I worked from my summary of it, not the file. Wrote a paraphrase when "go" came. Root cause: canonical sources must be read from disk at point-of-use, never from memory-of-memory.
2. "48-hour incident" hyperbole in the bits post: I briefed Barrett with a wrong window (counted aftershocks into the incident). Root cause: briefs built from summarized context instead of verified facts.
3. Pattern: post-compaction, confidence in reconstructed detail exceeds actual fidelity. Compaction is lossy and I don't feel the loss.

## Plan (each step → q8 subagent; I critically review every return)
- [x] Step 1: Root-cause analysis. Take tonight's incident log (above) + session evidence; find the underlying pattern, express it from first principles (what does a session-reset-tolerant system require?). Output: pattern statement + where else it likely bites in this gateway (agents, crons, memory files, handoffs).
- [x] Step 2: North-star audit. Read the barnabas.coach posts (200-day, bits, 5-mistakes, tips) + AARON-VOICE + workspace protocols. List every practice we claim publicly that we don't do, or don't do well, internally. Gap list, evidence for each.
- [x] Step 3: Harness design brainstorm. From steps 1+2: concrete mechanisms (checklists, file contracts, reset rituals, subagent brief templates) that make hourly resets safe. Cost-aware: what can be a script vs a model call.
- [x] Step 4: I compile steps 1-3 into an insights-and-changes doc; second critical pass; ponytail skill as reference not authority; keep only what holds.
- [x] Step 5: Final thorough change plan for the gateway (what to change, where, order, who/what executes, verification per change).

## Execution notes
- Subagents: q8 default (`ollama/quinn-q8:latest`), hidden, one step each; I critique returns and re-brief if fishy.
- All decisions/outcomes logged to memory/2026-09-09.md + orchestration-log.jsonl.
