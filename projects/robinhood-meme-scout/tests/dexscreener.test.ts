import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseTokenBatch, checkDivergence, type DexStats } from '../src/dexscreener.js';

const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const load = (name: string) => JSON.parse(fs.readFileSync(path.join(FIXTURES, name), 'utf8'));

test('parses tokens/v1 batch payload keyed by lowercase base token address', () => {
  const stats = parseTokenBatch(load('dexscreener-tokens.json'));
  assert.equal(stats.size, 2);
  const s = stats.get('0x020bfc650a365f8bb26819deaabf3e21291018b4')!;
  assert.ok(s.price > 0);
  assert.ok(s.liquidity_usd !== null && s.liquidity_usd > 1_000_000);
  assert.ok(typeof s.change_6h_pct === 'number');
  assert.ok(s.market_cap !== null && s.market_cap > 0);
});

test('multiple pools for one token: deepest liquidity wins', () => {
  const base = load('dexscreener-tokens.json')[0];
  const shallow = { ...base, dexId: 'giga', priceUsd: '0.5', liquidity: { usd: 100 } };
  const deep = { ...base, dexId: 'uniswap', priceUsd: '0.2', liquidity: { usd: 9_999_999 } };
  const stats = parseTokenBatch([shallow, deep]);
  const s = stats.get(base.baseToken.address.toLowerCase())!;
  assert.equal(s.dex_id, 'uniswap');
  assert.equal(s.price, 0.2);
});

test('tolerates missing priceChange/liquidity/marketCap; drops pairs without usable price', () => {
  const bare = { chainId: 'robinhood', dexId: 'uniswap', baseToken: { address: '0xAA' }, priceUsd: '1.5' };
  const noPrice = { chainId: 'robinhood', dexId: 'uniswap', baseToken: { address: '0xBB' } };
  const stats = parseTokenBatch([bare, noPrice]);
  const s = stats.get('0xaa')!;
  assert.equal(s.price, 1.5);
  assert.equal(s.change_6h_pct, null);
  assert.equal(s.liquidity_usd, null);
  assert.equal(s.market_cap, null);
  assert.equal(stats.has('0xbb'), false);
});

test('garbage payloads produce empty maps', () => {
  for (const p of [null, undefined, {}, 'x', 42, { pairs: 3 }]) {
    assert.equal(parseTokenBatch(p).size, 0);
  }
});

test('checkDivergence flags >25% relative price diff or >2x liquidity gap, null-safe', () => {
  const dex: DexStats = { price: 1.0, change_6h_pct: 0, change_24h_pct: 0, liquidity_usd: 100_000, market_cap: null, dex_id: 'uniswap' };
  const gmgn = { price: 1.1, change_6h_pct: 0, change_24h_pct: 0, liquidity_usd: 150_000, creator_status: null, total_supply: null, decimals: null };
  assert.equal(checkDivergence(dex, gmgn, 25), null);
  assert.equal(checkDivergence(dex, { ...gmgn, price: 2.0 }, 25), 'price');
  assert.equal(checkDivergence(dex, { ...gmgn, liquidity_usd: 250_000 }, 25), 'liquidity');
  // unknown liquidity on either side is not divergence
  assert.equal(checkDivergence({ ...dex, liquidity_usd: null }, gmgn, 25), null);
  assert.equal(checkDivergence(dex, { ...gmgn, liquidity_usd: null }, 25), null);
});
