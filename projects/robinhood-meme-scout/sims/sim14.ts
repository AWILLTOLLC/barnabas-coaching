import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync('/tmp/bt.db', { readOnly: true });
const FEE = 0.003;
type Out = { h: number; price: number; liquidity: number };
function priceAt(cs: Out[], e: number, h: number): number {
  if (h <= 0) return e;
  if (h >= cs[cs.length - 1].h) return cs[cs.length - 1].price;
  for (let i = 1; i < cs.length; i++) if (h <= cs[i].h) { const a = cs[i - 1], b = cs[i]; return a.price + (b.price - a.price) * (h - a.h) / (b.h - a.h); }
  return e;
}
function liqAt(cs: Out[], h: number): number {
  if (h <= cs[0].h) return cs[0].liquidity;
  if (h >= cs[cs.length - 1].h) return cs[cs.length - 1].liquidity;
  for (let i = 1; i < cs.length; i++) if (h <= cs[i].h) { const a = cs[i - 1], b = cs[i]; return a.liquidity + (b.liquidity - a.liquidity) * (h - a.h) / (b.h - a.h); }
  return 50000;
}
const clampSlip = (usd: number, l: number) => Math.min(Math.max(0.003, usd / Math.max(l, 1)), 0.5);
function sellUsd(usd: number, p: number, l: number) { return usd * (1 - clampSlip(usd, l)) * (1 - FEE); }

type Coin = { ticker: string; e: number; fs: number; regime: string; cs: Out[]; trigH: number | null; deadH: number | null };
const coins: Coin[] = [];
for (const c of db.prepare(`SELECT address, ticker, first_seen_ms fs, price_at_eval e, COALESCE(regime,'neutral') regime FROM coins WHERE alerted=1 AND price_at_eval > 0 ORDER BY first_seen_ms`).all() as any[]) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND h <= 24 AND status='captured' ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  const trig = cs.find(o => o.h > 0 && (o.price - c.e) / c.e >= 10);
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  coins.push({ ticker: c.ticker, e: c.e, fs: c.fs, regime: c.regime, cs, trigH: trig ? trig.h : null, deadH: dead && dead.dh != null ? dead.dh : null });
}

function planResult(c: Coin, stake: number) {
  const units0 = stake * (1 - FEE) / c.e;
  let proceeds = 0;
  if (c.deadH !== null && c.deadH <= 24) return proceeds;
  const csC = c.cs.map(o => ({ ...o, price: Math.min(o.price, c.e * 51) }));
  let remaining = units0;
  if (c.trigH !== null) { const p = priceAt(csC, c.e, c.trigH); proceeds += sellUsd(remaining * 0.25 * p, p, liqAt(csC, c.trigH)); remaining *= 0.75; }
  const posAt24 = remaining * priceAt(csC, c.e, 24);
  const l24 = liqAt(csC, 24);
  if (posAt24 / Math.max(l24, 1) < 0.005) proceeds += sellUsd(posAt24, priceAt(csC, c.e, 24), l24);
  else for (const t of [23, 23.33, 23.66, 24]) { const p = priceAt(csC, c.e, t); proceeds += sellUsd(remaining * 0.25 * p, p, liqAt(csC, t)); remaining *= 0.75; }
  return proceeds;
}

// 1) regimes present in window
const regimes: Record<string, number> = {};
for (const c of coins) regimes[c.regime] = (regimes[c.regime] || 0) + 1;
console.log('alerts by regime at entry:', JSON.stringify(regimes));

// regime timeline coverage
const snaps = db.prepare(`SELECT confirmed_label label, COUNT(*) n FROM regime_snapshots GROUP BY 1 ORDER BY 2 DESC`).all() as any[];
console.log('regime snapshots (all polls):', snaps.map((s: any) => `${s.label}:${s.n}`).join(' '));

// 2) per-regime cohort stats + PnL at flat $10
for (const rg of Object.keys(regimes)) {
  const grp = coins.filter(c => c.regime === rg);
  let wins = 0, pnl = 0, monsters = 0, rugs = 0;
  const detail: string[] = [];
  for (const c of grp) {
    const pr = planResult(c, 10);
    const ret = pr / 10 - 1;
    if (ret > 0) wins++;
    if (ret >= 10) monsters++;
    if (c.deadH !== null && c.deadH <= 24) rugs++;
    pnl += pr - 10;
    detail.push(`${c.ticker}:${(100 * ret).toFixed(0)}%`);
  }
  console.log(`\n[${rg}] n=${grp.length} win=${(100 * wins / grp.length).toFixed(0)}% monsters=${monsters} rugs=${rugs} PnL $10-stakes: $${pnl.toFixed(0)}`);
  console.log('  ' + detail.join(' '));
}

// 3) sizing sim: base $15, 2x when regime=hot at entry, cap 300, $1000 capital, sequential
function runSizing(multiplier: number, cap: number) {
  let cash = 1000, peak = 0, taken = 0, skipped = 0, maxDD = 0, peakEq = 1000;
  type E = { t: number; amt: number };
  const pending: E[] = [];
  for (const c of coins) {
    for (let i = pending.length - 1; i >= 0; i--) if (pending[i].t <= c.fs) { cash += pending[i].amt; pending.splice(i, 1); }
    const eq = cash;
    if (eq > peakEq) peakEq = eq;
    const dd = (peakEq - eq) / peakEq; if (dd > maxDD) maxDD = dd;
    const base = 15 * Math.floor(eq / 1000);
    const stake = Math.min(cap, Math.max(15, base * (c.regime === 'hot' ? multiplier : 1)));
    if (stake > peak) peak = stake;
    if (cash < stake) { skipped++; continue; }
    taken++; cash -= stake;
    const pr = planResult(c, stake);
    pending.push({ t: c.fs + 24 * 3_600_000, amt: pr });
  }
  for (const e of pending) cash += e.amt;
  return { cash, peak, taken, skipped, maxDD };
}
console.log('\nsizing sims ($1000 start, $15 base, $1k ladder):');
for (const [m, cap] of [[1, 150], [2, 300], [3, 450]] as [number, number][]) {
  const r = runSizing(m, cap);
  console.log(`hot multiplier ${m}x (cap $${cap}): final $${r.cash.toFixed(0)} (${(r.cash / 1000).toFixed(1)}x) | peak stake $${r.peak} | maxDD ${(100 * r.maxDD).toFixed(1)}% | taken ${r.taken} skipped ${r.skipped}`);
}
