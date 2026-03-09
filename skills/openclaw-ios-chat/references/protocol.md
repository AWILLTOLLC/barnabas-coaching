# Gateway WebSocket Protocol Reference

Source: `src/gateway/protocol/schema/` in openclaw/openclaw repo.
Swift types auto-generated via: `pnpm protocol:gen:swift`

## Framing

All frames are JSON text messages. Three types, discriminated by `type`:

```swift
// Request (client → gateway)
{ "type": "req", "id": "uuid", "method": "chat.send", "params": { ... } }

// Response (gateway → client)
{ "type": "res", "id": "uuid", "ok": true, "payload": { ... } }
{ "type": "res", "id": "uuid", "ok": false, "error": { "code": "...", "message": "..." } }

// Event (gateway → client, unsolicited)
{ "type": "event", "event": "chat", "payload": { ... }, "seq": 42 }
```

Always include a unique `id` per request. Match responses by `id`.

## Handshake

### Step 1: Gateway sends challenge (before client sends anything)
```json
{
  "type": "event",
  "event": "connect.challenge",
  "payload": { "nonce": "abc123", "ts": 1771960870988 }
}
```

### Step 2: Client sends connect
```json
{
  "type": "req",
  "id": "req-001",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 3,
    "client": {
      "id": "openclaw-ios",
      "displayName": "OpenClaw iOS",
      "version": "1.0.0",
      "platform": "ios",
      "deviceFamily": "iPhone",
      "mode": "operator"
    },
    "role": "operator",
    "scopes": ["operator.read", "operator.write"],
    "caps": [],
    "auth": {
      "token": "<gateway-token>",
      "deviceToken": "<stored-device-token-if-any>"
    },
    "locale": "en-US",
    "userAgent": "openclaw-ios/1.0.0",
    "device": {
      "id": "<stable-device-fingerprint>",
      "publicKey": "<base64-ed25519-pubkey>",
      "signature": "<base64-sign(nonce+ts)>",
      "signedAt": 1771960870988,
      "nonce": "abc123"
    }
  }
}
```

### Step 3: Gateway responds hello-ok
```json
{
  "type": "res",
  "id": "req-001",
  "ok": true,
  "payload": {
    "type": "hello-ok",
    "protocol": 3,
    "server": { "version": "2026.2.24", "connId": "conn-xyz" },
    "features": {
      "methods": ["chat.send", "chat.history", "chat.abort", ...],
      "events": ["chat", "agent", "tick", ...]
    },
    "auth": {
      "deviceToken": "<persist-this-in-keychain>",
      "role": "operator",
      "scopes": ["operator.read", "operator.write"]
    },
    "policy": {
      "maxPayload": 1048576,
      "tickIntervalMs": 15000
    }
  }
}
```

Persist `hello-ok.auth.deviceToken` in Keychain. Use on subsequent connects instead of the gateway token (token still needed as fallback if device token is revoked).

## Chat API

### chat.send — send a message

```json
{
  "type": "req",
  "id": "req-002",
  "method": "chat.send",
  "params": {
    "sessionKey": "agent:default:main",
    "message": "What's the weather in Seattle?",
    "idempotencyKey": "uuid-per-send-attempt"
  }
}
```

**Non-blocking.** Acks immediately:
```json
{ "type": "res", "id": "req-002", "ok": true, "payload": { "runId": "run-abc", "status": "started" } }
```

Resending same `idempotencyKey` while in-flight returns `{ "status": "in_flight" }`. Use a fresh UUID per unique send attempt; reuse the same UUID for retries of the same message.

### chat.history — load conversation

```json
{
  "type": "req",
  "id": "req-003",
  "method": "chat.history",
  "params": {
    "sessionKey": "agent:default:main",
    "limit": 50
  }
}
```

Returns array of transcript entries. Large entries may be truncated by the gateway for UI safety.

### chat.abort — cancel a running turn

```json
{
  "type": "req",
  "id": "req-004",
  "method": "chat.abort",
  "params": {
    "sessionKey": "agent:default:main",
    "runId": "run-abc"  // optional — omit to abort all active runs
  }
}
```

### chat events — streaming response

While a run is active, the gateway emits `chat` events:

```json
{
  "type": "event",
  "event": "chat",
  "payload": {
    "runId": "run-abc",
    "sessionKey": "agent:default:main",
    "seq": 0,
    "state": "delta",       // delta | final | aborted | error
    "message": { ... },     // present on delta and final
    "errorMessage": null,
    "usage": null,
    "stopReason": null
  }
}
```

State machine:
- `delta` — partial content, update UI progressively
- `final` — complete message, replace any delta content
- `aborted` — run was stopped (may have partial content in message)
- `error` — run failed (errorMessage has details)

**The working indicator:** show spinner from `chat.send` ack until first `delta` or `final` event arrives. Display elapsed time. If sub-agents are running, gateway may emit `agent` events — subscribe to those for "Running 2 sub-agents..." status.

### sessions.list — list available sessions

```json
{
  "type": "req",
  "id": "req-005",
  "method": "sessions.list",
  "params": {}
}
```

Returns sessions for the current agent. Default session key for direct chat: `agent:default:main`.

## Session key format

`agent:<agentId>:<sessionKey>`

Default single-agent setup: `agent:default:main`

## APNs registration

```json
{
  "type": "req",
  "id": "req-010",
  "method": "push.apns.register",
  "params": {
    "nodeId": "<device-id>",
    "token": "<apns-hex-token>",
    "environment": "sandbox"  // or "production"
  }
}
```

Call after hello-ok. Whenever APNs token refreshes (`didRegisterForRemoteNotificationsWithDeviceToken`), re-register with gateway.

## Keepalive

Gateway sends `tick` events every `policy.tickIntervalMs` (15s default):
```json
{ "type": "event", "event": "tick", "payload": { "ts": 1771960885000 } }
```

No client response required. Use tick absence to detect dead connections — reconnect if no frame received in `tickIntervalMs * 2`.

## Error codes to handle

- `PAIRING_REQUIRED` — device not paired, initiate pairing flow
- `AUTH_FAILED` — bad token, prompt re-setup
- `RATE_LIMITED` — back off and retry after `retryAfterMs`
- `SESSION_NOT_FOUND` — session key invalid, refresh session list

## Swift codegen

Generate typed Swift models from TypeBox schemas:
```bash
# from repo root
pnpm protocol:gen:swift
```

Output lands in `apps/ios/Sources/Generated/` (check project.yml for exact path). Regenerate after any schema changes — do not hand-edit generated files.
