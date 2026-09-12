# Answer Key — Nightly Consolidation Ground Truth

**Date range:** 2026-09-05 to 2026-09-11
**Source:** memory/YYYY-MM-DD.md nightly consolidation sections + MEMORY.md git history

## Confirmed Useful Events (Ground Truth)

### 2026-09-05
1. **Model cleanup** — Deleted gemma4 (9.6GB) + Qwen3.8-27B UD-Q6_K (22GB); kept uncensored Q8. Remaining: quinn-q8 (37GB), Jackrong Q4_K_M (17GB), HauhauCS uncensored Q8 (37GB).
2. **Dru model switch** — Main session now `openrouter/z-ai/glm-5.3-flash` ($0.07/$0.25, coding 71.5, agentic 51.5). Config default still v4-pro.
3. **LittleJohn registered as real agent** — `agents.entries.littlejohn`, ollama/quinn-q8:latest, workspace `agents/littlejohn/`.
4. **Cross-agent messaging enabled** — `tools.agentToAgent.enabled: true` + `tools.sessions.visibility: all`. Verified ping to Frankie.
5. **Discord relay nuance** — All relayed DMs appear under Quinn's bot identity; Aaron = erasei, ID 276104854303145994, on DM allowlist.
6. **Dashboard started** — "Fleet Overview" tab with 4 session:progress cards (main, marketing, qwen, littlejohn).

### 2026-09-06
7. **X2Claw Chrome Extension** — Aaron didn't like it; files deleted 2026-09-06. Idea archived.
8. **Memory system comparison** — Key finding: 4 knowledge stores with no conflict resolution; instincts self-scored with no external grading.
9. **Memory Fixes (BUILT)** — Fix 1: provenance-weighted search (`scripts/provenance_search.py`); Fix 2: instinct reconciliation loop (`scripts/reconcile_instincts.py`).
10. **Fern Agent Setup** — Created agent `fern` with isolated workspace at `~/.openclaw/workspace/agents/fern/`. Model: Quinn Q8 local.
11. **Lily Tailscale + Gateway Access** — Lily set up Tailscale account (lily.z.myers@gmail.com); configured identityScopes in gateway auth.

### 2026-09-07
12. **Signals pipeline activation (12:05pm)** — Nightly memory cron re-enabled; extract_signals.py fixed /root→/Users paths; reconcile_instincts.py updated with numeric confidence.
13. **Barnabas configurator — Step 4 rewrite (13:48)** — Rewrote Step 4 into "Hook it up to your agent"; 6 guided steps with verification cues.
14. **Hermes verified** — Docs at hermes-agent.nousresearch.com; `~/.hermes/SOUL.md` read at session start as slot #1.
15. **Barnabas configurator — Step 3/4 swap (14:xx)** — Export now Step 3; Preview & Export now Step 4. Progress bar updated.

### 2026-09-08
16. **Graph-engineering digest** — Aaron sent https://github.com/codejunkie99/graph-engineering; wrote digest to `memory/topics/graph-engineering.md`.
17. **Email delivery works via Posteo** — posteo.de:587, drubot@posteo.com; earlier failure was wrong-port, not ProtonMail block. Aaron's email: mac@kaw.cc.
18. **Buzz pitch** — Aaron approved; emailed CLIENT-PITCH.md + TEST-ENV.md to mac@kaw.cc via Posteo.
19. **PROMOTION** — Aaron made Dru **Chief of Staff** (was "personal AI assistant"); updated IDENTITY.md, SOUL.md, MEMORY.md, USER.md, MEMORY-L0.
20. **Delegation rules amended (18:32)** — AGENTS.md Orchestration Rule replaced with mechanical thresholds; instincts.md cumulative-counter instinct appended.
21. **Merkle & Bloom ownership** — Vera owns merkleandbloom.com domain/site admin (corrected from Avery); Vera got Cloudflare token + GitHub PAT.
22. **Dru:main webchat reset incident (19:14–19:50)** — Root cause: secrets tool call blocked; system-initiated recovery; gateway restart 19:50:12.
23. **OpenRouter credits tracker** — scripts/openrouter_credits.py live; Aaron created OPENROUTER_MANAGEMENT_KEY; cron `openrouter-credits-brief-line` 7am PT.
24. **200-day post deployed by Barrett** — https://barnabas.coach/agent-notes-200-days.html.

