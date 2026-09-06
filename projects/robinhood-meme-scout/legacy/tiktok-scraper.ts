/**
 * TikTok Private API Client
 * Read-only scraping for meme coin intelligence
 * Based on: https://tiktok-api.seeksocial.io/
 */

import { Signer } from './signer.js';
import { Endpoints } from './endpoints.js';
import { VelocityTracker } from './velocity-tracker.js';

export interface TikTokConfig {
  device_id: string;
  iid: string;
  region: 'US' | 'SG' | 'EU' | 'JP';
  version_code: string;
  aid: number; // 473824 = TikTok Lite
}

export interface VideoData {
  video_id: string;
  description: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  creator_followers: number;
  posted_at: string;
  hashtags: string[];
  sound_id: string;
  virality_score: number;
}

export interface CoinMention {
  ticker: string;
  mention_count_24h: number;
  velocity_change: number; // % change
  top_creators: string[];
  avg_engagement: number;
  videos: VideoData[];
}

export interface CommunityHealth {
  tiktok_score: number; // 0-100
  x_score: number; // 0-100
  correlation: number; // 0-1
  trend_direction: 'rising' | 'stable' | 'falling';
}

export class TikTokScraper {
  private config: TikTokConfig;
  private signer: Signer;
  private tracker: VelocityTracker;
  private deviceCache: Map<string, TikTokConfig>;

  constructor(config: TikTokConfig) {
    this.config = config;
    this.signer = new Signer(config);
    this.tracker = new VelocityTracker();
    this.deviceCache = new Map();
    this.deviceCache.set(`${config.device_id}_${config.iid}`, config);
  }

