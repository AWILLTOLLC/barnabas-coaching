# Robinhood Chain Meme Coin Scout

**Status:** ✅ Approved - Building  
**Date:** 2026-09-05  
**Author:** Dru

> **Note (2026-09-06):** Everything from here down to "DexScreener Integration (v2.3)" is the v1 plan, kept for history. TikTok, FOMO.Family, and iMessage are gone; README.md describes the system as actually built (v2: GMGN-only, Discord, feedback loop, regime tracker). New work is specced at the bottom of this file.

---

## Objective

Build an automated detection and evaluation system for Robinhood Chain meme coins using the BKANTHA stack: GMGN tape, FOMO.Family holder interrogation, candle-timing logic, and TikTok trend monitoring.

**Goal:** Identify 5-10M market cap gems before they run to 50-100M, avoid exit liquidity traps, and flag rugs early.

---

## Core Philosophy

**Tape first. People second. Patience third.**

Don't chase green candles. Hunt established coins that dumped but have live communities. Interrogate holders before they interrogate you.

---

## System Architecture

### Components (Completed)

1. ✅ **GMGN Monitor** - Real-time tape streaming (WIP) - *includes candle timer as filter*
2. ✅ **Holder Interrogator** - Wallet behavior scoring + bundle detection (WIP) - *bundles folded here*
3. ✅ **Community Health** - X/Twitter + TikTok validation (WIP)
4. ✅ **TikTok Meme Scout** - Trend detection via private API (DONE)
5. ✅ **Velocity Tracker** - 7-day mention history (DONE)

---

## Component 1: GMGN Monitor

**Purpose:** Live feed of Robinhood Chain meme coins, filtered by BKANTHA criteria.

### Features

- Chain filter: Robinhood only
- Three views:
  - **New Pairs:** <7 days old
  - **Trending:** Volume spikes
  - **Hot Searches:** Social velocity
- Market cap filters:
  - Established: 5-25M (7+ days old)
  - Fresh: 500K-2M (first hurdle to 10-20M)
- Volume sorting: High to low
- Alerts:
  - New pair under 25M MC
  - Volume spike >2x baseline
  - Entry demand at 100-200K (after 1-3M ATH)

### Tech Stack

- **Language:** TypeScript/Python
- **Data Source:** GMGN.ai API (or web scraping if no API)
- **Storage:** SQLite for coin history
- **Alerting:** iMessage + webhook

### Files

- `src/gmgn-monitor.ts` (WIP) - *includes candle timer filter*
- `src/filters.ts` (WIP) - BKANTHA logic
- `src/alerts.ts` (WIP) - iMessage/webhook delivery
- `src/holder-interrogator.ts` (WIP) - *includes bundle detection*

---

## Component 2: Holder Interrogator

**Purpose:** Score wallets by behavior patterns to identify "actually picking" vs. "spraying farmers."

### Features

- Pull holder data from FOMO.Family
- Analyze:
  - Last trade timestamp (stale = dead)
  - Buy→dump window (2-3 min = farming)
  - Launch frequency (every 200K = side wallets)
  - Selection quality (picking vs. spraying)
- Score each wallet 1-100
- Flag:
  - Sniper wallets
  - Bundle clusters
  - Exit liquidity providers
  - Early alpha callers

### Scoring Logic

**High Score (70-100):**
- Last trade <24h ago
- Hold time >1 hour before dump
- 1-3 launches per day
- 60%+ win rate
- Followed by other high-scorers

**Medium Score (40-69):**
- Mixed behavior
- Some farming, some picking
- Variable win rate

**Low Score (0-39):**
- Stale last trade
- Buy→dump in <5 min
- Sprays every launch
- Follower count > holdings quality

### Files

- `src/holder-interrogator.ts` (WIP) - *includes bundle detection*
- `src/wallet-scoring.ts` (WIP)
- `src/fomo-api.ts` (WIP)

---

## Component 4: Candle Timer

