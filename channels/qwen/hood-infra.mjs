#!/usr/bin/env node

/**
 * Infrastructure Flywheel Scanner
 * Finds utility projects on emerging chains with liquidity aggregation flywheels
 * Ponytail: ~150 lines, no over-engineering
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import { writeFileSync } from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

// Load GMGN API key from existing config
const GMGN_ENV_PATH = '/Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/.env';

let GMGN_API_KEY = '';
try {
  const envContent = fs.readFileSync(GMGN_ENV_PATH, 'utf8');
  const match = envContent.match(/^GMGN_API_KEY=(.+)$/m);
  if (match) {
    GMGN_API_KEY = match[1].trim();
  }
} catch (error) {
  console.warn('Warning: Could not load GMGN_API_KEY from .env');
}

// Configuration
const CONFIG = {
  pollingInterval: 600000, // 10 minutes (infrastructure moves slower, less rate limit pressure)
  discordTokenPath: '/Users/apollo/.openclaw/openclaw.json',
  discordRecipientId: '276104854303145994', // Aaron's Discord ID
  logFile: '/Users/apollo/.openclaw/workspace/channels/qwen/infra-scanner.log',
};

// Known list file for deduplication
const KNOWN_FILE = '/Users/apollo/.openclaw/workspace/channels/qwen/data/infra-known.json';

// Detection criteria
const CRITERIA = {
  chainAgeMonths: 12,
  minMarketCap: 5_000_000,    // Lowered from $20M to $5M
  maxMarketCap: 100_000_000,
  minProtocolLiquidity: 250_000,  // Lowered from $500K to $250K
  maxPSLPercent: 10,
  minPools: 10,               // Lowered from 25 to 10
  minTrendMonths: 3,
};

// Risk thresholds
const RISKS = {
  monthlyUnlockPercent: 5,
  top10HolderPercent: 40,
};

/**
 * Main entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Infrastructure Flywheel Scanner

Usage:
  hood-infra              Run once and exit
  hood-infra watch        Run continuously in background
  hood-infra --test       Test with sample data

Options:
  --help, -h              Show this help
`);
    process.exit(0);
  }

  const mode = args[0] || 'run';

  switch (mode) {
    case 'watch':
      await runContinuous();
      break;
    case 'test':
      await runTest();
      break;
    case 'run':
    default:
      await runScan();
      break;
  }
}

/**
 * Run continuous scan (background mode)
 */
async function runContinuous() {
  console.log('🏗️  Infrastructure Flywheel Scanner started');
  console.log(`Polling every ${CONFIG.pollingInterval / 1000}s`);
  console.log('Press Ctrl+C to stop\n');

  while (true) {
    try {
      await runScan();
      await new Promise(r => setTimeout(r, CONFIG.pollingInterval));
    } catch (error) {
      console.error('Scan error:', error.message);
      await new Promise(r => setTimeout(r, 60_000)); // Backoff
    }
  }
}

/**
 * Load known addresses from file
 */
function loadKnownList() {
  try {
    const data = JSON.parse(fs.readFileSync(KNOWN_FILE, 'utf8'));
    return new Set(data.known || []);
  } catch (error) {
    console.log('  No known list found, starting fresh');
    return new Set();
  }
}

/**
 * Save known addresses to file
 */
function saveKnownList(knownSet) {
  try {
    writeFileSync(KNOWN_FILE, JSON.stringify({ known: [...knownSet] }, null, 2));
  } catch (error) {
    console.error('  Failed to save known list:', error.message);
  }
}

/**
 * Run single scan
 */
