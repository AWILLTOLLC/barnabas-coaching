import { DatabaseSync } from 'node:sqlite';
import * as fs from 'node:fs';
import * as path from 'node:path';

export interface OrderRow {
  id: string;
  ts: number;
  pt_date: string;
  side: 'buy' | 'sell';
  address: string;
  ticker: string;
  amount_usd: number | null;
  token_amount: number | null;
  slippage_pct: number;
  status: 'pending' | 'filled' | 'failed';
  error: string | null;
  kind: 'entry' | 'moonbag' | 'tranche' | 'oneshot' | 'manual' | 'rug';
}

export interface PositionRow {
  address: string;
  ticker: string;
  opened_ms: number;
  entry_price: number; // fill price: P&L cost basis
  ref_price: number;   // scout ticket price: moon-bag trigger basis
  stake_usd: number;
  tokens_total: number;
  tokens_remaining: number;
  moonbag_done: number;
  status: 'open' | 'closed' | 'rugged';
  closed_ms: number | null;
  realized_usd: number; // total sell proceeds (USD, after fees)
  exit_tranches_done: number;
  missed_marks: number;
  pending_slippage_pct: number | null; // escalated slippage for next sell retry
}

const LA_DATE = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' });

export function ptDate(ms: number): string {
  return LA_DATE.format(new Date(ms));
}

export function openDb(file: string): DatabaseSync {
  if (file !== ':memory:') fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new DatabaseSync(file);
  db.exec(`
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY, ts INTEGER, pt_date TEXT, side TEXT, address TEXT, ticker TEXT,
      amount_usd REAL, token_amount REAL, slippage_pct REAL,
      status TEXT, error TEXT, kind TEXT
    );
    CREATE TABLE IF NOT EXISTS fills (
      order_id TEXT PRIMARY KEY, ts INTEGER, fill_price_usd REAL,
      token_amount REAL, usd_value REAL, fee_usd REAL, source TEXT
    );
    CREATE TABLE IF NOT EXISTS positions (
      address TEXT PRIMARY KEY, ticker TEXT, opened_ms INTEGER,
      entry_price REAL, ref_price REAL, stake_usd REAL,
      tokens_total REAL, tokens_remaining REAL, moonbag_done INTEGER DEFAULT 0,
      status TEXT DEFAULT 'open', closed_ms INTEGER, realized_usd REAL DEFAULT 0,
      exit_tranches_done INTEGER DEFAULT 0, missed_marks INTEGER DEFAULT 0,
      pending_slippage_pct REAL
    );
    CREATE TABLE IF NOT EXISTS marks (
      address TEXT, ts INTEGER, price_usd REAL, liquidity_usd REAL
    );
    CREATE INDEX IF NOT EXISTS idx_marks ON marks(address, ts);
    CREATE INDEX IF NOT EXISTS idx_orders_day ON orders(pt_date, kind, status);
  `);
  return db;
}

export function insertOrder(db: DatabaseSync, o: OrderRow): void {
  db.prepare(`INSERT INTO orders (id, ts, pt_date, side, address, ticker, amount_usd, token_amount, slippage_pct, status, error, kind)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(o.id, o.ts, o.pt_date, o.side, o.address, o.ticker, o.amount_usd, o.token_amount, o.slippage_pct, o.status, o.error, o.kind);
}

export function insertFill(db: DatabaseSync, f: { order_id: string; ts: number; fill_price_usd: number; token_amount: number; usd_value: number; fee_usd: number; source: string }): void {
  db.prepare(`INSERT INTO fills (order_id, ts, fill_price_usd, token_amount, usd_value, fee_usd, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)`)
    .run(f.order_id, f.ts, f.fill_price_usd, f.token_amount, f.usd_value, f.fee_usd, f.source);
}

export function openPosition(db: DatabaseSync, p: { address: string; ticker: string; opened_ms: number; entry_price: number; ref_price: number; stake_usd: number; tokens_total: number }): void {
  db.prepare(`INSERT INTO positions (address, ticker, opened_ms, entry_price, ref_price, stake_usd, tokens_total, tokens_remaining)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(p.address, p.ticker, p.opened_ms, p.entry_price, p.ref_price, p.stake_usd, p.tokens_total, p.tokens_total);
}

export function updatePosition(db: DatabaseSync, address: string, fields: Partial<PositionRow>): void {
  const keys = Object.keys(fields);
  if (!keys.length) return;
  db.prepare(`UPDATE positions SET ${keys.map(k => `${k} = ?`).join(', ')} WHERE address = ?`)
    .run(...keys.map(k => (fields as any)[k]), address);
}

export function closePosition(db: DatabaseSync, address: string, status: 'closed' | 'rugged', closed_ms: number): void {
  db.prepare(`UPDATE positions SET status = ?, closed_ms = ?, tokens_remaining = 0 WHERE address = ?`)
    .run(status, closed_ms, address);
}

export function getOpenPositions(db: DatabaseSync): PositionRow[] {
  return db.prepare(`SELECT * FROM positions WHERE status = 'open'`).all() as unknown as PositionRow[];
}

export function getPosition(db: DatabaseSync, address: string): PositionRow | undefined {
  return db.prepare('SELECT * FROM positions WHERE address = ?').get(address) as unknown as PositionRow | undefined;
}

export function openPositionCount(db: DatabaseSync): number {
  return ((db.prepare(`SELECT COUNT(*) n FROM positions WHERE status = 'open'`).get() as any).n ?? 0) as number;
}

export function hasPosition(db: DatabaseSync, address: string): boolean {
  return db.prepare('SELECT 1 FROM positions WHERE address = ?').get(address) !== undefined;
}

/** Filled entry orders today (PT). Gate-rejected/failed entries do not burn the cap. */
export function ordersToday(db: DatabaseSync, dateStr: string): number {
  return ((db.prepare(`SELECT COUNT(*) n FROM orders WHERE pt_date = ? AND kind = 'entry' AND status = 'filled'`).get(dateStr) as any).n ?? 0) as number;
}

export function deployedTodayUsd(db: DatabaseSync, dateStr: string): number {
  return ((db.prepare(`SELECT COALESCE(SUM(amount_usd), 0) n FROM orders WHERE pt_date = ? AND kind = 'entry' AND status = 'filled'`).get(dateStr) as any).n ?? 0) as number;
}

/**
 * Realized (cash) capital for the scaling ladder:
 *   starting capital − every stake deployed + every sell's proceeds.
 * Open positions count at −stake until they pay: conservative by design.
 */
export function realizedCapital(db: DatabaseSync, startingUsd: number): number {
  const row = db.prepare(`SELECT COALESCE(SUM(stake_usd), 0) staked, COALESCE(SUM(realized_usd), 0) proceeds FROM positions`).get() as any;
  return startingUsd - row.staked + row.proceeds;
}

export function insertMark(db: DatabaseSync, address: string, ts: number, price_usd: number, liquidity_usd: number): void {
  db.prepare('INSERT INTO marks (address, ts, price_usd, liquidity_usd) VALUES (?, ?, ?, ?)').run(address, ts, price_usd, liquidity_usd);
}

export function lastMark(db: DatabaseSync, address: string): { price_usd: number; liquidity_usd: number } | undefined {
  return db.prepare('SELECT price_usd, liquidity_usd FROM marks WHERE address = ? ORDER BY ts DESC LIMIT 1').get(address) as any;
}

export function pruneMarks(db: DatabaseSync, olderThanMs: number): void {
  db.prepare('DELETE FROM marks WHERE ts < ?').run(olderThanMs);
}
