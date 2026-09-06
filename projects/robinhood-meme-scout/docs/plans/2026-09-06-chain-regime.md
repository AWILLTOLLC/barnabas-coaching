# Chain Regime Tracker (v2.2) — measure-and-stamp mode

**Goal:** Label Robinhood Chain hot/neutral/cold from per-scan breadth stats, stamp the label on every recorded coin/alert/heartbeat, and let the feedback loop measure whether regime predicts outcomes. NO gating of alerts yet — measurement first (decided with user from @RitOnchain regime post, 2026-09-06).

**Design:**
- `Coin.price_change_1h_pct` added to normalizer (`price_change_percent1h`; trenches → null).
- `src/regime.ts`: `computeBreadth(coins)` → { n, median_1h_pct, green_share, total_volume_24h, new_launches_1h }; `labelRegime(breadth, cfg)` → hot | neutral | cold (hot needs median ≥ hot_median AND green ≥ hot_green; cold if median ≤ cold_median OR green ≤ cold_green); `RegimeTracker` requires `confirm_scans` consecutive raw labels before the confirmed label flips (anti-whipsaw), seeded from last db snapshot on restart.
- db: `regime_snapshots` table (ts, stats, raw, confirmed); `coins.regime` column (ALTER TABLE, try/catch for existing dbs); recordCoin takes regime.
- criteria.json `regime`: { hot_median_1h_pct: 3, cold_median_1h_pct: -3, hot_green_share: 0.55, cold_green_share: 0.35, confirm_scans: 5 }.
- monitor: compute per scan → tracker.update → snapshot row → stamp recordCoin; regime line in alert DM, heartbeat, thesis DATA.
- report: gate-passer 24h returns grouped by regime + snapshot label distribution.

**Tasks:**
1. [x] normalizer field + tests
2. [x] regime.ts + tests (breadth math, label thresholds, confirmation streak)
3. [x] db schema + stamping + report by-regime; tests
4. [x] monitor/alert/heartbeat/thesis wiring
5. [x] full tests, typecheck, restart service, verify snapshots, commit
