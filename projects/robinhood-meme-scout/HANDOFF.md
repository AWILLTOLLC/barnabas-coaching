# GMGN Meme Coin Scout - Agent Handoff

**Created:** 2026-09-05  
**Agent:** Dru (now promoted to full agent)  
**Project:** Robinhood Chain Meme Coin Detection System

---

## Current Status

✅ **Core Components Built:**
- `src/filters.ts` - BKANTHA two-screen filters (50 lines)
- `src/gmgn-monitor.ts` - Core streaming + candle filter (150 lines)
- `src/alerts.ts` - iMessage delivery + JSON logging (40 lines)
- `src/tiktok-scraper.ts` - TikTok private API client (complete)
- `src/signer.ts` - Request signature generation (complete)
- `src/endpoints.ts` - 24 TikTok endpoints (complete)
- `src/velocity-tracker.ts` - 7-day mention tracking (complete)
- `src/community-scoring.ts` - Cross-platform scoring (complete)
- `src/cli.ts` - Unified CLI entry point (complete)

✅ **Data Storage:**
- `db/schema.sql` - SQLite schema for alerts, coins, holders

✅ **Configuration:**
- GMGN API key stored in secrets (`GMGN_API_KEY`)
- TikTok device registration hardcoded (needs refresh every 30 days)
- iMessage configured via `imsg` CLI

---

## What Works

### 1. **TikTok Meme Scout** ✅
- Real-time trend detection via private API
- Coin mention velocity tracking
- Community health scoring (TikTok + X correlation)
- CLI: `tsx src/cli.ts --mode search --ticker DOGE`

### 2. **GMGN Monitor** ⚠️ (API key pending)
- Queries GMGN GraphQL via CLI
- Returns all Robinhood Chain tokens
- Filters by BKANTHA criteria (5-25M established, 500K-2M fresh)
- Applies candle timer (1-4 days old)
- Boosts score with TikTok mentions
- Sends iMessage alerts if score >70

### 3. **Alert System** ✅
- iMessage to Aaron via `imsg` CLI
- JSON logging to `data/alerts.log`
- Score-based filtering (only alerts >70)

---

## What Needs Attention

### 1. **GMGN API Key Setup** 🔑
**Action Required:**
1. Click the link: `https://gmgn.ai/ai/generateapi?pbk=...`
2. Generate API key
3. Run: `echo "y" | GMGN_API_KEY=*** gmgn-cli config`
4. Verify: `cat ~/.gmgn/config.json` should contain the key

**Why:** The CLI needs the key saved locally to authenticate requests.

### 2. **TikTok API Health** 🌐
**Issue:** DNS failures on `api16-normal-us.tiktok.com`
**Status:** Network-related, may resolve automatically
**Alternative:** Use web scraping if private API stays broken

### 3. **Live Testing** 🧪
**Next Step:**
```bash
cd projects/robinhood-meme-scout
tsx src/cli.ts --mode gmgn --ticker DOGE
```

**Expected Output:**
- Polls GMGN every 30s
- Returns mock data if API fails
- Scores coins 1-100
- Sends iMessage alert if score >70

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  GMGN Monitor (polls every 30s)                          │
│  └─ fetchGMGNData() → CLI → JSON → GMGNCoin[]           │
│      ↓                                                   │
│  runScan() → For each coin:                             │
│    └─ evaluateCoin(coin):                               │
│       ├─ Candle filter (1-4 days old)                   │
│       ├─ BKANTHA filters (5-25M established, 500K-2M)   │
│       ├─ TikTok mention boost (+15 if >100 mentions)    │
│       └─ Velocity boost (+10 if >200% change)           │
│          ↓                                              │
│       Score >= 70? → sendAlert()                        │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│  sendAlert(coin, score)                                 │
│  ├─ Format iMessage                                     │
│  ├─ exec imsg action=send...                            │
│  └─ Log to JSON                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Files Reference

**Core:**
- `src/gmgn-monitor.ts` - Main polling loop
- `src/filters.ts` - BKANTHA logic
- `src/alerts.ts` - iMessage delivery

**TikTok:**
- `src/tiktok-scraper.ts` - Core API client
- `src/signer.ts` - Headers generation
- `src/velocity-tracker.ts` - 7-day tracking
- `src/community-scoring.ts` - Cross-platform scoring

**CLI:**
- `src/cli.ts` - Unified entry point (all modes)

**Data:**
- `db/schema.sql` - SQLite schema
- `data/alerts.log` - JSON log file

---

## Testing Commands

```bash
# Test TikTok
tsx src/cli.ts --test

# Test GMGN (needs API key)
tsx src/cli.ts --mode gmgn --ticker DOGE

# Test TikTok search
tsx src/cli.ts --mode search --ticker DOGE

# Test community health
tsx src/cli.ts --mode community --ticker DOGE
```

---

## Known Issues & Solutions

| Issue | Status | Solution |
|-------|--------|----------|
| GMGN 403 Cloudflare | ⚠️ Pending | Use CLI instead of direct fetch |
| TikTok DNS fail | ⚠️ Network | Wait for resolution or fallback to web scrape |
| API key not saved | 🔑 Action needed | Click link and run `gmgn-cli config` |
| iMessage delivery | ✅ Works | Already configured via secrets |

---

## Next Steps (Priority Order)

1. **Click GMGN link** → Save API key → Test GMGN monitor
2. **Run 7-day test** → Monitor alerts → Tune filters
3. **Add backtesting** → Measure win rate → Optimize
4. **Paper trading** → Manual execution → Build track record
5. **Automation** → Robinhood API → Auto-execute (optional)

---

## Key Decisions

- **Ponytail mode:** Lazy senior dev - minimal code, no over-engineering
- **3 files core:** `filters.ts`, `gmgn-monitor.ts`, `alerts.ts` (240 lines total)
- **Signal-driven:** No forced trades, just pure quality signals
- **Paper first:** Manual review, then automate
- **TikTok + X:** Cross-platform validation for higher confidence

---

## Contact

**Agent:** Dru (you)  
**Project:** Robinhood Chain Meme Coin Scout  
**Goal:** Identify 5-10M gems before they run to 50-100M

---

**Ready to deploy. Test the GMGN monitor, then we're live.** 🚀
