import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DB = path.join(ROOT, 'data', 'trades.db');

test('cli buy: bad stdin JSON exits 1, records nothing', () => {
  const before = fs.existsSync(DB) ? fs.statSync(DB).size : 0;
  const r = spawnSync('tsx', ['src/cli.ts', 'buy', '--dry-run'], { cwd: ROOT, input: 'not json', encoding: 'utf8', timeout: 30_000 });
  assert.equal(r.status, 1);
  assert.match(r.stderr, /not valid ticket JSON/);
  const after = fs.existsSync(DB) ? fs.statSync(DB).size : 0;
  assert.equal(after, before);
});

test('cli buy: ticket for unknown token rejects with no-live-price, exit 1', () => {
  const ticket = JSON.stringify({ address: '0x0000000000000000000000000000000000000001', ticker: 'NOPE', price_usd: 0.001 });
  const r = spawnSync('tsx', ['src/cli.ts', 'buy', '--dry-run'], { cwd: ROOT, input: ticket, encoding: 'utf8', timeout: 60_000 });
  assert.equal(r.status, 1);
  assert.match(r.stdout, /no live price/);
});

test('cli status runs and reports capital + ladder', () => {
  const r = spawnSync('tsx', ['src/cli.ts', 'status'], { cwd: ROOT, encoding: 'utf8', timeout: 30_000 });
  assert.equal(r.status, 0);
  assert.match(r.stdout, /Realized capital: \$/);
  assert.match(r.stdout, /next stake: \$10/);
});

test('cli help lists commands', () => {
  const r = spawnSync('tsx', ['src/cli.ts'], { cwd: ROOT, encoding: 'utf8', timeout: 30_000 });
  assert.match(r.stdout, /buy\|sell\|status\|run\|contract/);
});
