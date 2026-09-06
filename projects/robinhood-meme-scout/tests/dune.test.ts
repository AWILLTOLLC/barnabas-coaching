import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fetchCreatorHistory, type DuneConfig } from '../src/dune.js';

const CFG: DuneConfig = { enabled: true, query_id: 12345, timeout_ms: 5000, poll_interval_ms: 1 };

function fakeFetch(responses: { status: number; body: unknown }[]): typeof fetch {
  let i = 0;
  return (async () => {
    const r = responses[Math.min(i++, responses.length - 1)];
    return { ok: r.status < 400, status: r.status, json: async () => r.body } as Response;
  }) as typeof fetch;
}

test('executes query, polls to completion, maps first row', async () => {
  const rows = [{ deployer: '0xabc', total_launches: 5, first_launch: '2026-08-12 10:00', last_launch: '2026-09-05 01:00' }];
  const f = fakeFetch([
    { status: 200, body: { execution_id: 'exec1' } },
    { status: 200, body: { state: 'QUERY_STATE_EXECUTING' } },
    { status: 200, body: { state: 'QUERY_STATE_COMPLETED', result: { rows } } },
  ]);
  const h = await fetchCreatorHistory('0xTOKEN', CFG, 'key', f);
  assert.equal(h?.deployer, '0xabc');
  assert.equal(h?.total_launches, 5);
  assert.equal(h?.first_launch, '2026-08-12 10:00');
});

test('null on API errors, failed executions, and empty results', async () => {
  assert.equal(await fetchCreatorHistory('0xT', CFG, 'key', fakeFetch([{ status: 402, body: {} }])), null);
  assert.equal(await fetchCreatorHistory('0xT', CFG, 'key', fakeFetch([
    { status: 200, body: { execution_id: 'e' } },
    { status: 200, body: { state: 'QUERY_STATE_FAILED' } },
  ])), null);
  assert.equal(await fetchCreatorHistory('0xT', CFG, 'key', fakeFetch([
    { status: 200, body: { execution_id: 'e' } },
    { status: 200, body: { state: 'QUERY_STATE_COMPLETED', result: { rows: [] } } },
  ])), null);
});

test('gives up after timeout while execution stays pending', async () => {
  const f = fakeFetch([
    { status: 200, body: { execution_id: 'e' } },
    { status: 200, body: { state: 'QUERY_STATE_EXECUTING' } },
  ]);
  const h = await fetchCreatorHistory('0xT', { ...CFG, timeout_ms: 20 }, 'key', f);
  assert.equal(h, null);
});
