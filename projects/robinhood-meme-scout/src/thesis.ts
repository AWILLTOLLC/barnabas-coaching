import type { Coin } from './gmgn.js';
import type { Evaluation } from './filters.js';
import type { Criteria } from './config.js';

/**
 * Build the prompt for the local LLM. Design notes:
 * - The model only sees facts we hand it, plus a maintained chain-context blurb
 *   from criteria.json (update that as the chain's meta rotates).
 * - Inference from the name/socials is allowed but must be hedged; everything
 *   else must trace to a DATA line. Numbers must be copied, not recomputed.
 * - Hard word cap + plain text keeps it DM-sized and stops rambling.
 */
export function buildThesisPrompt(coin: Coin, ev: Evaluation, chainContext: string): string {
  const ageH = coin.created_at_ms ? ((Date.now() - coin.created_at_ms) / 3_600_000).toFixed(0) : 'unknown';
  const data = [
    `name: ${coin.name}`,
    `ticker: $${coin.ticker}`,
    `market_cap_usd: ${Math.round(coin.market_cap)}`,
    `age_hours: ${ageH}`,
    `volume_24h_usd: ${Math.round(coin.volume_24h)}`,
    `liquidity_usd: ${Math.round(coin.liquidity_usd)}`,
    `holders: ${coin.holder_count}`,
    `top10_holder_pct: ${coin.top10_rate !== null ? (coin.top10_rate * 100).toFixed(1) : 'unknown'}`,
    `price_change_6h_pct: ${coin.price_change_6h_pct !== null ? coin.price_change_6h_pct.toFixed(1) : 'unknown'}`,
    `launchpad: ${coin.launchpad ?? 'unknown'}`,
    `lp_burned: ${coin.burn_status === 'yes' ? 'yes' : 'no/unknown'}`,
    `mint_and_freeze_renounced: ${coin.renounced_mint === true && coin.renounced_freeze === true ? 'yes' : 'no/unknown'}`,
    `twitter: ${coin.twitter ?? 'none listed'}`,
    `website: ${coin.website ?? 'none listed'}`,
    `scout_score: ${ev.score}/100 (${ev.reasons.join('; ')})`,
    ev.flags.length ? `warnings: ${ev.flags.join(', ')}` : null,
  ].filter(Boolean).join('\n');

  return `You are a skeptical crypto analyst writing a one-paragraph brief for a meme-coin alert. Using ONLY the DATA below, write exactly 2-3 sentences covering, in order:
1. What this coin most likely is, inferred from its name, socials, and launch venue. This is inference, so hedge it ("likely", "appears to be").
2. The single strongest fact in its favor from the DATA.
3. The single biggest risk visible in the DATA (missing website, holder concentration, momentum, thin liquidity, unknowns).

Hard rules: maximum 60 words total. Plain text, no markdown, no emoji, no headers. No price predictions and no buy/sell advice. No invented facts: if it is not in DATA or CONTEXT, do not mention it. Copy numbers exactly as given; round only to whole thousands/millions (e.g. 639000 -> $639K). A website or product you cannot see in DATA does not exist. CONTEXT describes the chain, NOT this coin: you may connect this coin to a narrative in CONTEXT only when the coin's own name or ticker in DATA contains a keyword of that narrative (e.g. a coin named after a cat and a cat meta); otherwise never mention that narrative at all. Output the brief only, nothing else.

CONTEXT: ${chainContext}

DATA:
${data}`;
}

export async function generateThesis(
  coin: Coin,
  ev: Evaluation,
  criteria: Criteria,
): Promise<string | null> {
  const prompt = buildThesisPrompt(coin, ev, criteria.chain_context);
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
