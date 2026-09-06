# Infrastructure Flywheel Scanner

## Overview

The Infrastructure Flywheel Scanner identifies utility projects on emerging chains that are building liquidity aggregation flywheels. It runs alongside the existing meme coin watcher but targets different opportunities.

## How It Works

The scanner:
1. Queries GMGN.ai for Robinhood Chain tokens via `hot-searches` endpoint
2. Filters by infrastructure flywheel criteria
3. Sends Discord alerts to Aaron for matches
4. Logs results to `infra-scanner.log`

## Detection Criteria

### Primary Filters
| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| Chain Age | < 12 months | New ecosystem, early infrastructure |
| Market Cap | $5M - $100M | Room to grow, not micro-cap noise |
| Trading Activity | 10K+ swaps | Liquidity aggregation signal |

### Risk Flags (Reported but not filtered)
- High PSL (protocol-owned liquidity) > 10% of top 10 holders
- Top 10 concentration > 40% of supply
- Bundle detection > 5 wallets

## Usage

### Start the scanner
```bash
cd /Users/apollo/.openclaw/workspace/channels/qwen
node hood-infra.mjs watch
```

### Run once and exit
```bash
node hood-infra.mjs run
```

### Test mode (sample data)
```bash
node hood-infra.mjs --test
```

### Stop the scanner
```bash
pkill -f "hood-infra.mjs watch"
```

## Current Status

✅ **Running in background** (PID: see `ps aux | grep hood-infra`)
- Polling interval: 10 minutes (to minimize rate limit pressure)
- Discord alerts: Enabled (sends to Aaron's Discord DM)
- Logging: `/Users/apollo/.openclaw/workspace/channels/qwen/infra-scanner.log`

## Differences from Meme Coin Watcher

| Aspect | Meme Coin Watcher | Infrastructure Flywheel |
|--------|-------------------|------------------------|
| Target | Viral potential | Economic engine |
| Metrics | Social, volume spikes | PSL, trading activity, trends |
| Timeframe | Short-term momentum | Medium-term fundamentals |
| Risk Profile | High volatility | Fundamentals + ecosystem risk |
| Polling | 30 seconds | 10 minutes |
| Emoji | 🚀 | 🏗️ |

## Files

- `hood-infra.mjs` - Main scanner script (~250 lines)
- `infra-scanner.log` - JSON log of scan results
- `infra-scanner.out` - Stdout/stderr output

## GMGN API Key

Uses the same API key as the meme coin watcher from:
`/Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/.env`

## Rate Limiting

The GMGN API has rate limits. The 10-minute polling interval is designed to:
- Minimize rate limit pressure
- Allow both scanners to run simultaneously
- Reduce false positives by catching trends over time

## Test Results

First test scan found 22 matches out of 100 coins scanned:
- $ZZZ, $MEME, $SHROOM, $Ponsan, $par, $SPCX, $SPY, $NVDA, and more
- Most had high PSL (>10% of top 10 holders)
- Trading activity ranged from 6K to 244K swaps

## Maintenance

### Check if running
```bash
ps aux | grep hood-infra
```

### View latest results
```bash
tail -50 /Users/apollo/.openclaw/workspace/channels/qwen/infra-scanner.log
```

### View Discord alerts
Check Aaron's Discord DM for messages from Qwen
