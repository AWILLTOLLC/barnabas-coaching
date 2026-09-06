---
name: "background-scanner-setup"
description: "Set up background scanner with Discord alerts matching meme coin watcher pattern"
---

# Background Scanner Setup Skill

## Trigger
User requests setting up a new background scanner (infrastructure, meme coin, etc.) that runs periodically with Discord alerts, matching an existing scanner pattern.

## Procedure

### 1. Explore existing setup
- Check for running processes: `ps aux | grep <scanner-name>`
- Find the existing scanner CLI (e.g., `hood-pulse.mjs`, `hood-infra.mjs`)
- Identify polling interval, alert mechanism, and data sources
- Check for shared configuration (API keys in `.env` files)

### 2. Create new scanner CLI
- Write script with `watch` and `run` modes
- Use same alert delivery mechanism (Discord DM via REST API)
- Reuse existing API keys where possible
- Set longer polling interval (5-10 min) to avoid rate limit conflicts
- Include test mode for verification

### 3. Configure filters
- Define detection criteria based on user requirements
- Set appropriate thresholds for the target use case
- Include risk flags to report (not filter out)
- Match emoji/style to differentiate from other scanners

### 4. Start in background
- Run with `nohup <script> watch > output.log 2>&1 &`
- Capture PID for later management
- Verify process is running: `ps aux | grep <script>`

### 5. Document and verify
- Create README with usage commands and criteria
- Log file location for monitoring
- Discord alert confirmation
- Provide stop/start commands

## Key Decisions
- **Polling interval:** 10 min for infrastructure, 30s for memes (rate limit balance)
- **API key sharing:** Reuse existing keys to minimize config duplication
- **Alert delivery:** Discord DM via REST API (zero-token path)
- **Emoji differentiation:** 🚀 for memes, 🏗️ for infrastructure

## Output
- Scanner running in background
- First scan results logged
- Discord alerts sent for matches
- Documentation with usage commands
