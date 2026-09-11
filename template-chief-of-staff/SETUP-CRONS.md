# Chief Template — Gateway Automations (Jeff setup)

Create these on the customer gateway (Control UI → Automations, or `openclaw cron` / automations API).
All delivery targets: the customer's main chat channel. Memory files are generic template files — no personal data.

| # | Name | Schedule | Payload | Purpose |
|---|------|----------|---------|---------|
| 1 | nightly-memory-consolidation | cron, 23:00 America/Los_Angeles (use customer's local tz) | agentTurn: consolidate today's daily memory note, promote significant items to MEMORY.md / topics, refresh L0 "Right now" header | Daily memory upkeep |
| 2 | memory-index-rebuild | cron, 01:00 local | agentTurn/script: rebuild memory semantic index | Keeps memory_search healthy |
| 3 | memory-dreaming-promotion | cron, 09:00 local | agentTurn: review recent daily notes, promote recurring patterns to topic files | Recursive improvement |
| 4 | auto-context-offload | every 30 min | script: check context size, offload when near limit | Session reliability |
| 5 | context-guard | cron every 30 min | script: watchdog on context/session state | Pairs with #4 |
| 6 | weekly-signal-compression | cron, Sunday 22:00 local | agentTurn: scan sessions for patterns/corrections, update instincts.md (atomic entries, confidence ≤0.6) | Self-improvement loop |
| 7 | memory-survival-test | cron, 07:00 local | agentTurn: verify memory files survived restart, report gaps | Trust check |
| 8 | skill-collection-review | every 7 days | agentTurn: review installed skills, suggest stale/missing ones | One job, not per-agent |
| 9 | heartbeat-main | every 30 min (wakeMode next-heartbeat) | declaration: heartbeat:main with starter HEARTBEAT.md present in workspace | Attention loop |

Notes:
- Schedule kinds mirror the production gateway (agent:main:main) — copy schedules 1:1 from Dru's gateway, replacing any personal payload text.
- Set explicit `delivery.channel` + `delivery.to` on jobs 1 and 7 (never inherit session bucket).
- Verify each job: `automations get <id>` after creation, then force-run one (`run`, runMode=force) to confirm it executes.
