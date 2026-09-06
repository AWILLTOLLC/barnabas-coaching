import type { Coin } from './gmgn.js';

export type RegimeLabel = 'hot' | 'neutral' | 'cold';

export interface RegimeConfig {
  hot_median_1h_pct: number;
  cold_median_1h_pct: number;
  hot_green_share: number;
  cold_green_share: number;
  confirm_scans: number;
}

export interface Breadth {
  n: number;
  median_1h_pct: number;
  green_share: number;
  total_volume_24h: number;
  new_launches_1h: number;
}

const MIN_SAMPLE = 10;

export function computeBreadth(coins: Coin[], now: number): Breadth {
  const changes = coins
    .map(c => c.price_change_1h_pct)
    .filter((v): v is number => v !== null)
    .sort((a, b) => a - b);
  const n = changes.length;
  const median = n === 0 ? 0
    : n % 2 === 1 ? changes[(n - 1) / 2]
    : (changes[n / 2 - 1] + changes[n / 2]) / 2;
  return {
    n,
    median_1h_pct: median,
    green_share: n === 0 ? 0 : changes.filter(v => v > 0).length / n,
    total_volume_24h: coins.reduce((s, c) => s + c.volume_24h, 0),
    new_launches_1h: coins.filter(c => c.created_at_ms !== null && now - c.created_at_ms < 3_600_000).length,
  };
}

export function labelRegime(b: Omit<Breadth, never>, cfg: RegimeConfig): RegimeLabel {
  if (b.n < MIN_SAMPLE) return 'neutral';
  if (b.median_1h_pct <= cfg.cold_median_1h_pct || b.green_share <= cfg.cold_green_share) return 'cold';
  if (b.median_1h_pct >= cfg.hot_median_1h_pct && b.green_share >= cfg.hot_green_share) return 'hot';
  return 'neutral';
}

/** Anti-whipsaw: the confirmed label flips only after confirm_scans consecutive raw readings. */
export class RegimeTracker {
  private confirmed: RegimeLabel;
  private streakLabel: RegimeLabel;
  private streak = 0;

  constructor(initial: RegimeLabel, private cfg: RegimeConfig) {
    this.confirmed = initial;
    this.streakLabel = initial;
  }

  get current(): RegimeLabel {
    return this.confirmed;
  }

  update(raw: RegimeLabel): RegimeLabel {
    if (raw === this.confirmed) {
      this.streak = 0;
      this.streakLabel = raw;
      return this.confirmed;
    }
    if (raw === this.streakLabel) {
      this.streak++;
    } else {
      this.streakLabel = raw;
      this.streak = 1;
    }
    if (this.streak >= this.cfg.confirm_scans) {
      this.confirmed = raw;
      this.streak = 0;
    }
    return this.confirmed;
  }
}
