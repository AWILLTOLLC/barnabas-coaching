# apps/ios Codebase Reference

## Actual file layout (verified from source)

```
apps/ios/
├── project.yml                         # xcodegen config — EDIT THIS, not xcodeproj
├── LocalSigning.xcconfig.example       # copy to LocalSigning.xcconfig for personal signing
├── Signing.xcconfig                    # org signing config
├── SwiftSources.input.xcfilelist       # input list for SwiftFormat/SwiftLint build phases
├── fastlane/
│   ├── Fastfile                        # beta (TestFlight) + metadata lanes
│   ├── Appfile                         # bundle ID + Apple ID
│   ├── .env.example                    # copy to .env, fill in ASC keys + team
│   └── SETUP.md                        # Fastlane setup instructions
├── Sources/
│   ├── OpenClaw.entitlements           # APNs, capabilities
│   ├── Info.plist
│   ├── OpenClawApp.swift               # @main entry point, environment setup
│   ├── RootView.swift                  # root view (onboarding or RootTabs)
│   ├── RootTabs.swift                  # tab bar: Screen / Voice / Settings (Chat tab missing)
│   ├── RootCanvas.swift                # canvas surface
│   ├── SessionKey.swift                # session key helpers
│   ├── Calendar/CalendarService.swift
│   ├── Camera/CameraController.swift
│   ├── Capabilities/NodeCapabilityRouter.swift
│   ├── Chat/
│   │   ├── ChatSheet.swift             # wraps OpenClawChatView — current chat entry point
│   │   └── IOSGatewayChatTransport.swift # implements OpenClawChatTransport protocol
│   ├── Contacts/ContactsService.swift
│   ├── Device/
│   │   ├── DeviceInfoHelper.swift
│   │   ├── DeviceStatusService.swift
│   │   ├── NetworkStatusService.swift
│   │   └── NodeDisplayName.swift
│   ├── EventKit/EventKitAuthorization.swift
│   ├── Gateway/
│   │   ├── GatewayConnectionController.swift  # main connection state machine
│   │   ├── GatewayConnectConfig.swift
│   │   ├── GatewayConnectionIssue.swift
│   │   ├── GatewayDiscoveryDebugLogView.swift
│   │   ├── GatewayDiscoveryModel.swift        # Bonjour discovery
│   │   ├── GatewayHealthMonitor.swift
│   │   ├── GatewayQuickSetupSheet.swift
│   │   ├── GatewayServiceResolver.swift       # mDNS service resolver
│   │   ├── GatewaySettingsStore.swift         # persists gateway URL/token
│   │   ├── GatewaySetupCode.swift
│   │   ├── GatewayTrustPromptAlert.swift      # TLS fingerprint trust UI
│   │   ├── DeepLinkAgentPromptAlert.swift
│   │   ├── KeychainStore.swift                # Keychain wrapper
│   │   └── TCPProbe.swift                     # pre-connect reachability probe
│   ├── Location/
│   │   ├── LocationService.swift
│   │   └── SignificantLocationMonitor.swift
│   ├── Media/PhotoLibraryService.swift
│   ├── Model/
│   │   ├── NodeAppModel.swift                 # main app model (@Observable)
│   │   ├── NodeAppModel+Canvas.swift
│   │   └── NodeAppModel+WatchNotifyNormalization.swift
│   ├── Motion/MotionService.swift
│   ├── Onboarding/
│   │   ├── GatewayOnboardingView.swift
│   │   ├── OnboardingStateStore.swift
│   │   ├── OnboardingWizardView.swift
│   │   └── QRScannerView.swift
│   ├── Reminders/RemindersService.swift
│   ├── Screen/
│   │   ├── ScreenController.swift
│   │   ├── ScreenRecordService.swift
│   │   ├── ScreenTab.swift                    # the "Screen" tab (canvas/WebView)
│   │   └── ScreenWebView.swift
│   ├── Services/
│   │   ├── NodeServiceProtocols.swift
│   │   ├── NotificationService.swift
│   │   └── WatchMessagingService.swift
│   ├── Settings/
│   │   ├── SettingsNetworkingHelpers.swift
│   │   ├── SettingsTab.swift
│   │   └── VoiceWakeWordsSettingsView.swift
│   ├── Status/
│   │   ├── StatusActivityBuilder.swift
│   │   ├── StatusPill.swift                   # connection status overlay pill
│   │   └── VoiceWakeToast.swift
│   └── Voice/
│       ├── TalkModeManager.swift
│       ├── TalkOrbOverlay.swift
│       ├── VoiceTab.swift                     # the "Voice" tab
│       ├── VoiceWakeManager.swift
│       └── VoiceWakePreferences.swift
├── ShareExtension/
│   ├── Info.plist
│   └── ShareViewController.swift
├── WatchApp/                                  # watchOS app target
│   ├── Assets.xcassets/
│   └── Info.plist
└── WatchExtension/
    ├── Sources/
    │   ├── OpenClawWatchApp.swift
    │   ├── WatchConnectivityReceiver.swift
    │   ├── WatchInboxStore.swift
    │   └── WatchInboxView.swift
    └── Info.plist
```

