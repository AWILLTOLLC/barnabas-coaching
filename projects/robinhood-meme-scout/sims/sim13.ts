import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync('/tmp/bt.db', { readOnly: true });
const FEE = 0.003, CAPITAL = 1000;
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

type Coin = { ticker: string; e: number; fs: number; cs: Out[]; trigH: number | null; deadH: number | null };
const coins: Coin[] = [];
for (const c of db.prepare(`SELECT address, ticker, first_seen_ms fs, price_at_eval e FROM coins WHERE alerted=1 AND price_at_eval > 0 ORDER BY first_seen_ms`).all() as any[]) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND h <= 24 AND status='captured' ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  const trig = cs.find(o => o.h > 0 && (o.price - c.e) / c.e >= 10);
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  coins.push({ ticker: c.ticker, e: c.e, fs: c.fs, cs, trigH: trig ? trig.h : null, deadH: dead && dead.dh != null ? dead.dh : null });
}

function runLadder(base: number, cap: number) {
  let cash = CAPITAL, taken = 0, skipped = 0, peak = base, maxDD = 0, peakEquity = CAPITAL;
  type Exit = { t: number; amt: number };
  const pending: Exit[] = [];
  const bigSells: string[] = [];
  const events: { t: number; cashAfter: number }[] = [];
  for (const c of coins) {
    // credit matured exits in time order
    for (let i = pending.length - 1; i >= 0; i--) if (pending[i].t <= c.fs) { cash += pending[i].amt; pending.splice(i, 1); }
    const equity = cash; // realized cash available
    const stake = Math.min(cap, Math.max(base, base * Math.floor(equity / 1000)));
    if (stake > peak) peak = stake;
    if (cash < stake) { skipped++; continue; }
    taken++;
    cash -= stake;
    const units0 = stake * (1 - FEE) / c.e;
    let proceeds = 0;
    if (c.deadH !== null && c.deadH <= 24) { /* rug: -100% */ }
    else {
      const csCapped = c.cs.map(o => ({ ...o, price: Math.min(o.price, c.e * 51) })); // +5000% cap
      let remaining = units0;
      if (c.trigH !== null) {
        const p = priceAt(csCapped, c.e, c.trigH), l = liqAt(csCapped, c.trigH);
        const usd = remaining * 0.25 * p;
        proceeds += sellUsd(usd, p, l);
        if (usd > 10000) bigSells.push(`$${c.ticker} $${usd.toFixed(0)}`);
        remaining *= 0.75;
      }
      const posAt24 = remaining * priceAt(csCapped, c.e, 24);
      const l24 = liqAt(csCapped, 24);
      if (posAt24 / Math.max(l24, 1) < 0.005) { proceeds += sellUsd(posAt24, priceAt(csCapped, c.e, 24), l24); if (posAt24 > 10000) bigSells.push(`$${c.ticker} $${posAt24.toFixed(0)}`); }
      else for (const t of [23, 23.33, 23.66, 24]) { const p = priceAt(csCapped, c.e, t), l = liqAt(csCapped, t); proceeds += sellUsd(remaining * 0.25 * p, p, l); remaining *= 0.75; }
    }
    pending.push({ t: c.fs + 24 * 3_600_000, amt: proceeds });
    // drawdown on realized equity
    const eq = cash + pending.reduce((a, x) => a + Math.min(x.amt, stake), 0); // conservative: open positions worth at most stake... use stake at risk
    events.push({ t: c.fs, cashAfter: cash });
    const dd = (peakEquity - cash) / peakEquity;
    if (cash > peakEquity) peakEquity = cash;
    if (dd > maxDD) maxDD = dd;
  }
  for (const e of pending) cash += e.amt;
  return { final: cash, taken, skipped, peak, maxDD, bigSells };
}

for (const [name, base, cap] of [['flat $10 (baseline)', 10, 100], ['ladder $15/step (new)', 15, 150], ['flat $15', 15, 999999], ['ladder $10/step (old)', 10, 100]] as [string, number, number][]) {
  const r = runLadder(base, cap);
  console.log(`${name}: final $${r.final.toFixed(0)} (${(r.final / CAPITAL).toFixed(1)}x) | taken ${r.taken} skipped ${r.skipped} | peak stake $${r.peak} | maxDD ${(100 * r.maxDD).toFixed(1)}%${r.bigSells.length ? ' | sells>10k: ' + r.bigSells.join(', ') : ''}`);
}
