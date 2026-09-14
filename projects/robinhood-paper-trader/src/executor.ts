import { spawn } from 'node:child_process';
import type { Strategy } from './config.js';

export interface Order {
  order_id: string;
  side: 'buy' | 'sell';
  token_address: string;
  ticker: string;
  amount_usd: number | null;   // buys: USD to spend
  token_amount: number | null; // sells: tokens to sell
  ref_price_usd: number;       // our current mark; wrapper derives min-out from this
  max_slippage_pct: number;
  deadline_s: number;
}

export interface Fill {
  order_id: string;
  status: 'filled' | 'failed';
  fill_price_usd: number;
  token_amount: number;
  usd_value: number;
  fee_usd: number;
  source: 'builtin' | 'external';
  tx_ref?: string;
  error?: string;
}

export interface LivePrice {
  price_usd: number;
  liquidity_usd: number;
}

const failed = (order: Order, source: Fill['source'], error: string): Fill =>
  ({ order_id: order.order_id, status: 'failed', fill_price_usd: 0, token_amount: 0, usd_value: 0, fee_usd: 0, source, error });

/**
 * Pure simulation engine. Fill price = live price moved against the order by a
 * constant-product-ish impact (order size ÷ pool depth), plus a 0.3% fee on the
 * input side. No chain, no network, no state.
 */
export function builtinExecute(order: Order, live: LivePrice | null, s: Strategy): Fill {
  if (!live || live.price_usd <= 0 || live.liquidity_usd <= 0) {
    return failed(order, 'builtin', 'no live market (feed dead — simulated market unavailable)');
  }
  const feeRate = s.fee_pct / 100;

  if (order.side === 'buy') {
    if (!order.amount_usd || order.amount_usd <= 0) return failed(order, 'builtin', 'buy without amount_usd');
    const impactPct = (order.amount_usd / live.liquidity_usd) * 100;
    const fillPrice = live.price_usd * (1 + impactPct / 100);
    const slipPct = ((fillPrice - order.ref_price_usd) / order.ref_price_usd) * 100;
    if (slipPct > order.max_slippage_pct) return failed(order, 'builtin', `slippage ${slipPct.toFixed(2)}% > ${order.max_slippage_pct}%`);
    const feeUsd = order.amount_usd * feeRate;
    const tokens = (order.amount_usd - feeUsd) / fillPrice;
    return { order_id: order.order_id, status: 'filled', fill_price_usd: fillPrice, token_amount: tokens, usd_value: order.amount_usd, fee_usd: feeUsd, source: 'builtin' };
  }

  if (!order.token_amount || order.token_amount <= 0) return failed(order, 'builtin', 'sell without token_amount');
  const grossUsd = order.token_amount * live.price_usd;
  const impactPct = (grossUsd / live.liquidity_usd) * 100;
  const fillPrice = live.price_usd * (1 - impactPct / 100);
  const slipPct = ((order.ref_price_usd - fillPrice) / order.ref_price_usd) * 100;
  if (slipPct > order.max_slippage_pct) return failed(order, 'builtin', `slippage ${slipPct.toFixed(2)}% > ${order.max_slippage_pct}%`);
  const usdBeforeFee = order.token_amount * fillPrice;
  const feeUsd = usdBeforeFee * feeRate;
  return { order_id: order.order_id, status: 'filled', fill_price_usd: fillPrice, token_amount: order.token_amount, usd_value: usdBeforeFee - feeUsd, fee_usd: feeUsd, source: 'builtin' };
}

/**
 * External adapter: spawns the user-supplied wrapper command, writes the order
 * as JSON to its stdin, reads one fill JSON object from stdout. Timeout,
 * nonzero exit, or unparseable output → failed fill; never throws. The wrapper
 * owns everything on the other side of this pipe.
 */
export function externalExecute(order: Order, cfg: { command: string; timeout_ms?: number }): Promise<Fill> {
  return new Promise((resolve) => {
    const child = spawn(cfg.command, [], { shell: false, stdio: ['pipe', 'pipe', 'pipe'] });
    const timeout = cfg.timeout_ms ?? 30_000;
    let stdout = '';
    let done = false;
    const finish = (fill: Fill) => { if (!done) { done = true; resolve(fill); } };
    const timer = setTimeout(() => { child.kill('SIGKILL'); finish(failed(order, 'external', `wrapper timeout after ${timeout}ms`)); }, timeout);

    child.stdout.on('data', d => { stdout += d; });
    child.on('error', err => { clearTimeout(timer); finish(failed(order, 'external', `wrapper spawn error: ${err.message}`)); });
    child.on('close', code => {
      clearTimeout(timer);
      if (code !== 0) return finish(failed(order, 'external', `wrapper exit ${code}`));
      try {
        const f = JSON.parse(stdout);
        if (f.order_id !== order.order_id) return finish(failed(order, 'external', 'wrapper returned mismatched order_id'));
        if (f.status !== 'filled') return finish(failed(order, 'external', String(f.error ?? 'wrapper reported failure')));
        return finish({
          order_id: order.order_id, status: 'filled',
          fill_price_usd: Number(f.fill_price_usd), token_amount: Number(f.token_amount),
          usd_value: Number(f.usd_value), fee_usd: Number(f.fee_usd ?? 0),
          source: 'external', tx_ref: f.tx_ref,
        });
      } catch {
        return finish(failed(order, 'external', 'wrapper stdout was not valid JSON'));
      }
    });

    child.stdin.write(JSON.stringify(order));
    child.stdin.end();
  });
}

export type Executor = (order: Order, live: LivePrice | null) => Promise<Fill>;

export function makeExecutor(s: Strategy): Executor {
  if (s.executor.type === 'external') {
    const cfg = s.executor;
    return (order) => externalExecute(order, cfg);
  }
  return async (order, live) => builtinExecute(order, live, s);
}
