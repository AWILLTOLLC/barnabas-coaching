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
const sellUsd = (usd: number, p: number, l: number) => usd * (1 - clampSlip(usd, l)) * (1 - FEE);

type Coin = { ticker: string; e: number; trigH: number | null; deadH: number | null; cs: Out[]; ret24: number; p72: number | null; p168: number | null; l72: number | null; l168: number | null; dead72: boolean; dead168: boolean };
const coins: Coin[] = [];
for (const c of db.prepare(`SELECT address, ticker, price_at_eval e FROM coins WHERE alerted=1 AND price_at_eval > 0`).all() as any[]) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND status='captured' AND h <= 24 ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  const trig = cs.find(o => o.h > 0 && (o.price - c.e) / c.e >= 10);
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  const ret24 = (priceAt(cs, c.e, 24) - c.e) / c.e;
  const g = (h: number) => {
    const r = db.prepare(`SELECT price, liquidity, status FROM outcomes WHERE address=? AND horizon_h=?`).get(c.address, h) as any;
    if (!r) return null;
    if (r.status === 'dead') return { dead: true, price: 0, liq: null };
    if (r.status !== 'captured' || !r.price) return null;
    return { dead: false, price: r.price, liq: r.liquidity || 50000 };
  };
  const g72 = g(72), g168 = g(168);
  coins.push({ ticker: c.ticker, e: c.e, trigH: trig ? trig.h : null, deadH: dead && dead.dh != null ? dead.dh : null, cs, ret24, p72: g72 ? g72.price : null, p168: g168 ? g168.price : null, l72: g72 ? g72.liq : null, l168: g168 ? g168.liq : null, dead72: g72 ? g72.dead : false, dead168: g168 ? g168.dead : false });
}

function run(scenario: 'sell-all' | 'moon5k' | 'moon1k', horizon: 72 | 168) {
  let total = 0; const rows: string[] = [];
  const STAKE = 10;
  for (const c of coins) {
    const units0 = STAKE * (1 - FEE) / c.e;
    if (c.deadH !== null && c.deadH <= 24) continue; // rugs: nothing either way
    let remaining = units0;
    if (c.trigH !== null) remaining *= 0.75; // 25% sold at trigger
    const qualifies = scenario === 'moon1k' ? c.ret24 >= 10 : c.ret24 >= 50;
    const keepTokens = qualifies ? 0.10 * units0 : 0;
    const sellTokens = Math.max(0, remaining - keepTokens);
    // sell everything except moon bag across 24h tranches
    let rem = sellTokens, proceeds = 0;
    const pos24 = rem * priceAt(c.cs, c.e, 24), l24 = liqAt(c.cs, 24);
    if (pos24 / Math.max(l24, 1) < 0.005) proceeds += sellUsd(pos24, priceAt(c.cs, c.e, 24), l24);
    else for (const t of [23, 23.33, 23.66, 24]) { const p = priceAt(c.cs, c.e, t); proceeds += sellUsd(rem * 0.25 * p, p, liqAt(c.cs, t)); }
    // value moon bag at horizon (assume sellable at price with 0.5% LP-relative slippage cap)
    let bag = 0, bagInfo = '—';
    if (keepTokens > 0) {
      const px = horizon === 72 ? c.p72 : c.p168;
      const lq = (horizon === 72 ? c.l72 : c.l168) || 100000;
      if (px === null) bagInfo = 'no data';
      else if ((horizon === 72 ? c.dead72 : c.dead168)) bagInfo = 'dead($0)';
      else { bag = keepTokens * px * (1 - Math.min(Math.max(0.003, keepTokens * px / lq), 0.5)); bagInfo = `$${bag.toFixed(2)}`; }
    }
    total += proceeds + (bagInfo === 'no data' ? 0 : bag);
    if (qualifies && keepTokens > 0) {
      const r72 = c.p72 !== null ? ((c.p72 / c.e - 1) * 100).toFixed(0) : (c.dead72 ? 'DEAD' : '?');
      const r168 = c.p168 !== null ? ((c.p168 / c.e - 1) * 100).toFixed(0) : (c.dead168 ? 'DEAD' : '?');
      rows.push(`$${c.ticker}: 24h ret ${(100 * c.ret24).toFixed(0)}% | bag24h value $${(keepTokens * priceAt(c.cs, c.e, 24) * (1 - FEE)).toFixed(2)} | 72h ret ${r72}% bag $${c.p72 !== null ? (keepTokens * c.p72).toFixed(2) : '—'} | 7d ret ${r168}% bag $${c.p168 !== null ? (keepTokens * c.p168).toFixed(2) : '—'}`);
    }
  }
  return { total, rows };
}

const base = run('sell-all', 72);
console.log(`BASELINE (sell 100% at 24h, incl +5000% cap): total $${base.total.toFixed(0)} on 62 x $10`);
for (const [name, sc] of [['Scenario 1: 10% moon bag, monsters >=5000%', 'moon5k'], ['Scenario 2: 10% moon bag, all >=1000%', 'moon1k']] as [string, 'moon5k' | 'moon1k'][]) {
  for (const h of [72, 168] as const) {
    const r = run(sc, h);
    console.log(`\n${name} — valued at ${h === 72 ? '72h' : '7d'}: total $${r.total.toFixed(0)} (${r.total >= base.total ? '+' : ''}$${(r.total - base.total).toFixed(0)} vs baseline)`);
    for (const row of r.rows) console.log('  ' + row);
  }
}
