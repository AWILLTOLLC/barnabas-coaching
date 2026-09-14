import { test } from 'node:test';
import assert from 'node:assert/strict';
import { stakeFor, checkEntry, moonbagDue, sellPlan } from '../src/limits.js';
import { loadStrategy } from '../src/config.js';

const s = loadStrategy();

test('ladder: base at <$1k, +$10 per $1k, capped at $100', () => {
  assert.equal(stakeFor(999, s), 10);
  assert.equal(stakeFor(1000, s), 10);
  assert.equal(stakeFor(2000, s), 20);
  assert.equal(stakeFor(5000, s), 50);
  assert.equal(stakeFor(47000, s), 100);
});

test('entry gates reject with the right reasons', () => {
  const base = { address: '0x1', liquidity_usd: 100_000, ordersToday: 0, deployedTodayUsd: 0, openPositions: 0, alreadyHasPosition: false, stakeUsd: 10 };
  assert.equal(checkEntry(base, s).ok, true);
  assert.match((checkEntry({ ...base, alreadyHasPosition: true }, s) as any).reason, /position-exists/);
  assert.match((checkEntry({ ...base, ordersToday: 25 }, s) as any).reason, /daily-order-cap/);
  assert.match((checkEntry({ ...base, deployedTodayUsd: 240, stakeUsd: 20 }, s) as any).reason, /daily-deployment-cap/);
  assert.equal(checkEntry({ ...base, deployedTodayUsd: 240, stakeUsd: 10 }, s).ok, true); // exactly at $250 is fine
  assert.match((checkEntry({ ...base, openPositions: 40 }, s) as any).reason, /open-positions-cap/);
  assert.match((checkEntry({ ...base, liquidity_usd: 900 }, s) as any).reason, /lp-entry-gate/); // $10 > 1% of $900
});

test('moonbag triggers on ref_price ×11, not entry price; fires once', () => {
  const p = { ref_price: 0.001, moonbag_done: 0 };
  assert.equal(moonbagDue(p, 0.011, s), true);
  assert.equal(moonbagDue(p, 0.0109, s), false);
  // fill slipped to 0.0012: trigger still keys off ref 0.001 — 0.011 fires even though entry×11 = 0.0132
  assert.equal(moonbagDue({ ref_price: 0.001, moonbag_done: 0 }, 0.011, s), true);
  assert.equal(moonbagDue({ ref_price: 0.001, moonbag_done: 1 }, 0.02, s), false);
});

test('oneshot below 0.5% LP fires only at the 24h boundary', () => {
  const a = { tokensRemaining: 100, price: 1, liquidity_usd: 100_000, ageHours: 23.5, tranchesDone: 0 }; // $100 = 0.1% LP
  assert.equal(sellPlan(a, s), null);
  const due = sellPlan({ ...a, ageHours: 24 }, s)!;
  assert.equal(due.kind, 'oneshot');
  assert.equal(due.tokenAmount, 100);
});

test('tranche path when ≥0.5% LP: schedule-timed, 2%-LP capped, final tranche drains', () => {
  // $1,000 position in $100k LP = 1% → tranche path; 2% LP cap = $2,000 → cap not binding
  const a = { tokensRemaining: 1000, price: 1, liquidity_usd: 100_000, ageHours: 22, tranchesDone: 0 };
  assert.equal(sellPlan(a, s), null);
  const t0 = sellPlan({ ...a, ageHours: 23 }, s)!;
  assert.equal(t0.kind, 'tranche');
  assert.equal(t0.tokenAmount, 250); // remaining/4
  const t3 = sellPlan({ ...a, tokensRemaining: 400, ageHours: 24, tranchesDone: 3 }, s)!;
  assert.equal(t3.tokenAmount, 400); // final drains all
});

test('tranche size capped at 2% of pool; keeps draining past boundary', () => {
  // $40k position in $100k LP: cap = $2,000/tranche
  const cap = sellPlan({ tokensRemaining: 40_000, price: 1, liquidity_usd: 100_000, ageHours: 23, tranchesDone: 0 }, s)!;
  assert.equal(cap.tokenAmount, 2000);
  // after all 4 tranches, still tokens at 24.1h → capped drain continues
  const drain = sellPlan({ tokensRemaining: 30_000, price: 1, liquidity_usd: 100_000, ageHours: 24.1, tranchesDone: 4 }, s)!;
  assert.equal(drain.tokenAmount, 2000);
});

test('value > $10k forces tranche path even under 0.5% LP', () => {
  // $12k position in $10M LP = 0.12% LP but > big_sell_usd
  const p = sellPlan({ tokensRemaining: 12_000, price: 1, liquidity_usd: 10_000_000, ageHours: 23, tranchesDone: 0 }, s)!;
  assert.equal(p.kind, 'tranche');
});
