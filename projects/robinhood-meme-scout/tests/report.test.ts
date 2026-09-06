import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, recordCoin, captureOutcome, dueOutcomes, markDead } from '../src/db.js';
import { computeReport, formatReport } from '../src/report.js';
import type { Coin } from '../src/gmgn.js';

const NOW = Date.parse('2026-09-06T12:00:00Z');
const H = 3_600_000;

function coin(address: string, ticker: string, price: number): Coin {
  return {
    address, name: ticker, ticker,
    price_usd: price, market_cap: 1_000_000, volume_24h: 600_000,
    liquidity_usd: 60_000, holder_count: 500, top10_rate: 0.2,
    created_at_ms: NOW - 48 * H, price_change_6h_pct: null,
    renounced_mint: null, renounced_freeze: null, burn_status: null,
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
  };
}

function capture(db: any, address: string, horizon: number, price: number, liq: number | null, t: number) {
  const row = db.prepare('SELECT id FROM outcomes WHERE address = ? AND horizon_h = ?').get(address, horizon);
  captureOutcome(db, row.id, price, liq, t);
}

test('computeReport: bands, returns, top rejected gainer, dead count', () => {
  const db = openDb(':memory:');
  const t0 = NOW - 26 * H;

  // alerted coin: doubled by 24h
  recordCoin(db, coin('0xa', 'WIN', 0.01), { passed: true, score: 80, reasons: [], flags: [] }, true, t0);
  capture(db, '0xa', 24, 0.02, 60_000, t0 + 24 * H);

  // near-miss (60-69): flat
  recordCoin(db, coin('0xb', 'MEH', 0.01), { passed: true, score: 65, reasons: [], flags: [] }, false, t0);
  capture(db, '0xb', 24, 0.0101, 60_000, t0 + 24 * H);

  // rejected coin that mooned 5x
  recordCoin(db, coin('0xc', 'MISS', 0.01), { passed: false, score: 0, reasons: ['age 10h outside 24-96h'], flags: [] }, false, t0);
  capture(db, '0xc', 24, 0.05, 200_000, t0 + 24 * H);

  // dead coin
  recordCoin(db, coin('0xd', 'RUG', 0.01), { passed: true, score: 72, reasons: [], flags: [] }, true, t0);
  const dead = db.prepare(`SELECT id FROM outcomes WHERE address = '0xd' AND horizon_h = 1`).get() as any;
  markDead(db, dead.id, t0 + H);

  // one coin first-seen inside the 24h window
  recordCoin(db, coin('0xe', 'FRESH', 0.01), { passed: true, score: 55, reasons: [], flags: [] }, false, NOW - 2 * H);

  const r = computeReport(db, NOW);
  assert.equal(r.last24h.new_coins, 1);
  assert.equal(r.last24h.alerts, 2);

  const alerted24 = r.bands.find(b => b.band === 'alerted' && b.horizon_h === 24)!;
  assert.equal(alerted24.n, 1);
  assert.ok(Math.abs(alerted24.median_return_pct - 100) < 0.01);

  const nearMiss24 = r.bands.find(b => b.band === 'near-miss' && b.horizon_h === 24)!;
  assert.ok(Math.abs(nearMiss24.median_return_pct - 1) < 0.01);

  assert.equal(r.top_rejected[0].ticker, 'MISS');
  assert.ok(Math.abs(r.top_rejected[0].return_pct - 400) < 0.01);
  assert.ok(r.top_rejected[0].reason.includes('age'));

  assert.equal(r.dead_outcomes, 1);

  const text = formatReport(r);
  assert.ok(text.includes('MISS'));
  assert.ok(text.includes('400'));
});
