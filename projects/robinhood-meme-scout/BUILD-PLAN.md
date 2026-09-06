# GMGN Monitor Build Plan

**Mode:** Ponytail full  
**Date:** 2026-09-05  
**Files to build:** 3

---

## Files

1. `src/gmgn-monitor.ts` - Core streaming + candle filter
2. `src/filters.ts` - BKANTHA filtering logic
3. `src/alerts.ts` - iMessage delivery

---

## Implementation Plan

### 1. `src/filters.ts` (start here - dependencies)

**Purpose:** BKANTHA two-screen filters

**What it does:**
- `isEstablished(coin)`: 5-25M MC, 7+ days old
- `isFresh(coin)`: 500K-2M MC, <7 days old
- `isDirtyTape(coin)`: bundle/sniper/rug check

**Stdlib:** Native JS, no deps

**Code size:** ~50 lines

### 2. `src/gmgn-monitor.ts` (core)

**Purpose:** Stream GMGN data, apply filters, score coins

**What it does:**
- Poll GMGN endpoint every 30s
- Apply `filters.ts` logic
- Run TikTok 7-day mention check
- Score coins 1-100
- Alert if score >70

**Dependencies:**
- `filters.ts`
- `velocity-tracker.ts` (already built)
- `tiktok-scraper.ts` (already built)

**Code size:** ~150 lines

**Candle filter:** Inline, not separate component
```typescript
// ponytail: candle logic as filter
if (coin.age < 1d || coin.age > 4d) continue;
```

### 3. `src/alerts.ts` (end)

**Purpose:** Send iMessage to Aaron

**What it does:**
- Format coin data into message
- Call `imsg` CLI
- Log to SQLite

**Stdlib:** `exec` for imsg, `better-sqlite3` for DB

**Code size:** ~40 lines

---

## Build Order

1. `filters.ts` - No dependencies
2. `gmgn-monitor.ts` - Uses filters + existing TikTok/velocity
3. `alerts.ts` - Depends on monitor output

**Total time:** ~30 minutes

---

## Test Plan

**Unit tests:** None (ponytail: YAGNI for one-liners)

**Integration test:**
```bash
tsx src/cli.ts --mode gmgn-test
```

**Manual test:** Run for 5 minutes, check iMessage alerts

---

## Skipped (for now)

- ❌ `entry-timing.ts` - candle logic is inline
- ❌ `bundle-detector.ts` - folded into filters
- ❌ `community-checker.ts` - using tiktok scraper directly
- ❌ `twitter-api.ts` - not needed yet
- ❌ `unit-tests.ts` - manual test first

**Add when:** velocity spikes >100/day, or alerts get noisy

---

## Output

**Code first.** Then one line: skipped [X], add when [Y].
