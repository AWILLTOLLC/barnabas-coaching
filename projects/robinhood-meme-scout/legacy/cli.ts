#!/usr/bin/env node

/**
 * TikTok Meme Scout CLI
 * Read-only scraping for meme coin intelligence
 */

import { TikTokScraper, Endpoints } from './tiktok-scraper.js';
import { CommunityScorer } from './community-scoring.js';
import { TikTokConfig } from './tiktok-scraper.js';
import { GMGNMonitor } from './gmgn-monitor.js';

interface CliArgs {
  mode?: 'trending' | 'search' | 'hashtag' | 'creator' | 'community' | 'gmgn';
  ticker?: string;
  hashtag?: string;
  user_id?: string;
  count?: number;
  compareTwitter?: boolean;
  test?: boolean;
}

async function main() {
  const args = parseArgs();

  // Initialize scraper
  const config: TikTokConfig = {
    device_id: '7680616891110524437', // Cache this in production
    iid: '7680617333853718293',
    region: 'US',
    version_code: '320820',
    aid: 473824,
  };

  const scraper = new TikTokScraper(config);
  const scorer = new CommunityScorer();

  // Execute mode
  // Handle --test as standalone flag
  if (args.test) {
    await runTest(scraper);
    return;
  }

  switch (args.mode) {
    case 'trending':
      await runTrending(scraper, args.count || 50);
      break;

    case 'search':
      if (!args.ticker) {
        console.error('Error: --ticker required for search mode');
        process.exit(1);
      }
      await runSearch(scraper, args.ticker, args.count || 30);
      break;

    case 'hashtag':
      if (!args.hashtag) {
        console.error('Error: --hashtag required for hashtag mode');
        process.exit(1);
      }
      await runHashtag(scraper, args.hashtag, args.count || 50);
      break;

    case 'creator':
      if (!args.user_id) {
        console.error('Error: --user_id required for creator mode');
        process.exit(1);
      }
      await runCreator(scraper, args.user_id, args.count || 20);
      break;

    case 'community':
      if (!args.ticker) {
        console.error('Error: --ticker required for community mode');
        process.exit(1);
      }
      await runCommunity(scraper, args.ticker, args.compareTwitter || false);
      break;

    case 'gmgn':
      // Ticker is optional - defaults to watching all coins
      await runGMGNMonitor(args.ticker);
      break;

    case 'test':
      await runTest(scraper);
      break;

    default:
      console.log('TikTok Meme Scout + GMGN Monitor');
      console.log('');
      console.log('Usage:');
      console.log('  tiktok-meme-scout --mode trending [--count 50]');
      console.log('  tiktok-meme-scout --mode search --ticker DOGE');
      console.log('  tiktok-meme-scout --mode hashtag --hashtag memecoin');
      console.log('  tiktok-meme-scout --mode creator --user_id 123456');
      console.log('  tiktok-meme-scout --mode community --ticker DOGE --compare-twitter');
      console.log('  tiktok-meme-scout --mode gmgn --ticker DOGE');
      console.log('  tiktok-meme-scout --test');
      break;
  }
}

/**
 * Run trending videos
 */
async function runTrending(scraper: TikTokScraper, count: number) {
  console.log('🔥 Fetching trending videos...\n');

  const videos = await scraper.getTrending(count);

  console.log(`Found ${videos.length} trending videos:\n`);

  for (const video of videos.slice(0, 10)) {
    console.log(`Video: ${video.video_id}`);
    console.log(`  Description: ${video.description.substring(0, 80)}...`);
    console.log(`  Views: ${video.views.toLocaleString()} | Likes: ${video.likes.toLocaleString()}`);
    console.log(`  Virality Score: ${(video.virality_score * 100).toFixed(1)}%`);
    console.log(`  Posted: ${new Date(video.posted_at).toLocaleString()}`);
    console.log(`  Hashtags: ${video.hashtags.join(', ') || 'none'}`);
    console.log('');
  }
}

/**
 * Run coin mention search
 */
async function runSearch(scraper: TikTokScraper, ticker: string, count: number) {
  console.log(`🔍 Searching for $${ticker} mentions...\n`);

  const result = await scraper.searchCoinMentions(ticker, count);

  console.log(`Found ${result.mention_count_24h} mentions in last 24h\n`);
  console.log(`Velocity Change: ${result.velocity_change > 0 ? '+' : ''}${result.velocity_change.toFixed(1)}%`);
  console.log(`Avg Engagement: ${(result.avg_engagement * 100).toFixed(2)}%`);
  console.log(`Top Creators: ${result.top_creators.slice(0, 5).join(', ') || 'none'}`);
  console.log('\nTop Videos:');

  for (const video of result.videos.slice(0, 5)) {
    console.log(`  - ${video.description.substring(0, 60)}...`);
    console.log(`    Views: ${video.views.toLocaleString()} | Virality: ${(video.virality_score * 100).toFixed(1)}%`);
  }
}

/**
 * Run hashtag query
 */
