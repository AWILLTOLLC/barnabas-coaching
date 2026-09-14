# Build Plan: Dollar-weighted portfolio tracking ("percent of dollars")

Date: 2026-09-14
Status: approved (owner go 2026-09-14)
Stake model: $100 per coin (equal-dollar). Median stats retained. Bands unchanged.

## Problem

Outcome tracking reports median/best/worst of per-coin % returns. Scale-blind: a $2M coin doing +40% and a $15M coin doing −50% can show the same median. No notion of dollars won or lost.

## Math

For each band × horizon cohort (rets already fetched by existing SQL):

```
ret_i      = (exit − entry)/entry × 100            (existing, unchanged)
pnl_$      = Σ (100 × ret_i / 100)  = Σ ret_i     (dollars, $100 stakes)
port_ret_% = pnl_$ / (100 × n) × 100              (= mean of rets under equal stakes)
```

`pnl_$` makes scale visible; `port_ret_%` is the portfolio return; median stays for the typical-coin view.

### Stage 1 — Compute dollar-weighted stats in report.ts

Action: python3 /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/dwr/stage1.py

Verify: cd /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout && grep -q "pnl_usd" src/report.ts

### Stage 2 — Regime portfolio return

Action: python3 /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/dwr/stage2.py

Verify: cd /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout && grep -q "portfolioReturnForRegime" src/report.ts && npx tsc --noEmit

### Stage 3 — Display + Ollama prompt framing

Action: python3 /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/dwr/stage3.py

Manual verify: run the report once against live scout.db and eyeball that the new $100/coin figures reconcile with the median rows for the same cohort, and the band line reads cleanly in Telegram-format output.

Verify: cd /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout && grep -q '\$100/coin' src/report.ts

### Stage 4 — Tests + full verify

Action: cd /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout && npx tsc --noEmit

Manual verify: confirm a synthetic cohort where one +900% coin among nine −10% coins shows median −10% but port ≈ +9%, proving median and dollar-weighted numbers diverge as intended.

Verify: cd /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout && npx tsc --noEmit

## Explicitly out of scope

- No removal of median/best/worst. No MC-weighting. No band/gate/capture/schema changes. Legacy/ untouched.

## Risk

Minimal: additive reporting math over stored data. Worst case is a display string; no pipeline behavior changes.
