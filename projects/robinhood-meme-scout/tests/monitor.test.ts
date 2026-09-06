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
    created_at_ms: Date.now() - 48 * 3_600_000, price_change_6h_pct: null, price_change_1h_pct: null,
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
  const statsCalls: string[] = [];
  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => coins,
    fetchStats: async (address) => { statsCalls.push(address); return { price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 50_000, creator_status: null, total_supply: null, decimals: null }; },
    fetchDex: async () => new Map(),
    thesis: async () => 'test thesis',
  });

  const r1 = await mon.scanOnce();
  assert.deepEqual(statsCalls, ['0x01']);
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

  // every coin (including the gate-fail) recorded once in the db
  const rows = mon.db.prepare('SELECT address, alerted, passed FROM coins ORDER BY address').all() as any[];
  assert.equal(rows.length, 3);
  assert.equal(rows.find(r => r.address === '0x01').alerted, 1);
  assert.equal(rows.find(r => r.address === '0x02').passed, 0);
});

test('finalist dumping 6h is momentum-rejected, no alert', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x09')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: -60, change_24h_pct: -80, liquidity_usd: 10_000, creator_status: null, total_supply: null, decimals: null }),
    fetchDex: async () => new Map(),
    thesis: async () => 'should not be called',
  });
  const r = await mon.scanOnce();
  assert.deepEqual(r.alerted, []);
});

test('momentum check prefers dex 6h change: dex dump rejects even when gmgn is green', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x11')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, creator_status: null, total_supply: null, decimals: null }),
    fetchDex: async () => new Map([['0x11', { price: 0.001, change_6h_pct: -60, change_24h_pct: -80, liquidity_usd: 200_000, market_cap: 8_000_000, dex_id: 'uniswap' }]]),
    thesis: async () => 'should not be called',
  });
  const r = await mon.scanOnce();
  assert.deepEqual(r.alerted, []);
});

test('source divergence is recorded in db, alert still sends (signal, not gate)', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x12')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, creator_status: null, total_supply: null, decimals: null }),
    fetchDex: async () => new Map([['0x12', { price: 0.002, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, market_cap: 8_000_000, dex_id: 'uniswap' }]]),
    thesis: async () => 'test thesis',
  });
  const r = await mon.scanOnce();
  assert.equal(r.alerted.length, 1);
  const rows = mon.db.prepare('SELECT address, field FROM divergences').all() as any[];
  assert.equal(rows.length, 1);
  assert.equal(rows[0].address, '0x12');
  assert.equal(rows[0].field, 'price');
});

test('agreeing sources record no divergence', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x13')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, creator_status: null, total_supply: null, decimals: null }),
    fetchDex: async () => new Map([['0x13', { price: 0.00102, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 210_000, market_cap: 8_000_000, dex_id: 'uniswap' }]]),
    thesis: async () => 'test thesis',
  });
  const r = await mon.scanOnce();
  assert.equal(r.alerted.length, 1);
  assert.equal((mon.db.prepare('SELECT COUNT(*) n FROM divergences').get() as any).n, 0);
});

test('v2.4: creator status lands in the alert; holder divergence recorded, not gating', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  let alertMsg = '';
  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x21')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, creator_status: 'creator_close', total_supply: 1_000_000_000, decimals: 18 }),
    fetchDex: async () => new Map(),
    fetchHolders: async () => ({ raw_top10_pct: 68, user_top10_pct: 30, contract_names: ['PoolManager'], sampled: 50 }),
    thesis: async () => 'test thesis',
  });
  (mon as any).sendAlert = undefined; // formatting goes through alerts.formatAlert
  const r = await mon.scanOnce();
  assert.equal(r.alerted.length, 1);
  // coin.top10_rate is 0.1 (10%); chain says 30% users → ratio 3 > 2 → divergence
  const rows = mon.db.prepare(`SELECT field FROM divergences`).all() as any[];
  assert.equal(rows.length, 1);
  assert.equal(rows[0].field, 'holders');
  // creator status persisted on the recorded coin snapshot
  const snap = JSON.parse((mon.db.prepare(`SELECT snapshot FROM coins WHERE address = '0x21'`).get() as any).snapshot);
  assert.equal(snap.creator_status, 'creator_close');
});

test('v2.4: agreeing holder counts record nothing', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scout-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const mon = new Monitor({
    dryRun: true, dataDir: dir, fetch: async () => [coin('0x22')],
    fetchStats: async () => ({ price: 0.001, change_6h_pct: 5, change_24h_pct: 10, liquidity_usd: 200_000, creator_status: null, total_supply: 1_000_000_000, decimals: 18 }),
    fetchDex: async () => new Map(),
    fetchHolders: async () => ({ raw_top10_pct: 68, user_top10_pct: 12, contract_names: ['PoolManager'], sampled: 50 }),
    thesis: async () => 'test thesis',
  });
  const r = await mon.scanOnce();
  assert.equal(r.alerted.length, 1);
  assert.equal((mon.db.prepare('SELECT COUNT(*) n FROM divergences').get() as any).n, 0);
});
