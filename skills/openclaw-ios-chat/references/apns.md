# APNs Push Notifications Reference

## Design: content-free push

Privacy principle: Apple's servers never see message content.

```
Agent sends message
  → gateway fires APNs push (empty payload: just "wake up")
  → iOS wakes app
  → app reconnects to gateway via Tailscale
  → app fetches actual message content
  → user sees notification with content (locally composed)
```

APNs payload sent by gateway:
```json
{
  "aps": {
    "content-available": 1,
    "alert": { "title": "New message", "body": "From Dru" }
  }
}
```

No message text, no session content, nothing sensitive in the APNs payload.

## iOS app side

### Registration

In `AppDelegate`:
```swift
func application(_ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
        guard granted else { return }
        DispatchQueue.main.async {
            application.registerForRemoteNotifications()
        }
    }
    return true
}

func application(_ application: UIApplication,
    didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let tokenHex = deviceToken.map { String(format: "%02x", $0) }.joined()
    // Register with gateway after connection is established
    Task { await GatewayConnection.shared.registerAPNsToken(tokenHex) }
}

func application(_ application: UIApplication,
    didFailToRegisterForRemoteNotificationsWithError error: Error) {
    // Simulator always fails — log and continue gracefully
    print("APNs registration failed: \(error)")
}
```

### Send token to gateway

After hello-ok succeeds, call `push.apns.register`:
```swift
func registerAPNsToken(_ token: String) async throws {
    let environment = Bundle.main.isDebugBuild ? "sandbox" : "production"
    try await send(method: "push.apns.register", params: [
        "nodeId": deviceIdentity.id,
        "token": token,
        "environment": environment
    ])
}

extension Bundle {
    var isDebugBuild: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
}
```

Re-register whenever token refreshes (iOS may rotate it).

### Background notification handler

```swift
func application(_ application: UIApplication,
    didReceiveRemoteNotification userInfo: [AnyHashable: Any],
    fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
    Task {
        do {
            // Reconnect if needed, fetch latest messages
            await GatewayConnection.shared.ensureConnected()
            let messages = try await GatewayConnection.shared.fetchLatestMessages()
            // Compose local notification with actual content
            if let latest = messages.last {
                showLocalNotification(for: latest)
            }
            completionHandler(.newData)
        } catch {
            completionHandler(.failed)
        }
    }
}
```

### Info.plist requirements

```xml
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
    <string>fetch</string>
</array>
```

In project.yml capabilities section:
```yaml
capabilities:
  - push-notifications
  - background-modes:
      modes: [remote-notification, fetch]
```

## Gateway side (what needs to be built)

The iOS app already registers its APNs token via `push.apns.register`. The gateway needs to **fire** the push when a chat event completes.

### Where to add it (gateway PR)

Location: wherever `chat` events are emitted after a run completes — look for where `state: "final"` events are broadcast to operator clients.

Logic:
1. After broadcasting `state: "final"` chat event
2. Look up registered APNs tokens for the session's agent
3. If any tokens exist and the operator WebSocket is not currently connected (backgrounded) → fire APNs push
4. Use `push.test` method (already exists in schema) as a starting point for the implementation

Gateway needs:
- Apple Developer account p8 key (`AuthKey_XXXXXXXXXX.p8`)
- Key ID, Team ID, bundle ID
- Config keys: `gateway.apns.keyId`, `gateway.apns.teamId`, `gateway.apns.bundleId`, `gateway.apns.keyPath`
- HTTP/2 calls to `api.push.apple.com` (sandbox) or `api.sandbox.push.apple.com`

Existing push schema (`src/gateway/protocol/schema/push.ts`) already has `PushTestParamsSchema` with `nodeId`, `title`, `body`, `environment` — the infrastructure is partially wired.

## APNs prerequisites

- Apple Developer Program membership ($99/yr)
- App ID with Push Notifications capability enabled in developer.apple.com
- APNs Auth Key (p8) — create in Certificates, Identifiers & Profiles → Keys
- Provisioning profile that includes the Push Notifications entitlement

## Testing push

```bash
# Test from gateway CLI (once gateway APNs support is added)
openclaw gateway call push.test --params '{"nodeId":"<device-id>","title":"Test","body":"Hello","environment":"sandbox"}'
```

For now, test with Apple's `apns2` CLI tool or Transporter app to verify the APNs key and token work before wiring up the gateway.

## Notification appearance

Local notifications (composed on-device after fetch):
```swift
func showLocalNotification(for message: ChatMessage) {
    let content = UNMutableNotificationContent()
    content.title = "Dru"
    content.body = String(message.text.prefix(200))  // truncate long messages
    content.sound = .default
    content.badge = NSNumber(value: unreadCount)

    let request = UNNotificationRequest(
        identifier: message.id,
        content: content,
        trigger: nil  // deliver immediately
    )
    UNUserNotificationCenter.current().add(request)
}
```

## Notification actions

Register in AppDelegate:
```swift
let replyAction = UNTextInputNotificationAction(
    identifier: "REPLY",
    title: "Reply",
    options: [],
    textInputButtonTitle: "Send",
    textInputPlaceholder: "Message"
)
let dismissAction = UNNotificationAction(identifier: "DISMISS", title: "Dismiss")
let category = UNNotificationCategory(
    identifier: "CHAT_MESSAGE",
    actions: [replyAction, dismissAction],
    intentIdentifiers: []
)
UNUserNotificationCenter.current().setNotificationCategories([category])
```

Handle reply action:
```swift
func userNotificationCenter(_ center: UNUserNotificationCenter,
    didReceive response: UNNotificationResponse,
    withCompletionHandler completionHandler: @escaping () -> Void) {
    if let textResponse = response as? UNTextInputNotificationResponse,
       response.actionIdentifier == "REPLY" {
        Task { try? await GatewayConnection.shared.sendMessage(textResponse.userText) }
    }
    completionHandler()
}
```
