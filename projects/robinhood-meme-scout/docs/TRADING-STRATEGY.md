# Meme Scout Trading Strategy — v1.0 (2026-09-14)

Status: APPROVED by Aaron (2026-09-14). Test portfolio only.
Backed by: 8.5 days of live tracking (Sept 6–14, 2026), 15,195 coins tracked, 62 alerted / 8,603 with clean outcome data. Sim details in `docs/plans/2026-09-14-dollar-weighted-returns.md` and `docs/plans/2026-09-14-full-history-backtest.md`.

## Thesis

Robinhood Chain memecoins are a fat-right-tail market: most coins die, a few go 10x–450x. The scout's gates are the alpha — they select a cohort that wins 66% of the time with 26% monster frequency, vs 4.6% / 0.15% for everything else. The strategy's job is to (a) take every gated signal, (b) survive the losers via position sizing, (c) hold winners long enough for the tail to pay, (d) never let one position or one bad day threaten the portfolio.

## Core Rules

### 1. Sizing — the scaling ladder
- Start: **$10 per position** on $1,000 working capital.
- Scale: stake = **$10 × floor(realized portfolio ÷ $1,000)**, i.e. +$10 of stake per +$1,000 of portfolio value. At $2,000 → $20 stakes. At $5,000 → $50 stakes.
- **Hard caps (code-enforced, non-negotiable):**
  - Max stake: **$100** until 15-min price-tick data validates larger sizes (raise only by explicit owner decision).
  - Never open a position larger than **1% of the pool's liquidity** (buy-side LP gate).
- Rationale: flat-small sizing fixed every blow-up scenario simulated. The ladder lets winners compound. The caps exist because microcap pools cannot absorb large entries/exits, and because dynamic sizing in sim compounded one coin's luck ($1,000 → $257k uncapped vs $42k with a +5000% cap).

### 2. Entries
- Buy every coin that passes the scout gates and is flagged for alert. No discretionary skips — the 66% win rate is a cohort property; you can't know in advance which signal is the monster.
- Entry price basis: first-seen price (`price_at_eval`).

### 3. Exits
- **Moon-bag trigger:** when a position crosses **+1000%**, immediately sell **25%** of the position. Locks the stake; leaves 75% running. House money.
- **Hard time boundary: everything exits at 24h**, regardless of profit. No exceptions. The 24h boundary is the stop — stops before it only converted −90% rugs into −50% stops and sold winners mid-climb.
- **Exit mechanics, LP-gated:**
  - Remaining position < 0.5% of pool liquidity → one-shot market dump. (At $10–$100 stakes this is virtually always true; slippage ≤ ~0.5%.)
  - ≥ 0.5% of pool liquidity → scale out: 4 tranches over the final hour (23h/23.33h/23.66h/24h), tranche size also capped at 2% of pool depth per order.
  - Any single sell projected > $10,000 → mandatory multi-tranche scale-out, min 5 minutes between orders, max-slippage 5% with retry-and-escalate.
- **No stop-losses.** Simulated cost, zero benefit at these sizes.
- **Rug contingency:** if a position dies before any exit, it's a −100%. Priced in: ~1.6% of alerted coins rug inside 24h. Never chase a revert loop; one retry with escalated tolerance, then abandon.

### 4. Expected performance (from backtests, 8.5-day window)
- Alerted cohort, flat $10: $1,000 → ~$11,661; maxDD 2.6%; 41/62 winners.
- Alerted cohort, scaling ladder: $1,000 → $42,454 (winners capped +5000%) / $257,845 (uncapped — treat as fantasy, not forecast).
- Stress tests passed: all winners capped at +100% (still positive), dead-coins-as-rugs (still ~9x), no-stop vs 50%-stop (no-stop wins).

## Wallet & Custody Rules

- **Hot/cold split:** hot wallet holds working capital only. **Whenever the hot wallet exceeds $3,000, sweep everything above $1,500 to cold storage.** (Aaron's $15k/$5k variant approved as acceptable; tighter sweep preferred — fewer exposure-days, hides realized profit from chain watchers.)
- Sweeps are one-way. Cold storage is not trading capital. Re-funding the hot wallet is a manual, deliberate decision.
- **Copy-trader defense:** at $10 stakes, tracking is not economic. Once stakes pass ~$100, rotate weekly across fresh wallets so no address builds a copyable history. Cold sweeps do most of the work by hiding bankroll and realized P&L.

## Execution Architecture (security)

- **LLM advises, code executes.** The thesis/scoring model never holds keys, never signs, never initiates transfers. An injected prompt can at worst poison a score, never a swap.
- All ingested external content (token metadata, socials, creator history) is treated as hostile. No instruction in scraped text may change trade behavior.
- Hard limits live in code, not in prompts: max stake, max daily deployment, max position/LP ratio, 24h boundary.
- Anomaly alert: if LLM recommendations diverge from mechanical gate behavior, alert the owner; do not auto-act.
- Swap params: max-slippage 5% default (retry with +2% escalation, max 20%, then abandon tranche for this cycle); fees: **0.3% DEX fee on graduated V4 pools, but Bags-launchpad tokens charge 2% on the ETH/WETH leg** (verified live 2026-09-14) — sim P&L for launchpad-phase tokens must use 2%.

## Instrumentation (in place / pending)

- ✅ Dollar-weighted tracking in daily reports ($100/coin PnL + portfolio return alongside medians).
- ✅ `price_ticks` table: per-poll price + liquidity capture, 30-day retention. **Needs monitor restart to activate.**
- ⬜ Run monitor 2 weeks with ticks live, then re-run all exit sims on real 15-min paths (replace checkpoint interpolation).
- ⬜ Re-evaluate: gate thresholds, monster frequency stability across regimes (hot/cold), stake ceiling raise.
- ⬜ If stakes ever exceed $100: revisit scale-out strategy for large sells (the +$10k sell list from the dynamic-sizing sim is the trigger set).

## Known Limitations of the Evidence

- One 8.5-day window, one regime (mostly neutral). Monster frequency (26% of alerts ≥10x) is almost certainly window-flattered.
- Checkpoint prices (1h/6h/24h), linear interpolation between them; real intra-hour paths are violent.
- Dead outcomes are a rug/delist proxy, not proof of zero.
- Dust-price artifacts in full-universe data (e.g., $SFM) — aggregates capped at +5000%/coin where noted.
