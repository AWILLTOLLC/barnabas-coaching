import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, recordCoin } from '../src/db.js';
import { liquidityBaseline } from '../src/peers.js';
import type { Coin } from '../src/gmgn.js';

const NOW = Date.parse('2026-09-10T12:00:00Z');
const BANDS: [number, number][] = [[500_000, 2_000_000], [5_000_000, 25_000_000]];

function coin(address: string, mc: number, liq: number): Coin {
  return {
    address, name: 'T', ticker: 'T',
    price_usd: 0.01, market_cap: mc, volume_24h: 600_000,
    liquidity_usd: liq, holder_count: 500, top10_rate: 0.2,
    created_at_ms: NOW - 48 * 3_600_000, price_change_6h_pct: null, price_change_1h_pct: null,
    renounced_mint: null, renounced_freeze: null, burn_status: null,
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
  };
}

function seed(db: any, n: number, ratioPct: (i: number) => number) {
  for (let i = 0; i < n; i++) {
    const mc = 1_000_000;
    recordCoin(db, coin(`0x${i}`, mc, mc * ratioPct(i) / 100), { passed: false, score: 0, reasons: [], flags: [] }, false, NOW - 3_600_000);
  }
}

test('liquidityBaseline: percentiles from band peers, verdict classification', () => {
  const db = openDb(':memory:');
  seed(db, 40, i => i + 1); // ratios 1%..40% → p25≈10, median≈20, p75≈30

  const typical = liquidityBaseline(db, coin('0xt', 1_800_000, 1_800_000 * 0.15), BANDS, NOW);
  assert.ok(typical);
  assert.equal(typical!.verdict, 'typical'); // 15% between p25 and p75
  assert.ok(Math.abs(typical!.median_pct - 20) <= 2);
  assert.equal(typical!.n, 40);

  const thin = liquidityBaseline(db, coin('0xu', 1_800_000, 1_800_000 * 0.03), BANDS, NOW);
  assert.equal(thin!.verdict, 'below typical'); // 3% < p25

  const rich = liquidityBaseline(db, coin('0xv', 1_800_000, 1_800_000 * 0.35), BANDS, NOW);
  assert.equal(rich!.verdict, 'above typical');
});

test('liquidityBaseline: null when out of band or sample too small', () => {
  const db = openDb(':memory:');
  seed(db, 5, () => 10);
  assert.equal(liquidityBaseline(db, coin('0xx', 1_000_000, 100_000), BANDS, NOW), null); // n < 20
  assert.equal(liquidityBaseline(db, coin('0xy', 100_000, 10_000), BANDS, NOW), null); // outside bands
});
