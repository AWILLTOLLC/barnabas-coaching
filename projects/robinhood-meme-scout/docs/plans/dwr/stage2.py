import pathlib
p = pathlib.Path('/Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/src/report.ts'); s = p.read_text()
s = s.replace("passed_returns_24h_by_regime: { regime: string; n: number; median_return_pct: number }[];",
"passed_returns_24h_by_regime: { regime: string; n: number; median_return_pct: number; portfolio_return_pct: number }[];")
s = s.replace("""function medianReturnForRegime(db: DatabaseSync, regime: string): number {""",
"""function portfolioReturnForRegime(db: DatabaseSync, regime: string): number {
  const rets = (db.prepare(`
    SELECT (o.price - c.price_at_eval) / c.price_at_eval * 100 AS ret
    FROM outcomes o JOIN coins c ON c.address = o.address
    WHERE o.status = 'captured' AND o.horizon_h = 24 AND c.passed = 1 AND c.price_at_eval > 0 AND c.regime = ?
    ORDER BY ret`).all(regime) as any[]).map(r => r.ret as number);
  return rets.length ? rets.reduce((a, r) => a + r, 0) / rets.length : 0;
}

function medianReturnForRegime(db: DatabaseSync, regime: string): number {""")
s = s.replace(".map(r => ({ regime: r.regime as string, n: r.n as number, median_return_pct: medianReturnForRegime(db, r.regime) }));",
".map(r => ({ regime: r.regime as string, n: r.n as number, median_return_pct: medianReturnForRegime(db, r.regime), portfolio_return_pct: portfolioReturnForRegime(db, r.regime) }));")
assert 'portfolioReturnForRegime' in s, 'regime patch failed'
p.write_text(s); print('stage2 patched')
