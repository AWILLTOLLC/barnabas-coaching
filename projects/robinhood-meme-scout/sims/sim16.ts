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

type Coin = { ticker: string; e: number; trigH: number | null; deadH: number | null; cs24: Out[] };
const coins: Coin[] = [];
for (const c of db.prepare(`SELECT address, ticker, price_at_eval e FROM coins WHERE alerted=1 AND price_at_eval > 0`).all() as any[]) {
  const cs24 = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND status='captured' AND h <= 24 ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs24.length) continue;
  const trig = cs24.find(o => o.h > 0 && (o.price - c.e) / c.e >= 10);
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  coins.push({ ticker: c.ticker, e: c.e, trigH: trig ? trig.h : null, deadH: dead && dead.dh != null ? dead.dh : null, cs24 });
}

function plan(c: Coin, boundary: number, capped: boolean): { proceeds: number; per24ret: number } {
  const STAKE = 10;
  if (c.deadH !== null && c.deadH <= boundary) return { proceeds: 0, per24ret: -1 };
  const cs = capped ? c.cs24.map(o => ({ ...o, price: Math.min(o.price, c.e * 51) })) : c.cs24;
  const units0 = STAKE * (1 - FEE) / c.e;
  let remaining = units0, proceeds = 0;
  // moon-bag at trigger only if trigger occurs before boundary
  if (c.trigH !== null && c.trigH <= boundary) { const p = priceAt(cs, c.e, c.trigH); proceeds += sellUsd(remaining * 0.25 * p, p, liqAt(cs, c.trigH)); remaining *= 0.75; }
  // tranches over the last hour before boundary
  const ts = [boundary - 1, boundary - 0.67, boundary - 0.33, boundary];
  const pos = remaining * priceAt(cs, c.e, boundary);
  const l = liqAt(cs, boundary);
  if (pos / Math.max(l, 1) < 0.005) proceeds += sellUsd(pos, priceAt(cs, c.e, boundary), l);
  else for (const t of ts) { const p = priceAt(cs, c.e, t); proceeds += sellUsd(remaining * 0.25 * p, p, liqAt(cs, t)); remaining *= 0.75; }
  return { proceeds, per24ret: proceeds / STAKE - 1 };
}

for (const capped of [true, false]) {
  console.log(capped ? '=== winners capped at +5000% ===' : '=== uncapped (raw) ===');
  for (const b of [6, 8, 12, 16, 18, 24] as const) {
    let total = 0, wins = 0, better = 0;
    const losses: string[] = [], gains: string[] = [];
    for (const c of coins) {
      const p24 = plan(c, 24, capped), pb = plan(c, b, capped);
      total += pb.proceeds;
      if (pb.proceeds > 10) wins++;
      const diff = pb.proceeds - p24.proceeds;
      if (diff > 0.5) { better++; gains.push(`${c.ticker}+${diff.toFixed(0)}`); }
      else if (diff < -0.5) losses.push(`${c.ticker}${diff.toFixed(0)}`);
    }
    console.log(`${String(b).padStart(2)}h boundary: total $${total.toFixed(0)} (${total / 620}x vs 24h ${(0).toFixed(0)}) | wins ${wins}/62 | ${better} coins better vs 24h`);
    console.log(`   better: ${gains.slice(0, 8).join(' ') || '—'}`);
    console.log(`   worse:  ${losses.slice(0, 8).join(' ') || '—'}`);
  }
  console.log();
}
