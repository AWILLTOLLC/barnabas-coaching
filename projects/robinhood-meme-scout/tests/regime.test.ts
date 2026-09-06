import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computeBreadth, labelRegime, RegimeTracker, type RegimeConfig } from '../src/regime.js';
import type { Coin } from '../src/gmgn.js';

const NOW = Date.parse('2026-09-06T12:00:00Z');

const cfg: RegimeConfig = {
  hot_median_1h_pct: 3, cold_median_1h_pct: -3,
  hot_green_share: 0.55, cold_green_share: 0.35,
  confirm_scans: 3,
};

function coin(change1h: number | null, createdAgoH = 48): Coin {
  return {
    address: `0x${Math.random().toString(16).slice(2)}`, name: 'T', ticker: 'T',
    price_usd: 0.01, market_cap: 1_000_000, volume_24h: 100_000,
    liquidity_usd: 60_000, holder_count: 500, top10_rate: 0.2,
    created_at_ms: NOW - createdAgoH * 3_600_000, price_change_6h_pct: null,
    price_change_1h_pct: change1h,
    renounced_mint: null, renounced_freeze: null, burn_status: null,
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
  };
}

test('computeBreadth: median, green share, launches, ignores unknown changes', () => {
  const coins = [coin(10), coin(-2), coin(5), coin(null), coin(-8, 0.5)];
  const b = computeBreadth(coins, NOW);
  assert.equal(b.n, 4); // null excluded
  assert.equal(b.median_1h_pct, 1.5); // sorted [-8,-2,5,10] → avg of -2 and 5
  assert.equal(b.green_share, 0.5);
  assert.equal(b.total_volume_24h, 500_000);
  assert.equal(b.new_launches_1h, 1);
});

test('labelRegime thresholds', () => {
  const base = { n: 50, total_volume_24h: 0, new_launches_1h: 0 };
  assert.equal(labelRegime({ ...base, median_1h_pct: 5, green_share: 0.6 }, cfg), 'hot');
  assert.equal(labelRegime({ ...base, median_1h_pct: 5, green_share: 0.4 }, cfg), 'neutral'); // hot needs both
  assert.equal(labelRegime({ ...base, median_1h_pct: -5, green_share: 0.6 }, cfg), 'cold'); // cold on either
  assert.equal(labelRegime({ ...base, median_1h_pct: 0, green_share: 0.3 }, cfg), 'cold');
  assert.equal(labelRegime({ ...base, median_1h_pct: 0, green_share: 0.5 }, cfg), 'neutral');
  assert.equal(labelRegime({ ...base, n: 3, median_1h_pct: 9, green_share: 0.9 }, cfg), 'neutral'); // too few coins
});

test('RegimeTracker flips only after confirm_scans consecutive readings', () => {
  const t = new RegimeTracker('neutral', cfg);
  assert.equal(t.update('cold'), 'neutral');
  assert.equal(t.update('cold'), 'neutral');
  assert.equal(t.update('hot'), 'neutral'); // streak broken
  assert.equal(t.update('cold'), 'neutral');
  assert.equal(t.update('cold'), 'neutral');
  assert.equal(t.update('cold'), 'cold'); // 3rd consecutive → flip
  assert.equal(t.update('cold'), 'cold');
});
