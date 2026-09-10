import * as fs from 'node:fs';
import * as path from 'node:path';
import { loadCriteria, loadEnv, PROJECT_ROOT, type Criteria } from './config.js';
import { fetchAllCoins, fetchTokenStats, type Coin, type TokenStats } from './gmgn.js';
import { evaluate } from './filters.js';
import { generateThesis } from './thesis.js';
import { liquidityBaseline } from './peers.js';
import { formatAlert, formatHeartbeat, sendDM, logEvent, type HeartbeatStats } from './alerts.js';
import { dueSlot, loadHeartbeatState, saveHeartbeatState } from './heartbeat.js';
import { openDb, recordCoin, hasCoin, markAlerted, recordRegimeSnapshot, lastConfirmedRegime, recordDivergence } from './db.js';
import { DEX_DEFAULTS, fetchDexStatsBatch, checkDivergence, type DexConfig, type DexStats } from './dexscreener.js';
import { BLOCKSCOUT_DEFAULTS, fetchHolderCheck, type BlockscoutConfig, type HolderCheck } from './blockscout.js';
import { computeBreadth, labelRegime, RegimeTracker, type RegimeLabel } from './regime.js';
import { captureDueOutcomes } from './outcomes.js';
import { computeReport, formatReport, narrate, creatorHistoryLines } from './report.js';
import { DUNE_DEFAULTS, fetchCreatorHistory, type DuneConfig } from './dune.js';
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
  fetchDex?: (addresses: string[]) => Promise<Map<string, DexStats>>;
  fetchHolders?: (address: string, totalSupply: number | null, decimals: number | null) => Promise<HolderCheck | null>;
  thesis?: (coin: Coin, ev: ReturnType<typeof evaluate>) => Promise<string | null>;
  criteria?: Criteria;
}

export class Monitor {
  private dryRun: boolean;
  private dataDir: string;
  private fetchCoins: () => Promise<Coin[]>;
  private fetchStats: (address: string) => Promise<TokenStats | null>;
  private fetchDex?: (addresses: string[]) => Promise<Map<string, DexStats>>;
  private fetchHolders?: (address: string, totalSupply: number | null, decimals: number | null) => Promise<HolderCheck | null>;
  private dexCfg: DexConfig;
  private bsCfg: BlockscoutConfig;
  private duneCfg: DuneConfig;
  private duneKey: string;
  private thesis: (coin: Coin, ev: ReturnType<typeof evaluate>) => Promise<string | null>;
  private criteria: Criteria;
  private known: Set<string>;
  readonly db: DatabaseSync;
  readonly regime: RegimeTracker;
  private stats: { scanned: number; passed_gates: number; alerted: string[]; best: { ticker: string; score: number } | null; since: Date };

  constructor(opts: MonitorOptions) {
    this.dryRun = opts.dryRun;
    this.dataDir = opts.dataDir ?? path.join(PROJECT_ROOT, 'data');
    const env = loadEnv();
    this.fetchCoins = opts.fetch ?? (() => fetchAllCoins(env));
    this.fetchStats = opts.fetchStats ?? ((address) => fetchTokenStats(address, env));
    this.criteria = opts.criteria ?? loadCriteria();
    this.dexCfg = { ...DEX_DEFAULTS, ...(this.criteria.dexscreener ?? {}) };
    this.fetchDex = opts.fetchDex ?? (this.dexCfg.enabled ? (addresses) => fetchDexStatsBatch(addresses, this.dexCfg) : undefined);
    this.bsCfg = { ...BLOCKSCOUT_DEFAULTS, ...(this.criteria.blockscout ?? {}) };
    this.fetchHolders = opts.fetchHolders ?? (this.bsCfg.enabled ? (a, ts, dec) => fetchHolderCheck(a, ts, dec, this.bsCfg) : undefined);
    this.duneCfg = { ...DUNE_DEFAULTS, ...(this.criteria.dune ?? {}) };
    this.duneKey = env.DUNE_API_KEY ?? '';
    this.thesis = opts.thesis ?? ((coin, ev) => generateThesis(coin, ev, this.criteria, {
      regime: this.regime?.current,
      liqPeers: liquidityBaseline(this.db, coin, this.criteria.market_cap_bands, Date.now()),
    }));
    this.known = this.loadKnown();
    this.db = openDb(path.join(this.dataDir, 'scout.db'));
    this.regime = new RegimeTracker((lastConfirmedRegime(this.db) as RegimeLabel) ?? 'neutral', this.criteria.regime);
    this.stats = this.freshStats();
  }

