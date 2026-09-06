# Robinhood Meme Scout

GMGN-powered monitor for Robinhood Chain meme coins. Polls GMGN, applies Aaron's criteria, and DMs alerts + heartbeats to Discord. **v2 (2026-09-05): TikTok scraper removed; GMGN-only rebuild.**

## What it does

Every `poll_interval_seconds` (default 60s):
1. Fetches Robinhood-chain tokens from `gmgn-cli` — `market trending`, `market trenches`, `market hot-searches` — and normalizes the three payload shapes into one coin type.
2. Applies **hard gates**: market cap in $500K–$2M or $5M–$25M, age 24–96h, top-10 holders ≤ 40%, no wash-trading flag.
3. Scores 0–100: base 40 + volume (≥$1M +20 / ≥$500K +10) + liquidity (≥$100K +15 / ≥$50K +10) + top10 ≤20% (+10) + mint & freeze renounced (+10) + LP burned (+5).
4. Score ≥ 70 → Discord DM with the full breakdown, then the address is added to `data/known.json` (never re-alerts).
5. Heartbeat DM every 4h at 6am/10am/2pm/6pm/10pm PT (silent overnight): coins scanned, gates passed, alerts sent, best non-alert. Silence outside those = something is wrong.

All thresholds live in `criteria.json` — edit it, restart, done. Every evaluated coin is logged to `data/alerts.log` (JSON lines) for tuning.

## Commands

```bash
tsx src/cli.ts scan --dry-run      # one scan, alerts printed not sent
tsx src/cli.ts monitor             # run forever (live DMs)
tsx src/cli.ts monitor --dry-run   # run forever, print instead of DM
tsx src/cli.ts heartbeat-test      # send one heartbeat DM now
npm test                           # unit tests (tsx --test)
```

## Setup

- `gmgn-cli` installed (`/opt/homebrew/bin/gmgn-cli`), API key in `.env` as `GMGN_API_KEY=...`
- Discord bot token read from `~/.openclaw/openclaw.json` (`channels.discord.token`); recipient is Aaron's Discord ID in `src/alerts.ts`.

## Run as a service (launchd)

A template is at `com.apollo.gmgn-scout.plist`. To install:

```bash
cp com.apollo.gmgn-scout.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.apollo.gmgn-scout.plist
```

Logs go to `data/monitor.log` / `data/monitor.err`. Unload with `launchctl unload ~/Library/LaunchAgents/com.apollo.gmgn-scout.plist`.

## Layout

- `src/config.ts` — criteria + .env loading
- `src/gmgn.ts` — gmgn-cli exec + payload normalizer (shapes pinned by `tests/fixtures/`)
- `src/filters.ts` — gates + scoring
- `src/heartbeat.ts` — PT slot scheduler
- `src/alerts.ts` — Discord DM, formatting, JSON log
- `src/monitor.ts` — loop, dedupe, stats
- `legacy/` — v1 TikTok-era code, kept for reference only (broken; do not revive the signer)

## Notes

- GMGN timestamps are Unix **seconds** (v1 treated them as ms — every age was wrong).
- Field quirks: trenches uses `volume_24h`, others use `volume`; trenches has no `creation_timestamp` (falls back to `open_timestamp`).
- No trading of any kind — this repo only watches and alerts.
