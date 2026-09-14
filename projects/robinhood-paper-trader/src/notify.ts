import * as fs from 'node:fs';
import * as path from 'node:path';
import { PROJECT_ROOT } from './config.js';

const DISCORD_TOKEN_PATH = '/Users/apollo/.openclaw/openclaw.json';
const DISCORD_RECIPIENT_ID = '276104854303145994'; // Aaron
const LOG_FILE = path.join(PROJECT_ROOT, 'data', 'events.log');

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
