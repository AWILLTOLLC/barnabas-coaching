import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { loadCriteria, loadEnv } from '../src/config.js';

test('loadCriteria reads the project criteria.json', () => {
  const c = loadCriteria();
  assert.equal(c.alert_score_threshold, 70);
  assert.equal(c.candle_age_hours.min, 24);
  assert.equal(c.candle_age_hours.max, 96);
  assert.deepEqual(c.market_cap_bands, [[500_000, 2_000_000], [5_000_000, 25_000_000]]);
  assert.deepEqual(c.heartbeat_hours_pt, [6, 10, 14, 18, 22]);
});

test('loadEnv parses KEY=VALUE, skipping comments and blanks', () => {
  const tmp = path.join(os.tmpdir(), `scout-env-${process.pid}`);
  fs.writeFileSync(tmp, '# comment\n\nGMGN_API_KEY=abc123\nOTHER=x=y\n');
  const env = loadEnv(tmp);
  fs.unlinkSync(tmp);
  assert.equal(env.GMGN_API_KEY, 'abc123');
  assert.equal(env.OTHER, 'x=y');
  assert.equal(Object.keys(env).length, 2);
});

test('loadEnv returns empty object for missing file', () => {
  assert.deepEqual(loadEnv('/nonexistent/.env'), {});
});
