export interface BlockscoutConfig {
  enabled: boolean;
  base_url: string;
  timeout_ms: number;
}

export const BLOCKSCOUT_DEFAULTS: BlockscoutConfig = {
  enabled: false,
  base_url: 'https://robinhoodchain.blockscout.com',
  timeout_ms: 8000,
};

export interface HolderCheck {
  raw_top10_pct: number;      // top 10 by balance, contracts included (what wallet apps show)
  user_top10_pct: number;     // top 10 EOA-only share (comparable to GMGN's top10_rate)
  contract_names: string[];   // named contracts among the raw top 10 (PoolManager, Pons locker, ...)
  sampled: number;
}

// `/api/v2/tokens/{address}/holders` items carry raw integer balances and an
// address object with is_contract + optional name (verified live 2026-09-06,
// see tests/fixtures/blockscout-holders.json). Supply and decimals come from
// the GMGN token-info call the monitor already makes for finalists.
export function computeHolderCheck(payload: unknown, totalSupplyTokens: number | null, decimals: number | null): HolderCheck | null {
  const items = (payload as any)?.items;
  if (!Array.isArray(items) || items.length === 0) return null;
  if (typeof totalSupplyTokens !== 'number' || totalSupplyTokens <= 0 || typeof decimals !== 'number' || decimals < 0) return null;

  const supplyRaw = totalSupplyTokens * 10 ** decimals;
  const holders: { pct: number; contract: boolean; name: string | null }[] = [];
  for (const it of items) {
    const value = Number(it?.value);
    if (!isFinite(value) || value <= 0) continue;
    const a = it?.address ?? {};
    holders.push({
      pct: (value / supplyRaw) * 100,
      contract: a.is_contract === true,
      name: typeof a.name === 'string' && a.name ? a.name : null,
    });
  }
  if (holders.length === 0) return null;

  const rawTop = holders.slice(0, 10);
  const userTop = holders.filter(h => !h.contract).slice(0, 10);
  return {
    raw_top10_pct: rawTop.reduce((s, h) => s + h.pct, 0),
    user_top10_pct: userTop.reduce((s, h) => s + h.pct, 0),
    contract_names: rawTop.filter(h => h.contract && h.name).map(h => h.name!),
    sampled: holders.length,
  };
}

/** Fail-soft fetch: null on any error. Blockscout wants a browser-ish UA. */
export async function fetchHolderCheck(
  address: string,
  totalSupplyTokens: number | null,
  decimals: number | null,
  cfg: BlockscoutConfig,
): Promise<HolderCheck | null> {
  try {
    const res = await fetch(`${cfg.base_url}/api/v2/tokens/${address}/holders`, {
      signal: AbortSignal.timeout(cfg.timeout_ms),
      headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', Accept: 'application/json' },
    });
    if (!res.ok) return null;
    return computeHolderCheck(await res.json(), totalSupplyTokens, decimals);
  } catch {
    return null;
  }
}
