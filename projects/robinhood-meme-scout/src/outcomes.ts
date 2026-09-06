import type { DatabaseSync } from 'node:sqlite';
import type { TokenStats } from './gmgn.js';
import { dueOutcomes, captureOutcome, bumpAttempts, markDead } from './db.js';

const MAX_ATTEMPTS = 3;

/**
 * Capture up to `limit` due outcome snapshots. A fetch that fails
 * MAX_ATTEMPTS times marks the outcome dead — itself a signal (rug/delist).
 * Returns the number captured.
 */
export async function captureDueOutcomes(
  db: DatabaseSync,
  fetchStats: (address: string) => Promise<TokenStats | null>,
  now: number,
  limit: number,
): Promise<number> {
  let captured = 0;
  for (const due of dueOutcomes(db, now, limit)) {
    const stats = await fetchStats(due.address);
    if (stats) {
      captureOutcome(db, due.id, stats.price, stats.liquidity_usd, now);
      captured++;
    } else if (bumpAttempts(db, due.id) >= MAX_ATTEMPTS) {
      markDead(db, due.id, now);
    }
  }
  return captured;
}
