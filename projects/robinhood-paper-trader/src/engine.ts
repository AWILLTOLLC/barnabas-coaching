import type { DatabaseSync } from 'node:sqlite';
import type { Strategy } from './config.js';
import type { Executor, Order, Fill, LivePrice } from './executor.js';
import type { Mark } from './prices.js';
import {
  insertOrder, insertFill, openPosition, updatePosition, closePosition,
  getOpenPositions, openPositionCount, hasPosition, ordersToday, deployedTodayUsd,
  realizedCapital, insertMark, lastMark, pruneMarks, ptDate, type PositionRow,
} from './db.js';
import { stakeFor, checkEntry, moonbagDue, sellPlan } from './limits.js';

export interface Ticket {
  address: string;
  ticker: string;
  name?: string;
  price_usd: number;
  liquidity_usd?: number;
  alerted_at?: string;
}

export interface OpenResult {
  ok: boolean;
  reason?: string;
  fill?: Fill;
  stake_usd?: number;
}

export interface EngineDeps {
  db: DatabaseSync;
  strategy: Strategy;
  executor: Executor;
  fetchMarks: (addresses: string[]) => Promise<Map<string, Mark>>;
  notify: (msg: string) => Promise<unknown>;
  logEvent: (obj: Record<string, unknown>) => void;
  now?: () => number;
}

const RUG_MISSED_MARKS = 3;
const DUST_USD = 0.01;

export class Engine {
  private d: EngineDeps;
  private now: () => number;

  constructor(deps: EngineDeps) {
    this.d = deps;
    this.now = deps.now ?? (() => Date.now());
  }

  /** Entry path: validate ticket → live re-fetch → gates → executor → position. */
  async openFromTicket(t: Ticket): Promise<OpenResult> {
    const s = this.d.strategy;
    if (!t?.address || typeof t.address !== 'string' || !isFinite(t.price_usd) || t.price_usd <= 0) {
      return { ok: false, reason: 'invalid ticket (address/price_usd required)' };
    }
    const ts = this.now();
    const live = (await this.d.fetchMarks([t.address])).get(t.address.toLowerCase()) ?? null;
    if (!live) return this.rejectEntry(t, ts, 'no live price for token');

    // staleness gate: the alert must still resemble the signal the gates validated.
    // Divergence between ticket ref and live price means the alert decayed before
    // execution; an aged ticket is a different trade than the one that scored.
    const staleness = s.staleness ?? { max_divergence_pct: 50, max_age_minutes: 15 };
    const divPct = Math.abs(live.price_usd - t.price_usd) / t.price_usd * 100;
    if (divPct > staleness.max_divergence_pct) {
      return this.rejectEntry(t, ts, `stale-ticket (live ${divPct.toFixed(0)}% from ref $${t.price_usd} > ${staleness.max_divergence_pct}%)`);
    }
    if (t.alerted_at) {
      const ageMin = (ts - Date.parse(t.alerted_at)) / 60_000;
      if (isFinite(ageMin) && ageMin > staleness.max_age_minutes) {
        return this.rejectEntry(t, ts, `stale-ticket (alert ${ageMin.toFixed(0)}min old > ${staleness.max_age_minutes}min)`);
      }
    }

    const stake = stakeFor(realizedCapital(this.d.db, s.starting_capital_usd), s);
    const gate = checkEntry({
      address: t.address,
      liquidity_usd: live.liquidity_usd,
      ordersToday: ordersToday(this.d.db, ptDate(ts)),
      deployedTodayUsd: deployedTodayUsd(this.d.db, ptDate(ts)),
      openPositions: openPositionCount(this.d.db),
      alreadyHasPosition: hasPosition(this.d.db, t.address),
      stakeUsd: stake,
    }, s);
    if (!gate.ok) return this.rejectEntry(t, ts, gate.reason);

    const order: Order = {
      order_id: orderId(ts), side: 'buy', token_address: t.address, ticker: t.ticker ?? '?',
      amount_usd: stake, token_amount: null, ref_price_usd: live.price_usd,
      max_slippage_pct: s.slippage.default_pct, deadline_s: 1800,
    };
    const fill = await this.d.executor(order, live);
    insertOrder(this.d.db, { id: order.order_id, ts, pt_date: ptDate(ts), side: 'buy', address: t.address, ticker: order.ticker, amount_usd: stake, token_amount: null, slippage_pct: order.max_slippage_pct, status: fill.status, error: fill.error ?? null, kind: 'entry' });
    if (fill.status !== 'filled') {
      this.d.logEvent({ event: 'entry_failed', address: t.address, ticker: t.ticker, error: fill.error });
      return { ok: false, reason: fill.error, stake_usd: stake };
    }
    insertFill(this.d.db, { order_id: order.order_id, ts, fill_price_usd: fill.fill_price_usd, token_amount: fill.token_amount, usd_value: fill.usd_value, fee_usd: fill.fee_usd, source: fill.source });
    openPosition(this.d.db, {
      address: t.address, ticker: order.ticker, opened_ms: ts,
      entry_price: fill.fill_price_usd,   // P&L cost basis
      ref_price: t.price_usd,             // scout basis: moon-bag trigger
      stake_usd: stake, tokens_total: fill.token_amount,
    });
    insertMark(this.d.db, t.address, ts, live.price_usd, live.liquidity_usd);
    this.d.logEvent({ event: 'entry_filled', address: t.address, ticker: t.ticker, stake, fill_price: fill.fill_price_usd, tokens: fill.token_amount });
    await this.d.notify(`🟢 PAPER BUY $${order.ticker}: $${stake} @ $${fill.fill_price_usd.toPrecision(4)} (${Math.round(fill.token_amount).toLocaleString()} tokens, scout ref $${t.price_usd.toPrecision(4)})`);
    return { ok: true, fill, stake_usd: stake };
  }

