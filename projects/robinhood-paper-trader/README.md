# Robinhood Paper Trader

Standalone paper-trade execution layer for Meme Scout signals. Meme Scout fires
`buy` with an alert ticket; this tool sizes the position, enforces the strategy's
hard limits, simulates the fill, and runs the full lifecycle (moon-bag trim, 24h
LP-gated exit, rug handling) with Discord notifications and P&L tracking.

**Simulation only.** This codebase never builds or sends an on-chain
transaction. Its default `builtin` executor is a pure price simulator. Real
execution lives entirely behind the `external` executor seam, in a wrapper you
author and operate (see `docs/EXECUTOR-CONTRACT.md`). Pointing that wrapper at a
real chain is a decision and an act outside this project.

Implements `../robinhood-meme-scout/docs/TRADING-STRATEGY.md` v1.0.

## Commands

```bash
echo '{"address":"0x…","ticker":"GRASS","price_usd":0.0063,"liquidity_usd":351000}' | tsx src/cli.ts buy
tsx src/cli.ts sell --address 0x… --pct 100   # manual override
tsx src/cli.ts status                          # capital, ladder stake, open positions, P&L
tsx src/cli.ts run [--dry-run]                 # daemon: mark positions + fire strategy exits
tsx src/cli.ts contract                        # print the executor wrapper contract
npm test
```

Meme Scout integration (handled outside this repo): on alert, pipe a ticket
JSON to `tsx src/cli.ts buy`. Ticket = `{address, ticker, price_usd,
liquidity_usd?, alerted_at?}`. `price_usd` is the scout's reference price and
becomes the **moon-bag trigger basis**; the tool re-fetches the live price for
sizing, gating, and the actual fill.

## Strategy knobs (`strategy.json`)

All limits live here and are enforced in code regardless of ticket contents:
$10 base stake, ladder +$10 per $1,000 realized capital, $100 max stake, entry
≤1% of pool liquidity, ≤25 entries/day, ≤$250 deployed/day, ≤40 open positions,
moon-bag +1000% (of scout ref price) → sell 25%, hard 24h exit, no stop-losses.

## Executor

`strategy.json → executor`:
- `{ "type": "builtin" }` — pure simulation (default): fills at live price ± a
  depth-based impact, 0.3% fee per side. No chain, no network beyond price feeds.
- `{ "type": "external", "command": "/path/to/wrapper", "timeout_ms": 30000 }` —
  spawns your wrapper (stdin order JSON → stdout fill JSON). See
  `docs/EXECUTOR-CONTRACT.md`. For anvil paper trading, your wrapper wraps the
  `cast` commands against a local fork.

## Run as a service (launchd)

`com.apollo.paper-trader.plist` template runs `run`. Not auto-installed — your
call, same convention as the scout:

```bash
cp com.apollo.paper-trader.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.apollo.paper-trader.plist
```

## Data

`data/trades.db` (SQLite, WAL): `orders`, `fills`, `positions`, `marks`.
`data/events.log` is a JSONL activity log. Marks retained 30 days.

## Layout

- `src/config.ts` — strategy.json + .env loader
- `src/db.ts` — schema + accessors
- `src/limits.ts` — ladder sizing + hard-limit gates + sell planner (pure)
- `src/executor.ts` — Order/Fill seam: builtin sim engine + external adapter
- `src/prices.ts` — DexScreener batch → gmgn-cli fallback marks
- `src/engine.ts` — position lifecycle (entry, marks, moon-bag, tranches, rug)
- `src/notify.ts` — Discord DM + event log
- `src/cli.ts` — buy/sell/status/run/contract
