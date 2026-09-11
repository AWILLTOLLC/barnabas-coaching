# Step 2 — North-Star Audit (q8 subagent, reviewed by Dru)

| Claim | Reality | Severity |
|-------|---------|----------|
| Everything durable lives in files; session disposable | Session loads wholesale; no reset-tolerant load path; context loading is advisory | HIGH |
| Search memory before answering past-work questions | Habit, not mechanism; documented failures when it slips | HIGH |
| Hard constraints enforced by gates ("small piece of code that runs before an action") | No gates deployed; all constraints live in markdown instructions | CRITICAL |
| Errors logged with prevention rule | ERRORS.md exists; nothing enforces every mistake gets logged | MEDIUM |
| Decisions logged | DECISIONS.md exists; advisory only | MEDIUM |
| Every session logs to daily file | End-of-session rule + nightly cron safety net; sessions can wind down unlogged | LOW |
| File-on-disk saves during incidents | PROVEN (bits-hit-the-fan recovery was reading, not archaeology) | PROVEN |
| Model selection secondary to harness | PROVEN (routing/local-q8 cost structure) | PROVEN |
| Instinct confidence gating | instincts.md with scores; partially enforced | PARTIAL |
| Orchestration JSONL logging | Rule exists; verification is manual ("nightly consolidation") | MEDIUM |

## Headline finding
Architecture works; **enforcement is advisory, not mechanical**. The gap between what we publish and what the workspace enforces is the harness gap.

## Top 3 gaps
1. No gates — hard constraints are prose, not code.
2. Memory checks are habits, not mechanisms.
3. Orchestration/memory logging has no automated verification.

## Meta (Dru)
Subagent claimed it wrote this file; it didn't. Audit validated live.
