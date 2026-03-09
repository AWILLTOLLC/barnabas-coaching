# Tailscale Connectivity Reference

## Aaron's current setup

- Gateway host: `ubuntu-ct`
- Tailscale hostname: `ubuntu-ct.tailb4a099.ts.net`
- Gateway config: `tailscale.mode = "serve"`, `bind = "loopback"`
- Tailscale Serve maps `https://ubuntu-ct.tailb4a099.ts.net` → `http://127.0.0.1:18789`
- Auth: token-based (`gateway.auth.mode = "token"`)

iOS app connects to: `wss://ubuntu-ct.tailb4a099.ts.net`

## Connection priority in the app

```swift
enum ConnectionPath {
    case localNetwork(url: URL)   // same WiFi, direct
    case tailscale(url: URL)      // cellular or cross-network
}
```

Attempt order:
1. **Local network** — try `ws://<local-ip>:18789` via mDNS/Bonjour (`_openclaw-gw._tcp`)
2. **Tailscale** — `wss://<tailscale-hostname>` (works on WiFi + cellular)

Fast-path: on same WiFi, prefer local (faster, no Tailscale latency). Fallback to Tailscale if local times out (1-2s timeout).

## Bonjour discovery (local network fast path)

The gateway advertises `_openclaw-gw._tcp` on `local.`. Use NetServiceBrowser to discover it:

```swift
import Network

class GatewayDiscovery: NSObject, NetServiceBrowserDelegate {
    let browser = NetServiceBrowser()

    func startDiscovery() {
        browser.delegate = self
        browser.searchForServices(ofType: "_openclaw-gw._tcp.", inDomain: "local.")
    }

    func netServiceBrowser(_ browser: NetServiceBrowser,
        didFind service: NetService, moreComing: Bool) {
        service.delegate = self
        service.resolve(withTimeout: 5)
        // → netServiceDidResolveAddress → extract host:port → try local connection
    }
}
```

Gateway advertises port 18789 (or configured port). Local connection uses `ws://` (not TLS).

Note: local connections auto-approve for pairing (no manual `devices approve` needed). Remote (Tailscale) connections require one-time pairing approval.

## TLS and certificate handling

Tailscale Serve provides valid TLS via Tailscale's CA — the cert is trusted by iOS automatically (it's a real Let's Encrypt cert for the MagicDNS hostname). No cert pinning needed for Tailscale Serve URLs.

If the user configures a manual hostname with a self-signed cert:
```swift
extension GatewayConnection: URLSessionDelegate {
    func urlSession(_ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // For self-signed: show fingerprint prompt to user, store accepted fingerprint
        // Match against gateway's advertised tlsFingerprint
        // DO NOT blanket-accept all certs
    }
}
```

Gateway config option: `gateway.remote.tlsFingerprint` — show this in setup UI so user can verify.

## Settings UI for connectivity

First-run setup screen should collect:
1. **Gateway URL** — pre-filled with `wss://` prefix hint
   - Example placeholder: `wss://ubuntu-ct.tailb4a099.ts.net`
   - Or: "Discover automatically" toggle (uses Bonjour, for same-network setup)
2. **Auth token** — paste from `openclaw gateway --show-token` or settings page
3. **Test connection** button — attempt connect, verify hello-ok, show success/error

Store in Keychain:
```swift
KeychainStore.save(key: "openclaw.gateway.url", data: url.absoluteString.data(using: .utf8)!)
KeychainStore.save(key: "openclaw.gateway.token", data: token.data(using: .utf8)!)
```

## Connection state machine

```
disconnected
    → connecting (open WebSocket)
    → challenging (waiting for connect.challenge)
    → authenticating (sent connect frame)
    → pairing_required (first remote connect)
    → connected
    → reconnecting (on error/timeout, exponential backoff)
```

Reconnect strategy:
```swift
var reconnectDelay: TimeInterval = 1.0
let maxDelay: TimeInterval = 60.0

func scheduleReconnect() {
    Task {
        try? await Task.sleep(nanoseconds: UInt64(reconnectDelay * 1_000_000_000))
        reconnectDelay = min(reconnectDelay * 2, maxDelay)
        await connect()
    }
}

// Reset delay on successful connect
func onConnected() {
    reconnectDelay = 1.0
}
```

## Cellular vs WiFi behavior

- **WiFi** — usually same network as gateway, Bonjour discovery works, fastest path
- **Cellular** — Tailscale routes traffic; iOS Tailscale app must be running and authenticated
- **Switched from WiFi to cellular** — WebSocket will drop, trigger reconnect
- **Background cellular** — iOS may kill background connections; APNs wake + reconnect is the reliability path

Monitor network path changes with `NWPathMonitor`:
```swift
let monitor = NWPathMonitor()
monitor.pathUpdateHandler = { path in
    if path.status == .satisfied {
        Task { await GatewayConnection.shared.ensureConnected() }
    }
}
monitor.start(queue: .global(qos: .background))
```

## Troubleshooting connectivity

| Symptom | Likely cause | Fix |
|---|---|---|
| `wss://` connection refused | Tailscale Serve not running | `openclaw gateway --tailscale serve` or check config |
| "Pairing required" error | First remote connect | `openclaw devices approve <id>` on gateway host |
| Connection drops on cellular | Tailscale not authenticated on device | Open Tailscale iOS app, re-authenticate |
| SSL error on local `ws://` | Using TLS URL for non-TLS local | Use `ws://` for local, `wss://` for Tailscale |
| Gateway not discovered via Bonjour | Different network segment or mDNS blocked | Use manual Tailscale URL instead |
| APNs push received but app can't reconnect | Gateway unreachable (VPN not up) | User needs to open Tailscale app first |

## Headscale (self-hosted Tailscale coordination)

For users who want zero third-party coordination server, Headscale is a drop-in replacement for the Tailscale control server. The iOS Tailscale client supports a custom control URL:

1. User sets up Headscale on a VPS
2. In Tailscale iOS app: Settings → Account → Custom control server URL
3. Enter headscale URL
4. Everything else works identically from the OpenClaw iOS app's perspective

No code changes needed in the OpenClaw iOS app — Tailscale handles the routing transparently.
