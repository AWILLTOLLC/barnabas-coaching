import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { loadStrategy, loadEnv } from '../src/config.js';

test('loadStrategy reads the project strategy.json', () => {
  const s = loadStrategy();
  assert.equal(s.base_stake_usd, 10);
  assert.equal(s.max_stake_usd, 100);
  assert.equal(s.max_daily_deployment_usd, 250);
  assert.equal(s.max_open_positions, 40);
  assert.equal(s.exit.tranche_schedule_hours.length, 4);
  assert.equal(s.executor.type, 'builtin');
  assert.equal(s.moonbag.trigger_pct, 1000);
});

test('loadEnv parses KEY=VALUE, skipping comments and blanks', () => {
  const tmp = path.join(os.tmpdir(), `pt-env-${process.pid}`);
  fs.writeFileSync(tmp, '# c\n\nGMGN_API_KEY=abc\n');
  const env = loadEnv(tmp);
  fs.unlinkSync(tmp);
  assert.equal(env.GMGN_API_KEY, 'abc');
});
