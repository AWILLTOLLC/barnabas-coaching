import type { DatabaseSync } from 'node:sqlite';
import type { Coin } from './gmgn.js';

export interface LiquidityBaseline {
  n: number;
  ratio_pct: number;
  p25_pct: number;
  median_pct: number;
  p75_pct: number;
  verdict: 'below typical' | 'typical' | 'above typical';
}

const WINDOW_MS = 7 * 24 * 3_600_000;
const MIN_SAMPLE = 20;

/**
 * Compare a coin's liquidity/market-cap ratio against its own MC band's peers
 * from the last 7 days of recorded first-sight snapshots. Null when the coin is
 * outside every band or the peer sample is too small to trust.
 */
export function liquidityBaseline(
  db: DatabaseSync,
  coin: Coin,
  bands: [number, number][],
  now: number,
): LiquidityBaseline | null {
  const band = bands.find(([lo, hi]) => coin.market_cap >= lo && coin.market_cap <= hi);
  if (!band || coin.market_cap <= 0 || coin.liquidity_usd <= 0) return null;

  const ratios = (db.prepare(`
    SELECT CAST(liquidity AS REAL) / market_cap AS r FROM coins
    WHERE first_seen_ms >= ? AND market_cap BETWEEN ? AND ? AND liquidity > 0 AND market_cap > 0
    ORDER BY r`).all(now - WINDOW_MS, band[0], band[1]) as any[]).map(x => x.r as number);
  if (ratios.length < MIN_SAMPLE) return null;

  const pct = (q: number) => ratios[Math.min(ratios.length - 1, Math.floor(ratios.length * q))] * 100;
  const p25 = pct(0.25);
  const p75 = pct(0.75);
  const ratio = (coin.liquidity_usd / coin.market_cap) * 100;
  return {
    n: ratios.length,
    ratio_pct: ratio,
    p25_pct: p25,
    median_pct: pct(0.5),
    p75_pct: p75,
    verdict: ratio < p25 ? 'below typical' : ratio > p75 ? 'above typical' : 'typical',
  };
}
