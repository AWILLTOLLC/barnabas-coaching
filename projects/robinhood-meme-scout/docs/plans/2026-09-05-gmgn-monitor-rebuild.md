# GMGN Robinhood-Chain Monitor Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken TikTok+GMGN scout with a lean, GMGN-only monitor that DMs Aaron on Discord when a new Robinhood-chain coin passes his confirmed criteria, with a 4-hour heartbeat 6am–10pm PT.

**Architecture:** A single polling loop shells out to the installed `gmgn-cli` (trending, trenches, hot-searches), normalizes the three payload shapes into one `Coin` type, applies hard gates + a transparent 0–100 score from `criteria.json`, dedupes against `data/known.json`, and delivers alerts/heartbeats via Discord DM (bot token from `~/.openclaw/openclaw.json`). No external npm deps beyond `typescript`/`tsx`; tests use `tsx --test` (node:test).

**Tech Stack:** TypeScript (ES2022, NodeNext), tsx (installed globally at `/opt/homebrew/bin/tsx`), node:test, `gmgn-cli` (installed, key in `.env` as `GMGN_API_KEY`), Discord REST v10.

**Spec:** The conversation-confirmed criteria (user approval 2026-09-05):
- Market-cap bands: fresh $500K–$2M, established $5M–$25M (either band qualifies)
- Candle window: coin must be 1–4 days old (24–96h) — hard gate
- Top-10 holder concentration must be under 40% — hard gate
- Volume thresholds as scoring signal (≥$500K good, ≥$1M strong)
- Alert threshold: score ≥ 70
- Heartbeat DM every 4h, 6am–10pm PT (slots 06,10,14,18,22 America/Los_Angeles), silent otherwise
- No TikTok scraping (forged-signature client removed, not rebuilt)
- No auto-trading; alerts only

## Global Constraints

- No new npm runtime dependencies; `package.json` deps stay `tsx` + `typescript` only.
- All GMGN access goes through `gmgn-cli` subprocesses with `GMGN_API_KEY` from the project `.env` explicitly passed in the child env.
- Timestamps from GMGN are Unix **seconds**; convert to ms (`< 1e12 → ×1000`).
- Field fallbacks (verified live 2026-09-05, fixtures in `tests/fixtures/`): `volume` (trending, hot-searches) vs `volume_24h` (trenches); `creation_timestamp` may be null → fall back to `open_timestamp`.
- Payload shapes: trending `{data:{rank:[]}}`; trenches `{completed:[],near_completion:[],new_creation:[]}`; hot-searches `[{tokens:[]}]`.
- Discord recipient ID `276104854303145994` (Aaron), bot token at `~/.openclaw/openclaw.json` → `channels.discord.token`.
- Never log or print the API key or bot token.
- Commits scoped to `projects/robinhood-meme-scout/` paths only; no push.

## File Structure

- `criteria.json` — all thresholds, editable without code changes
- `src/config.ts` — loads `.env` + `criteria.json`, typed
- `src/gmgn.ts` — CLI exec wrapper + payload normalizer → `Coin[]`
- `src/filters.ts` — gates + scoring (replaces old version)
- `src/heartbeat.ts` — PT slot scheduler with injectable clock
- `src/alerts.ts` — Discord DM + alert/heartbeat formatting + JSON log (rewrite)
- `src/monitor.ts` — polling loop, dedupe, stats
- `src/cli.ts` — entry: `scan|monitor|heartbeat-test` with `--dry-run` (rewrite)
- `legacy/` — old TikTok-era sources moved here untouched
- `tests/*.test.ts` — unit tests per module; `tests/fixtures/*.json` — live payload samples (already captured)

---

### Task 1: Archive legacy code, scaffold config

**Files:**
- Move: `src/tiktok-scraper.ts`, `src/signer.ts`, `src/endpoints.ts`, `src/velocity-tracker.ts`, `src/community-scoring.ts`, `src/due-diligence.ts`, `src/gmgn-monitor.ts`, `src/filters.ts`, `src/cli.ts`, `src/alerts.ts` → `legacy/`
- Create: `criteria.json`, `tsconfig.json` (if absent), update `package.json` scripts

**Interfaces:**
- Produces: `criteria.json` schema consumed by Task 2's `Criteria` type.

- [x] **Step 1: git mv legacy files** (`git mv src/<each> legacy/` — preserves history)
- [x] **Step 2: Write criteria.json**

