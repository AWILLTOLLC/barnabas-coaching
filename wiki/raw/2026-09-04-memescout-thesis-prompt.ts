---
source: /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/src/thesis.ts
fetched: 2026-09-11
type: code-source
---
import type { Coin } from './gmgn.js';
import type { Evaluation } from './filters.js';
import type { Criteria } from './config.js';
import type { LiquidityBaseline } from './peers.js';

export interface ThesisContext {
  regime?: string;
  liqPeers?: LiquidityBaseline | null;
}

/**
 * Build the prompt for the local LLM. Design notes (revised 2026-09-10 after
 * user feedback — see tasks/lessons.md):
 * - Chain metas (e.g. the cat meta) are injected ONLY when the coin's own
 *   name/ticker matches a meta keyword (criteria.json `metas`). The model never
 *   sees a narrative it could wrongly attach; base chain_context stays neutral.
 * - The launch venue is shared infrastructure on this chain; the prompt says so
 *   and forbids using it as evidence of what the coin is.
 * - Liquidity is judged against the coin's MC-band peers (7-day percentiles
 *   from scout.db), with the verdict pre-computed in code — "thin" is only
 *   allowed when the ratio is genuinely below the peer p25.
 * - The scout score is our own output and may not be cited as a strength.
 */
export function buildThesisPrompt(coin: Coin, ev: Evaluation, criteria: Criteria, ctx: ThesisContext = {}): string {
  const ageH = coin.created_at_ms ? ((Date.now() - coin.created_at_ms) / 3_600_000).toFixed(0) : 'unknown';
  const lp = ctx.liqPeers;
  const data = [
    `name: ${coin.name}`,
    `ticker: $${coin.ticker}`,
    `market_cap_usd: ${Math.round(coin.market_cap)}`,
    `age_hours: ${ageH}`,
    `volume_24h_usd: ${Math.round(coin.volume_24h)}`,
    `liquidity_usd: ${Math.round(coin.liquidity_usd)}`,
    lp
      ? `liquidity_vs_band_peers: ${lp.ratio_pct.toFixed(1)}% of market cap vs peer median ${lp.median_pct.toFixed(1)}% (p25 ${lp.p25_pct.toFixed(1)}%, p75 ${lp.p75_pct.toFixed(1)}%, n=${lp.n}, last 7d) -> verdict: ${lp.verdict}`
      : `liquidity_vs_band_peers: unknown (no peer baseline)`,
    `holders: ${coin.holder_count}`,
    `top10_holder_pct: ${coin.top10_rate !== null ? (coin.top10_rate * 100).toFixed(1) : 'unknown'}`,
    `price_change_6h_pct: ${coin.price_change_6h_pct !== null ? coin.price_change_6h_pct.toFixed(1) : 'unknown'}`,
    `launch_venue: ${coin.launchpad ?? 'unknown'} (shared launch infrastructure used by nearly every coin on this chain; says nothing about what this coin is)`,
    `lp_burned: ${coin.burn_status === 'yes' ? 'yes' : 'no/unknown'}`,
    `mint_and_freeze_renounced: ${coin.renounced_mint === true && coin.renounced_freeze === true ? 'yes' : 'no/unknown'}`,
    `twitter: ${coin.twitter ?? 'none listed'}`,
    `website: ${coin.website ?? 'none listed'}`,
    `scout_score: ${ev.score}/100 (${ev.reasons.join('; ')}) [this system's own rating, not an on-chain fact]`,
    ctx.regime ? `chain_regime_now: ${ctx.regime} (breadth of all trending coins, not this coin)` : null,
    ev.flags.length ? `warnings: ${ev.flags.join(', ')}` : null,
  ].filter(Boolean).join('\n');

  const metaNotes = matchMetas(coin, criteria.metas ?? []);
  const context = [criteria.chain_context, ...metaNotes].join(' ');

  return `You are a skeptical crypto analyst writing a one-paragraph brief for a meme-coin alert. Using ONLY the DATA below, write exactly 2-3 sentences covering, in order:
1. What this coin most likely is, inferred from its name and socials only. This is inference, so hedge it ("likely", "appears to be"). The launch venue is shared plumbing — never use it as evidence of theme, meta, or purpose. If the name and socials are not enough to tell what it is, say that plainly instead of guessing a theme.
2. The single strongest on-chain fact in its favor from the DATA. Never cite scout_score — it is this system's own rating, not evidence.
3. The single biggest risk visible in the DATA (holder concentration, momentum, missing socials, genuinely weak liquidity, unknowns).

Liquidity rule: judge liquidity ONLY by the liquidity_vs_band_peers verdict. "below typical" may be called thin or low. "typical" means standard for this chain and MUST NOT be described as thin, low, or a risk. "above typical" is a strength. If the verdict is unknown, do not characterize liquidity at all.

Hard rules: maximum 60 words total. Plain text, no markdown, no emoji, no headers. No price predictions and no buy/sell advice. No invented facts: if it is not in DATA or CONTEXT, do not mention it. Copy numbers exactly as given; round only to whole thousands/millions (e.g. 639000 -> $639K). A website or product you cannot see in DATA does not exist. CONTEXT is background about the chain, not about this coin. Output the brief only, nothing else.

CONTEXT: ${context}

DATA:
${data}`;
}

/** Meta narratives apply only when the coin's own name/ticker contains a keyword. */
export function matchMetas(coin: Coin, metas: { keywords: string[]; note: string }[]): string[] {
  const haystack = `${coin.name} ${coin.ticker}`.toLowerCase();
  return metas.filter(m => m.keywords.some(k => haystack.includes(k.toLowerCase()))).map(m => m.note);
}

export async function generateThesis(
  coin: Coin,
  ev: Evaluation,
  criteria: Criteria,
  ctx: ThesisContext = {},
): Promise<string | null> {
  const prompt = buildThesisPrompt(coin, ev, criteria, ctx);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), criteria.ollama.timeout_ms);
  try {
    const res = await fetch(`${criteria.ollama.url}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: criteria.ollama.model,
        prompt,
        stream: false,
        think: false,
        options: { temperature: 0.3, num_predict: 160 },
      }),
      signal: controller.signal,
    });
    if (!res.ok) {
      console.error(`ollama returned ${res.status}`);
      return null;
    }
    const body = await res.json() as { response?: string };
    const text = body.response?.trim();
    if (!text) return null;
    // strip any leaked chain-of-thought blocks and cap runaway output
    const clean = text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
    return clean.length > 600 ? clean.slice(0, 600) + '…' : clean;
  } catch (err: any) {
    console.error(`thesis generation failed: ${err.name === 'AbortError' ? 'timeout' : err.message}`);
    return null;
  } finally {
    clearTimeout(timer);
  }
}
