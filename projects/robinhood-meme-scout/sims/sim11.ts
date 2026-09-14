import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync('/tmp/bt.db', { readOnly: true });
const FEE = 0.003, STAKE = 10;
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
function sell(usd: number, p: number, l: number) { const slip = Math.min(Math.max(0.003, usd / l), 0.5); return usd * (1 - slip) * (1 - FEE); }
function plan(cs: Out[], e: number, deadH: number | null) {
  const units0 = STAKE * (1 - FEE) / e;
  let remaining = units0, proceeds = 0, txs = 0;
  if (deadH !== null && deadH <= 24) return { proceeds: 0, txs: 1, rug: true }; // rug before exit
  const trigH = cs.find(o => o.h > 0 && (o.price - e) / e >= 10);
  if (trigH) { const p = priceAt(cs, e, trigH.h); proceeds += sell(remaining * 0.25 * p, p, liqAt(cs, trigH.h)); remaining *= 0.75; txs++; }
  const posAt24 = remaining * priceAt(cs, e, 24);
  if (posAt24 / Math.max(liqAt(cs, 24), 1) < 0.005) { proceeds += sell(posAt24, priceAt(cs, e, 24), liqAt(cs, 24)); txs++; }
  else { for (const t of [23, 23.33, 23.66, 24]) { const p = priceAt(cs, e, t); proceeds += sell(remaining * 0.25 * p, p, liqAt(cs, t)); remaining *= 0.75; txs++; } }
  return { proceeds, txs, rug: false };
}
const cohorts: Record<string, { n: number; wins: number; rets: number[]; pnl: number; monsters: number; rugs: number; txs: number; firstSeen: number[] }> = {
  alerted: { n: 0, wins: 0, rets: [], pnl: 0, monsters: 0, rugs: 0, txs: 0, firstSeen: [] },
  passed: { n: 0, wins: 0, rets: [], pnl: 0, monsters: 0, rugs: 0, txs: 0, firstSeen: [] },
  rejected: { n: 0, wins: 0, rets: [], pnl: 0, monsters: 0, rugs: 0, txs: 0, firstSeen: [] },
};
const coins = db.prepare(`SELECT address, ticker, first_seen_ms fs, price_at_eval e, alerted, passed, market_cap mc, liquidity liq FROM coins WHERE price_at_eval > 0.0000000001 AND (market_cap IS NULL OR market_cap > 1000) AND (liquidity IS NULL OR liquidity > 100)`).all() as any[];
let withData = 0;
for (const c of coins) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND h <= 24 AND status='captured' ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  withData++;
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  const deadH = dead && dead.dh != null ? dead.dh : null;
  const r = plan(cs, c.e, deadH);
  let ret = r.proceeds / STAKE - 1;
  if (ret > 50) ret = 50; // data-artifact cap: dust-price entries can't be traded at size; mirrors our +5000% stress cap
  const key = c.alerted ? 'alerted' : c.passed ? 'passed' : 'rejected';
  const k = cohorts[key];
  k.n++; k.rets.push(ret); k.pnl += r.proceeds - STAKE; k.txs += r.txs;
  if (ret > 0) k.wins++;
  if (ret >= 10) k.monsters++;
  if (r.rug) k.rugs++;
  k.firstSeen.push(c.fs);
}
console.log(`coins with 24h outcome data: ${withData} / ${coins.length}\n`);
for (const [name, k] of Object.entries(cohorts)) {
  if (!k.n) continue;
  const rets = k.rets.slice().sort((a, b) => a - b);
  const median = rets[Math.floor(rets.length / 2)];
  const spanDays = ((Math.max(...k.firstSeen) - Math.min(...k.firstSeen)) / 86400000).toFixed(1);
  console.log(`${name}: n=${k.n} | win rate ${(100 * k.wins / k.n).toFixed(1)}% | median 24h ret ${(100 * median).toFixed(1)}% | monsters(>=10x) ${k.monsters} (${(100 * k.monsters / k.n).toFixed(2)}%) | rugs ${k.rugs} | plan PnL total $${k.pnl.toFixed(0)} (avg $${(k.pnl / k.n).toFixed(2)}/coin) | tx/coin ${(k.txs / k.n).toFixed(1)}`);
}
// top 10 winners overall
const all: { t: string; pnl: number; key: string }[] = [];
for (const c of coins) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND h <= 24 AND status='captured' ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  const deadH = dead && dead.dh != null ? dead.dh : null;
  const r = plan(cs, c.e, deadH);
  const key = c.alerted ? 'alerted' : c.passed ? 'passed' : 'rejected';
  all.push({ t: c.ticker, pnl: Math.min(r.proceeds, STAKE * 51) - STAKE, key });
}
all.sort((a, b) => b.pnl - a.pnl);
console.log('\ntop 10 PnL:', all.slice(0, 10).map(x => `$${x.t} +$${x.pnl.toFixed(0)} [${x.key}]`).join(', '));
console.log('total PnL all cohorts (all taken, unbounded capital): $' + all.reduce((a, x) => a + x.pnl, 0).toFixed(0));
