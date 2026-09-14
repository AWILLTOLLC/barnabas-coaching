# Full-History Backtest: Composite Trade Plan (2026-09-14)

Status: complete (re-run by LittleJohn after the subagent's query produced empty results)
Data: data/scout.db copy /tmp/bt.db. 8,603 coins with clean 24h outcome data + sanity floors (entry price > 1e-10, MC/liquidity > $1k where present). Window: Sept 6–14, 2026 (8.5 days).
Plan: $10 stake, 25% off at +1000% trigger, hold remainder to 24h boundary, LP-gated exit (one-shot if pos<0.5% of pool else 4 tranches 23–24h), no stop, dead outcome ≤24h = rug (−100%), 0.3% fee, slippage = clamp(order/LP, 0.3%–50%), per-coin returns capped at +5000% for aggregates (dust-price artifacts untradeable at size).

## Results by cohort

| Cohort | n | Win rate | Median 24h ret | Monsters (≥10x) | Rugs | Plan PnL | Avg PnL/coin |
|---|---|---|---|---|---|---|---|
| **Alerted** | 62 | **66.1%** | **+81%** | **16 (25.8%)** | 1 | **+$10,510** | +$169.52 |
| Passed gates, not alerted | 4 | 25.0% | −25% | 0 | 0 | +$16 | +$3.98 |
| Rejected | 8,537 | 4.6% | −76% | 13 (0.15%) | 669 | **−$47,613** | −$5.58 |

Total PnL if every coin were taken: −$37,087 (loses). Alerted-only: +$10,510 (wins).

## Verdict

1. **The gates are the alpha.** Alerted coins: 66% win rate, +81% median, 26% monster rate. Rejected: 4.6% win rate, −76% median, 0.15% monsters, 669 rugs. Taking everything loses ~$37k of hypothetical $10-stake PnL; taking only alerts wins. Gate quality is real, not luck — though one 8.5-day window.
2. **Unfiltered meme-coin buying is a slow bleed** (−$5.58/coin average; 8% of rejected coins rug before 24h).
3. **The monster asymmetry is real but fragile:** $MIRAI (+$11,897 pre-cap) was a REJECTED coin — the biggest raw winner escaped the gates. Even so, rejected-cohort total stays deeply negative. Missing one monster does not justify taking 8,537 dregs.
4. **Passed-but-not-alerted cohort is tiny (n=4)** — too small to judge the near-miss band.

## Caveats

- Checkpoint prices (1h/6h/24h), not tick data; interpolation between checkpoints.
- Dead = unfetchable (rug/delist proxy), treated as −100% at first dead horizon ≤24h.
- Dust-price artifacts (e.g., $SFM, $MOG showing +760M%) exist in raw rejected data; capped at +5000% per coin for aggregates. Their true tradeable value is ~0 (no liquidity at entry price).
- $10,510 alerted PnL includes the +5000% cap on CATGPT ($500 vs $4,490 uncapped).

## Follow-up implemented today

- `price_ticks` table + per-poll capture added to monitor (src/db.ts, src/monitor.ts) — needs monitor restart to activate. Future sims can use real 15-min paths.