  private rejectEntry(t: Ticket, ts: number, reason: string): OpenResult {
    insertOrder(this.d.db, { id: orderId(ts), ts, pt_date: ptDate(ts), side: 'buy', address: t.address, ticker: t.ticker ?? '?', amount_usd: null, token_amount: null, slippage_pct: 0, status: 'failed', error: reason, kind: 'entry' });
    this.d.logEvent({ event: 'entry_rejected', address: t.address, ticker: t.ticker, reason });
    return { ok: false, reason };
  }

  /** Owner-initiated sell of pct% of the remaining position at the current mark. */
  async manualSell(address: string, pct: number): Promise<Fill | { error: string }> {
    const p = getOpenPositions(this.d.db).find(x => x.address.toLowerCase() === address.toLowerCase());
    if (!p) return { error: 'no open position for that address' };
    const ts = this.now();
    const mark = (await this.d.fetchMarks([address])).get(address.toLowerCase()) ?? lastMark(this.d.db, address);
    if (!mark) return { error: 'no price available' };
    return this.sell(p, p.tokens_remaining * (pct / 100), { price_usd: mark.price_usd, liquidity_usd: mark.liquidity_usd }, ts, 'manual');
  }

  /** One mark cycle over all open positions. */
  async tick(): Promise<void> {
    const s = this.d.strategy;
    const open = getOpenPositions(this.d.db);
    if (open.length === 0) return;
    const ts = this.now();
    const marks = await this.d.fetchMarks(open.map(p => p.address));
    pruneMarks(this.d.db, ts - 30 * 24 * 3_600_000);

    for (const p of open) {
      const mark = marks.get(p.address.toLowerCase()) ?? null;
      if (mark) {
        insertMark(this.d.db, p.address, ts, mark.price_usd, mark.liquidity_usd);
        if (p.missed_marks > 0) updatePosition(this.d.db, p.address, { missed_marks: 0 });
        p.missed_marks = 0;
      } else {
        updatePosition(this.d.db, p.address, { missed_marks: p.missed_marks + 1 });
        p.missed_marks++;
        if (p.missed_marks >= RUG_MISSED_MARKS) await this.rugPath(p, ts);
        continue;
      }

      const ageHours = (ts - p.opened_ms) / 3_600_000;

      if (moonbagDue(p, mark.price_usd, s)) {
        const amount = Math.min(p.tokens_total * s.moonbag.sell_fraction, p.tokens_remaining);
        await this.sell(p, amount, mark, ts, 'moonbag');
        continue; // boundary logic picks up next tick
      }

      const plan = sellPlan({ tokensRemaining: p.tokens_remaining, price: mark.price_usd, liquidity_usd: mark.liquidity_usd, ageHours, tranchesDone: p.exit_tranches_done }, s);
      if (plan) await this.sell(p, plan.tokenAmount, mark, ts, plan.kind, plan.kind === 'tranche');
    }
  }

