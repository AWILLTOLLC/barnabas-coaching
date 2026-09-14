# Robinhood Paper Trader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone paper-trade execution tool that Meme Scout fires on alerts: it opens simulated positions, runs the full v1.0 strategy lifecycle (ladder sizing, moon-bag trim, 24h LP-gated exits), records fills and P&L, and DMs activity — with a documented executor seam where Aaron's own wrapper (e.g. around an anvil fork) can replace the builtin simulation engine.

**Architecture:** Standalone project `projects/robinhood-paper-trader/` mirroring the scout's stack: TypeScript ESM, tsx, `node:sqlite` (WAL mode — CLI and daemon share the db), no new npm deps. Two processes: a CLI (`buy`/`sell`/`status`) invoked externally, and a daemon (`run`) that marks positions and fires strategy exits. All money-touching behavior terminates at a single `executeOrder(order) → fill` seam; the builtin implementation is pure simulation (no chain, no cast, no network beyond price feeds). **Boundary (fixed):** this codebase never constructs or invokes on-chain transactions; the `external` executor type shells out to a user-supplied command that owns all of that.

**Tech Stack:** TypeScript ES2022/NodeNext, tsx test runner, node:sqlite, DexScreener HTTP API + `gmgn-cli` (price marks, reusing the scout's proven patterns), Discord REST (same DM path as the scout).

**Spec:** `../robinhood-meme-scout/docs/TRADING-STRATEGY.md` v1.0 (2026-09-14), plus conversation decisions (revised per Aaron's plan review 2026-09-14): max 25 orders/day AND max $250 deployed/day AND max 40 open positions; moon-bag +1000% **triggered on the scout's reference price** (the ticket's `price_usd`, i.e. the basis the backtest validated) while **P&L uses fill price** as cost basis; paper fills at **live price at order time**; wallet/custody sections out of scope (nothing real to sweep); external executor = user-authored wrapper, contract documented, never authored here.

## Global Constraints

- Deps stay `tsx` + `typescript` + `@types/node`. Storage `node:sqlite` with `journal_mode=WAL`.
- Hard limits enforced in `limits.ts` regardless of ticket contents: max stake $100; entry ≤ 1% of pool liquidity; ≤ 25 entry orders per PT calendar day; ≤ $250 deployed per PT calendar day; ≤ 40 open positions at once; one position per address lifetime (no re-entry after close — matches scout's never-re-alert dedupe).
- Strategy params all live in `strategy.json`; nothing strategy-tunable is hardcoded.
- Executor seam is the only path to a fill. Builtin engine: fill at live price with price-impact `impact_pct = order_usd / liquidity_usd × 100` (buys fill higher, sells lower) and 0.3% fee per side.
- All timestamps ms epoch in db; PT used only for the daily-order-count boundary (reuse scout's `laParts` Intl approach).
- Failed sells: one retry with slippage escalated +2% (max 20%); then abandon tranche this cycle. Position unreachable (price feed dead ≥ 3 consecutive marks AND sell attempts failed): close as rug, −100% of remaining.
- Never log/print the GMGN key or Discord token.
- Commits scoped to `projects/robinhood-paper-trader/`; no push.

## File Structure

- `strategy.json` — all knobs (below)
- `src/config.ts` — typed loader for strategy.json + `.env` (GMGN key)
- `src/db.ts` — schema + accessors (orders, fills, positions, marks, meta)
- `src/executor.ts` — Order/Fill types, `builtin` engine, `external` adapter (spawn, stdin JSON in / stdout JSON out, timeout)
- `src/limits.ts` — ladder sizing + every hard cap; pure functions
- `src/prices.ts` — DexScreener batch primary / gmgn-cli fallback (adapted from scout's `dexscreener.ts` + `gmgn.ts`; copied, not imported — projects stay standalone)
- `src/engine.ts` — position lifecycle: open, mark, moon-bag, tranche schedule, rug handling; injectable clock/prices/executor
- `src/notify.ts` — Discord DM + jsonl event log (scout's alerts.ts pattern)
- `src/cli.ts` — `buy` (ticket on stdin), `sell`, `status`, `portfolio`, `run`, `contract`
- `docs/EXECUTOR-CONTRACT.md` — the wrapper contract (schemas, exit codes, timeout; no cast code)
- `com.apollo.paper-trader.plist` — launchd template (not auto-installed)
- `tests/*.test.ts` + `tests/fixtures/` (DexScreener payload captured live; stub external wrapper script that echoes canned fill JSON)

### strategy.json (initial)

```json
{
  "starting_capital_usd": 1000,
  "base_stake_usd": 10,
  "ladder_step_usd": 1000,
  "max_stake_usd": 100,
  "max_entry_lp_ratio": 0.01,
  "max_orders_per_day": 25,
  "max_daily_deployment_usd": 250,
  "max_open_positions": 40,
  "moonbag": { "trigger_pct": 1000, "sell_fraction": 0.25 },
  "exit": {
    "boundary_hours": 24,
    "oneshot_max_lp_ratio": 0.005,
    "tranche_schedule_hours": [23, 23.333, 23.667, 24],
    "tranche_max_lp_ratio": 0.02,
    "big_sell_usd": 10000
  },
  "slippage": { "default_pct": 5, "escalate_pct": 2, "max_pct": 20 },
  "fee_pct": 0.3,
  "mark_interval_seconds": 60,
  "executor": { "type": "builtin" },
  "discord": { "enabled": true }
}
```

`executor` alternative: `{ "type": "external", "command": "/path/to/wrapper", "timeout_ms": 30000 }`.

### Seam contract (also the content of docs/EXECUTOR-CONTRACT.md)

Order (stdin to wrapper, one JSON object):
```json
{
  "order_id": "o_1726300000_ab12", "side": "buy",
  "token_address": "0x…", "ticker": "X",
  "amount_usd": 10,                  // buys: spend this much
  "token_amount": null,              // sells: sell this many tokens (buys: null)
  "ref_price_usd": 0.00123,          // our current mark, for min-out math
  "max_slippage_pct": 5, "deadline_s": 1800
}
```
Fill (stdout from wrapper, one JSON object, exit 0):
```json
{
  "order_id": "o_1726300000_ab12", "status": "filled",
  "fill_price_usd": 0.00125, "token_amount": 8000, "usd_value": 10.0,
  "tx_ref": "optional", "error": null
}
```
`status: "failed"` + `error` for a failed swap; nonzero exit or timeout = failed. The tool treats wrapper stdout as data only.

## Ticket schema (Meme Scout → `trade-tool buy` stdin)

```json
{ "address": "0x…", "ticker": "GRASS", "name": "Touch Grass",
  "price_usd": 0.0063, "liquidity_usd": 351000, "alerted_at": "2026-09-14T18:00:00Z" }
```
`price_usd`/`liquidity_usd` are advisory; the tool re-fetches live values before sizing and gating (a poisoned ticket can at worst open one correctly-capped position).

---

### Task 1: Scaffold + config

**Files:** `package.json`, `tsconfig.json`, `strategy.json`, `.env` (GMGN key copied by Aaron, not committed), `.gitignore` (data/, .env), `src/config.ts`, `tests/config.test.ts`

**Interfaces — Produces:** `interface Strategy` (mirror of strategy.json above), `loadStrategy(path?)`, `loadEnv(path?)` (same parser as scout).

- [ ] Failing test: loadStrategy returns base_stake 10, tranche schedule length 4, executor.type 'builtin'; loadEnv parses KEY=VALUE
- [ ] Implement; `npm test` green; commit `feat(paper-trader): scaffold + typed strategy config`

### Task 2: Database

**Files:** `src/db.ts`, `tests/db.test.ts`

**Interfaces — Produces:**
- `openDb(file)` → DatabaseSync with WAL; tables:
  - `orders(id TEXT PK, ts, side, address, ticker, amount_usd, token_amount, slippage_pct, status pending|filled|failed, error, kind entry|moonbag|tranche|manual|rug)`
  - `fills(order_id PK, ts, fill_price_usd, token_amount, usd_value, fee_usd, source builtin|external)`
  - `positions(address PK, ticker, opened_ms, entry_price /* fill price: P&L cost basis */, ref_price /* scout ticket price: moon-bag trigger basis */, stake_usd, tokens_total, tokens_remaining, moonbag_done INT, status open|closed|rugged, closed_ms, realized_usd, exit_tranches_done INT)`
  - `marks(address, ts, price_usd, liquidity_usd)` (30-day retention, pruned by daemon)
  - `meta(key PK, value)` (realized capital cache, counters)
- Accessors: `insertOrder/insertFill/openPosition/updatePosition/closePosition/getOpenPositions/openPositionCount/ordersToday(dateStr)/deployedTodayUsd(dateStr)/hasPosition(address)/realizedCapital(db, strategy)` (= starting + Σ position realized_usd − Σ open stakes? **No** — realized capital = starting_capital + Σ realized_usd over ALL positions, used by ladder; document formula in code)

- [ ] Failing tests: open+close roundtrip (entry_price and ref_price stored independently); ordersToday and deployedTodayUsd count only same PT day; openPositionCount excludes closed/rugged; realizedCapital math (start 1000, one closed +90 → 1090); hasPosition true after open incl. closed (lifetime dedupe)
- [ ] Implement; green; commit `feat(paper-trader): trades db schema + accessors`

### Task 3: Limits + ladder (pure)

**Files:** `src/limits.ts`, `tests/limits.test.ts`

**Interfaces — Produces:** `stakeFor(realizedCapitalUsd, s: Strategy): number`; `checkEntry(args {address, liquidity_usd, ordersToday, deployedTodayUsd, openPositions, alreadyHasPosition, stakeUsd}, s): {ok: true} | {ok: false, reason: string}`; `sellPlan(args {tokensRemaining, price, liquidity_usd, ageHours}, s): {kind:'oneshot'|'tranche', tokenAmount, trancheIndex?} | null` (which sell, if any, is due now); `moonbagDue(position, markPrice, s): boolean`.

Rules encoded exactly from spec: stake = clamp(base × floor(cap/1000), base, max_stake); entry rejected if stake > 1% LP, daily count ≥ 25, daily deployment + stake > $250, open positions ≥ 40, or position exists; **moonbag when mark ≥ ref_price × 11** (scout basis — backtest-comparable trigger) and !moonbag_done → sell 25% of tokens_total; boundary exits per tranche schedule with 2%-LP per-order cap and oneshot path < 0.5% LP; any projected sell > $10k forces tranche path.

- [ ] Failing tests: ladder (999→10, 1000→10, 2000→20, 5000→50, 47000→100 cap); entry gates each reject reason incl. $250 daily-deployment boundary (240 deployed + $20 stake → reject) and 40-open-positions cap; moonbag trigger exactly at ref_price × 11 (and NOT at entry_price × 11 when fill slipped above ref); oneshot vs tranche selection at 0.5% LP; tranche size capped at 2% LP; $10k forces tranches
- [ ] Implement; green; commit `feat(paper-trader): ladder sizing + hard limit gates`

### Task 4: Executor seam

**Files:** `src/executor.ts`, `tests/executor.test.ts`, `tests/fixtures/stub-wrapper.sh` (test-only: reads stdin, echoes canned fill JSON)

**Interfaces — Produces:** `interface Order` / `interface Fill` (contract above); `builtinExecute(order, live: {price_usd, liquidity_usd}, s): Fill` — price impact + fee model per Global Constraints, fails if implied slippage > order.max_slippage_pct; `externalExecute(order, cfg): Promise<Fill>` — spawn command, write order JSON to stdin, parse stdout, timeout/nonzero-exit/bad-JSON → `{status:'failed'}`; `makeExecutor(s, priceLookup) → (order) => Promise<Fill>`.

- [ ] Failing tests: builtin buy fills above ref price by impact+fee and token_amount math checks; builtin sell fills below; slippage breach → failed; external stub roundtrip (order_id preserved, source recorded); timeout & garbage-stdout → failed, never throws
- [ ] Implement; green; commit `feat(paper-trader): executor seam — builtin sim engine + external adapter`

### Task 5: Price marks

**Files:** `src/prices.ts`, `tests/prices.test.ts`, `tests/fixtures/dexscreener-batch.json` (captured live during this task)

**Interfaces — Produces:** `fetchMarks(addresses, env, cfg): Promise<Map<addressLower, {price_usd, liquidity_usd}>>` — DexScreener `/tokens/v1/{chain}/{csv}` batch primary (adapt scout's `parseTokenBatch`), per-address `gmgn-cli token info` fallback capped at 5/cycle, misses omitted from map.

- [ ] Failing tests: fixture parse → map with lowercase keys; fallback invoked only for misses (injected fns); all-sources-down → empty map, no throw
- [ ] Implement; green; commit `feat(paper-trader): price marks with dexscreener→gmgn fallback`

### Task 6: Engine (lifecycle)

**Files:** `src/engine.ts`, `tests/engine.test.ts`

**Interfaces — Produces:** `class Engine { constructor({db, strategy, executor, fetchMarks, notify, now?}) ; openFromTicket(ticket): Promise<Result>; tick(): Promise<void> }`
- `openFromTicket`: re-fetch live price+LP → limits.checkEntry → executor buy → record order+fill → open position → notify. Reject path records order with status failed + reason.
- `tick()`: fetch marks for open positions → insert marks, prune >30d → per position: (1) rug check — no mark for ≥3 consecutive ticks: **courtesy sell** with `ref_price_usd` = last recorded mark and min-out implied by max slippage (catches a feed outage where the pool is actually fine); one retry escalated, then close as rugged with **realized = actual proceeds (normally $0) against the fill-price cost basis** — no synthetic valuation; (2) moonbagDue (mark ≥ position.ref_price × 11) → sell 25% via executor, mark moonbag_done, realized += proceeds; (3) sellPlan due (23h+ tranches or oneshot at boundary) → execute, increment tranches_done, close when tokens_remaining ≈ 0 or age ≥ 24h with final tranche done; (4) failed sells → escalate next tick per slippage config, abandon this cycle after retry.
- Realized P&L bookkeeping on every fill; `meta` counters updated.

- [ ] Failing tests (injected fake clock/marks/executor, in-memory db): full happy path buy→24h oneshot exit with P&L math checked to the cent against fill basis; moonbag fires at ref_price × 11 and sells exactly 25% once; tranche path when remaining ≥0.5% LP (4 tranches at right times, 2%-LP cap splits respected); rug path (marks vanish → courtesy sell at last mark, executor fails twice → position rugged, realized = proceeds $0); feed-outage-but-pool-fine path (courtesy sell FILLS → position closes with real proceeds, not rugged); daily count, daily $250, and 40-open caps each block an entry; duplicate ticket rejected
- [ ] Implement; green; commit `feat(paper-trader): position lifecycle engine`

### Task 7: Notify + CLI + daemon

**Files:** `src/notify.ts`, `src/cli.ts`, `tests/cli.test.ts`

**Interfaces — Produces:** notify: `sendDM(msg, {dryRun})` (scout's Discord path, same recipient), `logEvent(obj)` → `data/events.log`; CLI: `buy` (ticket stdin → Engine.openFromTicket; prints fill/reject JSON, exit code 0/1), `sell --address [--pct 100]` (manual, kind=manual), `status`/`portfolio` (positions table, realized capital, ladder stake, today's order count), `run [--dry-run]` (daemon: Engine.tick every mark_interval, heartbeat log line), `contract` (prints EXECUTOR-CONTRACT.md).

- [ ] Failing tests: `buy` with valid ticket on stdin opens position (builtin, dry-run notify) and prints fill JSON; bad ticket JSON → exit 1, nothing recorded; `status` reflects the position
- [ ] Implement; green; commit `feat(paper-trader): cli + daemon + discord notifications`

### Task 8: Docs, service, end-to-end

**Files:** `docs/EXECUTOR-CONTRACT.md`, `README.md`, `com.apollo.paper-trader.plist`

- [ ] Write EXECUTOR-CONTRACT.md: schemas verbatim from seam contract, invocation semantics (stdin/stdout/exit codes/timeout), field-by-field notes incl. how min-out derives from ref_price × (1 − max_slippage). No transaction code of any kind.
- [ ] README: what it is, the boundary statement, commands, config, how Meme Scout calls `buy`, how to switch executor to external.
- [ ] launchd plist template for `run` (not installed — Aaron's call, same as scout precedent).
- [ ] End-to-end verification (documented in README): `echo '<real recent alert ticket built from scout.db>' | tsx src/cli.ts buy` against builtin; daemon `run --dry-run` for ≥3 mark cycles; `status` shows sane marks; full `npm test` + `tsc --noEmit` green.
- [ ] Commit `docs(paper-trader): executor contract, README, launchd template`

## Explicitly Out of Scope

- Authoring or invoking any on-chain transaction (cast/anvil commands, calldata, approvals) — including inside docs and fixtures. The stub wrapper in tests echoes canned JSON only.
- Modifying Meme Scout (integration is Aaron's, per brief).
- Wallet custody/sweeps/rotation (§Wallet rules) — nothing real exists in paper mode.
- Any "flip to live" configuration path. Pointing the external command at real execution is a decision and act that stays entirely outside this codebase and outside my involvement.

## Self-Review

- Spec coverage: §1 sizing/caps→T3; §2 entries→T3/T6 (fill-at-live-price decision noted in header); §3 exits incl. moonbag/tranches/rug→T3/T6; §Execution-Architecture hard-limits-in-code→T3 (LLM never in loop at all here); instrumentation dollar-tracking hooks→db schema supports, daily report integration deferred (listed for a later scout-side task, not this build). ✓
- Types consistent: Order/Fill (T4) consumed by T6/T7; Strategy (T1) consumed everywhere. ✓
- No placeholders; every step has concrete expected behavior; schemas written out. ✓
