import type { DatabaseSync } from 'node:sqlite';
import type { Criteria } from './config.js';
import { HORIZONS_H } from './db.js';

export interface BandStat {
  band: 'alerted' | 'near-miss' | 'passed-low' | 'rejected';
  horizon_h: number;
  n: number;
  median_return_pct: number;
  best_return_pct: number;
  worst_return_pct: number;
}

export interface ReportStats {
  last24h: { new_coins: number; passed_gates: number; alerts: number };
  bands: BandStat[];
  top_rejected: { ticker: string; return_pct: number; reason: string }[];
  dead_outcomes: number;
  source_divergences_24h: number;
  total_coins: number;
  regime: {
    current: string;
    distribution_24h: Record<string, number>;
    passed_returns_24h_by_regime: { regime: string; n: number; median_return_pct: number }[];
  };
}

const BAND_SQL: Record<BandStat['band'], string> = {
  'alerted': 'c.alerted = 1',
  'near-miss': 'c.alerted = 0 AND c.passed = 1 AND c.score >= 60',
  'passed-low': 'c.alerted = 0 AND c.passed = 1 AND c.score < 60',
  'rejected': 'c.passed = 0',
};

export function computeReport(db: DatabaseSync, now: number): ReportStats {
  const dayAgo = now - 24 * 3_600_000;
  const last24h = {
    new_coins: count(db, 'SELECT COUNT(*) n FROM coins WHERE first_seen_ms >= ?', dayAgo),
    passed_gates: count(db, 'SELECT COUNT(*) n FROM coins WHERE first_seen_ms >= ? AND passed = 1', dayAgo),
    alerts: count(db, 'SELECT COUNT(*) n FROM coins WHERE alerted = 1'),
  };

  const bands: BandStat[] = [];
  for (const band of Object.keys(BAND_SQL) as BandStat['band'][]) {
    for (const h of HORIZONS_H) {
      const rows = db.prepare(`
        SELECT (o.price - c.price_at_eval) / c.price_at_eval * 100 AS ret
        FROM outcomes o JOIN coins c ON c.address = o.address
        WHERE o.status = 'captured' AND o.horizon_h = ? AND c.price_at_eval > 0 AND ${BAND_SQL[band]}
        ORDER BY ret`).all(h) as unknown as { ret: number }[];
      if (rows.length === 0) continue;
      const rets = rows.map(r => r.ret);
      bands.push({
        band, horizon_h: h, n: rets.length,
        median_return_pct: rets[Math.floor(rets.length / 2)],
        best_return_pct: rets[rets.length - 1],
        worst_return_pct: rets[0],
      });
    }
  }

  const top_rejected = (db.prepare(`
    SELECT c.ticker, (o.price - c.price_at_eval) / c.price_at_eval * 100 AS ret, c.reasons
    FROM outcomes o JOIN coins c ON c.address = o.address
    WHERE o.status = 'captured' AND o.horizon_h = 24 AND c.passed = 0 AND c.price_at_eval > 0
    ORDER BY ret DESC LIMIT 3`).all() as unknown as { ticker: string; ret: number; reasons: string }[])
    .filter(r => r.ret > 0)
    .map(r => ({ ticker: r.ticker, return_pct: r.ret, reason: (JSON.parse(r.reasons)[0] ?? 'unknown') as string }));

  const distribution_24h: Record<string, number> = {};
  for (const row of db.prepare(`SELECT confirmed_label l, COUNT(*) n FROM regime_snapshots WHERE ts >= ? GROUP BY confirmed_label`).all(dayAgo) as any[]) {
    distribution_24h[row.l] = row.n;
  }
  const currentRegime = (db.prepare('SELECT confirmed_label l FROM regime_snapshots ORDER BY ts DESC LIMIT 1').get() as any)?.l ?? 'unknown';
  const passed_returns_24h_by_regime = (db.prepare(`
    SELECT c.regime, COUNT(*) n, (o.price - c.price_at_eval) / c.price_at_eval * 100 AS ret
    FROM outcomes o JOIN coins c ON c.address = o.address
    WHERE o.status = 'captured' AND o.horizon_h = 24 AND c.passed = 1 AND c.price_at_eval > 0
    GROUP BY c.regime`).all() as any[])
    .map(r => ({ regime: r.regime as string, n: r.n as number, median_return_pct: medianReturnForRegime(db, r.regime) }));

  return {
    last24h,
    bands,
    top_rejected,
    dead_outcomes: count(db, `SELECT COUNT(*) n FROM outcomes WHERE status = 'dead'`),
    source_divergences_24h: count(db, 'SELECT COUNT(*) n FROM divergences WHERE ts >= ?', dayAgo),
    total_coins: count(db, 'SELECT COUNT(*) n FROM coins'),
    regime: { current: currentRegime, distribution_24h, passed_returns_24h_by_regime },
  };
}

function medianReturnForRegime(db: DatabaseSync, regime: string): number {
  const rets = (db.prepare(`
    SELECT (o.price - c.price_at_eval) / c.price_at_eval * 100 AS ret
    FROM outcomes o JOIN coins c ON c.address = o.address
    WHERE o.status = 'captured' AND o.horizon_h = 24 AND c.passed = 1 AND c.price_at_eval > 0 AND c.regime = ?
    ORDER BY ret`).all(regime) as any[]).map(r => r.ret as number);
  return rets.length ? rets[Math.floor(rets.length / 2)] : 0;
}