### 2026-09-09
25. **Overnight plan** — All 5 steps complete; canonical copies written by Dru; verify-then-report rule added.
26. **Backup cron installed** — 2.3G tarball, 3:30am system crontab, 7d/30d retention.
27. **Memory-survival test deployed** — 8:30am PT, iMessage report.
28. **Barnabas site ideas from Anton** — Saved to projects/barnabas-coaching/IDEAS-anton-2026-09-09.md (parked).
29. **Chief-of-Staff template product** — Workshop went great; Jeff + Anton want to grow Barnabas; Jeff = first test customer.
30. **Chief template + droplet deployment** — Deployed to 134.209.217.142; SSH flakiness root-caused (UFW LIMIT + fail2ban); update gauntlet fixed.
31. **Durable record** — memory/topics/chief-template-droplet.md written; L0 updated.

### 2026-09-10
32. **Meme-scout memory backfill** — Wrote `memory/topics/robinhood-meme-scout.md` (L2); added L0 + L1 entries; evidence reconstructed.
33. **Rambo droplet day** — Old DO droplet (134.209.217.142) replaced with bare Ubuntu 24.04 droplet 143.198.151.243 (Jeff/Rambo).
34. **Add-provider-keys.sh created** — Hidden-prompt OpenRouter key → SecretRef → PROVIDER-PROOF-OK probe.
35. **Jeff/Rambo gateway** — OpenRouter key wired + proven; default model set to 5.3 Flash by Aaron.
36. **Sanitized 9-job cron set** — Deployed to Rambo droplet; report jobs delivery.mode=none until channel exists.
37. **Channel decision** — Jeff wants WhatsApp (knowingly accepts full-account tap); QR emailed to Jeff.
38. **Template package v2 complete** — OWNER-ACCESS-WALKTHROUGH.html, LESSONS-LEARNED.md, CHANNELS.md.
39. **Tailscale plan** — Droplet joins Jeff's tailnet; node-shared to Aaron.
40. **Aaron ordered Tello physical SIM** — eSIM unsupported on Galaxy A16 4G; Samsung A16 dual-SIM.
41. **Nightly Consolidation** — Signal extraction FAILED (no active .jsonl transcripts); MEMORY.md updated; backfill scan no orphans found.

### 2026-09-11
42. **Barnabas site: Creel removal** — Removed /creel page + footer link; deleted src/pages/creel.astro; rebuilt (9 pages); rsync'd; verified /creel 404.
43. **AGENTS.md orchestration rule fixed** — q8 default is `ollama/quinn-q8:ctx128k`; bare `:latest` never permitted.
44. **Gateway hiccup ~00:33-00:36** — DNS resolution failed on T-Mobile; Discord ENOTFOUND loop → profile-verification UNAVAILABLE storm (138 errs); clean restart 00:36:06→00:36:35.
45. **Droplet decision** — Aaron keeps 143.198.151.243 under his DO account and invoices Jeff directly.
46. **Rambo first-boot verified** — FULLINSTRUCTIONS run ✓; USER.md filled (owner "Lathamator", real estate); IDENTITY.md updated.
47. **gmgn-signal-relay resolved** — Duplicate jobs (3c06e3cf, d7da393a) DELETED; Aaron confirmed deletion.
48. **Meme-scout wiki ingest** — Verified + pushed (39c9526): 7 raw files (docs/criteria/lessons/thesis-prompt).

## Summary
- **Total confirmed useful events:** 48
- **Categories:**
  - Decisions: 12
  - State changes: 15
  - New facts (credentials, URLs, contacts): 10
  - Promotions/title changes: 3
  - Preference revelations: 4
  - Corrections: 4
