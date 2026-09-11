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
- `requester settle wake failed` repeating every ~60s = a tool call is blocked waiting on human input that was never delivered (the `secrets` masked-entry prompt has no delivery path on some surfaces). The session then self-resets: the sqlite `transcript_events` for the session shows a custom event with `reason: "reset"` timestamped within ~100ms of the next inbound `chat.send`, with no `sessions.reset` request in the gateway log — a system-initiated recovery, not a user action. Treat a "your turn was interrupted by a gateway restart" system message as unverified; confirm by grepping the log for actual SIGTERM/restart lines before reporting a restart as the cause.

## Step 2b — Unwedge a session blocked on a credential prompt

The only fix for a tool call blocked on masked entry is the credential arriving or the session resetting; the agent cannot cancel it. Before any agent calls `secrets`, confirm the credential already exists in the store (`secrets` action=list) — if missing, have the operator add it via the Control UI first, and never let an interactive main session sit on the request. Concurrent subagent spawns failing with `embedded tool authority registration does not match its attempt` during the wedge are a gateway-side fault: retry after the real gateway restart clears it, and report upstream if it recurs.

## Step 3 — Fix the compaction deadlock (the common trap)

`agents.defaults.compaction.reserveTokensFloor` is a GLOBAL default. If any model's `contextWindow` is smaller than that floor, every run needs prompt tokens + reserve > window, compaction can never satisfy it, and the run loops in `compact_only` forever. Resets and gateway restarts do NOT fix it — context re-inflates within a turn or two.

Fix: raise the model's `contextWindow` and `num_ctx` in its `models.providers` entry until window exceeds the floor with real working room, then bounce the model in Ollama (a `keep_alive: 0` request, then a reload request with the new `num_ctx` option — note a manual reload without `num_ctx` uses the model's arch default). Verify with a probe message.

Rule going forward: whenever adding or resizing a local model in this instance, check its context window clears the configured `reserveTokensFloor` (currently 80000) before wiring it to an agent.

## Step 3b — Fix Ollama context window mismatch (HTTP 500 on local models)

When local Ollama models return HTTP 500 errors but work fine via direct `curl` to port 11434, the cause is often a **context window mismatch**: OpenClaw's configured `contextWindow` exceeds the model's actual runtime context (`-c` flag in llama-server process args).

Symptoms: intermittent HTTP 500s that get worse as session context grows; direct API calls to `http://127.0.0.1:11434` succeed every time.

Diagnosis:
```bash
# Check what Ollama actually runs with
ps aux | grep "[l]lama-server" | grep -oE "\-c \d+"
# Check what OpenClaw thinks it has
cat ~/.openclaw/openclaw.json | python3 -c "import json,sys; [print(m['id'],m['contextWindow']) for m in json.load(sys.stdin)['models']['providers']['ollama']['models']]"
# Check the model's Modelfile
curl -s http://127.0.0.1:11434/api/show -d '{"name":"<model>"}' | python3 -c "import json,sys,re; m=json.load(sys.stdin)['modelfile']; print(re.search(r'num_ctx\s+(\d+)',m))"
```

Fix — create a variant with the correct context window:
```bash
# Write a Modelfile
cat > /tmp/model-fix.modelfile << EOF
FROM <model>:latest
PARAMETER num_ctx <matching_openclaw_config_value>
EOF
# Build and verify
ollama create <model>:ctx128k -f /tmp/model-fix.modelfile
curl -s http://127.0.0.1:11434/api/show -d '{"name":"<model>:ctx128k"}' | grep num_ctx
```
Then update all references in `openclaw.json` from `<model>:latest` to `<model>:ctx128k`. Restart gateway after.

## Step 3c — Fix the wedged overflow session ("prompt too large" even after fixes)

When `session_status` or the compaction sweeper shows a session's context over the model window (e.g. 186k in a 131k window), every model call fails with "Context overflow: prompt too large". Overflow recovery (compact → retry) also fails, because compaction itself is a model call on the same oversized transcript — the session wedges and only `/reset` from a larger-context model escapes it. Verify the model itself is healthy first: direct `curl` to Ollama, `ollama ps` for VRAM fit.

Prevention, in priority order:
1. Run the workspace sweeper `scripts/nightly-auto-compact.py --apply` on a short cron (every 30 min), not nightly — evening activity defeats a nightly slot, and a wedged session can't wait. Keep its idle guard short (45 min); a 6h guard skips the main session every evening.
2. Never raise `compaction.memoryFlush.softThresholdTokens` assuming it is an absolute token count. It is a DISTANCE below the compaction threshold: flush fires at `contextWindow - reserveTokensFloor - softThresholdTokens` (semantics in `src/auto-reply/reply/memory-flush.ts`, `shouldRunMemoryFlush`). Setting it to 80000 with a 40k floor flushes at ~11k tokens — constant flush spam. Default 4000 is correct.
3. Check `scripts/nightly-auto-compact.py` output on every run; a NameError mid-script silently leaves sessions uncompacted.

## Step 4 — Verify before declaring success

Send a probe via `sessions_send` and confirm the exact reply. Report the root cause arithmetic (window vs floor vs prompt size), not just "fixed it".
