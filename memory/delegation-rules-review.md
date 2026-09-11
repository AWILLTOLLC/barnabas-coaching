# Delegation Rules Review — 2026-09-08 (subagent report for Dru)
Trigger: Barnabas site work ran inline (30+ tool calls) despite rules; log empty; model deviation unstated.

## 1. Diagnosis — why the rules failed

**a) Bright line only counts web I/O.**
> "any task needing **more than 2 web searches or 3 web fetches** is NOT small"

Tonight's task ("look at my site" → "pull the html" → "check the repo" → "commit" → "push to cloudflare") involved 0 web fetches against rules' threshold. The rule measures the wrong resource: it counts *searches/fetches* but not total tool calls, file writes, git operations, builds, or deploys — which is what actually bloats main context.

**b) Thresholds are evaluated per-task, never re-checked in-flight.**
Nothing in AGENTS.md says when to re-classify. Each incremental step was individually under every threshold, so the check "passed" forever. There is no running counter, no checkpoint rule, no statement that a multi-message task is one task.

**c) Logging is judgment-gated, therefore skipped.**
> "When making a delegation decision (inline vs subagent), log it… Use: python3 scripts/track_orchestration.py --log"

Logging requires (1) recognizing a "delegation decision" happened, (2) invoking a separate script. Tonight both failed: `memory/orchestration-log.jsonl` has 2 lines total (2026-09-07 and one earlier entry); nothing from this session. Rule that says "Log every delegation decision" lives as a subordinate clause of the bright line — it disappears when the bright line never fires.

**d) Model default has no deviation protocol.**
> "spawn a subagent (`sessions_spawn`), defaulting to local q8 (`ollama/quinn-q8:latest`)."

GLM Flash was used with zero logging and zero stated reason. The rule states a default but nothing triggers awareness when deviating from it.

**e) Vague escape hatches swallow the rule.**
> "Exceptions only for VERY SMALL tasks" and "When in doubt, delegate."

"VERY SMALL" is undefined; in-flight tasks don't feel like exceptions. Judgment — exactly what failed — is the deciding mechanism.

## 2. Recommended amendment (paste-ready replacement for Orchestration Rule)

```markdown
## Orchestration Rule (Aaron, 2026-09-05; amended 2026-09-08 — standing order)

Dru orchestrates all agents. For any task Aaron assigns:
1. **Domain agent exists** → `sessions_send` to that agent; relay results back.
2. **Otherwise** → subagent, default model `ollama/quinn-q8:latest`. Any other model
   requires one line in your reply: `model deviation: <model> — <reason>`.
3. **Inline exception:** only single-command/single-read micro-tasks (≤2 tool calls total).

### Hard thresholds — check before every tool call; fire = delegate, no judgment
- Total tool calls in this task > 6
- Web searches > 2, web fetches > 3
- File writes/edits > 2, or ANY git commit/push, build, test run, or deploy command
- A second repo/directory touched

### Scope creep — incremental tasks are ONE task
Multi-message requests ("look at site" → "pull html" → "commit" → "push") are a single
task with a running counter from the first message. When a threshold fires mid-task:
1. Stop at the next clean checkpoint; state where you stopped.
2. Spawn the subagent with a handoff: work done, files touched, next steps.
Never reset the counter because "the next step is small." Checkpoints the user drives
do not lower the threshold.

### Model default
Deviation from q8 is allowed once, stated as above. Undeclared deviation = rule violation.

### Logging — same tool block, always
At task start, in the SAME tool-call block as the first tool call, append one JSON line
to `memory/orchestration-log.jsonl`:
{"ts":"...","task_type":"...","decision":"inline|subagent|domain-agent","model":"...","rationale":"≤1 line"}
At task end, append the outcome line (same fields + outcome, turns_needed).
ALL tasks are logged, inline included — inline is what must be audited. If a session
ends and the log has no line for work you did, the session failed this rule.
Nightly consolidation: verify today's daily note has a matching log line per task.
```

Design notes: every trigger is a count or an event type — machine-checkable; the log append is bound to a tool block (harder to skip than "remember to"); the nightly consolidation gives cron-based detection of skipped logging.

## 3. Instinct entry (append to instincts.md; do not edit yourself — included for Dru)

```markdown
### [2026-09-08] Incremental requests are one task — run a cumulative counter
**Trigger:** User feeds a task in small steps (look → read → edit → commit → push); each step alone stays under the delegation thresholds.
**Action:** Treat the whole sequence as one task with a running tool-call counter from the first message; when any threshold fires (see Orchestration Rule), stop at the next clean checkpoint and hand off to a subagent with a handoff note. Also log every task to orchestration-log.jsonl in the first tool block, and state any non-q8 subagent model as `model deviation: <model> — <reason>`.
**Confidence:** 0.5
**Evidence:** 2026-09-08 Barnabas site work ran inline as ~5 sequential "small" steps and became a 30+ tool-call project (html pull, repo check, commit, Cloudflare push) with zero orchestration-log entries and an undeclared GLM Flash subagent model.
```

## 4. Redundancies / contradictions with the fixes

1. **Line ~188 rule of thumb** — "If a task will read more than ~3 files or produce output the user doesn't need to see verbatim, delegate" — overlaps the thresholds with a different unit (files vs calls). Fold into the Hard thresholds list as "reads > ~3 files"; delete the prose.
2. **"VERY SMALL tasks" exception** (Orchestration Rule §2) — replaced by the ≤2-tool-call definition; delete the vague phrase.
3. **"When in doubt, delegate"** — fine as tiebreaker, but keep it out of threshold logic; thresholds are now absolute.
4. **Orchestration Tracking Protocol script wrapper** (`python3 scripts/track_orchestration.py --log`) — extra friction caused the skip. Replace with direct JSONL append (script may stay as optional analyzer for the weekly `--analyze`).
5. **Bright-line clause "Log every delegation decision per the Orchestration Tracking Protocol"** — move logging into its own enforced section (as above) so it doesn't depend on the bright line firing.
6. **"After: update with outcome"** — as written it implies editing the original line; outcome is an append-only second line (JSONL stays append-only).

## Recommended next steps for Dru
1. Paste §2 into AGENTS.md (replacing Orchestration Rule + Tracking Protocol), pending Aaron's approval.
2. Append §3 to instincts.md.
3. Run a 1-week audit: grep orchestration-log.jsonl daily; report missed-logging violations to Aaron.
