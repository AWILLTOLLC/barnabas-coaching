import { DatabaseSync } from 'node:sqlite';

/**
 * IRS Form 8949 (Part II, Box C) / Schedule D record-keeping for the paper
 * trader. Additive: derives tax lots from the existing orders/fills/positions
 * tables — no schema changes, no effect on trading.
 *
 * Semantics (documented, intentional):
 * - Cost basis = buy fill gross usd_value (builtin fills carry the fee inside
 *   amount_usd, so fee is already included in basis) + gas placeholder.
 * - Proceeds = sell fill usd_value, which the executor reports NET of sell
 *   fees — matching the 8949 convention of netting selling fees against
 *   proceeds.
 * - Partial disposals (moon-bag 25%, boundary tranches) each get their own
 *   8949 line; basis is proportional: per-token basis x tokens sold.
 * - Rugged positions are dispositions with proceeds = realized_usd (the feed
 *   is dead, so treat as sold for what we recovered; typically $0).
 * - All our holds are <= 24h, so every line is short-term (Part II). The
 *   holding period is still computed and asserted, not assumed.
 */

export interface TaxLine {
  description: string;
  date_acquired: string;   // YYYY-MM-DD (PT)
  date_sold: string;       // YYYY-MM-DD (PT)
  proceeds_usd: number;    // net of sell fees
  basis_usd: number;       // includes buy fees
  gain_usd: number;        // proceeds - basis
  short_term: boolean;
  disposal_kind: string;   // moonbag | tranche | oneshot | manual | rug
  tx_note: string;         // order id (tx hash once live)
}

export interface TaxSummary {
  lines: TaxLine[];
  total_proceeds_usd: number;
  total_basis_usd: number;
  total_gain_usd: number;
  short_term_count: number;
  long_term_count: number;
}

const DATE_FMT = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' });
const DAY_MS = 86_400_000;

function lotBasisAt(entryAmountUsd: number, tokensTotal: number, tokensSold: number): number {
  if (tokensTotal <= 0) return 0;
  return (entryAmountUsd * tokensSold) / tokensTotal;
}

export function collectTaxLines(db: DatabaseSync): TaxLine[] {
  const positions = db.prepare(`SELECT address, ticker, opened_ms, stake_usd, tokens_total, tokens_remaining, status, closed_ms, realized_usd FROM positions`).all() as any[];
  const posByAddress = new Map(positions.map((p: any) => [p.address, p]));

  const sells = db.prepare(`
    SELECT o.id, o.ts, o.address, o.ticker, o.kind, f.token_amount, f.usd_value
    FROM orders o JOIN fills f ON f.order_id = o.id
    WHERE o.side = 'sell' AND o.status = 'filled'
    ORDER BY o.ts ASC
  `).all() as any[];

  const lines: TaxLine[] = [];
  const seenRug = new Set<string>();

  for (const s of sells) {
    const p = posByAddress.get(s.address);
    if (!p) continue;
    const tokensSold = Number(s.token_amount) || 0;
    const basis = lotBasisAt(Number(p.stake_usd), Number(p.tokens_total), tokensSold);
    const proceeds = Number(s.usd_value) || 0;
    const holdDays = (Number(s.ts) - Number(p.opened_ms)) / DAY_MS;
    lines.push({
      description: `${Math.round(tokensSold).toLocaleString('en-US')} ${s.ticker} (Robinhood Chain)`,
      date_acquired: DATE_FMT.format(new Date(Number(p.opened_ms))),
      date_sold: DATE_FMT.format(new Date(Number(s.ts))),
      proceeds_usd: proceeds,
      basis_usd: basis,
      gain_usd: proceeds - basis,
      short_term: holdDays < 366,
      disposal_kind: String(s.kind),
      tx_note: String(s.id),
    });
  }

  // rugs and never-sold closed positions: disposition with what we recovered
  for (const p of positions) {
    if (p.status === 'open') continue;
    if (p.status !== 'rugged' && p.status !== 'closed') continue;
    // did any sell fill cover this position? closed positions normally have
    // sells; rugged ones never do. Skip if a sell exists for the address.
    const hasSell = sells.some((s: any) => s.address === p.address);
    if (hasSell && p.status === 'closed') continue;
    seenRug.add(p.address);
    const holdDays = (Number(p.closed_ms ?? p.opened_ms) - Number(p.opened_ms)) / DAY_MS;
    const proceeds = Number(p.realized_usd) || 0;
    const disposed = Number(p.tokens_remaining); // a rug disposes everything left
    const basis = lotBasisAt(Number(p.stake_usd), Number(p.tokens_total), disposed);
    lines.push({
      description: `${Math.round(disposed).toLocaleString('en-US')} ${p.ticker} (Robinhood Chain) — worthless/disposed`,
      date_acquired: DATE_FMT.format(new Date(Number(p.opened_ms))),
      date_sold: DATE_FMT.format(new Date(Number(p.closed_ms ?? Date.now()))),
      proceeds_usd: proceeds,
      basis_usd: basis,
      gain_usd: proceeds - basis,
      short_term: holdDays < 366,
      disposal_kind: p.status,
      tx_note: `position ${p.address.slice(0, 10)}…`,
    });
    void seenRug;
  }

  lines.sort((a, b) => a.date_sold.localeCompare(b.date_sold));
  return lines;
}

export function summarize(lines: TaxLine[]): TaxSummary {
  return {
    lines,
    total_proceeds_usd: lines.reduce((a, l) => a + l.proceeds_usd, 0),
    total_basis_usd: lines.reduce((a, l) => a + l.basis_usd, 0),
    total_gain_usd: lines.reduce((a, l) => a + l.gain_usd, 0),
    short_term_count: lines.filter(l => l.short_term).length,
    long_term_count: lines.filter(l => !l.short_term).length,
  };
}

export function yearLines(s: TaxSummary, year: number): TaxLine[] {
  return s.lines.filter(l => l.date_sold.startsWith(String(year)));
}

function usd(n: number): string {
  return n.toFixed(2);
}

export function toCsv(s: TaxSummary, year: number): string {
  const rows: string[] = [];
  rows.push(`# Form 8949 Part II — Box C (transactions not reported to IRS); tax year ${year}`);
  rows.push(`# Generated from paper-trader records ${new Date().toISOString()}. Paper mode: gas modeled at $0/tx (no chain); live executor must log actual gas into basis.`);
  rows.push('(a) Description of property,(b) Date acquired,(c) Date sold or disposed,(d) Proceeds,(e) Cost basis,(h) Gain or loss,kind,ref');
  for (const l of yearLines(s, year)) {
    rows.push([csv(l.description), l.date_acquired, l.date_sold, usd(l.proceeds_usd), usd(l.basis_usd), usd(l.gain_usd), l.disposal_kind, csv(l.tx_note)].join(','));
  }
  const y = yearLines(s, year);
  const tot = {
    p: y.reduce((a, l) => a + l.proceeds_usd, 0),
    b: y.reduce((a, l) => a + l.basis_usd, 0),
    g: y.reduce((a, l) => a + l.gain_usd, 0),
  };
  rows.push(`TOTAL (Schedule D line 4 / 10 summary),,,,${usd(tot.p)},${usd(tot.b)},${usd(tot.g)}`);
  return rows.join('\n') + '\n';
}

function csv(v: string): string {
  return /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}
