# X2Claw Implementation Plan

## Goal
Create a local loader script that auto-configures the X2Claw Chrome extension for the current OpenClaw gateway, then guides the operator to load it in Chrome.

## Scope
- Path 2: Manual install with auto-config
- No ClawHub dependency
- No Chrome Store yet
- Works for any operator with any gateway

## Files to Create/Update

### 1. Extension Config Auto-filler
**Path:** `~/.openclaw/extensions/x2claw/config.json` (created on first load)
**Purpose:** Auto-populated with current gateway URL

**Current state:** Extension has hardcoded placeholder or manual entry
**New state:** Script detects gateway, writes config.json with:
```json
{
  "webhookUrl": "https://<gateway-host>.tailb4a099.ts.net/hooks/x2claw",
  "agents": ["maven", "quinn", "littlejohn", ...]
}
```

### 2. Loader Script
**Path:** `/opt/homebrew/lib/node_modules/openclaw/bin/x2claw-load.js`
**Purpose:** One command to install + configure extension

**Commands:**
```bash
openclaw x2claw load      # Install and configure
openclaw x2claw update    # Update to latest version
openclaw x2claw status    # Show current status
```

**What it does:**
1. Downloads extension from GitHub repo (or copies from workspace)
2. Detects current gateway URL (reads from `openclaw.json` or `~/.openclaw/gateway.json`)
3. Auto-fills config.json with gateway URL
4. Prints instructions:
   ```
   X2Claw installed to: ~/.openclaw/extensions/x2claw/
   
   Next steps:
   1. Open Chrome
   2. Go to chrome://extensions
   3. Enable "Developer mode"
   4. Click "Load unpacked"
   5. Select: ~/.openclaw/extensions/x2claw
   6. Done!
   ```

### 3. Gateway Webhook Handler
**Path:** `/opt/homebrew/lib/node_modules/openclaw/gateway/handlers/x2claw.js`
**Purpose:** Handle incoming tweet URLs from extension

**What it does:**
1. Receives POST to `/hooks/x2claw`
2. Parses payload: `{ url, text, author, agent, prompt_prefix }`
3. Routes to specified agent via `sessions_send`
4. Returns queued confirmation

**Endpoint:** `POST https://<gateway-host>.ts.net/hooks/x2claw`

### 4. Agent List Auto-populator
**Path:** `~/.openclaw/extensions/x2claw/config.json`
**Purpose:** Pre-populate with current operator's agent roster

**What it does:**
1. Reads `~/.openclaw/gateway.json` or `openclaw.json`
2. Queries gateway API for available agents
3. Writes agent list to config.json
4. Extension reads this on load

## Files to Modify

### 1. Extension Popup
**Path:** `~/.openclaw/workspace/projects/x2claw/popup.js`
**Changes:**
- Remove hardcoded agent list
- Read from `config.json` instead
- Graceful fallback if config missing

### 2. Extension Options
**Path:** `~/.openclaw/workspace/projects/x2claw/options.js`
**Changes:**
- Auto-load config.json on first run
- Show "Configured" status if config exists
- Allow manual override if needed

## Build Steps

### Step 1: Extension Repo Setup
1. Create GitHub repo: `openclaw/x2claw`
2. Push extension files from `~/.openclaw/workspace/projects/x2claw/`
3. Add README with install instructions
4. Tag version: `v0.1.0`

### Step 2: Local Loader Script
1. Create `~/.openclaw/extensions/x2claw/` directory
2. Write `bin/x2claw-load.js`
3. Add to OpenClaw CLI:
   ```bash
   # Add to openclaw.json CLI commands
   {
     "commands": {
       "x2claw": {
         "load": "bin/x2claw-load.js",
         "update": "bin/x2claw-load.js --update",
         "status": "bin/x2claw-status.js"
       }
     }
   }
   ```

### Step 3: Gateway Webhook
1. Create `gateway/handlers/x2claw.js`
2. Register in gateway config:
   ```javascript
   // In gateway config
   app.post('/hooks/x2claw', x2clawHandler);
   ```
3. Test with curl:
   ```bash
   curl -X POST https://apollo-1.ts.net/hooks/x2claw \
     -H "Content-Type: application/json" \
     -d '{"url":"...","text":"...","agent":"maven"}'
   ```

### Step 4: Agent List API
1. Create endpoint: `GET /api/agents`
2. Returns list of available agents for current operator
3. Extension calls this on first load to populate dropdown

## Timeline

### Phase 1: Extension Repo (30 minutes)
- Push to GitHub
- Add README
- Tag v0.1.0

### Phase 2: Local Loader (1 hour)
- Write loader script
- Auto-detect gateway
- Auto-fill config
- Test on local machine

### Phase 3: Gateway Handler (1 hour)
- Create webhook handler
- Route to agent
- Test with curl

### Phase 4: Agent List API (30 minutes)
- Create `/api/agents` endpoint
- Return operator's agent roster
- Test with extension

**Total: 3 hours**

## Success Criteria

1. ✅ Run `openclaw x2claw load` → extension installed + configured
2. ✅ Open Chrome → Load unpacked → extension works
3. ✅ Click extension → tweet URL + text detected
4. ✅ Select agent → send → gateway routes to agent
5. ✅ Agent receives tweet + prompt prefix
6. ✅ Agent replies with analysis

## Edge Cases

1. **No gateway detected:** Prompt operator to enter URL manually
2. **Agent not found:** Show error, list available agents
3. **Webhook fails:** Show error, retry option
4. **Extension already loaded:** Detect and offer update

## Future Enhancements

1. Chrome Store submission (after Path 2 validated)
2. Auto-discovery of gateway on local network
3. Cloud config sync (operator email → gateway URL)
4. Batch send (multiple tweets at once)
5. Tagging system (categorize tweets by topic)

## Next Steps

1. Review this plan
2. Approve or request changes
3. Begin Phase 1 (extension repo)
4. Iterate through phases
