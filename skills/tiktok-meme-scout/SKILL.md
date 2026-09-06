---
name: "tiktok-meme-scout"
description: "Scrape TikTok trends, coin mentions, and viral patterns via private API for meme coin research."
---

# tiktok-meme-scout

**Trigger:** Evaluating meme coins, tracking trends, or researching community signals on TikTok.

**Produces:** Trending hashtags, viral video data, coin mention velocity, community health metrics.

## Procedure

1. **Register a device identity.** `POST /api/v1/device/register` with device brand/type/os/region/language. Cache the returned `device_id` and `iid`; rotate every 30 days. Completion: IDs cached and reusable.
2. **Query endpoints** (anonymous read-only):
   - Trending: `GET /aweme/v1/trending/list?count=50&region=US`
   - Coin search: `GET /aweme/v1/search/general/?keyword=$TICKER&count=30`
   - Hashtag videos: `GET /aweme/v1/hashtag/video/?hashtag_id=$ID&count=50`
   - Creator videos: `GET /aweme/v1/aweme/post/?user_id=$ID&count=20`
3. **Sign each request.** Build the query string by hand in exact parameter order (do not use `url.encode()`), then set five headers: `x-khronos` (timestamp), `x-ladon` (Speck-128/256, deterministic per device), `x-argus`, `x-gorgon`, `x-ss-req-ticket`. Verify determinism of signatures before batching.
4. **Respect limits.** Max 100 requests/minute; add a 1s delay between calls. Version gating: endpoints differ per `version_code`; re-verify signing keys monthly.
5. **Parse and score.** Extract views, likes, comments, posting time (velocity), creator followers, and hashtag reach. Score virality: `(views / 1e6) * (likes / views) * (comments / views) * creator_weight`.
6. **Output** one structured JSON object with `trending`, `coin_mentions` (ticker, mention_count_24h, velocity_change, top_creators, avg_engagement), and `community_health` blocks.

## Troubleshooting

- **Silent empty 200:** check response body length, not just HTTP status. In order: re-register device credentials; rebuild query string in exact order; try another regional host (SG/US/EU/JP); use OpenSSL with Android cert chain for TLS fingerprint mismatch.
- **Rate limiting:** back off to the 100 req/min cap.
- **Auth boundary:** anonymous only — no login, no DMs, no private videos.

## Notes

- Region-aware: US, SG, EU, JP trending feeds differ; pick region per query.
- Cache device IDs locally (SQLite works) for velocity tracking across runs.
