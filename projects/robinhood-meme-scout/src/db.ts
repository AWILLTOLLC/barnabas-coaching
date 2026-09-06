import { DatabaseSync } from 'node:sqlite';
import * as fs from 'node:fs';
import * as path from 'node:path';
import type { Coin } from './gmgn.js';
import type { Evaluation } from './filters.js';

export const HORIZONS_H = [1, 6, 24, 72, 168];

export interface DueOutcome {
  id: number;
  address: string;
  horizon_h: number;
  attempts: number;
}

export function openDb(file: string): DatabaseSync {
  if (file !== ':memory:') fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new DatabaseSync(file);
  db.exec(`
    CREATE TABLE IF NOT EXISTS coins (
      address TEXT PRIMARY KEY,
      ticker TEXT, name TEXT,
      first_seen_ms INTEGER,
      price_at_eval REAL, market_cap REAL, liquidity REAL,
      score INTEGER, passed INTEGER, alerted INTEGER,
      reasons TEXT, flags TEXT, snapshot TEXT
    );
    CREATE TABLE IF NOT EXISTS outcomes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      address TEXT, horizon_h INTEGER,
      due_ms INTEGER, captured_ms INTEGER,
      price REAL, liquidity REAL,
      status TEXT DEFAULT 'pending',
      attempts INTEGER DEFAULT 0,
      UNIQUE(address, horizon_h)
    );
    CREATE INDEX IF NOT EXISTS idx_outcomes_due ON outcomes(status, due_ms);
    CREATE TABLE IF NOT EXISTS regime_snapshots (
      ts INTEGER, n INTEGER, median_1h_pct REAL, green_share REAL,
      total_volume_24h REAL, new_launches_1h INTEGER,
      raw_label TEXT, confirmed_label TEXT
    );
  `);
  try {
    db.exec(`ALTER TABLE coins ADD COLUMN regime TEXT DEFAULT 'neutral'`);
  } catch {
    // column already exists
  }
  return db;
}

export function recordRegimeSnapshot(
  db: DatabaseSync, ts: number,
  b: { n: number; median_1h_pct: number; green_share: number; total_volume_24h: number; new_launches_1h: number },
  raw: string, confirmed: string,
): void {
  db.prepare(`INSERT INTO regime_snapshots (ts, n, median_1h_pct, green_share, total_volume_24h, new_launches_1h, raw_label, confirmed_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(ts, b.n, b.median_1h_pct, b.green_share, b.total_volume_24h, b.new_launches_1h, raw, confirmed);
}

export function lastConfirmedRegime(db: DatabaseSync): string | null {
  const row = db.prepare('SELECT confirmed_label FROM regime_snapshots ORDER BY ts DESC LIMIT 1').get() as any;
  return row?.confirmed_label ?? null;
}

export function hasCoin(db: DatabaseSync, address: string): boolean {
  return db.prepare('SELECT 1 FROM coins WHERE address = ?').get(address) !== undefined;
}

export function recordCoin(db: DatabaseSync, coin: Coin, ev: Evaluation, alerted: boolean, now: number, regime: string = 'neutral'): void {
  if (hasCoin(db, coin.address)) return;
  db.prepare(`INSERT INTO coins (address, ticker, name, first_seen_ms, price_at_eval, market_cap, liquidity, score, passed, alerted, reasons, flags, snapshot, regime)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
    coin.address, coin.ticker, coin.name, now,
    coin.price_usd, coin.market_cap, coin.liquidity_usd,
    ev.score, ev.passed ? 1 : 0, alerted ? 1 : 0,
    JSON.stringify(ev.reasons), JSON.stringify(ev.flags), JSON.stringify(coin), regime,
  );
  const ins = db.prepare('INSERT INTO outcomes (address, horizon_h, due_ms) VALUES (?, ?, ?)');
  for (const h of HORIZONS_H) ins.run(coin.address, h, now + h * 3_600_000);
}

export function dueOutcomes(db: DatabaseSync, now: number, limit: number): DueOutcome[] {
  return db.prepare(`SELECT id, address, horizon_h, attempts FROM outcomes
    WHERE status = 'pending' AND due_ms <= ? ORDER BY due_ms LIMIT ?`).all(now, limit) as unknown as DueOutcome[];
}

export function captureOutcome(db: DatabaseSync, id: number, price: number, liquidity: number | null, now: number): void {
  db.prepare(`UPDATE outcomes SET status = 'captured', price = ?, liquidity = ?, captured_ms = ? WHERE id = ?`)
    .run(price, liquidity, now, id);
}

export function bumpAttempts(db: DatabaseSync, id: number): number {
  db.prepare('UPDATE outcomes SET attempts = attempts + 1 WHERE id = ?').run(id);
  return (db.prepare('SELECT attempts FROM outcomes WHERE id = ?').get(id) as any).attempts as number;
}

export function markAlerted(db: DatabaseSync, address: string, score: number): void {
  db.prepare('UPDATE coins SET alerted = 1, score = ? WHERE address = ?').run(score, address);
}

export function markDead(db: DatabaseSync, id: number, now: number): void {
  db.prepare(`UPDATE outcomes SET status = 'dead', captured_ms = ? WHERE id = ?`).run(now, id);
}
