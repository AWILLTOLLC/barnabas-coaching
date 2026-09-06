import * as fs from 'node:fs';
import * as path from 'node:path';
import { loadCriteria, loadEnv, PROJECT_ROOT, type Criteria } from './config.js';
import { fetchAllCoins, fetchTokenStats, type Coin, type TokenStats } from './gmgn.js';
import { evaluate } from './filters.js';
import { generateThesis } from './thesis.js';
import { formatAlert, formatHeartbeat, sendDM, logEvent, type HeartbeatStats } from './alerts.js';
import { dueSlot, loadHeartbeatState, saveHeartbeatState } from './heartbeat.js';
import { openDb, recordCoin, hasCoin, markAlerted } from './db.js';
import { captureDueOutcomes } from './outcomes.js';
import type { DatabaseSync } from 'node:sqlite';

export interface ScanResult {
  scanned: number;
  passed_gates: number;
  alerted: string[];
  best: { ticker: string; score: number } | null;
}

export interface MonitorOptions {
  dryRun: boolean;
  dataDir?: string;
  fetch?: () => Promise<Coin[]>;
  fetchStats?: (address: string) => Promise<TokenStats | null>;
  thesis?: (coin: Coin, ev: ReturnType<typeof evaluate>) => Promise<string | null>;
  criteria?: Criteria;
}

export class Monitor {
  private dryRun: boolean;
  private dataDir: string;
  private fetchCoins: () => Promise<Coin[]>;
  private fetchStats: (address: string) => Promise<TokenStats | null>;
  private thesis: (coin: Coin, ev: ReturnType<typeof evaluate>) => Promise<string | null>;
  private criteria: Criteria;
  private known: Set<string>;
  readonly db: DatabaseSync;
  private stats: { scanned: number; passed_gates: number; alerted: string[]; best: { ticker: string; score: number } | null; since: Date };

  constructor(opts: MonitorOptions) {
    this.dryRun = opts.dryRun;
    this.dataDir = opts.dataDir ?? path.join(PROJECT_ROOT, 'data');
    const env = loadEnv();
    this.fetchCoins = opts.fetch ?? (() => fetchAllCoins(env));
    this.fetchStats = opts.fetchStats ?? ((address) => fetchTokenStats(address, env));
    this.criteria = opts.criteria ?? loadCriteria();
    this.thesis = opts.thesis ?? ((coin, ev) => generateThesis(coin, ev, this.criteria));
    this.known = this.loadKnown();
    this.db = openDb(path.join(this.dataDir, 'scout.db'));
    this.stats = this.freshStats();
  }

  async scanOnce(): Promise<ScanResult> {
    const coins = await this.fetchCoins();
    const result: ScanResult = { scanned: coins.length, passed_gates: 0, alerted: [], best: null };

    for (let c of coins) {
      if (this.known.has(c.address)) continue;
      const firstSeen = !hasCoin(this.db, c.address);
      let ev = evaluate(c, this.criteria);
      let alerted = false;
      if (!ev.passed) {
        if (firstSeen) recordCoin(this.db, c, ev, false, Date.now());
        continue;
      }
      if (firstSeen) {
        result.passed_gates++;
        logEvent({ event: 'evaluated', ticker: c.ticker, address: c.address, score: ev.score, flags: ev.flags });
      }

      if (ev.score >= this.criteria.alert_score_threshold) {
        // finalists get a momentum check before alerting: list payloads
        // have no 6h change, so enrich from token info and re-evaluate
        if (c.price_change_6h_pct === null) {
          const stats = await this.fetchStats(c.address);
          if (stats) {
            c = { ...c, price_change_6h_pct: stats.change_6h_pct };
            ev = evaluate(c, this.criteria);
            if (!ev.passed || ev.score < this.criteria.alert_score_threshold) {
              logEvent({ event: 'momentum_reject', ticker: c.ticker, address: c.address, change_6h_pct: stats.change_6h_pct });
              if (firstSeen) recordCoin(this.db, c, ev, false, Date.now());
              continue;
            }
          }
        }
        const thesis = await this.thesis(c, ev);
        const dm = await sendDM(formatAlert(c, ev, thesis), { dryRun: this.dryRun });
        logEvent({ event: 'alert', ticker: c.ticker, address: c.address, score: ev.score, success: dm.success, error: dm.error });
        if (dm.success) {
          alerted = true;
          result.alerted.push(c.ticker);
          this.known.add(c.address);
          this.saveKnown();
          if (!firstSeen) markAlerted(this.db, c.address, ev.score);
        }
      } else if (!result.best || ev.score > result.best.score) {
        result.best = { ticker: c.ticker, score: ev.score };
      }
      if (firstSeen) recordCoin(this.db, c, ev, alerted, Date.now());
    }

    // outcome tracking piggybacks on the poll loop, a few fetches per tick
    await captureDueOutcomes(this.db, this.fetchStats, Date.now(), 5);

    this.stats.scanned += result.scanned;
    this.stats.passed_gates += result.passed_gates;
    this.stats.alerted.push(...result.alerted);
    if (result.best && (!this.stats.best || result.best.score > this.stats.best.score)) {
      this.stats.best = result.best;
    }
    return result;
  }

  async run(): Promise<never> {
    console.log(`🔭 Robinhood scout started (${this.dryRun ? 'dry-run' : 'live'}). Known: ${this.known.size} addresses.`);
    while (true) {
      try {
        const r = await this.scanOnce();
        console.log(`[${new Date().toISOString()}] scanned ${r.scanned}, gates ${r.passed_gates}, alerts ${r.alerted.length}${r.best ? `, best $${r.best.ticker}@${r.best.score}` : ''}`);
        await this.maybeHeartbeat();
        await sleep(this.criteria.poll_interval_seconds * 1000);
      } catch (err) {
        console.error('scan error:', err);
        await sleep(60_000);
      }
    }
  }

  private async maybeHeartbeat(): Promise<void> {
    const stateFile = path.join(this.dataDir, 'heartbeat.json');
    const slot = dueSlot(new Date(), loadHeartbeatState(stateFile), this.criteria.heartbeat_hours_pt);
    if (slot === null) return;
    const hb: HeartbeatStats = {
      scanned: this.stats.scanned,
      passed_gates: this.stats.passed_gates,
      alerted: this.stats.alerted,
      best: this.stats.best,
      since: this.stats.since.toLocaleString('en-US', { timeZone: 'America/Los_Angeles', hour: 'numeric', minute: '2-digit' }),
    };
    const dm = await sendDM(formatHeartbeat(hb), { dryRun: this.dryRun });
    logEvent({ event: 'heartbeat', slot, success: dm.success, error: dm.error });
    if (dm.success) {
      const { date } = laDate();
      saveHeartbeatState(stateFile, { date, slot });
      this.stats = this.freshStats();
    }
  }

  private freshStats() {
    return { scanned: 0, passed_gates: 0, alerted: [] as string[], best: null as { ticker: string; score: number } | null, since: new Date() };
  }

  private loadKnown(): Set<string> {
    const file = path.join(this.dataDir, 'known.json');
    try {
      if (fs.existsSync(file)) return new Set(JSON.parse(fs.readFileSync(file, 'utf8')) as string[]);
    } catch (err) {
      console.error('failed to load known.json:', err);
    }
    return new Set();
  }

  private saveKnown(): void {
    fs.mkdirSync(this.dataDir, { recursive: true });
    fs.writeFileSync(path.join(this.dataDir, 'known.json'), JSON.stringify([...this.known], null, 2));
  }
}

function laDate(): { date: string } {
  const fmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' });
  return { date: fmt.format(new Date()) };
}

function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}
