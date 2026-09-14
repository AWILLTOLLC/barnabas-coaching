import pathlib
p = pathlib.Path('/Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/src/report.ts'); s = p.read_text()
s = s.replace("    const cells = rows.map(b => `${b.horizon_h}h: ${fmtPct(b.median_return_pct)} (n=${b.n}, ${fmtPct(b.worst_return_pct)}…${fmtPct(b.best_return_pct)})`);",
"    const cells = rows.map(b => `${b.horizon_h}h: ${fmtPct(b.median_return_pct)} (n=${b.n}, ${fmtPct(b.worst_return_pct)}…${fmtPct(b.best_return_pct)}) | $100/coin: ${b.pnl_usd >= 0 ? '+' : ''}$${b.pnl_usd.toFixed(0)} (port ${fmtPct(b.portfolio_return_pct)})`);")
s = s.replace("lines.push(`Gate-passer 24h returns by regime: ${r.regime.passed_returns_24h_by_regime.map(x => `${x.regime}: ${fmtPct(x.median_return_pct)} (n=${x.n})`).join(' | ')}`);",
"lines.push(`Gate-passer 24h returns by regime: ${r.regime.passed_returns_24h_by_regime.map(x => `${x.regime}: ${fmtPct(x.median_return_pct)} (n=${x.n}, port ${fmtPct(x.portfolio_return_pct)})`).join(' | ')}`);")
assert '$100/coin' in s, 'display patch failed'
p.write_text(s); print('stage3 patched')
