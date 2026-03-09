# BTC/USDT Ichimoku Cloud Backtest

## Task
Build and run a full backtest of the traditional Ichimoku Cloud strategy on BTC/USDT 15-minute candles. Two parameter sets side by side.

## Environment Setup
```bash
pip install vectorbt pandas pandas-ta requests pyarrow
```

---

## Step 1: Pull Historical Data

Source: Binance public API (no key needed)
- Endpoint: `https://api.binance.com/api/v3/klines`
- Symbol: `BTCUSDT`, interval: `15m`
- Date range: 2020-01-01 to 2024-12-31
- Binance returns max 1000 candles per call — paginate in a loop
- Columns: open_time, open, high, low, close, volume (all others can be dropped)
- Save to `btc_15m_2020_2024.parquet` so you don't re-fetch on re-runs

---

## Step 2: Ichimoku Calculations

Run for **both** parameter sets:

| Param | Standard | Crypto-Adjusted |
|-------|----------|-----------------|
| Tenkan | 9 | 20 |
| Kijun | 26 | 60 |
| Senkou B | 52 | 120 |
| Displacement | 26 | 60 |

Formulas:
- **Tenkan-sen** = (highest_high + lowest_low) / 2 over Tenkan periods
- **Kijun-sen** = (highest_high + lowest_low) / 2 over Kijun periods
- **Senkou Span A** = (Tenkan + Kijun) / 2 — shifted forward by displacement
- **Senkou Span B** = (highest_high + lowest_low) / 2 over Senkou B periods — shifted forward by displacement
- **Chikou Span** = Close — shifted backward by displacement (i.e., `close.shift(displacement)` for comparison)

---

## Step 3: Signal Logic

### Long Entry (ALL four conditions must be true on the same candle):
1. `close > max(senkou_a, senkou_b)` — price above cloud
2. Tenkan crosses above Kijun on this candle (was below last candle)
3. `close[i] > close[i - displacement]` — chikou above past price
4. `future_senkou_a[i] > future_senkou_b[i]` — cloud ahead is bullish (use unshifted values displaced forward)

### Short Entry (ALL four conditions must be true):
1. `close < min(senkou_a, senkou_b)` — price below cloud
2. Tenkan crosses below Kijun on this candle (was above last candle)
3. `close[i] < close[i - displacement]` — chikou below past price
4. `future_senkou_a[i] < future_senkou_b[i]` — cloud ahead is bearish

### Exit:
- Long exits when a Short entry fires (and vice versa)
- No stop loss, no take profit — pure signal-based

---

## Step 4: Backtest Parameters
- Starting capital: $10,000
- Fees: 0.1% per trade (per side, i.e. 0.2% round trip)
- Entry/exit at close price of signal candle
- Long + Short (not long-only)
- Use vectorbt (`vbt.Portfolio`) if possible; manual loop fallback if needed

---

## Step 5: Output

Print this for **each** parameter set:

```
=== ICHIMOKU BACKTEST: BTC/USDT 15m (Standard 9/26/52) ===
Period: 2020-01-01 to 2024-12-31
Total trades: X
Win rate: X%
Total return: X%
Annualized return: X%
Max drawdown: X%
Sharpe ratio: X
Profit factor: X
Avg trade duration: X hours
Best trade: +X%
Worst trade: -X%
Buy & Hold return (same period): X%
```

Also save full results to `ichimoku_15m_results.json` with both param sets.

---

## Notes
- Watch NaN alignment carefully — Senkou spans are shifted, Chikou comparisons need correct indexing
- The "future cloud" condition uses the cloud as plotted on the chart (shifted forward), so at index `i` you're checking Senkou values that were calculated at `i - displacement`
- Total candles: ~175,000 rows — should run fast with vectorbt
