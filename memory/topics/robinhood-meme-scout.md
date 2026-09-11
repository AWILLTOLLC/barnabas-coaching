# Robinhood Meme-Scout / GMGN Monitor (built 2026-09-04/05)

> Backfilled 2026-09-10 from `memory/.dreams/session-corpus/2026-09-05.txt`,
> dreaming/light files, and on-disk artifacts. Most of the build detail is
> reconstructed — the durable memory entry was lost (memory-independence gap).
> Tagged [reconstructed] vs [confirmed] per section.

## What it is
A meme-coin detection system for **Robinhood Chain** (public mainnet July 2026),
built 2026-09-04/05 by Dru via the LittleJohn subagent (ran on local quinn-q8 —
confirmed in corpus line `b50453d5#L431`). Lives at
`projects/robinhood-meme-scout/`. Two halves:

1. **TikTok meme-scout** — private-API trend/mention scraping (skill:
   `~/.openclaw/workspace/skills/tiktok-meme-scout/`; registered device
   identity, signed requests x-khronos/ladon/argus/gorgon, mention-velocity
   tracking, community scoring). [confirmed — skill file + src/tiktok-scraper.ts]
2. **GMGN monitor** — polls GMGN for Robinhood Chain tokens, applies BKANTHA
   filters (established $5–25M, fresh $500K–2M), candle-age gate (1–4 days),
   TikTok mention/velocity boosts, iMessage alert via `imsg` CLI when score
   ≥70. Criteria in `criteria.json` (poll 60s, heartbeat hours PT 6/10/14/18/22,
   report 7am, Dune/DexScreener/Blockscout cross-checks, ollama Qwen3.8-27B for
   alert theses). [confirmed — HANDOFF.md, criteria.json]

## Current state (as of 2026-09-10)
**All monitors are DEAD** — Aaron ordered "Disable all of the robinhood and
meme trackers, kill their processes and don't let them restart" on Sep 5.
[confirmed — corpus session 9c272ad2]
- Killed: `hood-infra.mjs watch`, the gmgn/tsx monitor, log tails.
- Root cause of respawns: launchd agent `com.apollo.gmgn-monitor` (KeepAlive,
  `tsx src/cli.ts --mode gmgn`) — unloaded and plist quarantined to
  `~/.openclaw/disabled-launchagents/com.apollo.gmgn-monitor.plist`.
  [confirmed — plist verified on disk]
- Note: `projects/robinhood-meme-scout/com.apollo.gmgn-scout.plist` also sits in
  the project dir (not loaded; verify with `launchctl list | grep gmgn` if in doubt).
- The **skill** (`tiktok-meme-scout`) and all code remain intact; only the
  always-on monitor was killed. Sep 10 lessons on LLM thesis quality were
  applied in `tasks/lessons.md` — this looks like later interactive work, not Sep 5.

## How to restart (only on Aaron's explicit request)
[reconstructed from HANDOFF.md + quarantined plist]
```bash
cd projects/robinhood-meme-scout
tsx src/cli.ts --mode gmgn          # foreground/one-shot test
# GMGN key (if not yet saved): echo "y" | GMGN_API_KEY=*** gmgn-cli config
# To restore the launchd agent (it was intentionally quarantined):
cp ~/.openclaw/disabled-launchagents/com.apollo.gmgn-monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.apollo.gmgn-monitor.plist
```
Logs were at `/tmp/gmgn-monitor.log` / `/tmp/gmgn-monitor.err.log`.

## Decisions
- LittleJohn promoted from one-shot subagent to a registered persistent agent
  (q8) — the Robinhood research + GMGN setup ran on him. [confirmed]
- Monitor was built before the GMGN API key existed; HANDOFF lists key setup as
  the main open item (key was pending as of Sep 5). [reconstructed]
- Aaron later killed all trackers (Sep 5) — cost/noise vs value; keep code, no
  auto-restart. [confirmed]

## Open questions
- Was the GMGN API key ever saved (`~/.gmgn/config.json`)? Unverified.
- TikTok private API had DNS failures (`api16-normal-us.tiktok.com`) — health unknown.
- `criteria.json` metas currently hardcode the "cat" (Cash Cat) meta — needs a
  refresh whenever the chain meta shifts.

## Relay jobs removed (2026-09-11)
Both duplicate `gmgn-signal-relay` stream automations deleted (they tailed the dead `/tmp/gmgn-monitor.log` waiting for `GMGN_ALERT_FIRE` markers the current monitor.ts never emits). Current alert path: monitor → `generateThesis()` (local Ollama `hf.co/unsloth/Qwen3.8-27B-GGUF:Q8_0` @ localhost:11434, guardrails per tasks/lessons.md) → `formatAlert` → direct Discord DM via Quinn bot token. No relay agent in the loop.

## Sources
**Wiki/raw archives:**
- `wiki/raw/2026-09-04-memescout-README.md` — v2 system spec (GMGN-only, Discord, feedback loop, regime tracker, v2.3/v2.4 additions)
- `wiki/raw/2026-09-04-memescout-HANDOFF.md` — v1 handoff (TikTok-era, superseded; points to v2 rebuild)
- `wiki/raw/2026-09-04-memescout-BUILD-PLAN.md` — ponytail build plan for 3 core files
- `wiki/raw/2026-09-04-memescout-PLAN.md` — initial v1 plan (TikTok, FOMO.Family, iMessage; superseded by README.md)
- `wiki/raw/2026-09-04-memescout-criteria.json` — all thresholds, Ollama config, DexScreener/Blockscout/Dune settings
- `wiki/raw/2026-09-10-memescout-lessons.md` — LLM thesis quality corrections (Sep 10 user feedback)
- `wiki/raw/2026-09-04-memescout-thesis-prompt.ts` — Ollama prompt source; load-bearing spec for how summaries are generated

**Referenced repo paths (not copied to wiki/raw):**
- `src/monitor.ts` — main polling loop, dedupe, stats
- `src/alerts.ts` — Discord DM formatting and JSON logging
- `src/filters.ts` — BKANTHA gates and scoring logic
- `src/thesis.ts` — prompt builder + Ollama client (full source; wiki/raw only has thesis.ts for the prompt spec)
- `criteria.json` — live config file with all thresholds and thresholds under `regime`
