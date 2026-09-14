import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

export const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export interface Strategy {
  starting_capital_usd: number;
  base_stake_usd: number;
  ladder_step_usd: number;
  max_stake_usd: number;
  max_entry_lp_ratio: number;
  max_orders_per_day: number;
  max_daily_deployment_usd: number;
  max_open_positions: number;
  moonbag: { trigger_pct: number; sell_fraction: number };
  exit: {
    boundary_hours: number;
    oneshot_max_lp_ratio: number;
    tranche_schedule_hours: number[];
    tranche_max_lp_ratio: number;
    big_sell_usd: number;
  };
  slippage: { default_pct: number; escalate_pct: number; max_pct: number };
  fee_pct: number;
  mark_interval_seconds: number;
  executor: { type: 'builtin' } | { type: 'external'; command: string; timeout_ms?: number };
  discord: { enabled: boolean };
}

export function loadStrategy(file: string = path.join(PROJECT_ROOT, 'strategy.json')): Strategy {
  return JSON.parse(fs.readFileSync(file, 'utf8')) as Strategy;
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
