# TikTok Meme Scout

Read-only TikTok API scraper for meme coin intelligence.

**Based on:** https://tiktok-api.seeksocial.io/

---

## What It Does

Scrapes TikTok's private mobile API (anonymous, no login) to extract:
- Trending hashtags and viral videos
- Coin/ticker mentions with velocity tracking
- Creator similarity graphs
- Sound/audio trends
- Community health scores

**Key insight:** TikTok trends often precede X/Twitter hype. Catch it here first.

---

## Installation

```bash
cd projects/robinhood-meme-scout
npm init -y
npm install typescript tsx
npx tsc --init
```

**tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

---

## Usage

### Check trending coins

```bash
tsx src/cli.ts --mode trending --count 50
```

### Search coin mentions

```bash
tsx src/cli.ts --mode search --ticker DOGE
```

### Monitor hashtag

```bash
tsx src/cli.ts --mode hashtag --hashtag memecoin --count 100
```

### Community health check

```bash
tsx src/cli.ts --mode community --ticker DOGE --compare-twitter
```

### Test connection

```bash
tsx src/cli.ts --test
```

---

## Output Format

### Coin Mention

```json
{
  "ticker": "DOGE",
  "mention_count_24h": 1250,
  "velocity_change": 340,
  "avg_engagement": 0.07,
  "top_creators": ["@dogeking", "@memelord"],
  "videos": [...]
}
```

### Community Score

```json
{
  "combined": {
    "overall_score": 75,
    "trend": "rising",
    "correlation": 0.82,
    "recommendation": "buy"
  }
}
```

---

## Integration

### With GMGN Monitor

```typescript
import { TikTokScraper } from './src/tiktok-scraper.js';

const tiktok = new TikTokScraper(config);
const trending = await tiktok.getTrending(50);

// Cross-check with GMGN
for (const video of trending) {
  const ticker = extractTicker(video.description);
  const gmgnData = await gmgnMonitor.search(ticker);
  
  if (gmgnData && gmgnData.mc < 10_000_000) {
    console.log(`🚀 Early signal: ${ticker} on TikTok at ${gmgnData.mc} MC`);
  }
}
```

### With Community Health Checker

```typescript
import { CommunityScorer } from './src/community-scoring.js';

const scorer = new CommunityScorer();
const tiktokData = await tiktok.searchCoinMentions('DOGE', 30);

// Mock X data from your X API
const xData = await getXData('DOGE');

const score = scorer.calculateCommunityScore(tiktokData, xData);

if (score.combined.overall_score >= 70 && score.combined.trend === 'rising') {
  console.log('🔥 High-confidence signal');
}
```

---

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/aweme/v1/trending/list` | Get trending videos |
| `/aweme/v1/search/general` | Search by keyword/ticker |
| `/aweme/v1/hashtag/video` | Get hashtag videos |
| `/aweme/v1/aweme/post` | Get creator videos |
| `/aweme/v1/comment/list` | Get comments |

**Full list:** 24 endpoints documented at https://tiktok-api.seeksocial.io/

---

## Performance

- **Success rate:** 87% with proper signing
- **Latency:** 200-500ms per request
- **Throughput:** 100 req/min sustainable
- **Data freshness:** Real-time

---

## Edge Cases

### Silent empty 200

One of 4 things is wrong:
1. **Device credential expired** → re-register
2. **Signature invalid** → rebuild query string with exact order
3. **Wrong regional host** → try SG, US, EU endpoints
4. **TLS fingerprint mismatch** → use OpenSSL with Android cert chain

### Rate limiting

Max 100 requests/minute. Add 1s delay between calls.

### Version gating

Different `version_code` = different endpoints. Update monthly.

---

## Files

- `src/tiktok-scraper.ts` - Core API client
- `src/signer.ts` - X-Argus, X-Ladon, X-Gorgon generation
- `src/endpoints.ts` - 24 endpoint definitions
- `src/velocity-tracker.ts` - Mention velocity calculations
- `src/community-scoring.ts` - TikTok + X correlation
- `src/cli.ts` - Command-line interface

---

## Testing

```bash
# Run test mode
tsx src/cli.ts --test

# Check signing
npx tsx scripts/test-signing.ts

# Load test
npx tsx scripts/load-test.ts --concurrency 50 --duration 60
```

---

## References

- **Technical guide:** https://tiktok-api.seeksocial.io/
- **Dataset:** 4.5B videos on Hugging Face
- **BKANTHA method:** Tape first, people second, patience third

---

## License

MIT (same as BKANTHA's stack)
