export interface DuneConfig {
  enabled: boolean;
  query_id: number;
  timeout_ms: number;
  poll_interval_ms: number;
}

export const DUNE_DEFAULTS: DuneConfig = {
  enabled: false,
  query_id: 0,
  timeout_ms: 60_000,
  poll_interval_ms: 2500,
};

export interface CreatorHistory {
  deployer: string;
  total_launches: number;
  first_launch: string | null;
  last_launch: string | null;
}

/**
 * Run the saved "Pons creator history" Dune query (docs/dune-creator-history.sql)
 * for one token address and return the first row. Execute-then-poll per the
 * Dune API v1 flow. Fail-soft: null on any error, timeout, or empty result —
 * the daily report simply omits the line.
 */
export async function fetchCreatorHistory(
  tokenAddress: string,
  cfg: DuneConfig,
  apiKey: string,
  fetchFn: typeof fetch = fetch,
): Promise<CreatorHistory | null> {
  try {
    const exec = await fetchFn(`https://api.dune.com/api/v1/query/${cfg.query_id}/execute`, {
      method: 'POST',
      headers: { 'X-Dune-API-Key': apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query_parameters: { token_address: tokenAddress.toLowerCase() } }),
    });
    if (!exec.ok) return null;
    const executionId = ((await exec.json()) as any)?.execution_id;
    if (typeof executionId !== 'string' || !executionId) return null;

    const deadline = Date.now() + cfg.timeout_ms;
    while (Date.now() < deadline) {
      const res = await fetchFn(`https://api.dune.com/api/v1/execution/${executionId}/results`, {
        headers: { 'X-Dune-API-Key': apiKey },
      });
      if (!res.ok) return null;
      const body = (await res.json()) as any;
      if (body?.state === 'QUERY_STATE_COMPLETED') {
        const row = body?.result?.rows?.[0];
        if (!row || typeof row.deployer !== 'string') return null;
        return {
          deployer: row.deployer,
          total_launches: Number(row.total_launches) || 0,
          first_launch: row.first_launch ?? null,
          last_launch: row.last_launch ?? null,
        };
      }
      if (typeof body?.state === 'string' && body.state.endsWith('FAILED')) return null;
      await new Promise(r => setTimeout(r, cfg.poll_interval_ms));
    }
    return null;
  } catch {
    return null;
  }
}
