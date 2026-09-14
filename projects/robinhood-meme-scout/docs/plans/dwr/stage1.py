import pathlib
p = pathlib.Path('/Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/src/report.ts'); s = p.read_text()
s = s.replace("""  median_return_pct: number;
  best_return_pct: number;
  worst_return_pct: number;""",
"""  median_return_pct: number;
  best_return_pct: number;
  worst_return_pct: number;
  pnl_usd: number;
  portfolio_return_pct: number;""")
s = s.replace("""      bands.push({
        band, horizon_h: h, n: rets.length,
        median_return_pct: rets[Math.floor(rets.length / 2)],
        best_return_pct: rets[rets.length - 1],
        worst_return_pct: rets[0],
      });""",
"""      bands.push({
        band, horizon_h: h, n: rets.length,
        median_return_pct: rets[Math.floor(rets.length / 2)],
        best_return_pct: rets[rets.length - 1],
        worst_return_pct: rets[0],
        pnl_usd: rets.reduce((a, r) => a + r, 0),
        portfolio_return_pct: rets.reduce((a, r) => a + r, 0) / rets.length,
      });""")
assert 'pnl_usd' in s, 'band patch failed'
p.write_text(s); print('stage1 patched')
