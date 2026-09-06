/**
 * TikTok API Endpoints
 * 24 endpoints for reading-only scraping
 * Based on: https://tiktok-api.seeksocial.io/
 */

export const Endpoints = {
  /**
   * Region partitioning
   * US, SG, EU, JP all have different hosts
   */
  REGIONS: {
    US: 'api16-normal-us.tiktok.com',
    SG: 'api16-normal-sg.tiktok.com',
    EU: 'api16-normal-eu.tiktok.com',
    JP: 'api16-normal-jp.tiktok.com',
  },

  /**
   * Device registration
   */
  REGISTER: 'https://api16-normal-us.tiktok.com/device/register',

  /**
   * Trending videos
   */
  TRENDING: {
    list: (params: { count: number; region: string }) => {
      return `https://${Endpoints.REGIONS[params.region as keyof typeof Endpoints.REGIONS]}/aweme/v1/trending/list?count=${params.count}&region=${params.region}`;
    },
  },

  /**
   * General search
   */
  SEARCH: {
    general: (params: { keyword: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/search/general/?keyword=${encodeURIComponent(params.keyword)}&count=${params.count}`;
    },
  },

  /**
   * Hashtag videos
   */
  HASHTAG: {
    video: (params: { hashtag: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/hashtag/video/?hashtag=${encodeURIComponent(params.hashtag)}&count=${params.count}`;
    },
  },

  /**
   * Creator videos (aweme/post)
   */
  AWEME: {
    post: (params: { user_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/aweme/post/?user_id=${params.user_id}&count=${params.count}`;
    },
  },

  /**
   * Sound videos
   */
  SOUND: {
    list: (params: { sound_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/music/video/?music_id=${params.sound_id}&count=${params.count}`;
    },
  },

  /**
   * Comment list
   */
  COMMENT: {
    list: (params: { aweme_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/comment/list/?aweme_id=${params.aweme_id}&count=${params.count}`;
    },
  },

  /**
   * Creator profile
   */
  PROFILE: {
    detail: (params: { user_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/user/?user_id=${params.user_id}`;
    },
  },

  /**
   * Followers list
   */
  FOLLOWERS: {
    list: (params: { user_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/follower/list/?user_id=${params.user_id}&count=${params.count}`;
    },
  },

  /**
   * Following list
   */
  FOLLOWING: {
    list: (params: { user_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/following/list/?user_id=${params.user_id}&count=${params.count}`;
    },
  },

  /**
   * Similar creators
   */
  SIMILAR: {
    creators: (params: { user_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/discover/related/?user_id=${params.user_id}`;
    },
  },

  /**
   * Trending sounds
   */
  TRENDING: {
    sounds: (params: { count: number; region: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/trending/sound/?count=${params.count}&region=${params.region}`;
    },
  },

  /**
   * Hashtag details
   */
  HASHTAG: {
    detail: (params: { hashtag_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/challenge/?challenge_id=${params.hashtag_id}`;
    },
  },

  /**
   * Keyword search (videos)
   */
  KEYWORD: {
    video: (params: { keyword: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/search/item/?keyword=${encodeURIComponent(params.keyword)}&search_type=video&count=${params.count}`;
    },
  },

  /**
   * Keyword search (creators)
   */
  KEYWORD: {
    creator: (params: { keyword: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/search/user/?keyword=${encodeURIComponent(params.keyword)}&count=${params.count}`;
    },
  },

  /**
   * Keyword search (sounds)
   */
  KEYWORD: {
    sound: (params: { keyword: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/search/music/?keyword=${encodeURIComponent(params.keyword)}&count=${params.count}`;
    },
  },

  /**
   * Trending shelves
   */
  TRENDING: {
    shelves: (params: { count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/trending/shelf/?count=${params.count}`;
    },
  },

  /**
   * Camera effects
   */
  EFFECTS: {
    list: (params: { count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/effect/list/?count=${params.count}`;
    },
  },

  /**
   * Video detail
   */
  VIDEO: {
    detail: (params: { aweme_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/aweme/detail/?aweme_id=${params.aweme_id}`;
    },
  },

  /**
   * Comment replies
   */
  COMMENT: {
    replies: (params: { comment_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/comment/list/comment/?comment_id=${params.comment_id}&count=${params.count}`;
    },
  },

  /**
   * Live stream info
   */
  LIVE: {
    info: (params: { room_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/live/stream/info/?room_id=${params.room_id}`;
    },
  },

  /**
   * User stats
   */
  STATS: {
    user: (params: { user_id: string }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/stats/?user_id=${params.user_id}`;
    },
  },

  /**
   * Creator graph
   */
  GRAPH: {
    similar: (params: { user_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/graph/similar/?user_id=${params.user_id}&count=${params.count}`;
    },
  },

  /**
   * Video interaction history
   */
  INTERACTION: {
    history: (params: { user_id: string; count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/interaction/history/?user_id=${params.user_id}&count=${params.count}`;
    },
  },

  /**
   * Bookmark list
   */
  BOOKMARK: {
    list: (params: { count: number }) => {
      return `https://api16-normal-us.tiktok.com/aweme/v1/bookmark/list/?count=${params.count}`;
    },
  },
};

// Type helper for endpoint parameters
export type EndpointParams = {
  [key: string]: string | number;
};
