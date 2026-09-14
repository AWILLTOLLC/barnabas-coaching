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
    CREATE TABLE IF NOT EXISTS price_ticks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      address TEXT NOT NULL,
      ts_ms INTEGER NOT NULL,
      price REAL,
      liquidity REAL,
      source TEXT,
      UNIQUE(address, ts_ms)
    );
    CREATE INDEX IF NOT EXISTS idx_price_ticks_ts ON price_ticks(ts_ms);
  `);
  try {
    db.exec(`ALTER TABLE coins ADD COLUMN regime TEXT DEFAULT 'neutral'`);
  } catch {
    // column already exists
  }
  try {
    db.exec(`ALTER TABLE outcomes ADD COLUMN source TEXT`);
  } catch {
    // column already exists
  }
  db.exec(`CREATE TABLE IF NOT EXISTS divergences (
    ts INTEGER, address TEXT, field TEXT, dex_value REAL, gmgn_value REAL
  )`);
  pruneOldTicks(db, 30);
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

export function captureOutcome(db: DatabaseSync, id: number, price: number, liquidity: number | null, now: number, source: string = 'gmgn'): void {
  db.prepare(`UPDATE outcomes SET status = 'captured', price = ?, liquidity = ?, captured_ms = ?, source = ? WHERE id = ?`)
    .run(price, liquidity, now, source, id);
}

export function recordDivergence(db: DatabaseSync, ts: number, address: string, field: string, dexValue: number | null, gmgnValue: number | null): void {
  db.prepare('INSERT INTO divergences (ts, address, field, dex_value, gmgn_value) VALUES (?, ?, ?, ?, ?)')
    .run(ts, address, field, dexValue, gmgnValue);
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

export function recordPriceTick(db: DatabaseSync, address: string, tsMs: number, price: number | null, liquidity: number | null, source: string = 'monitor'):
void {
  const existing = db.prepare('SELECT 1 FROM price_ticks WHERE address = ? AND ts_ms = ?').get(address, tsMs);
  if (existing) return;
  db.prepare('INSERT OR REPLACE INTO price_ticks (address, ts_ms, price, liquidity, source) VALUES (?, ?, ?, ?, ?)')
    .run(address, tsMs, price, liquidity, source);
}

export function pruneOldTicks(db: DatabaseSync, days: number = 30): number {
  const cutoff = Date.now() - days * 24 * 3600 * 1000;
  const result = db.prepare('DELETE FROM price_ticks WHERE ts_ms < ?').run(cutoff);
  return Number(result.changes);
}
