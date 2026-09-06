#!/usr/bin/env node
/**
 * Robinhood-chain meme coin scout.
 *   tsx src/cli.ts scan [--dry-run]        one scan, print results
 *   tsx src/cli.ts monitor [--dry-run]     poll forever with heartbeats
 *   tsx src/cli.ts heartbeat-test [--dry-run]  send one heartbeat DM now
 */
import { Monitor } from './monitor.js';
import { formatHeartbeat, sendDM } from './alerts.js';

async function main() {
  const args = process.argv.slice(2);
  const mode = args.find(a => !a.startsWith('--')) ?? 'help';
  const dryRun = args.includes('--dry-run');

  switch (mode) {
    case 'scan': {
      const mon = new Monitor({ dryRun });
      const r = await mon.scanOnce();
      console.log(`Scanned ${r.scanned} coins; ${r.passed_gates} passed gates; alerts: ${r.alerted.join(', ') || 'none'}`);
      if (r.best) console.log(`Best non-alert: $${r.best.ticker} at ${r.best.score}/100`);
      break;
    }
    case 'monitor': {
      await new Monitor({ dryRun }).run();
      break;
    }
    case 'report': {
      await new Monitor({ dryRun }).sendDailyReport(dryRun);
      break;
    }
    case 'heartbeat-test': {
      const msg = formatHeartbeat({ scanned: 0, passed_gates: 0, alerted: [], best: null, since: 'startup (test)' });
      const res = await sendDM(`${msg}\n(test heartbeat)`, { dryRun });
      console.log(res.success ? '✓ heartbeat delivered' : `✗ ${res.error}`);
      process.exitCode = res.success ? 0 : 1;
      break;
    }
    default:
      console.log('Usage: tsx src/cli.ts <scan|monitor|report|heartbeat-test> [--dry-run]');
  }
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
