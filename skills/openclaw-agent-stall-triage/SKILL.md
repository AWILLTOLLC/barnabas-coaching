---
name: "openclaw-agent-stall-triage"
description: "Diagnose OpenClaw agents whose messages queue forever or sessions appear hung; covers the context-window vs reserve floor deadlock"
---

# OpenClaw Agent Stall Triage

Steps for diagnosing an OpenClaw agent that appears hung: new messages sit in queue, session shows a spinner, resets and gateway restarts don't help. Do these in order.

## Step 1 — Confirm the run actually exists

Check `session_status` for the agent's canonical session key and `sessions_history` (pendingBefore=1). No pending inputs and a recent assistant turn with `stopReason: stop` means the agent is idle, not hung — the UI is showing stale client state. Have the operator hard-refresh before deeper work. A direct probe via `sessions_send` ("reply with exactly PING-OK") proves the backend path end to end.

## Step 2 — Read the gateway log for the stall reason

Grep today's `/tmp/openclaw/openclaw-<date>.log` for the session key and for `stalled session` and `context-pressure-diagnostic`. Two known signatures:

- `route=compact_only` repeating with the same `estimatedPromptTokens` = compaction deadlock.
- `stalled session ... reason=active_work_without_progress` = a run mid-work (long tool calls look like stalls; check whether it later completed).

## Step 3 — Fix the compaction deadlock (the common trap)

`agents.defaults.compaction.reserveTokensFloor` is a GLOBAL default. If any model's `contextWindow` is smaller than that floor, every run needs prompt tokens + reserve > window, compaction can never satisfy it, and the run loops in `compact_only` forever. Resets and gateway restarts do NOT fix it — context re-inflates within a turn or two.

Fix: raise the model's `contextWindow` and `num_ctx` in its `models.providers` entry until window exceeds the floor with real working room, then bounce the model in Ollama (a `keep_alive: 0` request, then a reload request with the new `num_ctx` option — note a manual reload without `num_ctx` uses the model's arch default). Verify with a probe message.

Rule going forward: whenever adding or resizing a local model in this instance, check its context window clears the configured `reserveTokensFloor` (currently 80000) before wiring it to an agent.

## Step 4 — Verify before declaring success

Send a probe via `sessions_send` and confirm the exact reply. Report the root cause arithmetic (window vs floor vs prompt size), not just "fixed it".
