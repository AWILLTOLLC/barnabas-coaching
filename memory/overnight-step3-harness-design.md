# Harness Design — Mechanical Enforcement for Reset-Tolerant Sessions

## 1. Session-Start Bootstrap
**What:** `/scripts/bootstrap-state.sh` — executable script that runs on every session start, reconstructs working state from files.

**Files checked (in order):**
1. `memory/MEMORY-L0.md` — load current focus
2. `memory/$(date +%Y-%m-%d).md` — today's daily note
3. `memory/$(date -d yesterday +%Y-%m-%d).md` — yesterday's log
4. `DECISIONS.md` — recent decisions
5. `ORCHESTRATION-LOG.jsonl` — verify orchestration logging exists
6. `.brv/` context tree — retrieve project patterns via `brv query`

**Checklist format:** Script writes `status/bootstrap-checklist.txt` with `✓`/`✗` per item before task execution. If any critical item missing, exits with code 1 and prints missing files.

**Cost:** ~50 tokens per session (shell echo), one-time execution.

---

## 2. Action Gate — Source Re-Verification
**What:** `/scripts/action-gate.sh` — pre-action verification wrapper called before `sessions_send`, cron prompts, memory writes.

**Enforcement:**
- Takes action type + context file paths as arguments
- For `sessions_send`: verifies source files exist and were read within last 24h (or re-reads them)
- For memory writes: checks `ORCHESTRATION-LOG.jsonl` has matching entry for this session
- For publishes: cross-checks timestamps in source logs vs. brief content
- Writes `status/action-gate-log.jsonl` with verification results

**Call pattern:** `scripts/action-gate.sh --action publish --sources memory/2026-09-08.md memory/2026-09-07.md`

**Cost:** ~30 tokens (shell glob + stat), runs on every action.

---

## 3. Canonical-Source Discipline — Point-of-Use Re-Read
**What:** Enforced via `brv` protocol + script check.

**Mechanism:**
- `brv query "<topic>"` returns file paths with last-modified timestamps
- Before any fact usage, script compares current file mtime vs. context mtime
- If `context_mtime < file_mtime`, script forces re-read and updates context
- Writes to `status/reread-trace.jsonl` for audit

**Template:** `/templates/brief-template.md` — subagent briefs must include `# Sources` section with file paths and read timestamps.

**Cost:** ~20 tokens per fact usage (stat + jsonl write).

---

## 4. Subagent Brief Template
**What:** `/templates/subagent-brief.md` — forces facts-with-provenance.

**Template structure:**
```markdown
# Task
<objective>

# Facts (with provenance)
- [X] fact_1 ← `memory/2026-09-08.md:line123` (read 2026-09-08T22:28)
- [X] fact_2 ← `memory/2026-09-07.md:line45` (read 2026-09-08T22:28)

# Sources to verify before action
- `memory/2026-09-08.md` — check timestamps vs. brief
- `ORCHESTRATION-LOG.jsonl` — verify logging entry exists

# Confidence discounting
- All facts treated as <24h old unless source-read timestamp present
- Reconstruction distance: 1 hop from summary = -0.2 confidence
```

**Enforcement:** `scripts/validate-brief.sh` checks template completeness before `sessions_spawn`.

**Cost:** ~40 tokens (script + template render).

---

## 5. Logging Enforcement
**What:** `/scripts/verify-logging.sh` — mechanical verification script.

**Checks:**
1. `memory/$(date +%Y-%m-%d).md` exists and has entries for session tasks
2. `ORCHESTRATION-LOG.jsonl` has matching entry per task (ts, task_type, decision, model, rationale, outcome, turns_needed)
3. `ERRORS.md` has new entry if any action failed
4. `DECISIONS.md` has new entry if any decision made

**Cron:** `0 23 * * * /scripts/verify-logging.sh` — nightly at 11pm PST

**Exit codes:** 0 = all present, 1 = missing entries (alerts via Control UI)

**Cost:** ~30 tokens (jsonl parse + file stat).

---

## 6. Compaction Insurance
**What:** Pre-compaction checkpoint script + policy.

**Script:** `/scripts/pre-compaction-checkpoint.sh`

**Writes BEFORE compaction:**
1. `status/pre-compaction-snapshot.json` — current working state (task list, open questions, confidence scores)
2. `memory/compaction-audit-$(date +%Y%m%d).md` — list of all files read this session with timestamps
3. `ORCHESTRATION-LOG.jsonl` — flushes any pending entries

**Policy:**
- Any fact used after compaction must re-verify against `memory/compaction-audit-*.md`
- If a fact's source file mtime > snapshot time, re-read required
- Script writes `status/compaction-verification-required.txt` listing facts needing re-verification

**Cron trigger:** Runs before any scheduled compaction (model-dependent).

**Cost:** ~50 tokens (json + md writes).

---

## Minimal Moving Parts Summary
| Mechanism | Location | Cost | Model Calls |
|-----------|----------|------|-------------|
| Bootstrap | `/scripts/bootstrap-state.sh` | ~50 tokens/session | 0 |
| Action Gate | `/scripts/action-gate.sh` | ~30 tokens/action | 0 |
| Re-Read Check | `brv` + `/scripts/reread-trace.sh` | ~20 tokens/fact | 0 |
| Brief Template | `/templates/subagent-brief.md` | ~40 tokens/brief | 0 |
| Logging Verify | `/scripts/verify-logging.sh` | ~30 tokens/nightly | 0 |
| Compaction | `/scripts/pre-compaction-checkpoint.sh` | ~50 tokens/compaction | 0 |

**Total:** ~220 tokens per full cycle (vs. ~500-1000 tokens for nightly model audit).

**OpenClaw features leveraged:**
- `sessions.reset` config (hourly reset)
- Cron automations (`openclaw cron register`)
- `brv` for context retrieval
- Control UI alerts for script failures

**Rejection criteria met:** All mechanisms use stdlib shell/python, no model calls where script suffices.