## Shared packages (apps/shared/OpenClawKit/)

```
Sources/
├── OpenClawKit/
│   └── ChatCommands.swift              # slash commands
├── OpenClawChatUI/
│   ├── ChatView.swift                  # top-level chat view (use this)
│   ├── ChatViewModel.swift             # @Observable, owns message list + send state
│   ├── ChatComposer.swift              # text input + send button
│   ├── ChatMessageViews.swift          # message bubble rendering
│   ├── ChatMarkdownPreprocessor.swift  # cleans up raw markdown
│   ├── ChatMarkdownRenderer.swift      # renders to AttributedString
│   ├── ChatModels.swift                # ChatMessage, ChatSession types
│   ├── ChatTheme.swift                 # colors, fonts
│   ├── ChatTransport.swift             # OpenClawChatTransport protocol
│   ├── ChatPayloadDecoding.swift       # decodes gateway chat payloads
│   ├── ChatSessions.swift              # session list + switcher
│   └── ChatSheets.swift               # sheet presentation helpers
└── OpenClawProtocol/
    └── ...                             # generated Swift types from TypeBox schemas
```

## Build system

The Xcode project is **generated** by xcodegen. Never edit `OpenClaw.xcodeproj` directly.

```bash
# After editing project.yml:
cd apps/ios && xcodegen generate

# Shortcut (signing + xcodegen + open):
pnpm ios:open
```

## How IOSGatewayChatTransport works

`IOSGatewayChatTransport` conforms to `OpenClawChatTransport` (defined in `OpenClawChatUI`). It wraps a `GatewayNodeSession` and translates gateway RPC calls:

```swift
struct IOSGatewayChatTransport: OpenClawChatTransport, Sendable {
    private let gateway: GatewayNodeSession

    // Implemented methods:
    func sendMessage(sessionKey:message:thinking:idempotencyKey:attachments:) async throws -> OpenClawChatSendResponse
    func requestHistory(sessionKey:) async throws -> OpenClawChatHistoryPayload
    func listSessions(limit:) async throws -> OpenClawChatSessionsListResponse
    func setActiveSessionKey(_:) async throws  // no-op for operator (no subscription needed)
    func abortRun(sessionKey:runId:) async throws
    func requestHealth(timeoutMs:) async throws -> Bool
    func events() -> AsyncStream<OpenClawChatTransportEvent>  // tick/seqGap/health/chat/agent events
}
```

The `events()` stream is the key — it bridges gateway server events into typed `OpenClawChatTransportEvent` cases that `ChatViewModel` consumes.

## How to add the Chat tab

In `Sources/RootTabs.swift`, the TabView currently has Screen (tag 0), Voice (tag 1), Settings (tag 2).

Add before the Screen tab:
```swift
Tab("Chat", systemImage: "bubble.left.and.bubble.right") {
    // ChatSheet is currently a modal wrapper — promote to a full view
    NavigationStack {
        OpenClawChatView(
            viewModel: OpenClawChatViewModel(
                sessionKey: appModel.defaultSessionKey,
                transport: IOSGatewayChatTransport(gateway: appModel.gatewaySession)),
            showsSessionSwitcher: true)
    }
}
.tag(0)
// Renumber existing tags: Screen→1, Voice→2, Settings→3
```

Check `NodeAppModel` for the correct property names (`gatewaySession`, `defaultSessionKey`).

## Common build failures

| Error | Cause | Fix |
|---|---|---|
| "Module not found" after xcodegen | DerivedData stale | `rm -rf ~/Library/Developer/Xcode/DerivedData/OpenClaw-*` |
| Signing error | Wrong team in LocalSigning.xcconfig | Check `OPENCLAW_DEVELOPMENT_TEAM` value |
| APNs registration failure | Running on simulator | Use real device |
| WebSocket SSL error | Using `ws://` for Tailscale URL | Use `wss://` for Tailscale Serve |
| "Pairing required" on first connect | New device, not approved | `openclaw devices approve <id>` on server |
| SwiftFormat error in build | Code style violation | Run `swiftformat .` in apps/ios/ |
| SwiftLint error in build | Lint violation | Fix or use `// swiftlint:disable:next rule-name` |

## Swift version and concurrency

The project uses **Swift 6.0** with `SWIFT_STRICT_CONCURRENCY = complete`. This means:
- All actor isolation errors are compile errors, not warnings
- Use `@MainActor` on all ObservableObject/Observable classes that touch UI
- Use `await MainActor.run { }` when crossing actor boundaries
- `Sendable` conformance required for types crossing concurrency boundaries (note `IOSGatewayChatTransport` is `Sendable`)
