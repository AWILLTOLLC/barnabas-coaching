import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, recordCoin, dueOutcomes } from '../src/db.js';
import { captureDueOutcomes } from '../src/outcomes.js';
import type { Coin } from '../src/gmgn.js';

const NOW = Date.parse('2026-09-06T12:00:00Z');

function coin(address: string): Coin {
  return {
    address, name: 'T', ticker: 'T',
    price_usd: 0.01, market_cap: 1_000_000, volume_24h: 600_000,
    liquidity_usd: 60_000, holder_count: 500, top10_rate: 0.2,
    created_at_ms: NOW - 48 * 3_600_000, price_change_6h_pct: null, price_change_1h_pct: null,
    renounced_mint: null, renounced_freeze: null, burn_status: null,
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
  };
}

test('captures due outcomes up to limit; failures become dead after 3 passes', async () => {
  const db = openDb(':memory:');
  for (let i = 0; i < 8; i++) {
    recordCoin(db, coin(`0x${i}`), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  }
  const t = NOW + 3_600_001; // all 8 one-hour horizons due

  // limit respected
  let calls = 0;
  const captured = await captureDueOutcomes(db, async () => { calls++; return { price: 0.02, change_6h_pct: 0, change_24h_pct: 0, liquidity_usd: 50_000 }; }, t, 5);
  assert.equal(captured, 5);
  assert.equal(calls, 5);
  assert.equal(dueOutcomes(db, t, 100).length, 3);

  // failing fetch: 3 passes then dead
  for (let pass = 0; pass < 3; pass++) {
    await captureDueOutcomes(db, async () => null, t, 10);
  }
  assert.equal(dueOutcomes(db, t, 100).length, 0);
  const dead = db.prepare(`SELECT COUNT(*) AS n FROM outcomes WHERE status = 'dead'`).get() as any;
  assert.equal(dead.n, 3);
});