export function formatReport(r: ReportStats): string {
  const lines = [
    `📊 Daily scout report`,
    `Last 24h: ${r.last24h.new_coins} new coins, ${r.last24h.passed_gates} passed gates. Lifetime: ${r.total_coins} tracked, ${r.last24h.alerts} alerts, ${r.dead_outcomes} dead snapshots.`,
  ];
  const order: BandStat['band'][] = ['alerted', 'near-miss', 'passed-low', 'rejected'];
  for (const band of order) {
    const rows = r.bands.filter(b => b.band === band);
    if (!rows.length) continue;
    const cells = rows.map(b => `${b.horizon_h}h: ${fmtPct(b.median_return_pct)} (n=${b.n}, ${fmtPct(b.worst_return_pct)}…${fmtPct(b.best_return_pct)})`);
    lines.push(`${band}: ${cells.join(' | ')}`);
  }
  if (r.top_rejected.length) {
    lines.push(`Rejects that ran (24h): ${r.top_rejected.map(t => `$${t.ticker} +${t.return_pct.toFixed(0)}% [${t.reason}]`).join(', ')}`);
  }
  if (r.source_divergences_24h > 0) {
    lines.push(`⚠️ Source divergences (24h): ${r.source_divergences_24h} (DexScreener vs GMGN — check alerts.log)`);
  }
  const dist = Object.entries(r.regime.distribution_24h).map(([l, n]) => `${l} ${n}`).join(', ');
  lines.push(`Regime: ${r.regime.current} now${dist ? ` (24h scans: ${dist})` : ''}`);
  if (r.regime.passed_returns_24h_by_regime.length) {
    lines.push(`Gate-passer 24h returns by regime: ${r.regime.passed_returns_24h_by_regime.map(x => `${x.regime}: ${fmtPct(x.median_return_pct)} (n=${x.n})`).join(' | ')}`);
  }
  return lines.join('\n');
}

/**
 * Optional Ollama narrative on top of the stats. Fail-soft: null on any error.
 * Framing rule: it interprets measurements and may suggest which criteria to
 * REVIEW, but the human changes criteria.json — no trade advice, no auto-tune.
 */
export async function narrate(r: ReportStats, criteria: Criteria): Promise<string | null> {
  const prompt = `You are reviewing the daily performance stats of a meme-coin alerting system. Its criteria: market cap bands ${JSON.stringify(criteria.market_cap_bands)}, age ${criteria.candle_age_hours.min}-${criteria.candle_age_hours.max}h, top10 holders <= ${criteria.max_top10_holder_rate * 100}%, alert threshold ${criteria.alert_score_threshold}.

STATS (median/worst/best % returns if held from first-seen price to each horizon, by band):
${JSON.stringify(r, null, 1)}

In at most 50 words of plain text: state whether alerted coins are outperforming near-misses and rejects, and name the ONE criteria parameter most worth reviewing based on these numbers (say "sample too small" if any n < 10). No trade advice, no predictions, no invented numbers. Output the summary only.`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), criteria.ollama.timeout_ms);
  try {
    const res = await fetch(`${criteria.ollama.url}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: criteria.ollama.model, prompt, stream: false, think: false, options: { temperature: 0.2, num_predict: 120 } }),
      signal: controller.signal,
    });
    if (!res.ok) return null;
    const body = await res.json() as { response?: string };
    const text = body.response?.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
    return text || null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Serial-deployer context for the daily report (v2.5, Dune-backed): one line
 * per coin alerted in the last 24h. Needs DUNE_API_KEY and a saved query id
 * (docs/dune-creator-history.sql); silently returns [] when unconfigured.
 */
export async function creatorHistoryLines(
  db: DatabaseSync,
  dune: { enabled: boolean; query_id: number },
  apiKey: string,
  now: number,
  fetchHistory: (address: string) => Promise<{ deployer: string; total_launches: number; first_launch: string | null; last_launch: string | null } | null>,
): Promise<string[]> {
  if (!dune.enabled || !dune.query_id || !apiKey) return [];
  const alerted = db.prepare(
    'SELECT address, ticker FROM coins WHERE alerted = 1 AND first_seen_ms >= ? LIMIT 10',
  ).all(now - 24 * 3_600_000) as unknown as { address: string; ticker: string }[];
  const lines: string[] = [];
  for (const c of alerted) {
    const h = await fetchHistory(c.address);
    if (!h) continue;
    const short = `${h.deployer.slice(0, 8)}…`;
    const since = h.first_launch ? ` since ${String(h.first_launch).slice(0, 10)}` : '';
    lines.push(`🏭 $${c.ticker} creator ${short}: ${h.total_launches} launches${since}${h.total_launches >= 5 ? ' ⚠️ serial deployer' : ''}`);
  }
  return lines;
}

function count(db: DatabaseSync, sql: string, ...args: unknown[]): number {
  return ((db.prepare(sql).get(...(args as any)) as any)?.n ?? 0) as number;
}

function fmtPct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(0)}%`;
}
