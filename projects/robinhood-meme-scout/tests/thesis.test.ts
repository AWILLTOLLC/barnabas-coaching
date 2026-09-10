import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildThesisPrompt } from '../src/thesis.js';
import { parseTokenStats } from '../src/gmgn.js';
import { evaluate } from '../src/filters.js';
import { loadCriteria } from '../src/config.js';
import type { Coin } from '../src/gmgn.js';

const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');

const coin: Coin = {
  address: '0xdeadbeef', name: 'Chrome Cat', ticker: 'CHROME',
  price_usd: 0.001, market_cap: 639_000, volume_24h: 3_100_000,
  liquidity_usd: 208_000, holder_count: 2659, top10_rate: 0.18,
  created_at_ms: Date.now() - 38 * 3_600_000, price_change_6h_pct: -12.5, price_change_1h_pct: null,
  renounced_mint: null, renounced_freeze: null, burn_status: 'yes',
  wash_trading: false, launchpad: 'longxyz',
  twitter: 'https://x.com/CatOnChrome', website: null, source: 'trending',
};

test('parseTokenStats computes 6h/24h change from token info payload', () => {
  const payload = JSON.parse(fs.readFileSync(path.join(FIXTURES, 'token-info.json'), 'utf8'));
  const stats = parseTokenStats(payload)!;
  assert.ok(Math.abs(stats.change_6h_pct - -32.35) < 0.5);
  assert.ok(stats.change_24h_pct < 0);
});

test('parseTokenStats returns null on garbage', () => {
  assert.equal(parseTokenStats({}), null);
  assert.equal(parseTokenStats(null), null);
});

test('momentum gate: dumping coin rejected, mild dip passes, unknown flagged', () => {
  const c = loadCriteria();
  const dumping = evaluate({ ...coin, price_change_6h_pct: -45 }, c);
  assert.equal(dumping.passed, false);
  assert.ok(dumping.reasons[0].includes('6h'));

  const mild = evaluate({ ...coin, price_change_6h_pct: -10 }, c);
  assert.equal(mild.passed, true);

  const unknown = evaluate({ ...coin, price_change_6h_pct: null }, c);
  assert.equal(unknown.passed, true);
  assert.ok(unknown.flags.includes('momentum-unknown'));
});

test('buildThesisPrompt contains facts, rules, and chain context', () => {
  const c = loadCriteria();
  const ev = evaluate(coin, c);
  const prompt = buildThesisPrompt(coin, ev, c);
  assert.ok(prompt.includes('CHROME'));
  assert.ok(prompt.includes('Chrome Cat'));
  assert.ok(prompt.includes('longxyz'));
  assert.ok(prompt.includes('CatOnChrome'));
  assert.ok(prompt.includes('-12.5'));
  assert.ok(/no invented facts/i.test(prompt));
  assert.ok(/no buy\/sell advice/i.test(prompt));
  assert.ok(prompt.includes('Robinhood Chain'));
});

test('meta note appears only for coins whose name/ticker matches a meta keyword', () => {
  const c = loadCriteria();
  const ev = evaluate(coin, c);
  // "Chrome Cat" matches the cat meta
  assert.ok(buildThesisPrompt(coin, ev, c).includes('Cash Cat'));
  // a non-cat coin never sees the cat narrative
  const dark = { ...coin, name: 'DarkRoute', ticker: 'DARK', twitter: null };
  assert.ok(!buildThesisPrompt(dark, evaluate(dark, c), c).includes('Cash Cat'));
});

test('launch venue is labeled shared infrastructure and score marked not-evidence', () => {
  const c = loadCriteria();
  const prompt = buildThesisPrompt(coin, evaluate(coin, c), c);
  assert.ok(prompt.includes('shared launch infrastructure'));
  assert.ok(/never use it as evidence/i.test(prompt));
  assert.ok(/Never cite scout_score/.test(prompt));
});

test('liquidity peer verdict line drives the liquidity rule', () => {
  const c = loadCriteria();
  const ev = evaluate(coin, c);
  const withPeers = buildThesisPrompt(coin, ev, c, {
    liqPeers: { n: 59, ratio_pct: 6.9, p25_pct: 7.9, median_pct: 10.6, p75_pct: 14.9, verdict: 'below typical' },
  });
  assert.ok(withPeers.includes('verdict: below typical'));
  assert.ok(withPeers.includes('peer median 10.6%'));
  assert.ok(/MUST NOT be described as thin/.test(withPeers));

  const without = buildThesisPrompt(coin, ev, c);
  assert.ok(without.includes('liquidity_vs_band_peers: unknown'));
});
