import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { collectTaxLines, summarize, toCsv } from '../src/tax.js';
import { openDb, insertOrder, insertFill, insertMark } from '../src/db.js';

function seedDb() {
  const db = openDb(':memory:');
  // one position: $10 stake, 9000 tokens @ 0.001 (gross incl fee), opened Jan 2
  db.prepare(`INSERT INTO positions (address, ticker, opened_ms, entry_price, ref_price, stake_usd, tokens_total, tokens_remaining, moonbag_done, status, closed_ms, realized_usd)
              VALUES ('0xaaa','WOJAK', 1767336000000 /*2026-01-02*/, 0.001, 0.0009, 10, 9000, 0, 1, 'closed', 1767422400000 /*2026-01-03*/, 40)`).run();
  // entry order+fill
  insertOrder(db, { id: 'o1', ts: 1767336000000, pt_date: '2026-01-02', side: 'buy', address: '0xaaa', ticker: 'WOJAK', amount_usd: 10, token_amount: 9000, slippage_pct: 5, status: 'filled', error: null, kind: 'entry' });
  insertFill(db, { order_id: 'o1', ts: 1767336000000, fill_price_usd: 0.001, token_amount: 9000, usd_value: 10, fee_usd: 0.03, source: 'builtin' });
  // two disposals: 25% moonbag (2250 tokens, $30), 75% oneshot (6750 tokens, $10)
  insertOrder(db, { id: 'o2', ts: 1767420000000, pt_date: '2026-01-03', side: 'sell', address: '0xaaa', ticker: 'WOJAK', amount_usd: null, token_amount: 2250, slippage_pct: 5, status: 'filled', error: null, kind: 'moonbag' });
  insertFill(db, { order_id: 'o2', ts: 1767420000000, fill_price_usd: 0.0134, token_amount: 2250, usd_value: 30, fee_usd: 0.09, source: 'builtin' });
  insertOrder(db, { id: 'o3', ts: 1767422400000, pt_date: '2026-01-03', side: 'sell', address: '0xaaa', ticker: 'WOJAK', amount_usd: null, token_amount: 6750, slippage_pct: 5, status: 'filled', error: null, kind: 'oneshot' });
  insertFill(db, { order_id: 'o3', ts: 1767422400000, fill_price_usd: 0.00148, token_amount: 6750, usd_value: 10, fee_usd: 0.03, source: 'builtin' });
  // one rugged position: $10 stake, never sold, realized 0
  db.prepare(`INSERT INTO positions (address, ticker, opened_ms, entry_price, ref_price, stake_usd, tokens_total, tokens_remaining, status, closed_ms, realized_usd)
              VALUES ('0xbbb','RUGGED', 1767420000000, 0.002, 0.002, 10, 5000, 5000, 'rugged', 1767506400000 /*2026-01-04*/, 0)`).run();
  // a mark so prune-style queries don't matter
  insertMark(db, '0xaaa', 1767420000000, 0.0134, 100000);
  return db;
}

describe('tax', () => {
  it('emits one line per disposal with proportional basis', () => {
    const db = seedDb();
    const s = summarize(collectTaxLines(db));
    assert.equal(s.lines.length, 3); // moonbag, oneshot, rug
    const moonbag = s.lines.find(l => l.disposal_kind === 'moonbag')!;
    assert.equal(moonbag.proceeds_usd, 30);
    assert.ok(Math.abs(moonbag.basis_usd - 2.5) < 1e-9); // 10 * 2250/9000
    assert.ok(Math.abs(moonbag.gain_usd - 27.5) < 1e-9);
    const oneshot = s.lines.find(l => l.disposal_kind === 'oneshot')!;
    assert.ok(Math.abs(oneshot.basis_usd - 7.5) < 1e-9);
    const rug = s.lines.find(l => l.disposal_kind === 'rugged')!;;
    assert.equal(rug.proceeds_usd, 0);
    assert.ok(Math.abs(rug.basis_usd - 10) < 1e-9);
    // everything short-term
    assert.equal(s.long_term_count, 0);
    assert.equal(s.short_term_count, 3);
  });

  it('totals line up and csv contains box C header and totals row', () => {
    const db = seedDb();
    const s = summarize(collectTaxLines(db));
    assert.ok(Math.abs(s.total_gain_usd - (s.total_proceeds_usd - s.total_basis_usd)) < 1e-9);
    const csv = toCsv(s, 2026);
    assert.match(csv, /Box C/);
    assert.match(csv, /TOTAL \(Schedule D line 4/);
    assert.equal(csv.split('\n').filter(r => r.startsWith('(a)')).length, 1);
  });

  it('year filter excludes other years', () => {
    const db = seedDb();
    const s = summarize(collectTaxLines(db));
    assert.equal(yearLinesEmptyHelper(s, 2025).length, 0);
    assert.equal(yearLinesEmptyHelper(s, 2026).length, 3);
  });
});

function yearLinesEmptyHelper(s: ReturnType<typeof summarize>, year: number) {
  return s.lines.filter(l => l.date_sold.startsWith(String(year)));
}
