---
name: openclaw-ios-chat
description: Build and extend the OpenClaw iOS native chat client (operator mode). Use when working on the apps/ios directory of the openclaw/openclaw repo to add or improve the chat UI, background notifications (APNs), Tailscale connectivity, or operator-mode gateway integration. Covers the gateway WebSocket protocol, chat API, device pairing, APNs push setup, and existing Swift/xcodegen codebase structure.
---

# OpenClaw iOS Chat Client

The iOS app lives at `apps/ios/` in the openclaw/openclaw repo. It is more complete than the README suggests. The shared `OpenClawKit` Swift package (at `apps/shared/OpenClawKit/`) contains the full chat UI, transport protocol, and gateway connection logic. The iOS app assembles these pieces.

## Key packages

| Package | Path | What it contains |
|---|---|---|
| `OpenClawKit` | `apps/shared/OpenClawKit/Sources/OpenClawKit/` | Gateway session, commands |
| `OpenClawChatUI` | `apps/shared/OpenClawKit/Sources/OpenClawChatUI/` | Full chat UI: ChatView, ChatViewModel, ChatComposer, markdown renderer, sessions |
| `OpenClawProtocol` | `apps/shared/OpenClawKit/Sources/OpenClawProtocol/` | Swift types generated from TypeBox schemas |
| `Swabble` | `Swabble/` (repo root) | Shared utilities |

## What's already done

- **Gateway WebSocket connection** — `GatewayConnectionController.swift`, `GatewaySettingsStore.swift`, `KeychainStore.swift`
- **Device pairing** — `GatewayDiscoveryModel.swift`, `GatewayQuickSetupSheet.swift`, `OnboardingWizardView.swift`, QR scanner
- **Bonjour discovery** — `GatewayServiceResolver.swift` (discovers `_openclaw-gw._tcp`)
- **Full chat UI** — `OpenClawChatUI` package: `ChatView`, `ChatViewModel`, `ChatComposer`, `ChatMarkdownRenderer`, `ChatMessageViews`, `ChatSessions`, session switcher
- **Chat transport** — `IOSGatewayChatTransport.swift`: implements `chat.send`, `chat.history`, `chat.abort`, `sessions.list`, event streaming
- **APNs token registration** — `push.apns.register` already called after connection
- **Watch app** — `WatchExtension/` with inbox view and WatchConnectivity messaging
- **Fastlane** — `fastlane/Fastfile` with `beta` lane (TestFlight) and `metadata` lane (App Store)
- **Share extension** — deep-link forwarding into connected gateway session
- **Voice wake + Talk mode** — `VoiceWakeManager`, `TalkModeManager`

## What the chat UI looks like now

`ChatSheet` (in `Sources/Chat/ChatSheet.swift`) wraps `OpenClawChatView` from `OpenClawChatUI`. It's presented as a modal sheet from other screens.

The main tab bar (`RootTabs.swift`) has: **Screen / Voice / Settings** — no dedicated Chat tab.

**The MVP change:** promote Chat to the first tab. It's a ~20 line change in `RootTabs.swift`.

## Build setup

**Prerequisites:**
```bash
brew install xcodegen swiftformat swiftlint
npm install -g pnpm  # or brew install pnpm
# Xcode 16+ from App Store
```

**Clone and build:**
```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
pnpm install
./scripts/ios-configure-signing.sh  # auto-detects Apple ID team
pnpm ios:open                        # xcodegen generate + open Xcode
```

**Personal Apple ID signing** (if script can't auto-detect team):
```bash
cp apps/ios/LocalSigning.xcconfig.example apps/ios/LocalSigning.xcconfig
# Edit LocalSigning.xcconfig — set OPENCLAW_DEVELOPMENT_TEAM and bundle IDs
```

**First device run:**
1. Select real iPhone (not simulator — APNs requires device)
2. Hit Run (`⌘R`)
3. On app: enter gateway URL (`wss://ubuntu-ct.tailb4a099.ts.net`) + token
4. First remote connect triggers pairing — approve on server: `openclaw devices approve <id>`

**Get gateway token:**
```bash
grep token ~/.openclaw/openclaw.json
```

## TestFlight (Fastlane)

```bash
cd apps/ios
cp fastlane/.env.example fastlane/.env
# Edit .env: set ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_CONTENT, IOS_DEVELOPMENT_TEAM
bundle exec fastlane beta
```

See `apps/ios/fastlane/SETUP.md` for full Fastlane setup instructions.

## What still needs building

| Feature | Status | Notes |
|---|---|---|
| Chat as first tab | 🔨 easy | ~20 lines in RootTabs.swift |
| Background APNs push firing | 🔨 gateway PR | Gateway needs to fire pushes on chat final events |
| Apple Developer account | 🔨 prereq | $99/yr, needed for TestFlight |

## Key files to know

- `Sources/Chat/ChatSheet.swift` — wraps OpenClawChatView, the current chat entry point
- `Sources/Chat/IOSGatewayChatTransport.swift` — all gateway chat methods implemented here
- `Sources/RootTabs.swift` — tab bar, where Chat tab needs to be added
- `Sources/Gateway/GatewayConnectionController.swift` — main connection state machine
- `Sources/Gateway/KeychainStore.swift` — Keychain wrapper for token/device storage
- `Sources/OpenClawApp.swift` — app entry point, environment setup
- `project.yml` — xcodegen config, edit instead of xcodeproj

**See references/protocol.md** for gateway WebSocket protocol and chat API details.
**See references/codebase.md** for actual file layout and Swift patterns.
**See references/apns.md** for APNs push implementation.
**See references/tailscale.md** for connectivity setup and troubleshooting.