**Purpose:** Time entries to avoid green candle FOMO.

### Features

- Track coin age:
  - <24h: Too fresh (skip)
  - 1-4 days: Sweet spot (alert)
  - >4 days: Too stale (maybe)
- Monitor dump-and-recovery patterns:
  - ATH reached
  - Dump completed (>50% from peak)
  - Demand building at 100-200K
- Alert when:
  - Community still active on X
  - CT posting regularly
  - Holder count growing (not just whales)

### Logic

```typescript
function shouldBuy(coin: Coin): boolean {
  if (coin.age < 1d || coin.age > 4d) return false;
  if (coin.dumpCompleted !== true) return false;
  if (coin.demandLevel < 100k) return false;
  if (coin.communityHealth < 50) return false;
  return true;
}
```

### Files

- `src/candle-timer.ts` (WIP) - *folded into gmgn-monitor as filter*

---

## Component 5: Community Health Checker

**Purpose:** Validate that a coin has real community, not just bots.

### Features

- **X/Twitter monitoring:**
  - Post frequency
  - Engagement rate (likes/retweets)
  - Follower growth vs. trading volume
  - CT mentions (quality accounts)
- **TikTok monitoring (NEW):**
  - Trending hashtags
  - Coin mention velocity
  - Creator similarity graphs
  - Sound/audio trends
- Discord/Telegram (optional, later):
  - Active user count
  - Message frequency
  - Bot ratio

### Scoring

- **Live Community:** 20+ posts/day, 5%+ engagement, CT mentions, TikTok traction
- **Dead Community:** <5 posts/day, <1% engagement, stale last post
- **Bot Farm:** High follower count, low engagement, spammy posts

### Files

- `src/community-checker.ts` (WIP)
- `src/twitter-api.ts` (WIP)
- `src/tiktok-scraper.ts` ✅ **DONE**
- `src/velocity-tracker.ts` ✅ **DONE** - *includes 7-day tracking*

---

## Integration Flow

```
1. GMGN Monitor streams new coins
2. For each coin:
   a. Apply market cap filter (5-25M established OR 500K-2M fresh)
   b. Run Holder Interrogator
   c. Run Bundle Detector
   d. Check Candle Timer status
   e. Validate Community Health (X + TikTok)
3. Score coin 1-100
4. Alert if score >70 and criteria met
5. Store all data in SQLite for backtesting
```

---

## Data Storage

**Database:** SQLite (local, fast, portable)

**Tables:**

- `coins` - Basic coin data (CA, name, MC, age, volume)
- `holders` - Wallet addresses and scores
- `bundles` - Coordinated ownership clusters
- `alerts` - Generated signals with timestamp
- `communities` - X/Twitter + TikTok activity metrics
- `velocity_snapshots` - Daily velocity tracking
- `tiktok_mentions` - TikTok mention data

---

## Deployment

**Local First:** Run on Aaron's MacBook Pro (apollo)

**Process Management:**
- systemd service (or launchd for macOS)
- Auto-restart on crash
- Log rotation

**Alerts:**
- iMessage to Aaron for high-score coins (manual review)
- Webhook to Discord/Slack (optional)
- Email digest (daily/weekly)

**Trading Mode:**
- **Paper trading first**: Manual review of each alert
- Aaron clicks to execute trade manually
- Full audit trail of decisions
- **Future**: Automated trading via Robinhood API (if desired)

---

## Testing & Backtesting

**Phase 1: Paper Trading **(7 days)
- Run scripts live with manual alerts
- Aaron reviews each signal, decides to trade or skip
- Track all decisions in database
- Measure hit rate, avoid false positives

**Phase 2: Backtesting**
- Pull historical data
- Simulate trades on past signals
- Measure win rate, ROI, rug rate
- Tune filters based on results

**Phase 3: Refined Paper Trading **(30 days)
- Continue manual execution
- Build track record
- Document patterns that work
- Only then consider automation