```json
{
  "candle_age_hours": { "min": 24, "max": 96 },
  "market_cap_bands": [[500000, 2000000], [5000000, 25000000]],
  "max_top10_holder_rate": 0.4,
  "strong_top10_holder_rate": 0.2,
  "min_volume_24h": 500000,
  "strong_volume_24h": 1000000,
  "min_liquidity_usd": 50000,
  "strong_liquidity_usd": 100000,
  "alert_score_threshold": 70,
  "poll_interval_seconds": 60,
  "heartbeat_hours_pt": [6, 10, 14, 18, 22]
}
```

- [x] **Step 3: package.json scripts** → `"scan": "tsx src/cli.ts scan --dry-run"`, `"monitor": "tsx src/cli.ts monitor"`, `"test": "tsx --test tests/*.test.ts"`; remove stale `bin`.
- [x] **Step 4: Verify** `npm test` runs (0 tests, exit 0) and `git status` shows moves.
- [x] **Step 5: Commit** `refactor: archive TikTok-era code to legacy/, add criteria.json`

### Task 2: Config loader

**Files:** Create `src/config.ts`, `tests/config.test.ts`

**Interfaces:**
- Produces: `interface Criteria` (mirrors criteria.json), `loadCriteria(path?): Criteria`, `loadEnv(path?): Record<string,string>` (parses `KEY=VALUE` lines, ignores comments/blanks).

- [x] **Steps:** failing test (loads real `criteria.json`, asserts `alert_score_threshold === 70`; parses a temp `.env` fixture string) → run/fail → implement → run/pass → commit `feat: typed config loader`.

### Task 3: GMGN client + normalizer

**Files:** Create `src/gmgn.ts`, `tests/gmgn.test.ts` (uses `tests/fixtures/*.json`)

**Interfaces:**
- Produces:
  - `interface Coin { address; name; ticker; price_usd; market_cap; volume_24h; liquidity_usd; holder_count; top10_rate: number|null; created_at_ms: number|null; renounced_mint: boolean|null; renounced_freeze: boolean|null; burn_status: string|null; wash_trading: boolean; launchpad: string|null; twitter: string|null; website: string|null; source: string }`
  - `parseCoins(payload: unknown, source: string): Coin[]` — walks `data.rank`, `completed/near_completion/new_creation`, `[].tokens`; maps `volume ?? volume_24h`, `creation_timestamp ?? open_timestamp` (seconds→ms), drops entries with no address or `market_cap <= 0`.
  - `fetchAllCoins(env): Promise<Coin[]>` — execs the three `gmgn-cli market …` commands (5s spacing, 10MB buffer, errors → `[]` + console.error), dedupes by address (first wins, trending first).

- [x] **Steps:** failing tests against all three fixtures (assert coin counts > 0, `market_cap` numeric > 0, `created_at_ms` is ms-scale for hot-searches entry, trenches entry gets volume from `volume_24h`) → run/fail → implement → run/pass → commit `feat: gmgn client with normalizer for three payload shapes`.

### Task 4: Filters + scoring

**Files:** Create `src/filters.ts`, `tests/filters.test.ts`

**Interfaces:**
- Consumes: `Coin` (Task 3), `Criteria` (Task 2).
- Produces: `interface Evaluation { passed: boolean; score: number; reasons: string[]; flags: string[] }`, `evaluate(coin: Coin, c: Criteria, now?: number): Evaluation`.

Logic (hard gates reject with reason): mc in a band; age known and within candle window; `top10_rate > max` rejects (null → flag `holders-unknown`, continue); `wash_trading` rejects. Score: base 40; volume ≥ strong +20 / ≥ min +10; liquidity ≥ strong +15 / ≥ min +10 / below → flag `low-liquidity`; top10 ≤ strong_top10 +10; both renounced flags true +10; `burn_status === 'yes'` +5. Max 100.

- [x] **Steps:** failing tests (gate rejections: too young, too old, mc out of band, top10 0.5, wash trading; scoring: a maxed coin = 100, a min-band coin with weak volume < 70; null top10 passes with flag) → run/fail → implement → run/pass → commit `feat: gate+score evaluation from criteria.json`.

### Task 5: Heartbeat scheduler

**Files:** Create `src/heartbeat.ts`, `tests/heartbeat.test.ts`

