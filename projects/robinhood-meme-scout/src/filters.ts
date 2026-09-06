import type { Coin } from './gmgn.js';
import type { Criteria } from './config.js';

export interface Evaluation {
  passed: boolean;
  score: number;
  reasons: string[];
  flags: string[];
}

export function evaluate(coin: Coin, c: Criteria, now: number = Date.now()): Evaluation {
  const reasons: string[] = [];
  const flags: string[] = [];

  const inBand = c.market_cap_bands.some(([lo, hi]) => coin.market_cap >= lo && coin.market_cap <= hi);
  if (!inBand) {
    return { passed: false, score: 0, reasons: [`mc $${fmt(coin.market_cap)} outside bands`], flags };
  }

  if (coin.created_at_ms === null) {
    return { passed: false, score: 0, reasons: ['age unknown'], flags };
  }
  const ageHours = (now - coin.created_at_ms) / 3_600_000;
  if (ageHours < c.candle_age_hours.min || ageHours > c.candle_age_hours.max) {
    return { passed: false, score: 0, reasons: [`age ${ageHours.toFixed(0)}h outside ${c.candle_age_hours.min}-${c.candle_age_hours.max}h`], flags };
  }

  if (coin.top10_rate !== null && coin.top10_rate > c.max_top10_holder_rate) {
    return { passed: false, score: 0, reasons: [`top10 hold ${(coin.top10_rate * 100).toFixed(0)}% > ${(c.max_top10_holder_rate * 100).toFixed(0)}%`], flags };
  }
  if (coin.top10_rate === null) flags.push('holders-unknown');

  if (coin.wash_trading) {
    return { passed: false, score: 0, reasons: ['wash trading flagged'], flags };
  }

  let score = 40;
  reasons.push('passed gates (+40)');

  if (coin.volume_24h >= c.strong_volume_24h) {
    score += 20; reasons.push(`volume $${fmt(coin.volume_24h)} (+20)`);
  } else if (coin.volume_24h >= c.min_volume_24h) {
    score += 10; reasons.push(`volume $${fmt(coin.volume_24h)} (+10)`);
  }

  if (coin.liquidity_usd >= c.strong_liquidity_usd) {
    score += 15; reasons.push(`liquidity $${fmt(coin.liquidity_usd)} (+15)`);
  } else if (coin.liquidity_usd >= c.min_liquidity_usd) {
    score += 10; reasons.push(`liquidity $${fmt(coin.liquidity_usd)} (+10)`);
  } else {
    flags.push('low-liquidity');
  }

  if (coin.top10_rate !== null && coin.top10_rate <= c.strong_top10_holder_rate) {
    score += 10; reasons.push(`top10 only ${(coin.top10_rate * 100).toFixed(0)}% (+10)`);
  }

  if (coin.renounced_mint === true && coin.renounced_freeze === true) {
    score += 10; reasons.push('mint+freeze renounced (+10)');
  }

  if (coin.burn_status === 'yes') {
    score += 5; reasons.push('lp burned (+5)');
  }

  return { passed: true, score: Math.min(100, score), reasons, flags };
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toFixed(0);
}
