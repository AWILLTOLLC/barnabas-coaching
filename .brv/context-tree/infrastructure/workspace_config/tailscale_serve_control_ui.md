# Tailscale Serve Control UI Fix

**Date:** 2026-08-26

**Problem:** Control UI WebSocket connection failed from remote devices over Tailscale. Error: "control ui requires device identity (use https or localhost secure context)"

**Root Cause:** The control UI uses WebCrypto to generate a device identity, which browsers only expose in **secure contexts**: HTTPS or localhost/127.0.0.1. The Tailscale IP `100.65.203.16` over plain HTTP wasn't a secure context, so the WebCrypto step failed and the WebSocket upgrade died.

**Solutions:**

1. **Local Mac (instant):** Use loopback address which counts as secure even over HTTP:
   ```
   http://127.0.0.1:18789/chat?session=***
   ```

2. **Remote devices over Tailscale (proper fix):** Enable Tailscale Serve for HTTPS:
   ```json
   "gateway": {
     "tailscale": {
       "mode": "serve"
     }
   }
   ```
   Then access via: `https://apollo-1.tailb4a099.ts.net/chat?session=***`

**Caveat:** `SIGUSR1` hot-reload doesn't re-run Serve setup; needs full gateway restart for config-driven management.

**Outcome:** Serve enabled live, remote Mac connection works. Gateway host name corrected to `apollo-1` (not `aarons-macbook-pro-2`).
