# Backtest Sims

Scenario scripts over the alerted cohort (Sept 6-14 2026 window). Each answers
one strategy question asked during plan design. Run from this directory:

    npx tsx sims/sim16.ts

Requires a read-only DB copy at /tmp/bt.db (copy of data/scout.db; external
sqlite can't open DBs under the OpenClaw state dir):

    cp data/scout.db /tmp/bt.db

Shared assumptions (copy-pasted, watch for drift): 0.3% fee, slippage =
clamp(order/LP, 0.3%-50%), prices interpolated linearly between outcome
checkpoints (1h/6h/24h; outcomes also carry 72h/168h), dead outcome <=
boundary = rug (-100%), results reported with winners capped at +5000%
where noted (dust-price artifacts).

| Script | Question | Verdict |
|---|---|---|
| sim11.ts | Full-history backtest: do the gates have alpha? | Yes: alerted 66% win/+$10.5k vs rejected 4.6%/-$47k |
| sim12.ts | Scaling ladder ($10 base, +$10/$1k portfolio) vs flat | Ladder: $1k->$257k uncapped / $42k capped, peak stake $420 |
| sim13.ts | $15 base ladder vs $10 | $15 ladder 31.5x, maxDD 31.5% vs 21% |
| sim14.ts | Regime-conditioned sizing (hot multiplier) | Inconclusive: 58/62 alerts in neutral, n=1 hot |
| sim15.ts | 10% moon bag on monsters / all >=1000% | -EV both: 3 of 6 monsters dead by 72h. REJECTED |
| sim16.ts | Exit boundary 6h-24h | 24h dominates monotonically. REJECTED alternatives |
