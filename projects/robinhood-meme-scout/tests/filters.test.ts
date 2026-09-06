import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluate } from '../src/filters.js';
import { loadCriteria } from '../src/config.js';
import type { Coin } from '../src/gmgn.js';

const criteria = loadCriteria();
const NOW = Date.parse('2026-09-05T12:00:00Z');
const hoursAgo = (h: number) => NOW - h * 3_600_000;

function coin(overrides: Partial<Coin> = {}): Coin {
  return {
    address: '0xabc', name: 'Test', ticker: 'TEST',
    price_usd: 0.001, market_cap: 1_000_000, volume_24h: 600_000,
    liquidity_usd: 60_000, holder_count: 500, top10_rate: 0.25,
    created_at_ms: hoursAgo(48), price_change_6h_pct: -5,
    renounced_mint: null, renounced_freeze: null, burn_status: null,
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
    ...overrides,
  };
}

test('gates reject: too young, too old, unknown age', () => {
  assert.equal(evaluate(coin({ created_at_ms: hoursAgo(10) }), criteria, NOW).passed, false);
  assert.equal(evaluate(coin({ created_at_ms: hoursAgo(200) }), criteria, NOW).passed, false);
  assert.equal(evaluate(coin({ created_at_ms: null }), criteria, NOW).passed, false);
});

test('gates reject: market cap outside both bands', () => {
  assert.equal(evaluate(coin({ market_cap: 100_000 }), criteria, NOW).passed, false);
  assert.equal(evaluate(coin({ market_cap: 3_000_000 }), criteria, NOW).passed, false);
  assert.equal(evaluate(coin({ market_cap: 50_000_000 }), criteria, NOW).passed, false);
});

test('gates reject: top10 concentration over max, wash trading', () => {
  assert.equal(evaluate(coin({ top10_rate: 0.5 }), criteria, NOW).passed, false);
  assert.equal(evaluate(coin({ wash_trading: true }), criteria, NOW).passed, false);
});

test('null top10 passes gates but is flagged', () => {
  const ev = evaluate(coin({ top10_rate: null }), criteria, NOW);
  assert.equal(ev.passed, true);
  assert.ok(ev.flags.includes('holders-unknown'));
});

test('fully strong coin scores 100', () => {
  const ev = evaluate(coin({
    market_cap: 10_000_000, volume_24h: 2_000_000, liquidity_usd: 200_000,
    top10_rate: 0.1, renounced_mint: true, renounced_freeze: true, burn_status: 'yes',
  }), criteria, NOW);
  assert.equal(ev.passed, true);
  assert.equal(ev.score, 100);
});

test('weak-volume coin passes gates but scores below alert threshold', () => {
  const ev = evaluate(coin({ volume_24h: 100_000, liquidity_usd: 20_000 }), criteria, NOW);
  assert.equal(ev.passed, true);
  assert.ok(ev.score < criteria.alert_score_threshold);
  assert.ok(ev.flags.includes('low-liquidity'));
});

test('mid coin: base + volume 10 + liquidity 10 = 60', () => {
  const ev = evaluate(coin(), criteria, NOW);
  assert.equal(ev.score, 60);
});
