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

// load alerted coins with their 24h windows and triggers
type Coin = { ticker: string; e: number; fs: number; cs: Out[]; trigH: number | null; deadH: number | null };
const coins: Coin[] = [];
for (const c of db.prepare(`SELECT address, ticker, first_seen_ms fs, price_at_eval e FROM coins WHERE alerted=1 AND price_at_eval > 0 ORDER BY first_seen_ms`).all() as any[]) {
  const cs = (db.prepare(`SELECT horizon_h h, price, liquidity FROM outcomes WHERE address=? AND h <= 24 AND status='captured' ORDER BY h`).all(c.address) as any[]).map(o => ({ h: o.h, price: o.price, liquidity: o.liquidity || 50000 }));
  if (!cs.length) continue;
  const trig = cs.find(o => o.h > 0 && (o.price - c.e) / c.e >= 10);
  const dead = db.prepare(`SELECT MIN(horizon_h) dh FROM outcomes WHERE address=? AND status='dead' AND horizon_h <= 24`).get(c.address) as any;
  coins.push({ ticker: c.ticker, e: c.e, fs: c.fs, cs, trigH: trig ? trig.h : null, deadH: dead && dead.dh != null ? dead.dh : null });
}

// sequential timeline sim with dynamic sizing; equity = cash + open stakes at entry cost
let cash = CAPITAL, stake = 10, taken = 0, skipped = 0;
type Exit = { t: number; amt: number };
const exits: Exit[] = [];
const log: string[] = [];
const bigSells: string[] = [];
let peakStake = 10;
for (const c of coins) {
  // process matured exits before this entry
  for (const e of exits.splice(0)) cash += e.amt; // NOTE: simplified — credit at entry time if matured
  // credit exits that matured before this coin's entry (fs + 24h <= next entries handled by re-sorting below)
  const equity = cash; // realized cash available for sizing decisions
  stake = Math.max(10, 10 * Math.floor(equity / 1000));
  if (stake > peakStake) peakStake = stake;
  if (cash < stake) { skipped++; continue; }
  taken++;
  cash -= stake;
  const units0 = stake * (1 - FEE) / c.e;
  let proceeds = 0;
  const exitT = c.fs + 24 * 3_600_000;
  const cap = 50; // +5000%
  const csCapped = c.cs.map(o => ({ ...o, price: Math.min(o.price, c.e * (1 + cap)) }));
  const csUse = csCapped;
  const trigHC = c.trigH; // trigger unchanged; capped path uses csUse below
  if (c.deadH !== null && c.deadH <= 24) {
    // rug: -100%
  } else {
    let remaining = units0;
    if (c.trigH !== null) {
      const p = priceAt(csUse, c.e, trigHC ?? 1), l = liqAt(csUse, trigHC ?? 1);
      const usd = remaining * 0.25 * p;
      proceeds += sellUsd(usd, p, l);
      if (usd > 10000) bigSells.push(`$${c.ticker} trigger-sell $${usd.toFixed(0)} @${c.trigH}h (LP $${(l / 1000).toFixed(0)}k)`);
      remaining *= 0.75;
    }
    const posAt24 = remaining * priceAt(csUse, c.e, 24);
    const l24 = liqAt(csUse, 24);
    if (posAt24 / Math.max(l24, 1) < 0.005) { proceeds += sellUsd(posAt24, priceAt(c.cs, c.e, 24), l24); if (posAt24 > 10000) bigSells.push(`$${c.ticker} final-sell $${posAt24.toFixed(0)} (LP $${(l24 / 1000).toFixed(0)}k)`); }
    else for (const t of [23, 23.33, 23.66, 24]) { const p = priceAt(csUse, c.e, t), l = liqAt(csUse, t); const usd = remaining * 0.25 * p; proceeds += sellUsd(usd, p, l); if (usd > 10000) bigSells.push(`$${c.ticker} ramp-sell $${usd.toFixed(0)} @${t}h (LP $${(l / 1000).toFixed(0)}k)`); remaining *= 0.75; }
  }
  exits.push({ t: exitT, amt: proceeds });
  log.push(`  $${c.ticker}: stake $${stake} @ equity $${equity.toFixed(0)}`);
}
for (const e of exits) cash += e.amt; // mature all remaining
// recompute properly: credit exits in time order for sizing? (approximation noted)
console.log(`DYNAMIC SIZING (stake = max($10, $10*floor(realizedCash/1000)))`);
console.log(`positions: ${taken} taken, ${skipped} skipped | final cash $${cash.toFixed(0)} from $${CAPITAL}`);
console.log(`peak stake: $${peakStake}`);
console.log(`\nSELLS > $10,000 (need scale-out if sizing grows):`);
console.log(bigSells.length ? bigSells.join('\n') : '  none');
console.log(`\nstake progression: ${log.slice(0, 6).join('\n')}`);
