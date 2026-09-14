import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { builtinExecute, externalExecute, type Order } from '../src/executor.js';
import { loadStrategy } from '../src/config.js';

const s = loadStrategy();
const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');

function order(overrides: Partial<Order> = {}): Order {
  return {
    order_id: 'o_test_1', side: 'buy', token_address: '0xabc', ticker: 'T',
    amount_usd: 10, token_amount: null, ref_price_usd: 0.001, max_slippage_pct: 5, deadline_s: 1800,
    ...overrides,
  };
}

test('builtin buy: impact above live price, fee on input, token math', () => {
  const f = builtinExecute(order(), { price_usd: 0.001, liquidity_usd: 100_000 }, s);
  assert.equal(f.status, 'filled');
  // $10 into $100k LP = 0.01% impact
  assert.ok(Math.abs(f.fill_price_usd - 0.001 * 1.0001) < 1e-12);
  assert.ok(Math.abs(f.fee_usd - 0.03) < 1e-9); // 0.3% of $10
  assert.ok(Math.abs(f.token_amount - 9.97 / f.fill_price_usd) < 1e-6);
  assert.equal(f.usd_value, 10);
});

test('builtin sell: impact below live price, fee on proceeds', () => {
  const f = builtinExecute(order({ side: 'sell', amount_usd: null, token_amount: 10_000 }), { price_usd: 0.001, liquidity_usd: 100_000 }, s);
  assert.equal(f.status, 'filled');
  assert.ok(f.fill_price_usd < 0.001);
  const gross = 10_000 * f.fill_price_usd;
  assert.ok(Math.abs(f.usd_value - gross * 0.997) < 1e-9);
});

test('builtin fails on slippage breach and on dead market', () => {
  // live price 10% above ref → buy slippage > 5%
  const slip = builtinExecute(order(), { price_usd: 0.0011, liquidity_usd: 100_000 }, s);
  assert.equal(slip.status, 'failed');
  assert.match(slip.error!, /slippage/);
  const dead = builtinExecute(order(), null, s);
  assert.equal(dead.status, 'failed');
  assert.match(dead.error!, /no live market/);
});

test('external stub roundtrip preserves order_id, stamps source', async () => {
  const f = await externalExecute(order(), { command: path.join(FIXTURES, 'stub-wrapper.sh') });
  assert.equal(f.status, 'filled');
  assert.equal(f.order_id, 'o_test_1');
  assert.equal(f.source, 'external');
  assert.equal(f.token_amount, 4985);
  assert.equal(f.tx_ref, 'stub');
});

test('external garbage stdout and missing command fail soft, never throw', async () => {
  const bad = await externalExecute(order(), { command: path.join(FIXTURES, 'bad-wrapper.sh') });
  assert.equal(bad.status, 'failed');
  assert.match(bad.error!, /not valid JSON/);
  const missing = await externalExecute(order(), { command: '/nonexistent/wrapper' });
  assert.equal(missing.status, 'failed');
});
