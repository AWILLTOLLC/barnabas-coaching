/**
 * GMGN Monitor - Core Streaming + Candle Filter
 * Ponytail: Native JS, folds candle logic into filter
 */

import { filters, CoinData } from './filters.js';
import { VelocityTracker } from './velocity-tracker.js';
import { TikTokScraper } from './tiktok-scraper.js';
import { sendAlert } from './alerts.js';
import { runDueDiligence, formatAlert } from './due-diligence.js';
import * as fs from 'fs';
import * as path from 'path';

export interface GMGNCoin {
  contract_address: string;
  name: string;
  ticker: string;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  created_at: string;
  holder_count: number;
  top_10_concentration?: number;
  bundle_count?: number;
  sniper_count?: number;
}

export class GMGNMonitor {
  private ticker: string;
  private velocityTracker: VelocityTracker;
  private tiktok: TikTokScraper;
  private lastRun: Map<string, number>;
  private knownListPath: string;
  private knownAddresses: Set<string>;

  constructor(ticker: string) {
    this.ticker = ticker;
    this.velocityTracker = new VelocityTracker();
    this.tiktok = new TikTokScraper({
      device_id: '7680616891110524437',
      iid: '7680617333853718293',
      region: 'US',
      version_code: '320820',
      aid: 473824,
    });
    this.lastRun = new Map();
    this.knownListPath = path.join(process.cwd(), 'data', 'infra-known.json');
    this.knownAddresses = new Set();
  }

  /**
   * Main polling loop
   */
  async start() {
    // Load known addresses at startup
    await this.loadKnownList();
    
    console.log(`🏗️  INFRASTRUCTURE FLYWHEEL STARTED for $${this.ticker}`);
    console.log(`   Known addresses: ${this.knownAddresses.size}`);
    
    while (true) {
      try {
        await this.runScan();
        // 30s polling (adjust as needed)
        await new Promise(r => setTimeout(r, 30_000));
      } catch (error) {
        console.error('Monitor error:', error);
        await new Promise(r => setTimeout(r, 60_000)); // Backoff on error
      }
    }
  }

  /**
   * Single scan run
   */
  private async runScan() {
    // Fetch from GMGN
    const coins = await this.fetchGMGNData();

    for (const coin of coins) {
      // Skip if already tracked
      if (this.knownAddresses.has(coin.contract_address)) {
        console.log(`✓ $${coin.ticker} - already tracked (known)`);
        continue;
      }
      
      const { score, diligence } = await this.evaluateCoin(coin);
      
      if (score >= 70) {
        // Send alert with diligence report
        const alertMsg = formatAlert(
          { ticker: coin.ticker, address: coin.contract_address, chain: 'robinhood' },
          diligence!
        );
        await sendAlert(coin, score, alertMsg);
        
        // Add to known list after successful alert
        this.knownAddresses.add(coin.contract_address);
        await this.saveKnownList();
      }
    }
  }

  /**
   * Evaluate coin with candle filter + due diligence
   * # ponytail: diligence inline, not separate component
   */
  private async evaluateCoin(coin: GMGNCoin): Promise<{ score: number; diligence?: any }> {
    const ageHours = (Date.now() - new Date(coin.created_at).getTime()) / 1000 / 3600;

    // Candle filter: 1-4 days old
    if (ageHours < 24 || ageHours > 96) {
      return { score: 0 }; // Too fresh or too stale
    }

    // Convert to filter format
    const filterData: CoinData = {
      market_cap: coin.market_cap,
      age_hours: ageHours,
      volume_24h: coin.volume_24h,
      holder_concentration: coin.top_10_concentration,
      has_bundle: coin.bundle_count && coin.bundle_count > 5,
      has_sniper: coin.sniper_count && coin.sniper_count > 10,
    };

    // Base score from BKANTHA filters
    let score = filters.scoreCoin(filterData);

    // TikTok mention boost
    const tiktokData = await this.tiktok.searchCoinMentions(coin.ticker, 30);
    if (tiktokData.mention_count_24h > 100) {
      score += 15; // 15-point boost
    }
    if (tiktokData.velocity_change > 200) {
      score += 10; // Extra 10 points
    }

    // Due diligence check
    const diligence = await runDueDiligence(coin.contract_address, 'robinhood', 'scout');
    
    // If diligence score < 70, reduce overall score
    if (diligence.score < 70) {
      score = Math.min(score, 60);
    } else {
      // Add diligence score as bonus (up to 20 points)
      score = Math.min(100, score + (diligence.score - 70) * 0.2);
    }

    return { score, diligence };
  }

  /**
   * Fetch from GMGN using CLI
   * # ponytail: 3 endpoints for early detection, rate-limited
   */
  private async fetchGMGNData(): Promise<GMGNCoin[]> {
    try {
      const { exec } = await import('child_process');
      
      const endpoints = [
        `gmgn-cli market trenches --chain robinhood --limit 50`,
        `gmgn-cli market hot-searches --chain robinhood --limit 50`,
        `gmgn-cli market trending --chain robinhood --interval 1h --limit 50`,
      ];
      
      const allCoins: GMGNCoin[] = [];
      
      for (const cmd of endpoints) {
        const result = await new Promise<{stdout: string}>((resolve, reject) => {
          exec(cmd, { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
            if (error) {
              console.error(`GMGN CLI error (${cmd}):`, error.message);
              resolve({ stdout: '[]' });
            } else {
              resolve({ stdout });
            }
          });
        });
        
        try {
          const data = JSON.parse(result.stdout);
          const coins = (data.data?.rank || []) as any[];
          
          const parsed = coins.map((token: any) => ({
            contract_address: token.address || '',
            name: token.name || '',
            ticker: token.symbol || '',
            price_usd: token.price || 0,
            market_cap: token.marketCap || 0,
            volume_24h: token.volume || 0,
            created_at: new Date(token.creation_timestamp || token.open_timestamp || Date.now()).toISOString(),
            holder_count: token.holder_count || 0,
            top_10_concentration: token.top_10_holder_rate,
            bundle_count: token.bundleCount,
            sniper_count: token.sniperCount,
          })).filter(coin => coin.market_cap > 0);
          
          allCoins.push(...parsed);
        } catch (parseError) {
          console.error('GMGN parse error:', parseError);
        }
        
        // Rate limit: 5s between endpoints
        await new Promise(r => setTimeout(r, 5000));
      }
      
      // Dedupe by address
      return [...new Map(allCoins.map(c => [c.contract_address, c])).values()];
    } catch (error) {
      console.error('GMGN fetch error:', error);
      return [];
    }
  }

  /**
   * Load known addresses from disk
   */
  private async loadKnownList(): Promise<void> {
    try {
      if (fs.existsSync(this.knownListPath)) {
        const data = fs.readFileSync(this.knownListPath, 'utf8');
        const addresses = JSON.parse(data) as string[];
        this.knownAddresses = new Set(addresses);
        console.log(`   Loaded ${this.knownAddresses.size} known addresses`);
      } else {
        console.log('   No known list found, starting fresh');
        this.knownAddresses = new Set();
      }
    } catch (error) {
      console.error('Error loading known list:', error);
      this.knownAddresses = new Set();
    }
  }

  /**
   * Save known addresses to disk
   */
  private async saveKnownList(): Promise<void> {
    try {
      const addresses = Array.from(this.knownAddresses);
      fs.writeFileSync(this.knownListPath, JSON.stringify(addresses, null, 2));
    } catch (error) {
      console.error('Error saving known list:', error);
    }
  }
}
