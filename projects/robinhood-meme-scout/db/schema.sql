-- TikTok Meme Scout Database Schema
-- SQLite for local storage

-- Coins table: track meme coins being monitored
CREATE TABLE IF NOT EXISTS coins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    name TEXT,
    contract_address TEXT,
    chain TEXT DEFAULT 'robinhood',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tiktok mentions: store mention data with timestamps
CREATE TABLE IF NOT EXISTS tiktok_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    video_id TEXT,
    description TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    creator_followers INTEGER,
    posted_at DATETIME,
    hashtags TEXT, -- JSON array
    virality_score REAL,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id)
);

-- Velocity tracking: daily velocity snapshots
CREATE TABLE IF NOT EXISTS velocity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    date DATE NOT NULL,
    mention_count_24h INTEGER,
    velocity_change REAL,
    avg_engagement REAL,
    top_creators TEXT, -- JSON array
    velocity_score INTEGER,
    trend TEXT, -- 'rising', 'stable', 'falling'
    UNIQUE(coin_id, date),
    FOREIGN KEY (coin_id) REFERENCES coins(id)
);

-- Community scores: combined TikTok + X scores
CREATE TABLE IF NOT EXISTS community_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tiktok_score INTEGER,
    x_score INTEGER,
    combined_score INTEGER,
    trend TEXT, -- 'rising', 'stable', 'falling'
    correlation REAL,
    recommendation TEXT, -- 'buy', 'watch', 'avoid'
    FOREIGN KEY (coin_id) REFERENCES coins(id)
);

-- Alerts: generated signals
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL, -- 'trending', 'velocity_spike', 'community_high'
    score INTEGER,
    message TEXT,
    action_taken TEXT, -- 'bought', 'watched', 'skipped'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tiktok_mentions_coin ON tiktok_mentions(coin_id);
CREATE INDEX IF NOT EXISTS idx_tiktok_mentions_posted ON tiktok_mentions(posted_at);
CREATE INDEX IF NOT EXISTS idx_velocity_coin_date ON velocity_snapshots(coin_id, date);
CREATE INDEX IF NOT EXISTS idx_alerts_coin ON alerts(coin_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