**Interfaces:**
- Produces: `laParts(d: Date): { date: string; hour: number }` (Intl, America/Los_Angeles), `dueSlot(now: Date, lastSent: {date:string;slot:number}|null, hours: number[]): number|null`, `loadHeartbeatState(path)/saveHeartbeatState(path, state)` (JSON file `data/heartbeat.json`).

Logic: eligible only when LA hour ∈ [6, 22]; `latest = max(h ≤ laHour)`; due iff `lastSent` ≠ `{laDate, latest}` (restart after downtime sends only the latest slot, never backfills).

- [x] **Steps:** failing tests with UTC-constructed dates (2026-09-05T13:00Z = 6am PDT → slot 6; same time with lastSent {date,6} → null; 18:30Z = 11:30am → slot 10; 06:00Z = 11pm prev-day PDT → null; 22:05Z = 3:05pm after downtime, lastSent null → 14 only) → run/fail → implement → run/pass → commit `feat: PT heartbeat slot scheduler`.

### Task 6: Alerts + Discord delivery

**Files:** Create `src/alerts.ts` (new), `tests/alerts.test.ts`

**Interfaces:**
- Consumes: `Coin`, `Evaluation`.
- Produces: `formatAlert(coin, ev): string` (ticker, score + reasons list, MC, age h, volume, liquidity, holders + top10%, flags, CA, gmgn.ai link, socials); `formatHeartbeat(stats): string`; `sendDM(message, opts: {dryRun: boolean}): Promise<{success:boolean;error?:string}>` (dry-run prints `[DRY RUN]` and returns success); `logEvent(obj)` appends JSON line to `data/alerts.log`. Discord flow identical to legacy (create DM channel, post message).

- [x] **Steps:** failing tests (formatAlert contains CA, score, gmgn link; dry-run sendDM succeeds without network) → run/fail → implement → run/pass → commit `feat: discord alerts with dry-run and heartbeat formatting`.

### Task 7: Monitor loop + CLI

**Files:** Create `src/monitor.ts`, `src/cli.ts`, `tests/monitor.test.ts`

**Interfaces:**
- Consumes: everything above.
- Produces: `class Monitor { constructor(opts: {dryRun: boolean}); scanOnce(): Promise<ScanResult>; run(): Promise<never> }` where `ScanResult = { scanned: number; passed_gates: number; alerted: string[]; best: {ticker,score}|null }`. Dedupe file `data/known.json` (renamed from infra-known.json, same format). Stats accumulate between heartbeats and reset after each. CLI: `tsx src/cli.ts scan [--dry-run]`, `monitor [--dry-run]`, `heartbeat-test [--dry-run]`.

- [x] **Steps:** failing test (Monitor with injected fetch returning fixture coins: scanOnce counts scanned, dedupes a known address, dry-run alert recorded) → run/fail → implement (loop: scan → sleep poll_interval; each tick check `dueSlot` → send heartbeat with stats, persist state, reset stats; errors backoff 60s) → run/pass → commit `feat: monitor loop, dedupe, cli`.

### Task 8: Live verification + docs + service file

**Files:** Modify `README.md`, `HANDOFF.md`; Create `com.apollo.gmgn-scout.plist` (project root, not installed)

- [x] **Step 1:** `npm test` — all green.
- [x] **Step 2:** `tsx src/cli.ts scan --dry-run` live — expect nonzero scanned count, correct ages/MCs printed, zero or plausible alerts.
- [x] **Step 3:** `tsx src/cli.ts heartbeat-test` — sends ONE real Discord DM (explicitly user-requested deliverable) and verify success.
- [x] **Step 4:** Rewrite README (what it does now, commands, criteria file, heartbeat schedule); mark HANDOFF superseded.
- [x] **Step 5:** Write launchd plist running `monitor` with KeepAlive; include load instructions in README but do NOT `launchctl load` (user's call).
- [x] **Step 6:** Commit `docs: rewrite README for GMGN-only monitor; add launchd template`.

## Self-Review

- Spec coverage: bands→T4, candle→T4, top10 gate→T4, volume scoring→T4, threshold→criteria.json+T7, heartbeat schedule→T5+T7, TikTok removal→T1, no-trading→no swap code anywhere. ✓
- Types consistent across tasks (`Coin`, `Criteria`, `Evaluation`, `ScanResult`). ✓
- No placeholders; parser rules pinned to captured fixtures. ✓
