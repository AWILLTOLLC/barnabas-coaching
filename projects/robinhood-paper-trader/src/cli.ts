#!/usr/bin/env node
/**
 * Paper-trade execution layer for Meme Scout signals. SIMULATION ONLY:
 * this codebase never constructs or sends on-chain transactions. The
 * `external` executor shells out to a user-supplied wrapper that owns
 * all of that (see docs/EXECUTOR-CONTRACT.md).
 *
 *   echo '{"address":"0x..","ticker":"X","price_usd":0.001}' | tsx src/cli.ts buy
 *   tsx src/cli.ts sell --address 0x.. [--pct 100]
 *   tsx src/cli.ts status
 *   tsx src/cli.ts run [--dry-run]     # daemon: marks + strategy exits
 *   tsx src/cli.ts contract            # print the wrapper contract
 */
import * as fs from 'node:fs';
import * as path from 'node:path';
import { loadStrategy, loadEnv, PROJECT_ROOT } from './config.js';
import { openDb, getOpenPositions, realizedCapital, ordersToday, deployedTodayUsd, ptDate, lastMark, portfolioSummaryLine } from './db.js';
import { makeExecutor } from './executor.js';
import { fetchMarks, PRICES_DEFAULTS } from './prices.js';
import { Engine } from './engine.js';
import { sendDM, logEvent } from './notify.js';
import { stakeFor } from './limits.js';
import { collectTaxLines, summarize, toCsv, yearLines } from './tax.js';

function buildEngine(dryRun: boolean) {
  const strategy = loadStrategy();
  const env = loadEnv();
  const db = openDb(path.join(PROJECT_ROOT, 'data', 'trades.db'));
  const engine = new Engine({
    db, strategy,
    executor: makeExecutor(strategy),
    fetchMarks: (addrs) => fetchMarks(addrs, env, PRICES_DEFAULTS),
    notify: (msg) => strategy.discord.enabled
      ? sendDM(msg + '\n' + portfolioSummaryLine(db, strategy.starting_capital_usd), { dryRun })
      : Promise.resolve({ success: true }),
    logEvent,
  });
  return { engine, db, strategy, env };
}

async function readStdin(): Promise<string> {
  let data = '';
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

async function main() {
  const args = process.argv.slice(2);
  const mode = args.find(a => !a.startsWith('--')) ?? 'help';
  const dryRun = args.includes('--dry-run');
  const flag = (name: string) => {
    const i = args.indexOf(`--${name}`);
    return i >= 0 ? args[i + 1] : undefined;
  };

  switch (mode) {
    case 'buy': {
      let ticket;
      try {
        ticket = JSON.parse(await readStdin());
      } catch {
        console.error(JSON.stringify({ ok: false, reason: 'stdin was not valid ticket JSON' }));
        process.exit(1);
      }
      const { engine } = buildEngine(dryRun);
      const r = await engine.openFromTicket(ticket);
      console.log(JSON.stringify(r));
      process.exit(r.ok ? 0 : 1);
    }
    case 'sell': {
      const address = flag('address');
      if (!address) { console.error('--address required'); process.exit(1); }
      const pct = Number(flag('pct') ?? 100);
      const { engine } = buildEngine(dryRun);
      const fill = await engine.manualSell(address, pct);
      console.log(JSON.stringify(fill));
      process.exit('status' in fill && fill.status === 'filled' ? 0 : 1);
    }
    case 'status':
    case 'portfolio': {
      const { db, strategy } = buildEngine(true);
      const cap = realizedCapital(db, strategy.starting_capital_usd);
      const today = ptDate(Date.now());
      console.log(`Realized capital: $${cap.toFixed(2)} | next stake: $${stakeFor(cap, strategy)} | today: ${ordersToday(db, today)} orders, $${deployedTodayUsd(db, today).toFixed(0)} deployed`);
      const open = getOpenPositions(db);
      console.log(`Open positions: ${open.length}`);
      for (const p of open) {
        const ageH = ((Date.now() - p.opened_ms) / 3_600_000).toFixed(1);
        const mark = lastMark(db, p.address);
        const value = mark ? (p.tokens_remaining * mark.price_usd).toFixed(2) : '?';
        console.log(`  $${p.ticker} ${p.address.slice(0, 10)}… age ${ageH}h stake $${p.stake_usd} value $${value} realized $${p.realized_usd.toFixed(2)}${p.moonbag_done ? ' [moonbag ✓]' : ''}`);
      }
      const closed = db.prepare(`SELECT status, COUNT(*) n, COALESCE(SUM(realized_usd - stake_usd),0) pnl FROM positions WHERE status != 'open' GROUP BY status`).all() as any[];
      for (const c of closed) console.log(`${c.status}: ${c.n} positions, P&L ${c.pnl >= 0 ? '+' : ''}$${c.pnl.toFixed(2)}`);
      break;
    }
    case 'run': {
      const { engine, db, strategy } = buildEngine(dryRun);
      console.log(`📈 Paper trader daemon (${dryRun ? 'dry-run' : 'live DMs'}; executor: ${strategy.executor.type}). Tick every ${strategy.mark_interval_seconds}s.`);
      while (true) {
        try {
          await engine.tick();
          console.log(`[${new Date().toISOString()}] tick: ${getOpenPositions(db).length} open, capital $${realizedCapital(db, strategy.starting_capital_usd).toFixed(2)}`);
        } catch (err) {
          console.error('tick error:', err);
        }
        await new Promise(r => setTimeout(r, strategy.mark_interval_seconds * 1000));
      }
    }
    case 'tax': {
      const year = Number(flag('year') ?? new Date().getFullYear());
      const { db } = buildEngine(true);
      const s = summarize(collectTaxLines(db));
      const csv = toCsv(s, year);
      const out = path.join(PROJECT_ROOT, 'data', `irs-8949-${year}.csv`);
      fs.writeFileSync(out, csv);
      console.log(`Wrote ${out}`);
      console.log(`Form 8949 Part II Box C, tax year ${year}: ${yearLines(s, year).length} disposals`);
      console.log(`Proceeds $${s.total_proceeds_usd.toFixed(2)} | basis $${s.total_basis_usd.toFixed(2)} | gain $${s.total_gain_usd.toFixed(2)} (short-term ${s.short_term_count}, long-term ${s.long_term_count})`);
      break;
    }
    case 'contract': {
      console.log(fs.readFileSync(path.join(PROJECT_ROOT, 'docs', 'EXECUTOR-CONTRACT.md'), 'utf8'));
      break;
    }
    default:
      console.log('Usage: tsx src/cli.ts <buy|sell|status|tax|run|contract> [--dry-run] [--address 0x..] [--pct N] [--year YYYY]');
  }
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
