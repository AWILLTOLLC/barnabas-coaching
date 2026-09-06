import * as fs from 'node:fs';
import * as path from 'node:path';

export interface HeartbeatState {
  date: string;
  slot: number;
}

const LA_FMT = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'America/Los_Angeles',
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', hour12: false,
});

export function laParts(d: Date): { date: string; hour: number } {
  const parts = Object.fromEntries(LA_FMT.formatToParts(d).map(p => [p.type, p.value]));
  // Intl may render midnight as "24" depending on runtime
  const hour = Number(parts.hour) % 24;
  return { date: `${parts.year}-${parts.month}-${parts.day}`, hour };
}

/**
 * Returns the heartbeat slot due right now, or null.
 * Active window is [first slot, last slot] LA time; outside it, silent.
 * A restart after downtime sends only the latest elapsed slot — no backfill.
 */
export function dueSlot(now: Date, lastSent: HeartbeatState | null, hours: number[]): number | null {
  const { date, hour } = laParts(now);
  const sorted = [...hours].sort((a, b) => a - b);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  if (hour < first || hour > last) return null;
  const latest = sorted.filter(h => h <= hour).pop();
  if (latest === undefined) return null;
  if (lastSent && lastSent.date === date && lastSent.slot === latest) return null;
  return latest;
}

export function loadHeartbeatState(file: string): HeartbeatState | null {
  try {
    if (!fs.existsSync(file)) return null;
    return JSON.parse(fs.readFileSync(file, 'utf8')) as HeartbeatState;
  } catch {
    return null;
  }
}

export function saveHeartbeatState(file: string, state: HeartbeatState): void {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(state));
}
