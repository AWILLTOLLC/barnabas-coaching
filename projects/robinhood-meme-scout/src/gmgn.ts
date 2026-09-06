import { exec } from 'node:child_process';

export interface Coin {
  address: string;
  name: string;
  ticker: string;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  liquidity_usd: number;
  holder_count: number;
  top10_rate: number | null;
  created_at_ms: number | null;
  price_change_6h_pct: number | null;
  renounced_mint: boolean | null;
  renounced_freeze: boolean | null;
  burn_status: string | null;
  wash_trading: boolean;
  launchpad: string | null;
  twitter: string | null;
  website: string | null;
  source: string;
}

// Payload shapes (verified live 2026-09-05, see tests/fixtures/):
//   trending:     { code, data: { rank: [...] } }
//   trenches:     { completed: [...], near_completion: [...], new_creation: [...] }
//   hot-searches: [ { interval, chain, tokens: [...] } ]
function extractTokenArrays(payload: unknown): unknown[][] {
  const arrays: unknown[][] = [];
  const p = payload as any;
  if (Array.isArray(p)) {
    for (const group of p) {
      if (Array.isArray(group?.tokens)) arrays.push(group.tokens);
    }
    return arrays;
  }
  if (Array.isArray(p?.data?.rank)) arrays.push(p.data.rank);
  for (const key of ['completed', 'near_completion', 'new_creation']) {
    if (Array.isArray(p?.[key])) arrays.push(p[key]);
  }
  return arrays;
}

// GMGN timestamps are Unix seconds; anything below 1e12 gets promoted to ms.
function toMs(ts: unknown): number | null {
  if (typeof ts !== 'number' || ts <= 0) return null;
  return ts < 1e12 ? ts * 1000 : ts;
}

export function parseCoins(payload: unknown, source: string): Coin[] {
  const coins: Coin[] = [];
  for (const tokens of extractTokenArrays(payload)) {
    for (const t of tokens as any[]) {
      const address = typeof t?.address === 'string' ? t.address : '';
      const market_cap = typeof t?.market_cap === 'number' ? t.market_cap : 0;
      if (!address || market_cap <= 0) continue;
      coins.push({
        address,
        name: t.name ?? '',
        ticker: t.symbol ?? '',
        price_usd: t.price ?? 0,
        market_cap,
        volume_24h: t.volume ?? t.volume_24h ?? 0,
        liquidity_usd: t.liquidity ?? 0,
        holder_count: t.holder_count ?? 0,
        top10_rate: typeof t.top_10_holder_rate === 'number' ? t.top_10_holder_rate : null,
        created_at_ms: toMs(t.creation_timestamp) ?? toMs(t.open_timestamp),
        // list payloads only carry 1m/5m/1h changes; 6h comes from enrichment
        price_change_6h_pct: null,
        renounced_mint: typeof t.renounced_mint === 'boolean' ? t.renounced_mint : null,
        renounced_freeze: typeof t.renounced_freeze_account === 'boolean' ? t.renounced_freeze_account : null,
        burn_status: t.burn_status ?? null,
        wash_trading: t.is_wash_trading === true,
        launchpad: t.launchpad ?? null,
        twitter: t.twitter_username ?? null,
        website: t.website ?? null,
        source,
      });
    }
  }
  return coins;
}

export function dedupeCoins(coins: Coin[]): Coin[] {
  const seen = new Map<string, Coin>();
  for (const c of coins) {
    if (!seen.has(c.address)) seen.set(c.address, c);
  }
  return [...seen.values()];
}

export interface TokenStats {
  price: number;
  change_6h_pct: number;
  change_24h_pct: number;
}

// `gmgn-cli token info` payload: price fields are strings under .price
export function parseTokenStats(payload: unknown): TokenStats | null {
  const p = (payload as any)?.price;
  const price = Number(p?.price);
  const price6h = Number(p?.price_6h);
  const price24h = Number(p?.price_24h);
  if (!isFinite(price) || !isFinite(price6h) || price6h <= 0 || !isFinite(price24h) || price24h <= 0) return null;
  return {
    price,
    change_6h_pct: ((price - price6h) / price6h) * 100,
    change_24h_pct: ((price - price24h) / price24h) * 100,
  };
}

export async function fetchTokenStats(address: string, env: Record<string, string>): Promise<TokenStats | null> {
  const payload = await execJson(`gmgn-cli token info --chain robinhood --address ${address}`, env);
  return payload === null ? null : parseTokenStats(payload);
}

const COMMANDS: [string, string][] = [
  ['trending', 'gmgn-cli market trending --chain robinhood --interval 1h --limit 50'],
  ['trenches', 'gmgn-cli market trenches --chain robinhood --limit 50'],
  ['hot', 'gmgn-cli market hot-searches --chain robinhood --limit 50'],
];

function execJson(cmd: string, env: Record<string, string>): Promise<unknown | null> {
  return new Promise((resolve) => {
    exec(cmd, { maxBuffer: 10 * 1024 * 1024, env: { ...process.env, ...env } }, (error, stdout) => {
      if (error) {
        console.error(`gmgn-cli failed (${cmd.split(' ').slice(0, 3).join(' ')}): ${error.message.split('\n')[0]}`);
        return resolve(null);
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        console.error(`gmgn-cli returned non-JSON (${cmd.split(' ').slice(0, 3).join(' ')})`);
        resolve(null);
      }
    });
  });
}

export async function fetchAllCoins(env: Record<string, string>): Promise<Coin[]> {
  const all: Coin[] = [];
  for (let i = 0; i < COMMANDS.length; i++) {
    const [source, cmd] = COMMANDS[i];
    const payload = await execJson(cmd, env);
    if (payload !== null) all.push(...parseCoins(payload, source));
    if (i < COMMANDS.length - 1) await new Promise(r => setTimeout(r, 5000));
  }
  return dedupeCoins(all);
}