async function runScan() {
  const startTime = Date.now();
  console.log(`\n[${new Date().toISOString()}] Running scan...\n`);

  // Load known addresses
  const knownAddresses = loadKnownList();
  console.log(`  Known addresses: ${knownAddresses.size}\n`);

  // Fetch data from GMGN (trenches, hot searches, trending)
  const coins = await fetchGMGNData();
  console.log(`Found ${coins.length} coins to evaluate\n`);

  const matches = [];

  for (const coin of coins) {
    const result = evaluateCoin(coin);
    if (result.match) {
      // Check if already known
      if (knownAddresses.has(coin.address)) {
        console.log(`✓ ${coin.symbol} - already tracked (known)\n`);
        continue;
      }
      
      matches.push(result);
      console.log(formatMatch(coin, result));
      await sendDiscordAlert(coin, result);
      
      // Add to known list
      knownAddresses.add(coin.address);
    }
  }

  // Save updated known list
  saveKnownList(knownAddresses);
  console.log(`\nUpdated known list: ${knownAddresses.size} addresses`);

  const duration = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\nScan complete in ${duration}s - Found ${matches.length} new matches`);

  // Log to file
  const logEntry = {
    timestamp: new Date().toISOString(),
    durationSeconds: parseFloat(duration),
    matches: matches.length,
    coinsScanned: coins.length,
  };
  fs.appendFileSync(CONFIG.logFile, JSON.stringify(logEntry) + '\n');
}

/**
 * Fetch coin data from GMGN CLI
 */
async function fetchGMGNData() {
  try {
    // Use only hot-searches to minimize rate limit pressure
    const endpoints = [
      `GMGN_API_KEY=${GMGN_API_KEY} gmgn-cli market hot-searches --chain robinhood --limit 100`,
    ];

    const allCoins = [];

    for (const cmd of endpoints) {
      try {
        const { stdout } = await execAsync(cmd, { maxBuffer: 10 * 1024 * 1024 });
        const data = JSON.parse(stdout);
        
        // Handle different response formats
        let coins = [];
        if (Array.isArray(data)) {
          // hot-searches returns array
          coins = data[0]?.tokens || [];
        } else if (data.data?.rank) {
          coins = data.data.rank;
        } else if (data.data?.tokens) {
          coins = data.data.tokens;
        } else if (data.completed) {
          coins = data.completed;
        }
        
        const parsed = coins
          .map(token => parseGMGNCoin(token))
          .filter(c => c.marketCap > 0);
        
        allCoins.push(...parsed);
        await new Promise(r => setTimeout(r, 5000)); // Rate limit
      } catch (error) {
        console.error(`GMGN endpoint error:`, error.message);
      }
    }

    // Dedupe by address
    return [...new Map(allCoins.map(c => [c.address, c])).values()];
  } catch (error) {
    console.error('GMGN fetch error:', error);
    return [];
  }
}

/**
 * Parse GMGN coin data
 */
function parseGMGNCoin(token) {
  const creationTime = token.creation_timestamp || token.open_timestamp || Date.now();
  // Convert from Unix seconds to milliseconds if needed
  const timestamp = creationTime > 1e12 ? creationTime : creationTime * 1000;
  const ageHours = (Date.now() - timestamp) / 3600_000;
  const ageMonths = ageHours / (30 * 24);

  return {
    address: token.address || '',
    name: token.name || '',
    symbol: token.symbol || '',
    price: token.price || 0,
    marketCap: token.market_cap || 0,
    volume24h: token.volume || 0,
    liquidity: token.liquidity || 0,
    createdAt: new Date(timestamp).toISOString(),
    ageMonths: ageMonths,
    holderCount: token.holder_count || 0,
    top10Concentration: token.top_10_holder_rate,
    poolCount: token.pool_count || 0,      // May be 0
    swaps: token.swaps || 0,               // Trading activity
    bundleCount: token.bundleCount,
    sniperCount: token.sniperCount,
  };
}

/**
 * Evaluate coin against infrastructure flywheel criteria
 */
function evaluateCoin(coin) {
  const reasons = [];
  const risks = [];

  // Chain age filter (< 12 months)
  if (coin.ageMonths < CRITERIA.chainAgeMonths) {
    reasons.push(`Chain age: ${coin.ageMonths.toFixed(1)} months`);
  } else {
    return { match: false };
  }

  // Market cap filter ($5M - $100M)
  if (coin.marketCap >= CRITERIA.minMarketCap && coin.marketCap <= CRITERIA.maxMarketCap) {
    reasons.push(`Market cap: $${(coin.marketCap / 1_000_000).toFixed(1)}M`);
  } else {
    return { match: false };
  }

  // Trading activity filter (25K+ swaps = liquidity aggregation)
  if (coin.swaps >= CRITERIA.minPools) {
    reasons.push(`Trading activity: ${coin.swaps.toLocaleString()} swaps`);
  } else {
    return { match: false };
  }

  // Check PSL (protocol-owned liquidity) - from top_10_concentration
  if (coin.top10Concentration) {
    const psLPercent = coin.top10Concentration * 100;
    if (psLPercent > CRITERIA.maxPSLPercent) {
      risks.push(`High PSL: ${psLPercent.toFixed(1)}% of top 10`);
    }
  }

  // Holder concentration risk
  if (coin.top10Concentration && coin.top10Concentration > RISKS.top10HolderPercent / 100) {
    risks.push(`Concentration: Top 10 holds ${(coin.top10Concentration * 100).toFixed(1)}%`);
  }

  // Bundle/sniper risk
  if (coin.bundleCount && coin.bundleCount > 5) {
    risks.push(`Bundle risk: ${coin.bundleCount} detected`);
  }

  return {
    match: true,
    reasons,
    risks,
  };
}

/**
 * Format match output
 */
function formatMatch(coin, result) {
  return `
🏗️  INFRASTRUCTURE FLYWHEEL MATCH

Project: $${coin.symbol} on Robinhood Chain

Metrics:
  • MC: $${(coin.marketCap / 1_000_000).toFixed(1)}M
  • Age: ${coin.ageMonths.toFixed(1)} months
  • Pools: ${coin.poolCount}
  • Holders: ${coin.holderCount.toLocaleString()}

Why it matches:
  ${result.reasons.map(r => `  • ${r}`).join('\n')}

${result.risks.length > 0 ? `Risk factors:
  ${result.risks.map(r => `  • ${r}`).join('\n')}
` : ''}

CA: ${coin.address}
`.trim();
}

/**
 * Send Discord alert
 */
async function sendDiscordAlert(coin, result) {
  try {
    const config = JSON.parse(fs.readFileSync(CONFIG.discordTokenPath, 'utf8'));
    const token = config?.channels?.discord?.token;

    if (!token) {
      console.log('  Discord token not found');
      return;
    }

    const headers = {
      'Authorization': `Bot ${token}`,
      'Content-Type': 'application/json',
    };

    // Get or create DM channel
    const dmRes = await fetch('https://discord.com/api/v10/users/@me/channels', {
      method: 'POST',
      headers,
      body: JSON.stringify({ recipient_id: CONFIG.discordRecipientId }),
    });

    if (!dmRes.ok) {
      console.log(`  Discord DM channel create failed: ${dmRes.status}`);
      return;
    }

    const dm = await dmRes.json();
    const message = formatMatch(coin, result);

    const sendRes = await fetch(`https://discord.com/api/v10/channels/${dm.id}/messages`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content: message }),
    });

    if (!sendRes.ok) {
      console.log(`  Discord message send failed: ${sendRes.status}`);
    } else {
      console.log('  ✓ Alert sent to Discord');
    }
  } catch (error) {
    console.log(`  Discord error: ${error.message}`);
  }
}

/**
 * Test mode with sample data
 */
async function runTest() {
  console.log('🧪 Running test scan...\n');

  const sampleCoin = {
    address: '0x1234567890abcdef1234567890abcdef12345678',
    name: 'TestProtocol',
    symbol: 'TEST',
    price: 0.0001,
    marketCap: 35_000_000,
    volume24h: 2_500_000,
    createdAt: new Date(Date.now() - 45 * 24 * 3600_000).toISOString(), // 45 days old
    ageMonths: 1.5,
    holderCount: 12500,
    top10Concentration: 0.35,
    poolCount: 45,
    bundleCount: 3,
    sniperCount: 8,
  };

  const result = evaluateCoin(sampleCoin);
  console.log(formatMatch(sampleCoin, result));

  if (result.match) {
    await sendDiscordAlert(sampleCoin, result);
  }
}

// Run
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