async function runHashtag(scraper: TikTokScraper, hashtag: string, count: number) {
  console.log(`📊 Fetching #${hashtag} videos...\n`);

  const videos = await scraper.getHashtagVideos(hashtag, count);

  console.log(`Found ${videos.length} videos with #${hashtag}\n`);

  const sorted = [...videos].sort((a, b) => b.virality_score - a.virality_score);

  for (const video of sorted.slice(0, 10)) {
    console.log(`Video: ${video.video_id}`);
    console.log(`  Views: ${video.views.toLocaleString()} | Likes: ${video.likes.toLocaleString()}`);
    console.log(`  Virality Score: ${(video.virality_score * 100).toFixed(1)}%`);
    console.log(`  Creator Followers: ${video.creator_followers.toLocaleString()}`);
    console.log('');
  }
}

/**
 * Run creator query
 */
async function runCreator(scraper: TikTokScraper, userId: string, count: number) {
  console.log(`👤 Fetching creator ${userId} videos...\n`);

  const videos = await scraper.getCreatorVideos(userId, count);

  console.log(`Found ${videos.length} videos\n`);

  for (const video of videos.slice(0, 10)) {
    console.log(`Video: ${video.video_id}`);
    console.log(`  Views: ${video.views.toLocaleString()} | Likes: ${video.likes.toLocaleString()}`);
    console.log(`  Posted: ${new Date(video.posted_at).toLocaleString()}`);
    console.log('');
  }
}

/**
 * Run community health check
 */
async function runCommunity(scraper: TikTokScraper, ticker: string, compareTwitter: boolean) {
  console.log(`🏥 Checking community health for $${ticker}...\n`);

  const tiktokData = await scraper.searchCoinMentions(ticker, 30);

  // Mock X data (would integrate with real X API)
  const xData = {
    mention_count_24h: tiktokData.mention_count_24h * 0.8,
    avg_engagement: tiktokData.avg_engagement * 0.9,
    velocity_change: tiktokData.velocity_change * 0.7,
    top_influencers: [],
    sentiment_score: 0.3,
  };

  const score = scorer.calculateCommunityScore(tiktokData, xData);

  console.log('TikTok Score:', score.tiktok.score, '/100');
  console.log('  Mentions (24h):', score.tiktok.mentions_24h);
  console.log('  Velocity:', score.tiktok.velocity.toFixed(1), '%');
  console.log('  Quality:', score.tiktok.quality);
  console.log('');
  console.log('X Score:', score.x.score, '/100');
  console.log('  Mentions (24h):', score.x.mentions_24h);
  console.log('  Velocity:', score.x.velocity.toFixed(1), '%');
  console.log('  Quality:', score.x.quality);
  console.log('');
  console.log('Combined Score:', score.combined.overall_score, '/100');
  console.log('Trend:', score.combined.trend);
  console.log('Correlation:', score.combined.correlation.toFixed(2));
  console.log('Recommendation:', score.combined.recommendation.toUpperCase());
}

/**
 * Run GMGN Monitor
 */
async function runGMGNMonitor(ticker: string) {
  const displayTicker = ticker || 'ALL';
  console.log(`🚀 Starting GMGN Monitor for $${displayTicker}...`);
  console.log('Press Ctrl+C to stop\n');

  const monitor = new GMGNMonitor(ticker || 'ALL');
  await monitor.start();
}

/**
 * Run test mode
 */
async function runTest(scraper: TikTokScraper) {
  console.log('🧪 Running tests...\n');

  try {
    console.log('1. Testing device registration...');
    const newConfig = await scraper.registerDevice('Samsung', 'SM-A136U', 'US');
    console.log('   ✓ Device registered:', newConfig.device_id);

    console.log('2. Testing trending endpoint...');
    const trending = await scraper.getTrending(5);
    console.log('   ✓ Got', trending.length, 'trending videos');

    console.log('3. Testing search endpoint...');
    const search = await scraper.searchCoinMentions('DOGE', 5);
    console.log('   ✓ Found', search.mention_count_24h, 'mentions');

    console.log('\n✅ All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

/**
 * Parse command line arguments
 */
function parseArgs(): CliArgs {
  const args = process.argv.slice(2);
  const parsed: CliArgs = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--mode') {
      parsed.mode = args[++i] as CliArgs['mode'];
    } else if (args[i] === '--ticker') {
      parsed.ticker = args[++i];
    } else if (args[i] === '--hashtag') {
      parsed.hashtag = args[++i];
    } else if (args[i] === '--user_id') {
      parsed.user_id = args[++i];
    } else if (args[i] === '--count') {
      parsed.count = parseInt(args[++i], 10);
    } else if (args[i] === '--compare-twitter') {
      parsed.compareTwitter = true;
    } else if (args[i] === '--test') {
      parsed.test = true;
    }
  }

  return parsed;
}

// Run
main().catch((error) => {
  console.error('Error:', error.message);
  process.exit(1);
});