  private async sell(p: PositionRow, tokenAmount: number, live: LivePrice, ts: number, kind: 'moonbag' | 'tranche' | 'oneshot' | 'rug' | 'manual', countTranche = false): Promise<Fill> {
    const s = this.d.strategy;
    const slippage = Math.min(p.pending_slippage_pct ?? s.slippage.default_pct, s.slippage.max_pct);
    const order: Order = {
      order_id: orderId(ts), side: 'sell', token_address: p.address, ticker: p.ticker,
      amount_usd: null, token_amount: tokenAmount, ref_price_usd: live.price_usd,
      max_slippage_pct: slippage, deadline_s: 1800,
    };
    const fill = await this.d.executor(order, live);
    insertOrder(this.d.db, { id: order.order_id, ts, pt_date: ptDate(ts), side: 'sell', address: p.address, ticker: p.ticker, amount_usd: null, token_amount: tokenAmount, slippage_pct: slippage, status: fill.status, error: fill.error ?? null, kind });

    if (fill.status !== 'filled') {
      // escalate for the next attempt; abandon this cycle (strategy §3)
      const next = Math.min(slippage + s.slippage.escalate_pct, s.slippage.max_pct);
      updatePosition(this.d.db, p.address, { pending_slippage_pct: next });
      this.d.logEvent({ event: 'sell_failed', kind, address: p.address, ticker: p.ticker, error: fill.error, next_slippage_pct: next });
      return fill;
    }

    insertFill(this.d.db, { order_id: order.order_id, ts, fill_price_usd: fill.fill_price_usd, token_amount: fill.token_amount, usd_value: fill.usd_value, fee_usd: fill.fee_usd, source: fill.source });
    const remaining = Math.max(0, p.tokens_remaining - fill.token_amount);
    const realized = p.realized_usd + fill.usd_value;
    const fields: Partial<PositionRow> = { tokens_remaining: remaining, realized_usd: realized, pending_slippage_pct: null };
    if (kind === 'moonbag') fields.moonbag_done = 1;
    if (countTranche) fields.exit_tranches_done = p.exit_tranches_done + 1;
    updatePosition(this.d.db, p.address, fields);
    Object.assign(p, fields);

    const done = remaining * fill.fill_price_usd < DUST_USD;
    if (done && kind !== 'moonbag') {
      closePosition(this.d.db, p.address, 'closed', ts);
      const pnl = realized - p.stake_usd;
      await this.d.notify(`🔴 PAPER EXIT $${p.ticker} (${kind}): proceeds $${realized.toFixed(2)} on $${p.stake_usd} stake → P&L ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`);
    } else if (kind === 'moonbag') {
      await this.d.notify(`💰 MOON BAG $${p.ticker}: sold 25% for $${fill.usd_value.toFixed(2)} at +${(((fill.fill_price_usd / p.ref_price) - 1) * 100).toFixed(0)}% vs scout ref — 75% still running`);
    }
    this.d.logEvent({ event: 'sell_filled', kind, address: p.address, ticker: p.ticker, usd: fill.usd_value, remaining });
    return fill;
  }

  /**
   * Dead-feed path: courtesy sell against the LAST recorded mark (catches a
   * feed outage where the pool is fine — the executor may still fill). Builtin
   * receives live=null and fails by design (no simulated market without a
   * feed). One escalated retry, then rugged: realized = actual proceeds
   * (normally $0) against the fill-price cost basis. No synthetic valuation.
   */
  private async rugPath(p: PositionRow, ts: number): Promise<void> {
    const s = this.d.strategy;
    const last = lastMark(this.d.db, p.address);
    const ref = last ?? { price_usd: p.entry_price, liquidity_usd: 0 };

    const attempt = async (slippagePct: number): Promise<Fill> => {
      const order: Order = {
        order_id: orderId(ts), side: 'sell', token_address: p.address, ticker: p.ticker,
        amount_usd: null, token_amount: p.tokens_remaining, ref_price_usd: ref.price_usd,
        max_slippage_pct: slippagePct, deadline_s: 1800,
      };
      const fill = await this.d.executor(order, null); // no live market
      insertOrder(this.d.db, { id: order.order_id, ts, pt_date: ptDate(ts), side: 'sell', address: p.address, ticker: p.ticker, amount_usd: null, token_amount: p.tokens_remaining, slippage_pct: slippagePct, status: fill.status, error: fill.error ?? null, kind: 'rug' });
      return fill;
    };

    let fill = await attempt(s.slippage.default_pct);
    if (fill.status !== 'filled') fill = await attempt(s.slippage.max_pct);

    let realized = p.realized_usd;
    if (fill.status === 'filled') {
      insertFill(this.d.db, { order_id: fill.order_id, ts, fill_price_usd: fill.fill_price_usd, token_amount: fill.token_amount, usd_value: fill.usd_value, fee_usd: fill.fee_usd, source: fill.source });
      realized += fill.usd_value;
      updatePosition(this.d.db, p.address, { realized_usd: realized });
      closePosition(this.d.db, p.address, 'closed', ts);
      await this.d.notify(`🟡 FEED-OUTAGE EXIT $${p.ticker}: courtesy sell filled $${fill.usd_value.toFixed(2)} — closed, not rugged`);
      return;
    }
    closePosition(this.d.db, p.address, 'rugged', ts);
    const pnl = realized - p.stake_usd;
    this.d.logEvent({ event: 'rugged', address: p.address, ticker: p.ticker, realized_usd: realized, pnl });
    await this.d.notify(`💀 RUGGED $${p.ticker}: feed dead ${RUG_MISSED_MARKS}+ marks, sells failed. Realized $${realized.toFixed(2)} on $${p.stake_usd} stake (P&L ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)})`);
  }
}

let seq = 0;
function orderId(ts: number): string {
  return `o_${ts}_${(seq++).toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}
