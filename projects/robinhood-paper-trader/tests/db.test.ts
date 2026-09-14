import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  openDb, insertOrder, openPosition, updatePosition, closePosition, getPosition,
  openPositionCount, hasPosition, ordersToday, deployedTodayUsd, realizedCapital, ptDate,
} from '../src/db.js';

const NOW = Date.parse('2026-09-14T20:00:00Z'); // 13:00 PDT
const TODAY = ptDate(NOW);

function entryOrder(id: string, ts: number, usd: number, status: 'filled' | 'failed' = 'filled') {
  return { id, ts, pt_date: ptDate(ts), side: 'buy' as const, address: `0x${id}`, ticker: 'T', amount_usd: usd, token_amount: null, slippage_pct: 5, status, error: null, kind: 'entry' as const };
}

test('position roundtrip stores entry_price and ref_price independently', () => {
  const db = openDb(':memory:');
  openPosition(db, { address: '0xa', ticker: 'A', opened_ms: NOW, entry_price: 0.0011, ref_price: 0.001, stake_usd: 10, tokens_total: 9000 });
  const p = getPosition(db, '0xa')!;
  assert.equal(p.entry_price, 0.0011);
  assert.equal(p.ref_price, 0.001);
  assert.equal(p.tokens_remaining, 9000);
  updatePosition(db, '0xa', { realized_usd: 100, tokens_remaining: 0 });
  closePosition(db, '0xa', 'closed', NOW + 1000);
  assert.equal(getPosition(db, '0xa')!.status, 'closed');
});

test('ordersToday / deployedTodayUsd count only filled entries from the same PT day', () => {
  const db = openDb(':memory:');
  insertOrder(db, entryOrder('a', NOW, 10));
  insertOrder(db, entryOrder('b', NOW, 20));
  insertOrder(db, entryOrder('c', NOW, 30, 'failed')); // rejected — burns nothing
  insertOrder(db, entryOrder('d', NOW - 24 * 3_600_000, 40)); // yesterday PT
  assert.equal(ordersToday(db, TODAY), 2);
  assert.equal(deployedTodayUsd(db, TODAY), 30);
});

test('openPositionCount excludes closed and rugged; hasPosition is lifetime', () => {
  const db = openDb(':memory:');
  openPosition(db, { address: '0x1', ticker: 'A', opened_ms: NOW, entry_price: 1, ref_price: 1, stake_usd: 10, tokens_total: 10 });
  openPosition(db, { address: '0x2', ticker: 'B', opened_ms: NOW, entry_price: 1, ref_price: 1, stake_usd: 10, tokens_total: 10 });
  closePosition(db, '0x2', 'rugged', NOW);
  assert.equal(openPositionCount(db), 1);
  assert.equal(hasPosition(db, '0x2'), true); // no re-entry after close
});

test('realizedCapital: starting − stakes + proceeds', () => {
  const db = openDb(':memory:');
  openPosition(db, { address: '0x1', ticker: 'A', opened_ms: NOW, entry_price: 1, ref_price: 1, stake_usd: 10, tokens_total: 10 });
  updatePosition(db, '0x1', { realized_usd: 100 });
  closePosition(db, '0x1', 'closed', NOW);
  openPosition(db, { address: '0x2', ticker: 'B', opened_ms: NOW, entry_price: 1, ref_price: 1, stake_usd: 10, tokens_total: 10 });
  // 1000 − 10 + 100 (closed winner) − 10 (open, unpaid) = 1080
  assert.equal(realizedCapital(db, 1000), 1080);
});
