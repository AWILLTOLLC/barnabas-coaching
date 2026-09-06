import * as fs from 'node:fs';
import * as path from 'node:path';
import type { Coin } from './gmgn.js';
import type { Evaluation } from './filters.js';
import { PROJECT_ROOT } from './config.js';

const DISCORD_TOKEN_PATH = '/Users/apollo/.openclaw/openclaw.json';
const DISCORD_RECIPIENT_ID = '276104854303145994'; // Aaron
const LOG_FILE = path.join(PROJECT_ROOT, 'data', 'alerts.log');

export interface HeartbeatStats {
  scanned: number;
  passed_gates: number;
  alerted: string[];
  best: { ticker: string; score: number } | null;
  since: string;
}

export function formatAlert(coin: Coin, ev: Evaluation): string {
  const ageH = coin.created_at_ms ? ((Date.now() - coin.created_at_ms) / 3_600_000).toFixed(0) : '?';
  const lines = [
    `🚀 Robinhood Scout: $${coin.ticker} (${coin.name}) — ${ev.score}/100`,
    `MC $${m(coin.market_cap)} | Vol $${m(coin.volume_24h)} | Liq $${m(coin.liquidity_usd)} | Age ${ageH}h`,
    `Holders ${coin.holder_count}${coin.top10_rate !== null ? ` (top10 ${(coin.top10_rate * 100).toFixed(0)}%)` : ''}`,
    `Score: ${ev.reasons.join(', ')}`,
  ];
  if (ev.flags.length) lines.push(`⚠️ ${ev.flags.join(', ')}`);
  lines.push(`CA: ${coin.address}`);
  lines.push(`https://gmgn.ai/robinhood/token/${coin.address}`);
  if (coin.twitter) lines.push(`X: ${coin.twitter}`);
  if (coin.website) lines.push(`Web: ${coin.website}`);
  return lines.join('\n');
}

export function formatHeartbeat(s: HeartbeatStats): string {
  const lines = [
    `💓 Scout alive — since ${s.since}: scanned ${s.scanned} coins, ${s.passed_gates} passed gates, ${s.alerted.length} alert${s.alerted.length === 1 ? '' : 's'}.`,
  ];
  if (s.alerted.length) lines.push(`Alerted: ${s.alerted.map(t => `$${t}`).join(', ')}`);
  if (s.best && !s.alerted.length) lines.push(`Best non-alert: $${s.best.ticker} at ${s.best.score}/100`);
  return lines.join('\n');
}

export async function sendDM(message: string, opts: { dryRun: boolean }): Promise<{ success: boolean; error?: string }> {
  if (opts.dryRun) {
    console.log(`[DRY RUN] Discord DM:\n${message}\n`);
    return { success: true };
  }
  try {
    const config = JSON.parse(fs.readFileSync(DISCORD_TOKEN_PATH, 'utf8'));
    const token = config?.channels?.discord?.token;
    if (!token) return { success: false, error: 'no discord token in openclaw.json' };
    const headers = { 'Authorization': `Bot ${token}`, 'Content-Type': 'application/json' };

    const dmRes = await fetch('https://discord.com/api/v10/users/@me/channels', {
      method: 'POST', headers, body: JSON.stringify({ recipient_id: DISCORD_RECIPIENT_ID }),
    });
    if (!dmRes.ok) return { success: false, error: `DM channel create failed: ${dmRes.status}` };
    const dm = await dmRes.json() as { id: string };

    const sendRes = await fetch(`https://discord.com/api/v10/channels/${dm.id}/messages`, {
      method: 'POST', headers, body: JSON.stringify({ content: message }),
    });
    if (!sendRes.ok) return { success: false, error: `message send failed: ${sendRes.status}` };
    return { success: true };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

export function logEvent(event: Record<string, unknown>): void {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fs.appendFileSync(LOG_FILE, JSON.stringify({ timestamp: new Date().toISOString(), ...event }) + '\n');
}

function m(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toFixed(0);
}
