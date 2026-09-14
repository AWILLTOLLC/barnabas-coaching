import type { Strategy } from './config.js';
import type { PositionRow } from './db.js';

/** Scaling ladder: $base × floor(realized capital ÷ step), clamped to [base, max]. */
export function stakeFor(realizedCapitalUsd: number, s: Strategy): number {
  const laddered = s.base_stake_usd * Math.floor(realizedCapitalUsd / s.ladder_step_usd);
  return Math.min(s.max_stake_usd, Math.max(s.base_stake_usd, laddered));
}

export interface EntryArgs {
  address: string;
  liquidity_usd: number;
  ordersToday: number;
  deployedTodayUsd: number;
  openPositions: number;
  alreadyHasPosition: boolean;
  stakeUsd: number;
}

export type GateResult = { ok: true } | { ok: false; reason: string };

/** Every hard cap from the strategy doc, enforced regardless of ticket contents. */
export function checkEntry(a: EntryArgs, s: Strategy): GateResult {
  if (a.alreadyHasPosition) return { ok: false, reason: 'position-exists (lifetime one position per address)' };
  if (a.ordersToday >= s.max_orders_per_day) return { ok: false, reason: `daily-order-cap (${s.max_orders_per_day}/day)` };
  if (a.deployedTodayUsd + a.stakeUsd > s.max_daily_deployment_usd) return { ok: false, reason: `daily-deployment-cap ($${s.max_daily_deployment_usd}/day)` };
  if (a.openPositions >= s.max_open_positions) return { ok: false, reason: `open-positions-cap (${s.max_open_positions})` };
  if (a.stakeUsd > a.liquidity_usd * s.max_entry_lp_ratio) return { ok: false, reason: `lp-entry-gate (stake > ${s.max_entry_lp_ratio * 100}% of $${Math.round(a.liquidity_usd)} LP)` };
  return { ok: true };
}

/** Moon-bag triggers on the SCOUT reference price (backtest-comparable), not the fill price. */
export function moonbagDue(p: Pick<PositionRow, 'ref_price' | 'moonbag_done'>, markPrice: number, s: Strategy): boolean {
  return !p.moonbag_done && markPrice >= p.ref_price * (1 + s.moonbag.trigger_pct / 100);
}

export interface SellPlanArgs {
  tokensRemaining: number;
  price: number;
  liquidity_usd: number;
  ageHours: number;
  tranchesDone: number;
}

export type SellPlan = { kind: 'oneshot' | 'tranche'; tokenAmount: number; trancheIndex?: number } | null;

/**
 * Which boundary sell (if any) is due now.
 * - Position value < oneshot_max_lp_ratio of LP AND ≤ big_sell_usd → single dump at the 24h boundary.
 * - Otherwise scale out on the tranche schedule (23h/23.33h/23.67h/24h), each order
 *   capped at tranche_max_lp_ratio of pool depth; keeps selling capped chunks past
 *   the boundary until empty.
 */
export function sellPlan(a: SellPlanArgs, s: Strategy): SellPlan {
  if (a.tokensRemaining <= 0) return null;
  const valueUsd = a.tokensRemaining * a.price;
  const oneshotOk = valueUsd < a.liquidity_usd * s.exit.oneshot_max_lp_ratio && valueUsd <= s.exit.big_sell_usd;

  if (oneshotOk) {
    if (a.ageHours >= s.exit.boundary_hours) return { kind: 'oneshot', tokenAmount: a.tokensRemaining };
    return null;
  }

  const schedule = s.exit.tranche_schedule_hours;
  const dueCount = schedule.filter(h => a.ageHours >= h).length;
  if (dueCount <= a.tranchesDone && a.ageHours < s.exit.boundary_hours) return null;
  if (dueCount <= a.tranchesDone && a.ageHours >= s.exit.boundary_hours) {
    // past boundary with tokens left (cap-limited earlier tranches): keep draining
    const cap = (a.liquidity_usd * s.exit.tranche_max_lp_ratio) / a.price;
    return { kind: 'tranche', tokenAmount: Math.min(a.tokensRemaining, cap), trancheIndex: a.tranchesDone };
  }

  const tranchesLeft = Math.max(1, schedule.length - a.tranchesDone);
  const even = a.tokensRemaining / tranchesLeft;
  const cap = (a.liquidity_usd * s.exit.tranche_max_lp_ratio) / a.price;
  const isFinal = a.tranchesDone === schedule.length - 1;
  const size = Math.min(isFinal ? a.tokensRemaining : even, cap);
  return { kind: 'tranche', tokenAmount: size, trancheIndex: a.tranchesDone };
}
