/**
 * Community Health Scoring
 * Cross-references TikTok and X/Twitter for meme coin community validation
 */

import { CommunityHealth, CoinMention } from './tiktok-scraper.js';

export interface XData {
  mention_count_24h: number;
  avg_engagement: number;
  velocity_change: number;
  top_influencers: string[];
  sentiment_score: number; // -1 to 1
}

export interface CommunityScore {
  tiktok: {
    score: number; // 0-100
    mentions_24h: number;
    velocity: number; // % change
    quality: 'high' | 'medium' | 'low';
  };
  x: {
    score: number; // 0-100
    mentions_24h: number;
    velocity: number; // % change
    quality: 'high' | 'medium' | 'low';
  };
  combined: {
    overall_score: number; // 0-100
    trend: 'rising' | 'stable' | 'falling';
    correlation: number; // 0-1
    recommendation: 'buy' | 'watch' | 'avoid';
  };
}

export class CommunityScorer {
  /**
   * Calculate comprehensive community score
   */
  calculateCommunityScore(
    tiktokData: CoinMention,
    xData: XData
  ): CommunityScore {
    const tiktokScore = this._calculatePlatformScore(tiktokData, 'tiktok');
    const xScore = this._calculatePlatformScore(xData, 'x');

    // Calculate combined score
    const overallScore = this._calculateCombinedScore(tiktokScore.score, xScore.score);
    const trend = this._determineTrend(tiktokData.velocity_change, xData.velocity_change);
    const correlation = this._calculateCorrelation(tiktokData, xData);
    const recommendation = this._getRecommendation(overallScore, trend, correlation);

    return {
      tiktok: tiktokScore,
      x: xScore,
      combined: {
        overall_score: overallScore,
        trend,
        correlation,
        recommendation,
      },
    };
  }

  /**
   * Calculate platform-specific score
   */
  private _calculatePlatformScore(
    data: CoinMention | XData,
    platform: 'tiktok' | 'x'
  ): { score: number; mentions_24h: number; velocity: number; quality: 'high' | 'medium' | 'low' } {
    let score = 0;
    let mentions = 0;
    let velocity = 0;

    if (platform === 'tiktok') {
      const tiktokData = data as CoinMention;
      mentions = tiktokData.mention_count_24h;
      velocity = tiktokData.velocity_change;

      // TikTok scoring logic
      score = this._calculateTikTokScore(tiktokData);
    } else {
      const xData = data as XData;
      mentions = xData.mention_count_24h;
      velocity = xData.velocity_change;

      // X scoring logic
      score = this._calculateXScore(xData);
    }

    // Determine quality tier
    let quality: 'high' | 'medium' | 'low' = 'medium';
    if (score >= 70) quality = 'high';
    else if (score <= 30) quality = 'low';

    return {
      score,
      mentions_24h: mentions,
      velocity,
      quality,
    };
  }

  /**
   * Calculate combined score (weighted average)
   */
  private _calculateCombinedScore(tiktokScore: number, xScore: number): number {
    // TikTok weighted 60%, X weighted 40%
    return Math.round(tiktokScore * 0.6 + xScore * 0.4);
  }

  /**
   * Determine trend direction
   */
  private _determineTrend(tiktokVelocity: number, xVelocity: number): 'rising' | 'stable' | 'falling' {
    const avgVelocity = (tiktokVelocity + xVelocity) / 2;

    if (avgVelocity > 30) return 'rising';
    if (avgVelocity < -30) return 'falling';
    return 'stable';
  }

  /**
   * Calculate correlation between platforms
   */
  private _calculateCorrelation(
    tiktokData: CoinMention,
    xData: XData
  ): number {
    // Simplified correlation based on velocity alignment
    const tiktokVel = tiktokData.velocity_change;
    const xVel = xData.velocity_change;

    const diff = Math.abs(tiktokVel - xVel);

    if (diff < 20) return 0.9; // Nearly identical
    if (diff < 50) return 0.7; // Strong correlation
    if (diff < 100) return 0.5; // Moderate correlation
    if (diff < 150) return 0.3; // Weak correlation
    return 0.1; // Divergent
  }

  /**
   * Get trading recommendation
   */
  private _getRecommendation(
    overallScore: number,
    trend: 'rising' | 'stable' | 'falling',
    correlation: number
  ): 'buy' | 'watch' | 'avoid' {
    // High score + rising trend + high correlation = buy
    if (overallScore >= 70 && trend === 'rising' && correlation >= 0.7) {
      return 'buy';
    }

    // Medium score or mixed signals = watch
    if (overallScore >= 50 && overallScore < 70) {
      return 'watch';
    }

    // Low score or falling trend = avoid
    if (overallScore < 50 || trend === 'falling') {
      return 'avoid';
    }

    return 'watch';
  }

  /**
   * Calculate TikTok-specific score
   */
  private _calculateTikTokScore(data: CoinMention): number {
    let score = 0;

    // Velocity bonus (up to 40)
    if (data.velocity_change > 200) score += 40;
    else if (data.velocity_change > 100) score += 30;
    else if (data.velocity_change > 50) score += 20;
    else if (data.velocity_change > 0) score += 10;

    // Engagement bonus (up to 30)
    if (data.avg_engagement > 0.1) score += 30;
    else if (data.avg_engagement > 0.05) score += 20;
    else if (data.avg_engagement > 0.02) score += 10;

    // Volume bonus (up to 30)
    if (data.mention_count_24h > 500) score += 30;
    else if (data.mention_count_24h > 200) score += 20;
    else if (data.mention_count_24h > 50) score += 10;

    return Math.min(100, score);
  }

  /**
   * Calculate X-specific score
   */
  private _calculateXScore(data: XData): number {
    let score = 0;

    // Velocity bonus (up to 40)
    if (data.velocity_change > 200) score += 40;
    else if (data.velocity_change > 100) score += 30;
    else if (data.velocity_change > 50) score += 20;
    else if (data.velocity_change > 0) score += 10;

    // Engagement bonus (up to 30)
    if (data.avg_engagement > 0.08) score += 30;
    else if (data.avg_engagement > 0.04) score += 20;
    else if (data.avg_engagement > 0.02) score += 10;

    // Volume bonus (up to 20)
    if (data.mention_count_24h > 1000) score += 20;
    else if (data.mention_count_24h > 500) score += 15;
    else if (data.mention_count_24h > 200) score += 10;

    // Sentiment bonus (up to 10)
    if (data.sentiment_score > 0.5) score += 10;
    else if (data.sentiment_score > 0.2) score += 5;

    return Math.min(100, score);
  }
}
