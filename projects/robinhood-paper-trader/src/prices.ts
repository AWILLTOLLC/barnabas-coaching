import { exec } from 'node:child_process';

export interface Mark {
  price_usd: number;
  liquidity_usd: number;
}

export interface PricesConfig {
  base_url: string;
  batch_size: number;
  timeout_ms: number;
  gmgn_fallback_per_cycle: number;
}

export const PRICES_DEFAULTS: PricesConfig = {
  base_url: 'https://api.dexscreener.com',
  batch_size: 30,
  timeout_ms: 5000,
  gmgn_fallback_per_cycle: 5,
};

// `GET /tokens/v1/robinhood/{addr,...}` returns a flat array of pair objects;
// the deepest-liquidity pair wins per token. (Same shape the scout verified
// live 2026-09-06; fixture: tests/fixtures/dexscreener-tokens.json.)
export function parseDexBatch(payload: unknown): Map<string, Mark> {
  const marks = new Map<string, Mark>();
  const depth = new Map<string, number>();
  if (!Array.isArray(payload)) return marks;
  for (const p of payload as any[]) {
    const address = typeof p?.baseToken?.address === 'string' ? p.baseToken.address.toLowerCase() : '';
    const price = Number(p?.priceUsd);
    const liquidity = Number(p?.liquidity?.usd);
    if (!address || !isFinite(price) || price <= 0 || !isFinite(liquidity) || liquidity <= 0) continue;
    if (marks.has(address) && liquidity <= (depth.get(address) ?? 0)) continue;
    marks.set(address, { price_usd: price, liquidity_usd: liquidity });
    depth.set(address, liquidity);
  }
  return marks;
}

async function fetchDex(addresses: string[], cfg: PricesConfig): Promise<Map<string, Mark>> {
  const all = new Map<string, Mark>();
  for (let i = 0; i < addresses.length; i += cfg.batch_size) {
    const chunk = addresses.slice(i, i + cfg.batch_size);
    try {
      const res = await fetch(`${cfg.base_url}/tokens/v1/robinhood/${chunk.join(',')}`, { signal: AbortSignal.timeout(cfg.timeout_ms) });
      if (!res.ok) continue;
      for (const [a, m] of parseDexBatch(await res.json())) all.set(a, m);
    } catch (err) {
      console.error(`dexscreener fetch failed: ${(err as Error).message}`);
    }
  }
  return all;
}

async function fetchGmgnOne(address: string, env: Record<string, string>): Promise<Mark | null> {
  return new Promise((resolve) => {
    exec(`gmgn-cli token info --chain robinhood --address ${address}`,
      { maxBuffer: 10 * 1024 * 1024, env: { ...process.env, ...env } },
      (error, stdout) => {
        if (error) return resolve(null);
        try {
          const p = JSON.parse(stdout);
          const price = Number(p?.price?.price);
          const liquidity = Number(p?.liquidity);
          if (!isFinite(price) || price <= 0 || !isFinite(liquidity) || liquidity <= 0) return resolve(null);
          resolve({ price_usd: price, liquidity_usd: liquidity });
        } catch {
          resolve(null);
        }
      });
  });
}

/**
 * Marks for a set of addresses: DexScreener batch primary, gmgn-cli per-token
 * fallback (capped per cycle). Misses are simply absent from the map — the
 * engine's missed-mark counter handles the rest.
 */
export async function fetchMarks(
  addresses: string[],
  env: Record<string, string>,
  cfg: PricesConfig = PRICES_DEFAULTS,
  deps: { dex?: typeof fetchDex; gmgn?: typeof fetchGmgnOne } = {},
): Promise<Map<string, Mark>> {
  if (addresses.length === 0) return new Map();
  const marks = await (deps.dex ?? fetchDex)(addresses, cfg);
  const misses = addresses.filter(a => !marks.has(a.toLowerCase()));
  for (const a of misses.slice(0, cfg.gmgn_fallback_per_cycle)) {
    const m = await (deps.gmgn ?? fetchGmgnOne)(a, env);
    if (m) marks.set(a.toLowerCase(), m);
  }
  return marks;
}
