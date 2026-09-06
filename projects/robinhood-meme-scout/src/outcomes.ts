import type { DatabaseSync } from 'node:sqlite';
import type { TokenStats } from './gmgn.js';
import type { DexStats } from './dexscreener.js';
import { dueOutcomes, captureOutcome, bumpAttempts, markDead } from './db.js';

const MAX_ATTEMPTS = 3;
// GMGN calls per tick stay capped even in batch mode, so a DexScreener outage
// degrades to the old v2.1 pace instead of hammering gmgn-cli.
const GMGN_BUDGET = 5;

/**
 * Capture up to `limit` due outcome snapshots. When `fetchBatch` is provided
 * (DexScreener enabled), one batch call covers every due address and GMGN is
 * only a per-token fallback for misses. A token that fails MAX_ATTEMPTS times
 * across both sources is marked dead — itself a signal (rug/delist).
 * Misses beyond the GMGN budget stay pending untouched for the next tick.
 * Returns the number captured.
 */
export async function captureDueOutcomes(
  db: DatabaseSync,
  fetchStats: (address: string) => Promise<TokenStats | null>,
  now: number,
  limit: number,
  fetchBatch?: (addresses: string[]) => Promise<Map<string, DexStats>>,
): Promise<number> {
  const due = dueOutcomes(db, now, limit);
  const batch = fetchBatch ? await fetchBatch([...new Set(due.map(d => d.address))]) : new Map<string, DexStats>();

  let captured = 0;
  let gmgnBudget = fetchBatch ? GMGN_BUDGET : limit;
  const gmgnCache = new Map<string, TokenStats | null>();
  for (const d of due) {
    const dex = batch.get(d.address.toLowerCase());
    if (dex) {
      captureOutcome(db, d.id, dex.price, dex.liquidity_usd, now, 'dexscreener');
      captured++;
      continue;
    }
    let stats: TokenStats | null;
    if (gmgnCache.has(d.address)) {
      stats = gmgnCache.get(d.address)!;
    } else {
      if (gmgnBudget <= 0) continue; // stays pending, no attempt burned
      gmgnBudget--;
      stats = await fetchStats(d.address);
      gmgnCache.set(d.address, stats);
    }
    if (stats) {
      captureOutcome(db, d.id, stats.price, stats.liquidity_usd, now, 'gmgn');
      captured++;
    } else if (bumpAttempts(db, d.id) >= MAX_ATTEMPTS) {
      markDead(db, d.id, now);
    }
  }
  return captured;
}