**Phase 4: Automation **(optional)
- Auto-execute via Robinhood API
- Position sizing logic
- Stop-loss/take-profit rules

---

## Timeline

**Week 1**: GMGN Monitor + basic filters  
**Week 2**: Holder Interrogator + scoring  
**Week 3**: Bundle Detector + Candle Timer  
**Week 4**: Community Health (X-only) + integration  
**Week 5**: TikTok trend monitoring (DONE)  
**Week 6**: Testing + backtesting  
**Week 7**: Paper trading (manual alerts) + refinement  
**Week 8+**: Scale or automate based on results

---

## Success Metrics

- **Detection Rate:** % of 50-100M coins caught at 5-10M
- **Rug Avoidance:** % of flagged rugs that actually rugged
- **Win Rate:** % of alerts that hit 2x+
- **Time-to-Alert:** Average hours from launch to first alert
- **ROI:** Average return on successful trades

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| GMGN API changes | Fallback to web scraping |
| Holder data stale | Cross-reference with Etherscan |
| False positives | Manual review for all alerts (paper first) |
| Over-trading | Signal-driven, no time limits |
| Rug despite flags | Position sizing <5% per coin (manual control) |
| Latency | Run locally on apollo, not cloud |
| Missed alerts | iMessage + webhook redundancy |
| TikTok API changes | Fallback to web scraping |

## Key Decisions (2026-09-05)

1. **Market cap ranges**: ✅ 5-25M established, 500K-2M fresh (BKANTHA standard)
2. **Signal-driven**: ✅ No forced trades, no time limits, just pure signal quality
3. **Community checker**: ✅ X-only + TikTok (added 2026-09-05)
4. **Trading mode**: ✅ Paper first, manual review, manual execution → future automation
5. **Alert delivery**: ✅ iMessage to Aaron for each high-score signal
6. **TikTok integration**: ✅ Read-only scraping for trend detection (added 2026-09-05)

---

## Next Steps

1. ✅ **Plan reviewed and approved**
2. ✅ **TikTok skill created and applied**
3. **Build GMGN Monitor** first (highest leverage)
4. **Test for 7 days** before adding complexity
5. **Iterate** based on real data

---

## Files Created

```
projects/robinhood-meme-scout/
├── PLAN.md ✅
├── README.md ✅
├── package.json ✅
├── db/
│   └── schema.sql ✅
├── src/
│   ├── gmgn-monitor.ts (WIP) - *includes candle timer filter*
│   ├── filters.ts (WIP)
│   ├── alerts.ts (WIP)
│   ├── holder-interrogator.ts (WIP) - *includes bundle detection*
│   ├── wallet-scoring.ts (WIP)
│   ├── fomo-api.ts (WIP)
│   ├── tiktok-scraper.ts ✅
│   ├── signer.ts ✅
│   ├── endpoints.ts ✅
│   ├── velocity-tracker.ts ✅ - *includes 7-day tracking*
│   ├── community-scoring.ts ✅
│   └── cli.ts ✅
├── scripts/
│   └── run-monitor.sh (WIP)
└── tests/
    └── unit-tests.ts (WIP)
```

---

## Questions for Review

1. **Market cap ranges:** ✅ 5-25M (established) and 500K-2M (fresh) - confirmed
2. **Alert frequency:** ✅ Signal-driven, no limit
3. **Community checker:** ✅ X + TikTok (Telegram later)
4. **Paper vs. real:** ✅ Paper first, manual alerts
5. **BKANTHA stack:** ✅ All pieces included + TikTok added

---

**Status:** 🚀 Building GMGN Monitor next

---

# DexScreener Integration (v2.3)

**Status:** ✅ Built 2026-09-06 (TDD, 53 tests green, live dry-run verified)
**Author:** research session 2026-09-06 (Claude, approved by Aaron)

## Why

Two problems in v2.1/v2.2 that DexScreener's free API solves cheaply:

