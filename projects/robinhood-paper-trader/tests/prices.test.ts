import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDexBatch, fetchMarks, PRICES_DEFAULTS } from '../src/prices.js';

const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');

test('parseDexBatch: lowercase keys, positive price and liquidity', () => {
  const payload = JSON.parse(fs.readFileSync(path.join(FIXTURES, 'dexscreener-tokens.json'), 'utf8'));
  const marks = parseDexBatch(payload);
  assert.ok(marks.size > 0);
  for (const [addr, m] of marks) {
    assert.equal(addr, addr.toLowerCase());
    assert.ok(m.price_usd > 0);
    assert.ok(m.liquidity_usd > 0);
  }
});

test('gmgn fallback only for misses, capped per cycle', async () => {
  const gmgnCalls: string[] = [];
  const marks = await fetchMarks(
    ['0xA', '0xB', '0xC', '0xD', '0xE', '0xF', '0xG', '0xH'],
    {},
    { ...PRICES_DEFAULTS, gmgn_fallback_per_cycle: 5 },
    {
      dex: async () => new Map([['0xa', { price_usd: 1, liquidity_usd: 1000 }]]),
      gmgn: async (a) => { gmgnCalls.push(a); return a === '0xB' ? { price_usd: 2, liquidity_usd: 2000 } : null; },
    },
  );
  assert.equal(gmgnCalls.length, 5); // 7 misses, capped at 5
  assert.ok(!gmgnCalls.includes('0xA'));
  assert.equal(marks.get('0xb')!.price_usd, 2);
});

test('all sources down → empty map, no throw', async () => {
  const marks = await fetchMarks(['0x1'], {}, PRICES_DEFAULTS, { dex: async () => new Map(), gmgn: async () => null });
  assert.equal(marks.size, 0);
});
