/**
 * Mention Velocity Tracker
 * Calculates velocity changes and trends for coin mentions
 */

import { VideoData } from './tiktok-scraper.js';

export interface VelocityData {
  change_24h: number; // % change in mentions
  change_1h: number; // % change in last hour
  peak_time: string | null;
  trend: 'rising' | 'stable' | 'falling';
  velocity_score: number; // 0-100
}

export class VelocityTracker {
  private cache: Map<string, VelocityData>;

  constructor() {
    this.cache = new Map();
  }

  /**
   * Calculate velocity from video data
   */
  calculateVelocity(videos: VideoData[]): VelocityData {
    if (videos.length === 0) {
      return {
        change_24h: 0,
        change_1h: 0,
        peak_time: null,
        trend: 'stable',
        velocity_score: 0,
      };
    }

    // Group by time buckets
    const hourlyBuckets = this._bucketByHour(videos);
    const dailyBuckets = this._bucketByDay(videos);

    // Calculate changes
    const lastHour = hourlyBuckets[hourlyBuckets.length - 1]?.count || 0;
    const prevHour = hourlyBuckets[hourlyBuckets.length - 2]?.count || 0;
    const change1h = prevHour > 0 ? ((lastHour - prevHour) / prevHour) * 100 : 0;

    const lastDay = dailyBuckets[dailyBuckets.length - 1]?.count || 0;
    const prevDay = dailyBuckets[dailyBuckets.length - 2]?.count || 0;
    const change24h = prevDay > 0 ? ((lastDay - prevDay) / prevDay) * 100 : 0;

    // Find peak time
    const peakHour = hourlyBuckets.reduce((max, bucket) =>
      bucket.count > max.count ? bucket : max
    );

    // Determine trend
    let trend: 'rising' | 'stable' | 'falling' = 'stable';
    if (change24h > 20) trend = 'rising';
    else if (change24h < -20) trend = 'falling';

    // Calculate velocity score (0-100)
    const velocityScore = this._calculateVelocityScore(
      videos.length,
      Math.abs(change24h),
      peakHour.count
    );

    return {
      change_24h: change24h,
      change_1h: change1h,
      peak_time: peakHour.time,
      trend,
      velocity_score: velocityScore,
    };
  }

  /**
   * Get cached velocity for a ticker
   */
  getCachedVelocity(ticker: string): VelocityData | null {
    return this.cache.get(ticker) || null;
  }

  /**
   * Cache velocity data
   */
  cacheVelocity(ticker: string, velocity: VelocityData): void {
    this.cache.set(ticker, velocity);
  }

  /**
   * Bucket videos by hour
   */
  private _bucketByHour(videos: VideoData[]): Array<{ time: string; count: number }> {
    const buckets: Map<string, number> = new Map();

    // Get current hour as reference
    const now = new Date();
    const currentHour = now.toISOString().slice(0, 13); // YYYY-MM-DDTHH

    // Initialize last 24 hours
    for (let i = 23; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourStr = hour.toISOString().slice(0, 13);
      buckets.set(hourStr, 0);
    }

    // Fill buckets with actual data
    for (const video of videos) {
      const videoHour = video.posted_at.slice(0, 13);
      if (buckets.has(videoHour)) {
        buckets.set(videoHour, buckets.get(videoHour)! + 1);
      }
    }

    // Convert to array
    return Array.from(buckets.entries())
      .map(([time, count]) => ({ time, count }))
      .sort((a, b) => a.time.localeCompare(b.time));
  }

  /**
   * Bucket videos by day
   */
  private _bucketByDay(videos: VideoData[]): Array<{ time: string; count: number }> {
    const buckets: Map<string, number> = new Map();

    // Get last 7 days
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const day = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const dayStr = day.toISOString().slice(0, 10); // YYYY-MM-DD
      buckets.set(dayStr, 0);
    }

    // Fill buckets
    for (const video of videos) {
      const videoDay = video.posted_at.slice(0, 10);
      if (buckets.has(videoDay)) {
        buckets.set(videoDay, buckets.get(videoDay)! + 1);
      }
    }

    // Convert to array
    return Array.from(buckets.entries())
      .map(([time, count]) => ({ time, count }))
      .sort((a, b) => a.time.localeCompare(b.time));
  }

  /**
   * Calculate velocity score (0-100)
   */
  private _calculateVelocityScore(
    totalVideos: number,
    velocityChange: number,
    peakCount: number
  ): number {
    let score = 0;

    // Volume bonus (up to 40 points)
    if (totalVideos > 100) score += 40;
    else if (totalVideos > 50) score += 30;
    else if (totalVideos > 20) score += 20;
    else if (totalVideos > 5) score += 10;

    // Velocity bonus (up to 30 points)
    if (velocityChange > 200) score += 30;
    else if (velocityChange > 100) score += 20;
    else if (velocityChange > 50) score += 10;

    // Peak intensity bonus (up to 30 points)
    if (peakCount > 50) score += 30;
    else if (peakCount > 20) score += 20;
    else if (peakCount > 10) score += 10;

    return Math.min(100, score);
  }
}
