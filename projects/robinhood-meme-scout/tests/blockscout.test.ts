import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { computeHolderCheck } from '../src/blockscout.js';

const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const load = (name: string) => JSON.parse(fs.readFileSync(path.join(FIXTURES, name), 'utf8'));

// Fixture captured live 2026-09-06 for ROBIN: 992,491,223.6 total supply, 18 decimals.
const TOTAL = 992_491_223.6;

test('computes raw and EOA-only top-10 shares against total supply', () => {
  const hc = computeHolderCheck(load('blockscout-holders.json'), TOTAL, 18)!;
  // ROBIN's raw top 10 ≈ 67.5% — dominated by the v4 PoolManager, matching
  // what wallet apps display (the "68%" from the 2026-09-06 incident)
  assert.ok(hc.raw_top10_pct > 60 && hc.raw_top10_pct < 75, `raw ${hc.raw_top10_pct}`);
  assert.ok(hc.user_top10_pct > 0 && hc.user_top10_pct < hc.raw_top10_pct);
  assert.equal(hc.sampled, 50);
});

test('names contract holders in the raw top 10 (PoolManager, Pons locker)', () => {
  const hc = computeHolderCheck(load('blockscout-holders.json'), TOTAL, 18)!;
  assert.ok(hc.contract_names.includes('PoolManager'));
  assert.ok(hc.contract_names.includes('PonsV2LaunchLocker'));
});

test('null on garbage payloads or unusable supply', () => {
  assert.equal(computeHolderCheck({}, TOTAL, 18), null);
  assert.equal(computeHolderCheck(null, TOTAL, 18), null);
  assert.equal(computeHolderCheck(load('blockscout-holders.json'), 0, 18), null);
  assert.equal(computeHolderCheck(load('blockscout-holders.json'), null, 18), null);
});
