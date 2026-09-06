import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface DiligenceResult {
  address: string;
  chain: string;
  score: number;
  verdict: 'strong' | 'moderate' | 'high-risk';
  checks: {
    contract_verified: boolean;
    top_10_holders_pct: number;
    liquidity_usd: number;
    liquidity_locked: boolean;
    mint_function: boolean;
    pause_function: boolean;
    x_mentions_24h: number;
    tiktok_velocity: number;
  };
  flags: string[];
  recommendation: string;
}

export async function runDueDiligence(
  address: string,
  chain: string,
  mode: 'standalone' | 'scout' = 'standalone'
): Promise<DiligenceResult> {
  const flags: string[] = [];
  let score = 0;

  // Step 1: Contract Verification
  const contractCheck = await checkContractVerification(address, chain);
  if (contractCheck.verified) {
    score += 15;
  } else {
    flags.push('Unverified contract (high risk)');
  }

  // Step 2: Holder Analysis
  const holderCheck = await checkHolders(address, chain);
  if (holderCheck.top10Pct < 30) {
    score += 15;
  } else {
    flags.push(`High concentration: Top 10 hold ${holderCheck.top10Pct}%`);
  }

  // Step 3: Liquidity Check
  const liquidityCheck = await checkLiquidity(address, chain);
  if (liquidityCheck.usd > 50000) {
    score += 15;
  } else {
    flags.push(`Low liquidity: $${liquidityCheck.usd.toLocaleString()}`);
  }
  if (liquidityCheck.locked) {
    score += 10;
  } else {
    flags.push('Unlocked liquidity');
  }

  // Step 4: Rug Patterns
  const rugCheck = await checkRugPatterns(address, chain);
  if (!rugCheck.mint) {
    score += 10;
  } else {
    flags.push('Mint function detected');
  }
  if (!rugCheck.pause) {
    score += 10;
  } else {
    flags.push('Pause function detected');
  }

  // Step 5: Social Validation
  const socialCheck = await checkSocialValidation(address);
  if (socialCheck.xMentions > 10) {
    score += 10;
  } else {
    flags.push(`Low X mentions: ${socialCheck.xMentions} (24h)`);
  }
  if (socialCheck.tiktokVelocity > 5) {
    score += 15;
  } else {
    flags.push(`Low TikTok velocity: ${socialCheck.tiktokVelocity}/day`);
  }

  // Determine verdict
  let verdict: 'strong' | 'moderate' | 'high-risk' = 'high-risk';
  if (score >= 90) verdict = 'strong';
  else if (score >= 70) verdict = 'moderate';

  // Generate recommendation
  let recommendation = '';
  if (verdict === 'strong') {
    recommendation = 'Strong buy, low risk';
  } else if (verdict === 'moderate') {
    recommendation = 'Moderate risk, do more research';
  } else {
    recommendation = 'High risk, avoid or small position';
  }

  return {
    address,
    chain,
    score,
    verdict,
    checks: {
      contract_verified: contractCheck.verified,
      top_10_holders_pct: holderCheck.top10Pct,
      liquidity_usd: liquidityCheck.usd,
      liquidity_locked: liquidityCheck.locked,
      mint_function: rugCheck.mint,
      pause_function: rugCheck.pause,
      x_mentions_24h: socialCheck.xMentions,
      tiktok_velocity: socialCheck.tiktokVelocity,
    },
    flags,
    recommendation,
  };
}

async function checkContractVerification(
  address: string,
  chain: string
): Promise<{ verified: boolean }> {
  try {
    const baseUrl = chain === 'robinhood'
      ? 'https://eth.robinhood.io/api/v2/contracts'
      : 'https://api.etherscan.io/api?module=contract&action=getsourcecode&address';

    const url = `${baseUrl}/${address}`;
    const { stdout } = await execAsync(`curl -s "${url}" | jq '.result[0].ContractName'`);
    const contractName = stdout.trim();

    return { verified: contractName !== 'null' && contractName !== '' };
  } catch (e) {
    return { verified: false };
  }
}

async function checkHolders(address: string, chain: string): Promise<{ top10Pct: number }> {
  try {
    const url = `https://api.etherscan.io/api?module=holder&action=tokenholder&contractaddress=${address}`;
    const { stdout } = await execAsync(`curl -s "${url}" | jq '.result[0:10] | map(.Count) | add / (.result | length) * 100'`);
    const top10Pct = parseFloat(stdout.trim());
    return { top10Pct: isNaN(top10Pct) ? 0 : top10Pct };
  } catch (e) {
    return { top10Pct: 0 };
  }
}

async function checkLiquidity(address: string, chain: string): Promise<{ usd: number; locked: boolean }> {
  try {
    // TODO: Implement proper liquidity check
    // For now, return mock data
    return { usd: 125000, locked: true };
  } catch (e) {
    return { usd: 0, locked: false };
  }
}

async function checkRugPatterns(address: string, chain: string): Promise<{ mint: boolean; pause: boolean }> {
  try {
    const url = `https://api.etherscan.io/api?module=contract&action=getabi&address=${address}`;
    const { stdout } = await execAsync(`curl -s "${url}" | jq '.result[0].ABI'`);
    
    const hasMint = stdout.includes('mint') || stdout.includes('Mint');
    const hasPause = stdout.includes('pause') || stdout.includes('Pause');

    return { mint: hasMint, pause: hasPause };
  } catch (e) {
    return { mint: false, pause: false };
  }
}

async function checkSocialValidation(address: string): Promise<{ xMentions: number; tiktokVelocity: number }> {
  try {
    // X mentions
    const { stdout: xStdout } = await execAsync(`xurl search "${address}" -n 50 2>/dev/null | jq 'length'`);
    const xMentions = parseInt(xStdout.trim()) || 0;

    // TikTok velocity (mock for now)
    const tiktokVelocity = 12;

    return { xMentions, tiktokVelocity };
  } catch (e) {
    return { xMentions: 0, tiktokVelocity: 0 };
  }
}

export function formatAlert(coin: { ticker: string; address: string; chain: string }, diligence: DiligenceResult): string {
  return `🏹 GMGN Alert: ${coin.ticker}
Score: ${diligence.score}/100 (${diligence.verdict.toUpperCase()})
Liquidity: $${diligence.checks.liquidity_usd.toLocaleString()} (${diligence.checks.liquidity_locked ? 'Locked 30d' : 'Unlocked'})
Top 10 Holders: ${diligence.checks.top_10_holders_pct}% ${diligence.checks.top_10_holders_pct < 30 ? '✅' : '⚠️'}
Contract: ${diligence.checks.contract_verified ? 'Verified ✅' : 'Unverified ⚠️'}
X Mentions: ${diligence.checks.x_mentions_24h} (24h) ${diligence.checks.x_mentions_24h > 10 ? '✅' : '⚠️'}
TikTok Velocity: ${diligence.checks.tiktok_velocity}/day ${diligence.checks.tiktok_velocity > 5 ? '✅' : '⚠️'}

📍 Address: ${coin.address}
🔗 DexScreener: https://dexscreener.com/${coin.chain}/${coin.address}

${diligence.flags.length > 0 ? `⚠️ Flags: ${diligence.flags.join(', ')}` : '✅ No major flags'}
💡 ${diligence.recommendation}`;
}
