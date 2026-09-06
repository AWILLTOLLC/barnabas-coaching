/**
 * Alert Delivery - iMessage + SQLite
 * Ponytail: Minimal, uses imsg CLI
 */

import { GMGNCoin } from './gmgn-monitor.js';
import * as fs from 'fs';
import * as path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'alerts.db');

/**
 * Discord DM delivery via bot REST API (zero-token path)
 * Bot token read from openclaw.json; recipient is Aaron's Discord ID (DM allowlist).
 */
const DISCORD_TOKEN_PATH = '/Users/apollo/.openclaw/openclaw.json';
const DISCORD_RECIPIENT_ID = '276104854303145994';

async function sendDiscordDM(message: string): Promise<{ success: boolean; error?: string }> {
  try {
    const config = JSON.parse(fs.readFileSync(DISCORD_TOKEN_PATH, 'utf8'));
    const token = config?.channels?.discord?.token;
    if (!token) return { success: false, error: 'no discord token in openclaw.json' };

    const headers = { 'Authorization': `Bot ${token}`, 'Content-Type': 'application/json' };

    // Get or create DM channel with recipient
    const dmRes = await fetch('https://discord.com/api/v10/users/@me/channels', {
      method: 'POST', headers, body: JSON.stringify({ recipient_id: DISCORD_RECIPIENT_ID })
    });
    if (!dmRes.ok) return { success: false, error: `DM channel create failed: ${dmRes.status}` };
    const dm = await dmRes.json() as { id: string };

    const sendRes = await fetch(`https://discord.com/api/v10/channels/${dm.id}/messages`, {
      method: 'POST', headers, body: JSON.stringify({ content: message })
    });
    if (!sendRes.ok) return { success: false, error: `message send failed: ${sendRes.status}` };
    return { success: true };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/**
 * Send alert to Aaron via iMessage
 */
export async function sendAlert(
  coin: GMGNCoin, 
  score: number, 
  customMessage?: string
) {
  const message = customMessage || formatAlertMessage(coin, score);
  
  // Discord DM only (Aaron: no iMessage alerts)
  const discord = await sendDiscordDM(message);
  if (!discord.success) {
    console.error('Discord DM failed:', discord.error);
  }
  const result = discord;
  
  // Log to SQLite
  await logAlert(coin, score, result.success);
  
  return result;
}

/**
 * Format alert message
 */
function formatAlertMessage(coin: GMGNCoin, score: number): string {
  return `🚀 GMGN Signal: $${coin.ticker}
Score: ${score}/100
MC: $${(coin.market_cap / 1_000_000).toFixed(1)}M
Age: ${((Date.now() - new Date(coin.created_at).getTime()) / 3600_000).toFixed(0)}h
Volume: $${(coin.volume_24h / 1_000_000).toFixed(1)}M
CA: ${coin.contract_address}

Review at Robinhood app.`;
}

/**
 * Call imsg CLI
 */
async function execImsg(message: string): Promise<{ success: boolean; error?: string }> {
  try {
    const { exec } = await import('child_process');
    return new Promise((resolve) => {
      exec(`imsg action=send channel=webchat target=mac@kaw.cc message="${message}"`, 
        (error, stdout, stderr) => {
          if (error) {
            resolve({ success: false, error: error.message });
          } else {
            resolve({ success: true });
          }
        });
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Log alert to SQLite
 */
async function logAlert(coin: GMGNCoin, score: number, success: boolean) {
  // ponytail: use simple JSON file instead of full SQLite setup
  const logDir = path.dirname(DB_PATH);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  const logFile = path.join(logDir, 'alerts.log');
  const entry = {
    timestamp: new Date().toISOString(),
    ticker: coin.ticker,
    contract_address: coin.contract_address,
    score,
    market_cap: coin.market_cap,
    success,
  };

  fs.appendFileSync(logFile, JSON.stringify(entry) + '\n');
}
