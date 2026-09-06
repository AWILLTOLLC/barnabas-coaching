import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export interface Criteria {
  candle_age_hours: { min: number; max: number };
  market_cap_bands: [number, number][];
  max_top10_holder_rate: number;
  strong_top10_holder_rate: number;
  min_volume_24h: number;
  strong_volume_24h: number;
  min_liquidity_usd: number;
  strong_liquidity_usd: number;
  max_drop_6h_pct: number;
  alert_score_threshold: number;
  poll_interval_seconds: number;
  heartbeat_hours_pt: number[];
  report_hour_pt: number;
  regime: {
    hot_median_1h_pct: number;
    cold_median_1h_pct: number;
    hot_green_share: number;
    cold_green_share: number;
    confirm_scans: number;
  };
  chain_context: string;
  ollama: { url: string; model: string; timeout_ms: number };
  dexscreener?: {
    enabled: boolean;
    base_url?: string;
    batch_size?: number;
    timeout_ms?: number;
    divergence_pct?: number;
  };
  blockscout?: {
    enabled: boolean;
    base_url?: string;
    timeout_ms?: number;
  };
  dune?: {
    enabled: boolean;
    query_id?: number;
    timeout_ms?: number;
    poll_interval_ms?: number;
  };
}

export function loadCriteria(file: string = path.join(PROJECT_ROOT, 'criteria.json')): Criteria {
  return JSON.parse(fs.readFileSync(file, 'utf8')) as Criteria;
}

export function loadEnv(file: string = path.join(PROJECT_ROOT, '.env')): Record<string, string> {
  const env: Record<string, string> = {};
  if (!fs.existsSync(file)) return env;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq <= 0) continue;
    env[trimmed.slice(0, eq)] = trimmed.slice(eq + 1);
  }
  return env;
}

export { PROJECT_ROOT };
