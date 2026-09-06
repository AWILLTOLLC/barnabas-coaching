---
name: "openclaw-cron-automations"
description: "Register and verify scheduled script-mode cron automations via OpenClaw CLI; use when creating cron jobs or script automations."
---

# OpenClaw cron automations via CLI

Register scheduled script jobs on the gateway with `openclaw cron`, and verify them end to end.

## Procedure

1. Write the job as a standalone Python script; prefer pure Python over bash heredocs. Inside a quoted heredoc (`<< 'EOF'`), bash variables never expand; interpolate via environment or arguments instead.
2. Read the gateway token from `~/.openclaw/openclaw.json` (`gateway.auth.token`) inside the script at runtime; never hardcode or echo it.
3. Call the gateway with `openclaw gateway call <method> --params '<json>' --json --timeout 180000 --token <token>`. The CLI's default transport timeout is 10s, which kills slow operations like compacting a large session; always pass an explicit `--timeout` for anything heavy.
4. Pick the right session-metric field: `contextTokens` is the configured context **window size**, not usage. Real current usage is `contextBudgetStatus.estimatedPromptTokens`. Filtering sessions on `contextTokens` matches nearly every session.
5. Register: `openclaw cron add <name> --cron "<expr>" --tz "America/Los_Angeles" --command "<cmd>" --command-cwd <dir> --announce --channel discord --to "user:<id>" --best-effort-deliver`. Delivery refuses to inherit an implicit target from the agent-main session bucket; an explicit `--to` is required for isolated cron runs.
6. Verify: force-run with `openclaw cron run <id>`, then inspect `openclaw cron runs <id> --json` and check `completionStatus`, the summary, and `deliveryStatus` all say ok/delivered. Confirm the filtering logic with a dry-run mode before enabling apply.
7. Check for zombie runs after gateway restarts: `subagents` status can show "running" for runs killed by a restart. Compare the last transcript timestamp against wall time before waiting on a subagent; if stale, take the work over inline.

## Notes

- Job run summary lands in the runs entry's `summary` field; keep the script's stdout to a single JSON object so it reads as one line.
- `openclaw cron list --json` returns job IDs needed for run/edit/rm.
