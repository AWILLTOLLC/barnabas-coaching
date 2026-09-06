import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatAlert, formatHeartbeat, sendDM } from '../src/alerts.js';
import type { Coin } from '../src/gmgn.js';
import type { Evaluation } from '../src/filters.js';

const coin: Coin = {
  address: '0xdeadbeef', name: 'Test Coin', ticker: 'TEST',
  price_usd: 0.001, market_cap: 8_000_000, volume_24h: 1_500_000,
  liquidity_usd: 120_000, holder_count: 900, top10_rate: 0.15,
  created_at_ms: Date.now() - 48 * 3_600_000,
  renounced_mint: true, renounced_freeze: true, burn_status: 'yes',
  wash_trading: false, launchpad: 'pons_v2',
  twitter: 'https://x.com/test', website: null, source: 'trending',
};
const ev: Evaluation = { passed: true, score: 100, reasons: ['passed gates (+40)'], flags: [] };

test('formatAlert includes essentials', () => {
  const msg = formatAlert(coin, ev);
  assert.ok(msg.includes('TEST'));
  assert.ok(msg.includes('100/100'));
  assert.ok(msg.includes('0xdeadbeef'));
  assert.ok(msg.includes('gmgn.ai'));
  assert.ok(msg.includes('8.0M'));
});

test('formatHeartbeat includes counts', () => {
  const msg = formatHeartbeat({ scanned: 120, passed_gates: 3, alerted: ['TEST'], best: { ticker: 'FOO', score: 65 }, since: '6:00' });
  assert.ok(msg.includes('120'));
  assert.ok(msg.includes('FOO'));
});

test('sendDM dry-run succeeds without network', async () => {
  const res = await sendDM('hello', { dryRun: true });
  assert.equal(res.success, true);
});
