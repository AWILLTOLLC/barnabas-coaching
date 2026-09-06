import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { Monitor } from '../src/monitor.js';
import type { Coin } from '../src/gmgn.js';

function coin(address: string, overrides: Partial<Coin> = {}): Coin {
  return {
    address, name: 'T', ticker: `T${address.slice(-2)}`,
    price_usd: 0.001, market_cap: 8_000_000, volume_24h: 2_000_000,
    liquidity_usd: 200_000, holder_count: 900, top10_rate: 0.1,
    created_at_ms: Date.now() - 48 * 3_600_000,
    renounced_mint: true, renounced_freeze: true, burn_status: 'yes',
    wash_trading: false, launchpad: null, twitter: null, website: null,
    source: 'trending',
    ...overrides,
  };
}

test('scanOnce evaluates, alerts on high scores, dedupes known addresses', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const coins = [
    coin('0x01'),                                     // score 100 → alert
    coin('0x02', { market_cap: 100_000 }),            // fails gates
    coin('0x03', { volume_24h: 0, liquidity_usd: 0 }), // passes gates, low score
  ];
  const mon = new Monitor({ dryRun: true, dataDir: dir, fetch: async () => coins });

  const r1 = await mon.scanOnce();
  assert.equal(r1.scanned, 3);
  assert.equal(r1.passed_gates, 2);
  assert.deepEqual(r1.alerted, ['T01']);
  assert.equal(r1.best?.ticker, 'T03');

  // second scan: 0x01 now known, no re-alert
  const r2 = await mon.scanOnce();
  assert.deepEqual(r2.alerted, []);

  // known list persisted
  const known = JSON.parse(fs.readFileSync(path.join(dir, 'known.json'), 'utf8'));
  assert.ok(known.includes('0x01'));
});
