# Feedback Loop Implementation Plan (v2.1)

> **For agentic workers:** Use superpowers:executing-plans. Follow-on to 2026-09-05-gmgn-monitor-rebuild.md.

**Goal:** Turn the scout into a self-measuring system: record every coin seen (including rejects), track each coin's price outcomes at fixed horizons, and DM a daily tuning report so criteria evolve from evidence. Execution of trades stays human — nothing here touches `gmgn-cli swap`.

**Architecture:** Single process (the existing monitor). SQLite via `node:sqlite` (built into Node 26, zero new deps). Recording happens at first sight of each address; an outcome capturer piggybacks on the poll loop (≤5 token-info fetches/tick); the daily report reuses the heartbeat slot scheduler with its own state file and is drafted stats-first with an Ollama narrative on top.

**Spec (user, 2026-09-06):** daily report cadence (chain moves fast); stages 1+2+3 from the agreed loop design; human approves criteria changes; no auto-trading.

## Global Constraints
- No new npm deps; storage is `node:sqlite` (`DatabaseSync`).
- Outcome horizons: 1h, 6h, 24h, 72h, 168h from first_seen.
- Max 5 outcome fetches per poll tick (rate limit).
- Report slot: `report_hour_pt` in criteria.json (default 7), state in `data/report-state.json`, reusing `dueSlot` with `hours=[report_hour_pt]`.
- A failed token-info fetch after 3 attempts marks the outcome `dead` (itself a label: likely rug/delist).
- Descriptive stats only in the report (returns if held from first-seen price to each horizon) — measurement, not trade advice.

## Files
- `src/db.ts` — DatabaseSync wrapper: `coins` (address PK, ticker, name, first_seen_ms, price_at_eval, market_cap, liquidity, score, passed, alerted, reasons, flags, snapshot JSON) + `outcomes` (address, horizon_h, due_ms, captured_ms, price, liquidity, status pending/captured/dead, attempts). `recordCoin`, `hasCoin`, `dueOutcomes(now, limit)`, `captureOutcome`, `markDead`, report query helpers.
- `src/outcomes.ts` — `captureDueOutcomes(db, fetchStats, now, limit)`.
- `src/report.ts` — `computeReport(db, now)` pure stats; `formatReport(stats)`; `narrate(stats, criteria)` via Ollama (optional, fail-soft); `runDailyReport(...)`.
- `src/monitor.ts` — record every first-seen coin; call capturer each tick; report slot check next to heartbeat.
- `src/cli.ts` — add `report [--dry-run]`.
- Tests: `tests/db.test.ts`, `tests/outcomes.test.ts`, `tests/report.test.ts` on temp DBs.

## Tasks
1. [x] db.ts + tests (schema, record, due query ordering, capture, dead marking)
2. [x] outcomes.ts + tests (limit respected, attempts increment, dead after 3)
3. [x] monitor records first-seen coins + wires capturer; tests
4. [x] report.ts + tests (stats math on synthetic data: alert vs near-miss bands, top rejected gainers, dead counts)
5. [x] report scheduling in monitor + cli `report`; criteria.json `report_hour_pt`
6. [x] live verify: restart service, confirm rows appear, run `report --dry-run`; README; commit
