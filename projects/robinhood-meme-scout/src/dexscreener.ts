import type { TokenStats } from './gmgn.js';

export interface DexConfig {
  enabled: boolean;
  base_url: string;
  batch_size: number;
  timeout_ms: number;
  divergence_pct: number;
}

export const DEX_DEFAULTS: DexConfig = {
  enabled: false,
  base_url: 'https://api.dexscreener.com',
  batch_size: 30,
  timeout_ms: 5000,
  divergence_pct: 25,
};

export interface DexStats {
  price: number;
  change_6h_pct: number | null;
  change_24h_pct: number | null;
  liquidity_usd: number | null;
  market_cap: number | null;
  dex_id: string;
}

// `GET /tokens/v1/robinhood/{addr,...}` returns a flat array of pair objects
// (verified live 2026-09-06, see tests/fixtures/dexscreener-tokens.json).
// One token can trade in several pools; the deepest-liquidity pair wins.
export function parseTokenBatch(payload: unknown): Map<string, DexStats> {
  const stats = new Map<string, DexStats>();
  const depth = new Map<string, number>();
  if (!Array.isArray(payload)) return stats;
  for (const p of payload as any[]) {
    const address = typeof p?.baseToken?.address === 'string' ? p.baseToken.address.toLowerCase() : '';
    const price = Number(p?.priceUsd);
    if (!address || !isFinite(price) || price <= 0) continue;
    const liquidity = Number(p?.liquidity?.usd);
    const liq = isFinite(liquidity) ? liquidity : 0;
    if (stats.has(address) && liq <= (depth.get(address) ?? 0)) continue;
    const h6 = Number(p?.priceChange?.h6);
    const h24 = Number(p?.priceChange?.h24);
    const mc = Number(p?.marketCap);
    stats.set(address, {
      price,
      change_6h_pct: typeof p?.priceChange?.h6 === 'number' && isFinite(h6) ? h6 : null,
      change_24h_pct: typeof p?.priceChange?.h24 === 'number' && isFinite(h24) ? h24 : null,
      liquidity_usd: isFinite(liquidity) ? liquidity : null,
      market_cap: isFinite(mc) && mc > 0 ? mc : null,
      dex_id: typeof p?.dexId === 'string' ? p.dexId : '',
    });
    depth.set(address, liq);
  }
  return stats;
}

/**
 * Compare the two sources for the same token. Returns which field diverges
 * ('price' | 'liquidity') or null. Price: relative gap > pct. Liquidity: >2x
 * ratio. Unknown values on either side never count as divergence.
 */
export function checkDivergence(dex: DexStats, gmgn: TokenStats, pct: number): 'price' | 'liquidity' | null {
  const priceGap = Math.abs(dex.price - gmgn.price) / Math.max(Math.abs(dex.price), Math.abs(gmgn.price)) * 100;
  if (priceGap > pct) return 'price';
  if (dex.liquidity_usd !== null && gmgn.liquidity_usd !== null && dex.liquidity_usd > 0 && gmgn.liquidity_usd > 0) {
    const ratio = Math.max(dex.liquidity_usd, gmgn.liquidity_usd) / Math.min(dex.liquidity_usd, gmgn.liquidity_usd);
    if (ratio > 2) return 'liquidity';
  }
  return null;
}

/**
 * Batch-fetch stats for up to `batch_size` addresses per request.
 * Fail-soft: a failed chunk contributes nothing; callers treat missing
 * addresses via their own fallback (GMGN), so an outage degrades, not breaks.
 */
export async function fetchDexStatsBatch(addresses: string[], cfg: DexConfig): Promise<Map<string, DexStats>> {
  const all = new Map<string, DexStats>();
  for (let i = 0; i < addresses.length; i += cfg.batch_size) {
    const chunk = addresses.slice(i, i + cfg.batch_size);
    try {
      const res = await fetch(`${cfg.base_url}/tokens/v1/robinhood/${chunk.join(',')}`, {
        signal: AbortSignal.timeout(cfg.timeout_ms),
      });
      if (!res.ok) {
        console.error(`dexscreener HTTP ${res.status} (${chunk.length} addresses)`);
        continue;
      }
      for (const [addr, s] of parseTokenBatch(await res.json())) all.set(addr, s);
    } catch (err) {
      console.error(`dexscreener fetch failed: ${(err as Error).message}`);
    }
  }
  return all;
}
