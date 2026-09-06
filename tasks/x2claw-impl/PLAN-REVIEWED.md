# X2Claw Implementation Plan (Ponytail-Approved)

## Goal
Create a local loader script that auto-configures the X2Claw Chrome extension for the current OpenClaw gateway, then guides the operator to load it in Chrome.

## Scope
- Path 2: Manual install with auto-config
- No ClawHub dependency
- No Chrome Store yet
- Works for any operator with any gateway
- **Lean:** 30 minutes, not 3 hours

## Files to Create/Update

### 1. Extension Config (inline, no separate file)
**Path:** `~/.openclaw/extensions/x2claw/.config` (optional, for persistence)
**Purpose:** Auto-populated with current gateway URL

**Current state:** Extension has hardcoded placeholder or manual entry
**New state:** Script writes config inline during load:
```json
{
  "webhookUrl": "https://<gateway-host>.ts.net/hooks/x2claw",
  "agents": ["maven", "quinn", "littlejohn", ...]
}
```

### 2. Loader Script (single file)
**Path:** `/opt/homebrew/lib/node_modules/openclaw/bin/x2claw.js`
**Purpose:** One command to install + configure extension

**Commands:**
```bash
openclaw x2claw load      # Install and configure
openclaw x2claw update    # Update to latest version
openclaw x2claw status    # Show current status
```

**What it does:**
1. Copies extension from workspace to `~/.openclaw/extensions/x2claw/`
2. Detects current gateway URL (reads from `openclaw.json` or `~/.openclaw/gateway.json`)
3. Auto-fills config inline
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

### 3. Gateway Webhook Handler (inline)
**Path:** Inline in gateway config or minimal file
**Purpose:** Handle incoming tweet URLs from extension

**What it does:**
1. Receives POST to `/hooks/x2claw`
2. Parses payload: `{ url, text, author, agent, prompt_prefix }`
3. Routes to specified agent via `sessions_send`
4. Returns queued confirmation

**Endpoint:** `POST https://<gateway-host>.ts.net/hooks/x2claw`

### 4. Agent List (read from local file)
**Path:** Extension reads `~/.openclaw/gateway.json` directly
**Purpose:** Auto-populate with current operator's agent roster

**What it does:**
1. Extension reads `~/.openclaw/gateway.json` on load
2. Extracts agent list
3. Populates dropdown
4. Graceful fallback if file missing

## Files to Modify

### 1. Extension Popup
**Path:** `~/.openclaw/workspace/projects/x2claw/popup.js`
**Changes:**
- Read config inline (no separate file)
- Graceful fallback if config missing

### 2. Extension Options
**Path:** `~/.openclaw/workspace/projects/x2claw/options.js`
**Changes:**
- Read config inline on first run
- Show "Configured" status if config exists
- Allow manual override if needed

## Build Steps (30 minutes)

### Step 1: Copy Extension (5 minutes)
1. Copy `~/.openclaw/workspace/projects/x2claw/` to `~/.openclaw/extensions/x2claw/`
2. Update `popup.js` to read config inline
3. Test: open extension, check if config loads

### Step 2: Write Loader Script (10 minutes)
1. Create `~/.openclaw/extensions/x2claw/.config`
2. Write `/opt/homebrew/lib/node_modules/openclaw/bin/x2claw.js` with subcommands
3. Auto-detect gateway from `openclaw.json`
4. Test: run `openclaw x2claw load`

### Step 3: Gateway Webhook (10 minutes)
1. Add inline handler to gateway config
2. Register POST `/hooks/x2claw`
3. Test: curl from terminal
4. Test: send tweet from extension

### Step 4: End-to-End Test (5 minutes)
1. Run `openclaw x2claw load`
2. Load extension in Chrome
3. Click extension on tweet
4. Send to agent
5. Verify agent receives message

**Total: 30 minutes**

## Success Criteria

1. ✅ Run `openclaw x2claw load` → extension installed + configured
2. ✅ Extension loads in Chrome, detects tweet
3. ✅ Tweet routes to agent, agent replies

## Edge Cases

1. **Gateway not found:** Prompt operator to enter URL manually
2. **Agent not found:** Show error, list available agents

## Next Steps

1. ✅ Review this plan (ponytail-approved)
2. ✅ Subagent builds it
3. ✅ Test end-to-end
4. ✅ Ship
