# Step 5 — Gateway Change Plan (final; Dru, morning-ready)

Ordered, each item with verification. Nothing executed yet except items already live.

## Already deployed tonight (done, verified)
1. ✅ Backup cron: `30 3 * * *` system crontab, script `Documents/OpenClawBackups/openclaw-backup.sh`, 7d dailies / 30d Sundays, tested with real 2.3G run.
2. ✅ Memory-survival test: daily 8:30am PT automation, announces to iMessage, scores transcript facts vs memory files.

## Changes, in execution order

### Phase 1 — protocol text (cheap, this week)
3. **Point-of-use re-read rule** → AGENTS.md Retrieval Protocol, one line: "Any content that arrived as attachment, paste, or summary is re-read from disk at point-of-use before acting on it. Never act on a remembered version of a file."
   - Verify: rule present after next reset; grep-able.
4. **Verify-then-report rule** → AGENTS.md: "Report done only after verifying the artifact exists (read it back, curl the URL, run the command). Applies to subagent returns too; never relay an unverified claim." Log in ERRORS.md both q8 incidents.
5. **Subagent brief template** → `templates/subagent-brief.md`: Facts (each with file path + read timestamp), Sources to verify, Task, Verification. Mandatory for all spawn/send briefs.
   - Verify: template exists; next 3 briefs use it.

### Phase 2 — mechanical enforcement (scripts + cron)
6. **verify-logging.sh** (stdlib bash): checks today's daily note exists + every task in orchestration-log.jsonl has start+end lines; exit 1 on gap. Cron `0 23 * * *` alongside (or inside) the 11pm sweep; failure alerts via automations failure route.
   - Verify: real run tonight with a deliberately missing entry.
7. **Bootstrap checklist upgrade** → AGENTS.md "Every Session" gains: after reading L0/daily files, verify last-modified timestamps and read back the most recent entry before claiming context. No new script; it's a checklist edit.
   - Verify: next session start shows the check happened.

### Phase 3 — structural (needs a go from Aaron)
8. **Hourly reset trial**: once Phases 1-2 have run for ~3 days and the 8:30am report reads N/N, run a 1-day trial of hourly main-session resets during work hours; measure via the survival test + missed-beat count.
9. **Gates where code can actually sit in the path** (audit follow-on): git pre-commit hook in barnabas-coaching repo refusing commits without attribution trailers + a build check refusing deploys when verification steps weren't logged. Only worth doing if trial shows remaining gaps.
10. **Offload pass**: move any recurring model-call work that a script can do (credit checks already scripted; review automations list for candidates) to q8/scripts per standing order.

## Token discipline
- All new scripts: stdlib, zero model calls.
- Memory-survival test stays the single empirical metric; if its reports go N/N for a week, Phase 3 triggers are met.
