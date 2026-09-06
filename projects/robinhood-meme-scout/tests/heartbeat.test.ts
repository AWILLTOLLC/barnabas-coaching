import { test } from 'node:test';
import assert from 'node:assert/strict';
import { laParts, dueSlot } from '../src/heartbeat.js';

const HOURS = [6, 10, 14, 18, 22];
// 2026-09-05 is during PDT (UTC-7): 13:00Z == 06:00 PDT
const at = (utc: string) => new Date(utc);

test('laParts converts UTC to LA date/hour', () => {
  const p = laParts(at('2026-09-05T13:00:00Z'));
  assert.equal(p.date, '2026-09-05');
  assert.equal(p.hour, 6);
  const q = laParts(at('2026-09-05T06:00:00Z')); // 11pm Sep 4 PDT
  assert.equal(q.date, '2026-09-04');
  assert.equal(q.hour, 23);
});

test('6am PDT with nothing sent → slot 6', () => {
  assert.equal(dueSlot(at('2026-09-05T13:00:00Z'), null, HOURS), 6);
});

test('9am PDT with slot 6 already sent today → null', () => {
  assert.equal(dueSlot(at('2026-09-05T16:30:00Z'), { date: '2026-09-05', slot: 6 }, HOURS), null);
});

test('11:30am PDT with slot 6 sent → slot 10 due', () => {
  assert.equal(dueSlot(at('2026-09-05T18:30:00Z'), { date: '2026-09-05', slot: 6 }, HOURS), 10);
});

test('quiet hours: 11pm and 3am PDT → null even with nothing sent', () => {
  assert.equal(dueSlot(at('2026-09-06T06:00:00Z'), null, HOURS), null); // 11pm PDT
  assert.equal(dueSlot(at('2026-09-05T10:00:00Z'), null, HOURS), null); // 3am PDT
});

test('restart after downtime at 3:05pm PDT sends only slot 14 (no backfill)', () => {
  assert.equal(dueSlot(at('2026-09-05T22:05:00Z'), { date: '2026-09-05', slot: 6 }, HOURS), 14);
});

test('new day resets: 6am with yesterday slot 22 sent → slot 6', () => {
  assert.equal(dueSlot(at('2026-09-05T13:00:00Z'), { date: '2026-09-04', slot: 22 }, HOURS), 6);
});

test('10pm slot fires during hour 22, silent at hour 23', () => {
  assert.equal(dueSlot(at('2026-09-06T05:30:00Z'), { date: '2026-09-05', slot: 18 }, HOURS), 22); // 10:30pm PDT
  assert.equal(dueSlot(at('2026-09-06T06:30:00Z'), { date: '2026-09-05', slot: 18 }, HOURS), null); // 11:30pm PDT
});
