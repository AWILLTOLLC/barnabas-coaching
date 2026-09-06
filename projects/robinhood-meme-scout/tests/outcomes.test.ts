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

test('batch path: one dex call covers all due rows, dedupes addresses, stamps source', async () => {
  const db = openDb(':memory:');
  recordCoin(db, coin('0xA'), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  recordCoin(db, coin('0xB'), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  const t = NOW + 6 * 3_600_000 + 1; // 1h + 6h horizons due for both coins → 4 rows, 2 addresses

  const batchCalls: string[][] = [];
  let gmgnCalls = 0;
  const captured = await captureDueOutcomes(
    db,
    async () => { gmgnCalls++; return null; },
    t, 30,
    async (addresses) => {
      batchCalls.push(addresses);
      return new Map([
        ['0xa', { price: 0.02, change_6h_pct: 1, change_24h_pct: 2, liquidity_usd: 70_000, market_cap: 1_500_000, dex_id: 'uniswap' }],
        ['0xb', { price: 0.03, change_6h_pct: 1, change_24h_pct: 2, liquidity_usd: 80_000, market_cap: 2_500_000, dex_id: 'uniswap' }],
      ]);
    },
  );
  assert.equal(captured, 4);
  assert.equal(batchCalls.length, 1);
  assert.deepEqual([...batchCalls[0]].sort(), ['0xA', '0xB']);
  assert.equal(gmgnCalls, 0);
  const rows = db.prepare(`SELECT source, COUNT(*) n FROM outcomes WHERE status = 'captured' GROUP BY source`).all() as any[];
  assert.equal(rows.length, 1);
  assert.equal(rows[0].source, 'dexscreener');
  assert.equal(rows[0].n, 4);
});

test('batch misses fall back to gmgn (source stamped), gmgn-null misses go dead after 3 passes', async () => {
  const db = openDb(':memory:');
  recordCoin(db, coin('0xA'), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  recordCoin(db, coin('0xB'), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  const t = NOW + 3_600_001; // 1h horizon due for both

  const emptyBatch = async () => new Map();
  const gmgnOnlyA = async (address: string) =>
    address === '0xA' ? { price: 0.05, change_6h_pct: 0, change_24h_pct: 0, liquidity_usd: 40_000 } : null;

  for (let pass = 0; pass < 3; pass++) {
    await captureDueOutcomes(db, gmgnOnlyA, t, 30, emptyBatch);
  }
  const a = db.prepare(`SELECT status, source FROM outcomes WHERE address = '0xA' AND horizon_h = 1`).get() as any;
  assert.equal(a.status, 'captured');
  assert.equal(a.source, 'gmgn');
  const b = db.prepare(`SELECT status FROM outcomes WHERE address = '0xB' AND horizon_h = 1`).get() as any;
  assert.equal(b.status, 'dead');
});

test('gmgn fallback is budget-capped at 5 per tick; the rest stay pending untouched', async () => {
  const db = openDb(':memory:');
  for (let i = 0; i < 8; i++) {
    recordCoin(db, coin(`0x${i}`), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  }
  const t = NOW + 3_600_001;

  let gmgnCalls = 0;
  await captureDueOutcomes(db, async () => { gmgnCalls++; return null; }, t, 30, async () => new Map());
  assert.equal(gmgnCalls, 5);
  const untouched = db.prepare(`SELECT COUNT(*) n FROM outcomes WHERE status = 'pending' AND due_ms <= ? AND attempts = 0`).get(t) as any;
  assert.equal(untouched.n, 3);
});