  async scanOnce(): Promise<ScanResult> {
    const coins = await this.fetchCoins();
    const result: ScanResult = { scanned: coins.length, passed_gates: 0, alerted: [], best: null };

    // chain regime: measure-and-stamp only, never gates alerts (yet)
    const breadth = computeBreadth(coins, Date.now());
    const raw = labelRegime(breadth, this.criteria.regime);
    const confirmed = this.regime.update(raw);
    recordRegimeSnapshot(this.db, Date.now(), breadth, raw, confirmed);

    for (let c of coins) {
      if (this.known.has(c.address)) continue;
      const firstSeen = !hasCoin(this.db, c.address);
      let ev = evaluate(c, this.criteria);
      let alerted = false;
      if (!ev.passed) {
        if (firstSeen) recordCoin(this.db, c, ev, false, Date.now(), confirmed);
        continue;
      }
      if (firstSeen) {
        result.passed_gates++;
        logEvent({ event: 'evaluated', ticker: c.ticker, address: c.address, score: ev.score, flags: ev.flags });
      }

      if (ev.score >= this.criteria.alert_score_threshold) {
        // finalists get a momentum check before alerting: list payloads have
        // no 6h change. DexScreener is primary, GMGN token info is fallback
        // and cross-check — a divergence is recorded, never gates the alert.
        if (c.price_change_6h_pct === null) {
          const dex = this.fetchDex ? (await this.fetchDex([c.address])).get(c.address.toLowerCase()) : undefined;
          const stats = await this.fetchStats(c.address);
          if (dex && stats) {
            const field = checkDivergence(dex, stats, this.dexCfg.divergence_pct);
            if (field) {
              const [dv, gv] = field === 'price' ? [dex.price, stats.price] : [dex.liquidity_usd, stats.liquidity_usd];
              recordDivergence(this.db, Date.now(), c.address, field, dv, gv);
              logEvent({ event: 'source_divergence', ticker: c.ticker, address: c.address, field, dex_value: dv, gmgn_value: gv });
            }
          }
          // v2.4 (Warden-inspired): creator status rides the alert; Blockscout
          // holder cross-check records divergence — signals, never gates
          if (stats?.creator_status) c = { ...c, creator_status: stats.creator_status };
          if (this.fetchHolders && stats?.total_supply) {
            const hc = await this.fetchHolders(c.address, stats.total_supply, stats.decimals);
            if (hc && c.top10_rate !== null && c.top10_rate > 0.01 && hc.user_top10_pct > 1) {
              const gmgnPct = c.top10_rate * 100;
              const ratio = Math.max(hc.user_top10_pct, gmgnPct) / Math.min(hc.user_top10_pct, gmgnPct);
              if (ratio > 2) {
                recordDivergence(this.db, Date.now(), c.address, 'holders', hc.user_top10_pct, gmgnPct);
                logEvent({ event: 'source_divergence', ticker: c.ticker, address: c.address, field: 'holders', chain_user_top10_pct: hc.user_top10_pct, gmgn_top10_pct: gmgnPct, contracts: hc.contract_names });
              }
            }
          }
          const change6h = dex?.change_6h_pct ?? stats?.change_6h_pct ?? null;
          if (change6h !== null) {
            c = { ...c, price_change_6h_pct: change6h };
            ev = evaluate(c, this.criteria);
            if (!ev.passed || ev.score < this.criteria.alert_score_threshold) {
              logEvent({ event: 'momentum_reject', ticker: c.ticker, address: c.address, change_6h_pct: change6h });
              if (firstSeen) recordCoin(this.db, c, ev, false, Date.now(), confirmed);
              continue;
            }
          }
        }
        const thesis = await this.thesis(c, ev);
        const dm = await sendDM(formatAlert(c, ev, thesis, this.regime.current), { dryRun: this.dryRun });
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
      if (firstSeen) recordCoin(this.db, c, ev, alerted, Date.now(), confirmed);
    }

    // outcome tracking piggybacks on the poll loop: one DexScreener batch
    // covers the whole due set, GMGN fills misses (budget-capped in outcomes.ts)
    await captureDueOutcomes(this.db, this.fetchStats, Date.now(), this.fetchDex ? this.dexCfg.batch_size : 5, this.fetchDex);

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
        await this.maybeDailyReport();
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
      regime: this.regime.current,
    };
    const dm = await sendDM(formatHeartbeat(hb), { dryRun: this.dryRun });
    logEvent({ event: 'heartbeat', slot, success: dm.success, error: dm.error });
    if (dm.success) {
      const { date } = laDate();
      saveHeartbeatState(stateFile, { date, slot });
      this.stats = this.freshStats();
    }
  }

  private async maybeDailyReport(): Promise<void> {
    const stateFile = path.join(this.dataDir, 'report-state.json');
    const slot = dueSlot(new Date(), loadHeartbeatState(stateFile), [this.criteria.report_hour_pt]);
    if (slot === null) return;
    await this.sendDailyReport(false);
    const { date } = laDate();
    saveHeartbeatState(stateFile, { date, slot });
  }

  async sendDailyReport(dryRun: boolean): Promise<void> {
    const stats = computeReport(this.db, Date.now());
    const narrative = await narrate(stats, this.criteria);
    const creators = await creatorHistoryLines(this.db, this.duneCfg, this.duneKey, Date.now(),
      (address) => fetchCreatorHistory(address, this.duneCfg, this.duneKey));
    const msg = formatReport(stats)
      + (creators.length ? `\n${creators.join('\n')}` : '')
      + (narrative ? `\n🧠 ${narrative}` : '');
    const dm = await sendDM(msg, { dryRun: dryRun || this.dryRun });
    logEvent({ event: 'daily_report', success: dm.success, error: dm.error });
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