  /**
   * Register a new device identity
   */
  async registerDevice(
    device_brand: string = 'Samsung',
    device_type: string = 'SM-A136U',
    region: TikTokConfig['region'] = 'US'
  ): Promise<TikTokConfig> {
    const response = await fetch(`${Endpoints.REGISTER}?aid=${this.config.aid}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-agent': `com.ss.android.ugc.tiktok.lite/${this.config.version_code}`,
      },
      body: JSON.stringify({
        device_brand,
        device_type,
        os_version: '12',
        os_api: '30',
        resolution: '1080*2280',
        dpi: '440',
        region,
        carrier_region: region,
        sys_region: region,
        mcc_mnc: region === 'US' ? '310260' : '52506',
        language: 'en',
        app_language: 'en',
        locale: 'en-US',
        timezone_name: 'America/Los_Angeles',
        channel: 'googleplay',
        app_type: 'normal',
      }),
    });

    if (!response.ok) {
      throw new Error(`Device registration failed: ${response.status}`);
    }

    const data = await response.json();
    const newConfig: TikTokConfig = {
      ...this.config,
      device_id: data.device_id,
      iid: data.install_id,
      region,
    };

    this.deviceCache.set(`${newConfig.device_id}_${newConfig.iid}`, newConfig);
    return newConfig;
  }

  /**
   * Get trending videos
   */
  async getTrending(count: number = 50): Promise<VideoData[]> {
    const url = Endpoints.TRENDING.list({
      count,
      region: this.config.region,
    });

    const response = await this._makeRequest(url);
    const videos = response.aweme_list || [];

    return videos.map((v: any) => ({
      video_id: v.aweme_id,
      description: v.desc || '',
      views: v.stat?.play_count || 0,
      likes: v.stat?.digg_count || 0,
      comments: v.stat?.comment_count || 0,
      shares: v.stat?.share_count || 0,
      creator_followers: v.author?.follower_count || 0,
      posted_at: new Date(v.create_time * 1000).toISOString(),
      hashtags: v.text_extra?.map((t: any) => t.hashtag_name || '').filter(Boolean) || [],
      sound_id: v.music?.id || '',
      virality_score: this._calculateVirality(v),
    }));
  }

  /**
   * Search for coin mentions
   */
  async searchCoinMentions(ticker: string, count: number = 30): Promise<CoinMention> {
    const url = Endpoints.SEARCH.general({
      keyword: ticker,
      count,
    });

    const response = await this._makeRequest(url);
    const videos = response.data || [];

    const videosData: VideoData[] = videos.map((v: any) => ({
      video_id: v.aweme_id,
      description: v.desc || '',
      views: v.stat?.play_count || 0,
      likes: v.stat?.digg_count || 0,
      comments: v.stat?.comment_count || 0,
      shares: v.stat?.share_count || 0,
      creator_followers: v.author?.follower_count || 0,
      posted_at: new Date(v.create_time * 1000).toISOString(),
      hashtags: v.text_extra?.map((t: any) => t.hashtag_name || '').filter(Boolean) || [],
      sound_id: v.music?.id || '',
      virality_score: this._calculateVirality(v),
    }));

    // Calculate velocity
    const velocity = this.tracker.calculateVelocity(videosData);

    return {
      ticker,
      mention_count_24h: videosData.length,
      velocity_change: velocity.change_24h,
      top_creators: this._extractTopCreators(videosData, 10),
      avg_engagement: videosData.reduce((sum, v) => sum + (v.likes + v.comments) / v.views, 0) / videosData.length || 0,
      videos: videosData,
    };
  }

  /**
   * Get hashtag videos
   */
  async getHashtagVideos(hashtag: string, count: number = 50): Promise<VideoData[]> {
    const url = Endpoints.HASHTAG.video({
      hashtag,
      count,
    });

    const response = await this._makeRequest(url);
    const videos = response.aweme_list || [];

    return videos.map((v: any) => ({
      video_id: v.aweme_id,
      description: v.desc || '',
      views: v.stat?.play_count || 0,
      likes: v.stat?.digg_count || 0,
      comments: v.stat?.comment_count || 0,
      shares: v.stat?.share_count || 0,
      creator_followers: v.author?.follower_count || 0,
      posted_at: new Date(v.create_time * 1000).toISOString(),
      hashtags: v.text_extra?.map((t: any) => t.hashtag_name || '').filter(Boolean) || [],
      sound_id: v.music?.id || '',
      virality_score: this._calculateVirality(v),
    }));
  }

  /**
   * Get creator videos
   */
  async getCreatorVideos(user_id: string, count: number = 20): Promise<VideoData[]> {
    const url = Endpoints.AWEME.post({
      user_id,
      count,
    });

    const response = await this._makeRequest(url);
    const videos = response.aweme_list || [];

    return videos.map((v: any) => ({
      video_id: v.aweme_id,
      description: v.desc || '',
      views: v.stat?.play_count || 0,
      likes: v.stat?.digg_count || 0,
      comments: v.stat?.comment_count || 0,
      shares: v.stat?.share_count || 0,
      creator_followers: v.author?.follower_count || 0,
      posted_at: new Date(v.create_time * 1000).toISOString(),
      hashtags: v.text_extra?.map((t: any) => t.hashtag_name || '').filter(Boolean) || [],
      sound_id: v.music?.id || '',
      virality_score: this._calculateVirality(v),
    }));
  }

  /**
   * Calculate community health score
   */
  async calculateCommunityHealth(
    ticker: string,
    xData: any
  ): Promise<CommunityHealth> {
    const tiktokData = await this.searchCoinMentions(ticker);
    const tiktokScore = this._calculateTikTokScore(tiktokData);
    const xScore = this._calculateXScore(xData);
    const correlation = this._calculateCorrelation(tiktokData, xData);

    return {
      tiktok_score: tiktokScore,
      x_score: xScore,
      correlation: correlation,
      trend_direction: correlation > 0.7 ? 'rising' : correlation < -0.3 ? 'falling' : 'stable',
    };
  }

  /**
   * Private: Make signed request
   */
  private async _makeRequest(url: string): Promise<any> {
    const headers = await this.signer.generateHeaders(url, this.config);

    const response = await fetch(url, {
      headers: {
        ...headers,
        'user-agent': `com.ss.android.ugc.tiktok.lite/${this.config.version_code}`,
      },
    });

    if (!response.ok) {
      throw new Error(`TikTok API error: ${response.status}`);
    }

    const data = await response.json();

    // Check for silent empty 200
    if (Object.keys(data).length === 0 || !data.aweme_list) {
      console.warn('Silent empty 200 received - check device/signature/host');
    }

    return data;
  }

  /**
   * Calculate virality score (0-1)
   */
  private _calculateVirality(video: any): number {
    const views = video.stat?.play_count || 0;
    const likes = video.stat?.digg_count || 0;
    const comments = video.stat?.comment_count || 0;
    const creatorFollowers = video.author?.follower_count || 0;

    const engagementRate = (likes + comments) / views || 0;
    const creatorWeight = creatorFollowers > 100000 ? 1.5 : creatorFollowers > 10000 ? 1.2 : 1.0;

    return Math.min(1.0, (engagementRate * creatorWeight));
  }

  /**
   * Extract top creators by follower count
   */
  private _extractTopCreators(videos: VideoData[], limit: number): string[] {
    return [...videos]
      .sort((a, b) => b.creator_followers - a.creator_followers)
      .slice(0, limit)
      .map((v) => v.description.split('@')[1]?.split(' ')[0] || 'unknown');
  }

  /**
   * Calculate TikTok score (0-100)
   */
  private _calculateTikTokScore(mentionData: CoinMention): number {
    const velocity = mentionData.velocity_change;
    const engagement = mentionData.avg_engagement;
    const mentions = mentionData.mention_count_24h;

    let score = 0;

    // Velocity bonus (up to 40 points)
    if (velocity > 200) score += 40;
    else if (velocity > 100) score += 30;
    else if (velocity > 50) score += 20;
    else if (velocity > 0) score += 10;

    // Engagement bonus (up to 30 points)
    if (engagement > 0.1) score += 30;
    else if (engagement > 0.05) score += 20;
    else if (engagement > 0.02) score += 10;

    // Mention volume bonus (up to 30 points)
    if (mentions > 500) score += 30;
    else if (mentions > 200) score += 20;
    else if (mentions > 50) score += 10;

    return Math.min(100, score);
  }

  /**
   * Calculate X score from Twitter data
   */
  private _calculateXScore(xData: any): number {
    // Simplified - would integrate with actual X API
    const mentions = xData?.mention_count_24h || 0;
    const engagement = xData?.avg_engagement || 0;

    let score = 0;
    if (mentions > 500) score += 50;
    else if (mentions > 200) score += 30;
    else if (mentions > 50) score += 15;

    if (engagement > 0.05) score += 30;
    else if (engagement > 0.02) score += 20;
    else if (engagement > 0.01) score += 10;

    return Math.min(100, score);
  }

  /**
   * Calculate correlation between TikTok and X
   */
  private _calculateCorrelation(tiktokData: CoinMention, xData: any): number {
    // Simplified correlation logic
    const tiktokVelocity = tiktokData.velocity_change;
    const xVelocity = xData?.velocity_change || 0;

    if (tiktokVelocity > 0 && xVelocity > 0) return 0.8; // Both rising
    if (tiktokVelocity < 0 && xVelocity < 0) return 0.7; // Both falling
    if (Math.abs(tiktokVelocity - xVelocity) < 50) return 0.5; // Similar
    return 0.2; // Divergent
  }
}

// Export for use in other modules
export { Endpoints } from './endpoints.js';
export { Signer } from './signer.js';
