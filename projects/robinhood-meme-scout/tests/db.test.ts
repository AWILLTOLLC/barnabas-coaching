import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, recordCoin, hasCoin, dueOutcomes, captureOutcome, bumpAttempts, markDead, HORIZONS_H } from '../src/db.js';
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

test('recordCoin stores row and schedules all horizons; hasCoin true after', () => {
  const db = openDb(':memory:');
  assert.equal(hasCoin(db, '0x1'), false);
  recordCoin(db, coin('0x1'), { passed: true, score: 75, reasons: ['r'], flags: [] }, true, NOW);
  assert.equal(hasCoin(db, '0x1'), true);
  // all horizons pending, none due yet at NOW
  assert.equal(dueOutcomes(db, NOW, 10).length, 0);
  // after 1h+, the 1h horizon is due
  const due = dueOutcomes(db, NOW + 3_600_001, 10);
  assert.equal(due.length, 1);
  assert.equal(due[0].horizon_h, 1);
  assert.equal(due[0].address, '0x1');
});

test('recordCoin is idempotent per address', () => {
  const db = openDb(':memory:');
  recordCoin(db, coin('0x1'), { passed: false, score: 0, reasons: ['mc'], flags: [] }, false, NOW);
  recordCoin(db, coin('0x1'), { passed: true, score: 90, reasons: [], flags: [] }, true, NOW);
  const due = dueOutcomes(db, NOW + 200 * 3_600_000, 100);
  assert.equal(due.length, HORIZONS_H.length); // not doubled
});

test('captureOutcome fills row; dead after 3 failed attempts', () => {
  const db = openDb(':memory:');
  recordCoin(db, coin('0x1'), { passed: true, score: 75, reasons: [], flags: [] }, false, NOW);
  const t1 = NOW + 3_600_001;
  const [d] = dueOutcomes(db, t1, 1);
  captureOutcome(db, d.id, 0.02, 70_000, t1);
  assert.equal(dueOutcomes(db, t1, 10).length, 0); // 1h no longer due

  const t6 = NOW + 6 * 3_600_000 + 1;
  const [d6] = dueOutcomes(db, t6, 1);
  bumpAttempts(db, d6.id);
  bumpAttempts(db, d6.id);
  bumpAttempts(db, d6.id);
  markDead(db, d6.id, t6);
  assert.equal(dueOutcomes(db, t6, 10).length, 0);
});