1. **Outcome capture is GMGN-throttled.** `outcomes.ts` snapshots tracked coins at +1h/6h/24h/72h/168h via GMGN `token info`, capped at ≤5 fetches per tick. As the tracked set grows, captures queue up and slip past their windows.
2. **Single-source risk.** Every number in the pipeline comes from GMGN. v1's timestamp bug (seconds-as-ms) shows what one bad payload assumption costs. No independent cross-check exists.

## Verified facts (probed 2026-09-06)

- Chain ID is `robinhood` on DexScreener's public API. Confirmed live via `/latest/dex/search?q=CASHCAT`: pairs return with `marketCap`, `volume.{m5,h1,h6,h24}`, `priceChange` windows, `liquidity.usd`, `txns` buys/sells, `pairCreatedAt`.
- `GET /tokens/v1/robinhood/{addr1,...,addr30}` — up to 30 token addresses per call, 300 req/min, no API key.
- One token can have several pairs (CASHCAT showed uniswap, giga, and "up" DEX pools). Rule: use the pair with the highest `liquidity.usd`.
- Boost/profile endpoints (60 req/min) expose paid promotion — recorded as a signal, not a gate.

## Phase 1 — batch outcome capture (build first)

Replace per-coin GMGN `token info` calls in `outcomes.ts` with one DexScreener batch call per tick:

- Collect all due-for-capture addresses (up to 30), hit `tokens/v1/robinhood/…`, map: price ← `priceUsd`, liquidity ← `liquidity.usd`, mc ← `marketCap`, using the deepest-liquidity pair per token.
- Record the source (`dexscreener`) on each outcome row in `scout.db` so mixed-source medians in the daily report are auditable.
- **Fallback:** on HTTP error, rate-limit, or a token missing from the response, fall back to the existing GMGN path for that token. Token absent from both → counts toward the existing 3-strikes dead-coin rule.
- Net effect: 5-fetch cap goes away; a full tracked set snapshots in 1 request.

## Phase 2 — momentum cross-check

- The score-≥70 momentum check (`max_drop_6h_pct`) reads `priceChange.h6` from DexScreener first; GMGN `token info` becomes the fallback instead of the primary.
- When both sources respond and disagree by >25% relative on price or >2x on liquidity, log a `source_divergence` line to `alerts.log` and stamp the alert. Divergence itself is a data-quality signal; the daily report should count them.

## Config (`criteria.json` additions)

```json
"dexscreener": {
  "enabled": true,
  "base_url": "https://api.dexscreener.com",
  "batch_size": 30,
  "timeout_ms": 5000,
  "divergence_pct": 25
}
```

## Files

- `src/dexscreener.ts` (new) — fetch + pair-selection (deepest liquidity) + normalizer, shapes pinned by `tests/fixtures/dexscreener-*.json`
- `src/outcomes.ts` — batch capture path + per-token GMGN fallback
- `src/monitor.ts` — momentum check reads DexScreener first
- `src/report.ts` — divergence count in the daily report
- `src/config.ts` — new config block

## Acceptance

- Unit tests: normalizer against fixtures (multi-pair token picks deepest pool; missing `pairCreatedAt` tolerated), fallback triggers on simulated 429/timeout.
- 7 days dry-run: zero missed capture windows, divergence rate known, no change to alert criteria.

## Explicitly out of scope (decided 2026-09-06)

- **pump.fun** — skip. Trades RH-chain tokens but launches remain Solana-side; Pons is the chain's actual launchpad. No coin universe GMGN + DexScreener don't cover.
- **Pons on-chain indexer** — deferred, revisit with outcome data. Pons (ponsfamily.com) has no API; data means indexing `TokenLaunched`/graduation events over RPC. Worth building only if daily reports show (a) alerts fire too late relative to graduation, or (b) losses cluster on repeat deployers (creator-wallet history is the unique signal). Bitquery sells a hosted Pons/Robinhood API as a build-vs-buy alternative.
- DexScreener boosts as a *gate* — record only, until the feedback loop says otherwise.
