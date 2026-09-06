import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCoins, dedupeCoins } from '../src/gmgn.js';

const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
const load = (name: string) => JSON.parse(fs.readFileSync(path.join(FIXTURES, name), 'utf8'));

test('parses trending payload (data.rank)', () => {
  const coins = parseCoins(load('trending.json'), 'trending');
  assert.ok(coins.length > 0);
  for (const c of coins) {
    assert.ok(c.address.startsWith('0x'));
    assert.ok(c.market_cap > 0);
    assert.equal(c.source, 'trending');
  }
});

test('parses trenches payload (completed/near_completion/new_creation), volume from volume_24h', () => {
  const raw = load('trenches.json');
  const coins = parseCoins(raw, 'trenches');
  assert.ok(coins.length > 0);
  const first = coins.find(c => c.address === raw.completed[0].address)!;
  assert.equal(first.volume_24h, raw.completed[0].volume_24h);
  // creation_timestamp is null in trenches; falls back to open_timestamp, seconds → ms
  assert.ok(first.created_at_ms !== null && first.created_at_ms > 1e12);
});

test('parses hot-searches payload ([].tokens), timestamps in ms', () => {
  const coins = parseCoins(load('hot-searches.json'), 'hot');
  assert.ok(coins.length > 0);
  assert.ok(coins[0].created_at_ms !== null && coins[0].created_at_ms > 1e12);
  assert.ok(coins[0].top10_rate !== null && coins[0].top10_rate < 1);
});

test('drops entries without address or with non-positive market cap', () => {
  const payload = { data: { rank: [
    { address: '', symbol: 'X', market_cap: 5 },
    { address: '0xabc', symbol: 'Y', market_cap: 0 },
    { address: '0xdef', symbol: 'Z', market_cap: 100 },
  ] } };
  const coins = parseCoins(payload, 't');
  assert.equal(coins.length, 1);
  assert.equal(coins[0].ticker, 'Z');
});

test('dedupeCoins keeps first occurrence per address', () => {
  const mk = (address: string, source: string) =>
    parseCoins({ data: { rank: [{ address, symbol: 'A', market_cap: 1 }] } }, source)[0];
  const deduped = dedupeCoins([mk('0x1', 'trending'), mk('0x1', 'hot'), mk('0x2', 'hot')]);
  assert.equal(deduped.length, 2);
  assert.equal(deduped[0].source, 'trending');
});
