---
source: /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/PLAN.md
fetched: 2026-09-11
type: internal-doc
---
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
