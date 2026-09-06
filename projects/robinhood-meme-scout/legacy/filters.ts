/**
 * BKANTHA Two-Screen Filters
 * Ponytail: Native JS, no deps
 */

export interface CoinData {
  market_cap: number;
  age_hours: number;
  volume_24h: number;
  holder_concentration?: number;
  has_bundle?: boolean;
  has_sniper?: boolean;
  rug_flags?: string[];
}

export type FilterResult = 'pass' | 'fail' | 'dirty_tape';

export const filters = {
  /**
   * Established coins: 5-25M MC, 7+ days old
   */
  isEstablished(coin: CoinData): boolean {
    return coin.market_cap >= 5_000_000 &&
           coin.market_cap <= 25_000_000 &&
           coin.age_hours >= 168; // 7 days
  },

  /**
   * Fresh coins: 500K-2M MC, <7 days old
   */
  isFresh(coin: CoinData): boolean {
    return coin.market_cap >= 500_000 &&
           coin.market_cap <= 2_000_000 &&
           coin.age_hours < 168;
  },

  /**
   * Dirty tape check: bundle, sniper, rug flags
   */
  checkTape(coin: CoinData): FilterResult {
    if (coin.has_bundle) return 'dirty_tape';
    if (coin.has_sniper) return 'dirty_tape';
    if (coin.rug_flags && coin.rug_flags.length > 0) return 'dirty_tape';
    if (coin.holder_concentration && coin.holder_concentration > 0.4) {
      return 'dirty_tape'; // Top 10 holders >40%
    }
    return 'pass';
  },

  /**
   * Combined filter: returns score 0-100
   */
  scoreCoin(coin: CoinData): number {
    let score = 0;

    // Market cap score (30 points)
    if (coin.market_cap >= 5_000_000 && coin.market_cap <= 25_000_000) score += 30;
    else if (coin.market_cap >= 500_000 && coin.market_cap <= 2_000_000) score += 20;

    // Age score (20 points)
    if (coin.age_hours >= 168) score += 20; // Established
    else if (coin.age_hours >= 24 && coin.age_hours < 168) score += 10; // 1-7 days

    // Volume score (20 points)
    if (coin.volume_24h > 1_000_000) score += 20;
    else if (coin.volume_24h > 500_000) score += 10;

    // Dirty tape penalty (30 points)
    const tape = this.checkTape(coin);
    if (tape === 'dirty_tape') score -= 30;
    else if (tape === 'fail') score -= 10;

    return Math.max(0, Math.min(100, score));
  },
};
