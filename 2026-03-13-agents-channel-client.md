# Agents Channel — Client-Side Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add client-side support for a shared "agents channel" where multiple per-channel agents collaborate — model changes, creation UI, and agent attribution badges on chat bubbles.

**Architecture:** Minimal surface area — one new field on VantageChannel, one new field on DisplayMessage, UI toggles in CreateChannelSheet, and an agent name badge in ChatBubbleView. No new files. Server-side fan-out/cooldown is Eagle's domain (spec in `docs/plans/2026-03-13-agents-channel-design.md`).

**Tech Stack:** SwiftUI macOS 14+, @Observable, GRDB

---

### Task 1: Add `isAgentsChannel` to VantageChannel Model

**Files:**
- Modify: `VantageOC/Models/Channel.swift:4-64`

**Step 1: Add field to struct**

Add `var isAgentsChannel: Bool` after `agentName` (line 15):

```swift
var agentName: String?
var isAgentsChannel: Bool
```

**Step 2: Update memberwise init (line 34)**

Add `isAgentsChannel: Bool = false` parameter:

```swift
init(slug: String, name: String, description: String? = nil, icon: String? = nil, workspacePath: String? = nil, createdAt: Int, unreadCount: Int, isMain: Bool = false, soul: String? = nil, agentName: String? = nil, isAgentsChannel: Bool = false) {
```

And assign it:

```swift
self.agentName = agentName
self.isAgentsChannel = isAgentsChannel
```

**Step 3: Update decoder init (line 47)**

After line 62, add:

```swift
isAgentsChannel = try container.decodeIfPresent(Bool.self, forKey: .isAgentsChannel) ?? false
```

**Step 4: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 5: Commit**

```bash
git add VantageOC/Models/Channel.swift
git commit -m "feat: add isAgentsChannel field to VantageChannel model"
```

---

### Task 2: Add `agentName` to DisplayMessage

**Files:**
- Modify: `VantageOC/ViewModels/ChannelViewModel.swift:328-399`

**Step 1: Add field to DisplayMessage struct**

After `var attachmentImages: [NSImage]` (line 341), add:

```swift
/// Agent name for messages authored by an agent in the agents channel.
var agentName: String?
```

**Step 2: Add parameter to memberwise init**

After `attachmentImages: [NSImage] = []` (line 374), add:

```swift
agentName: String? = nil
```

And assign in the body after `self.attachmentImages = attachmentImages`:

```swift
self.agentName = agentName
```

**Step 3: Parse agentName from metadata in `init(stored:)`**

After `self.attachmentImages = []` (line 398), add:

```swift
// Parse agentName from metadata JSON (set by gateway for agent-authored messages)
if let metaString = stored.metadata,
   let metaData = metaString.data(using: .utf8),
   let json = try? JSONSerialization.jsonObject(with: metaData) as? [String: Any],
   let agent = json["agentName"] as? String {
    self.agentName = agent
} else {
    self.agentName = nil
}
```

**Step 4: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 5: Commit**

```bash
git add VantageOC/ViewModels/ChannelViewModel.swift
git commit -m "feat: parse agentName from message metadata for agent attribution"
```

---

### Task 3: Preserve `agentName` in Dedup Paths

**Files:**
- Modify: `VantageOC/ViewModels/ChannelViewModel.swift:188-194` (refreshMessages dedup)
- Modify: `VantageOC/ViewModels/ChannelViewModelStreaming.swift:98-110` (handleChat dedup)

**Step 1: Preserve in refreshMessages**

In `refreshMessages()`, after `serverMsg.attachmentImages = localImages` (line 193), add:

```swift
if serverMsg.agentName == nil { serverMsg.agentName = messages[localIdx].agentName }
```

Note: For agent-authored messages, the server copy's metadata WILL have agentName (parsed in init(stored:)), so this is a safety net — the local copy wouldn't have it anyway (only human-sent messages are local). This line is defensive only.

**Step 2: Preserve in handleChat**

In `handleChat()`, the dedup replacement already carries `attachmentImages: localImages`. After that line (109), the `agentName` isn't relevant here because chat envelope dedup is for user-sent or streamed messages, not agent-channel messages. No change needed — agent messages arrive via polling, not WebSocket envelope.

**Step 3: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 4: Commit**

```bash
git add VantageOC/ViewModels/ChannelViewModel.swift
git commit -m "feat: preserve agentName during message dedup"
```

---

### Task 4: Update GatewayAPI with New RPC Parameters

**Files:**
- Modify: `VantageOC/Services/GatewayAPI.swift:83-104`

**Step 1: Update createChannel signature and body**

Replace the existing `createChannel` method (lines 83-91):

```swift
@discardableResult
func createChannel(slug: String, name: String, description: String? = nil, icon: String? = nil, soul: String? = nil, agentName: String? = nil, isAgentsChannel: Bool = false, joinAgentsChannel: Bool = false) async throws -> Any? {
    var params: [String: Any] = ["slug": slug, "name": name]
    if let description { params["description"] = description }
    if let icon { params["icon"] = icon }
    if let soul { params["soul"] = soul }
    if let agentName { params["agentName"] = agentName }
    if isAgentsChannel { params["isAgentsChannel"] = true }
    if joinAgentsChannel { params["joinAgentsChannel"] = true }
    return try await request("vantage.channels.create", params: params)
}
```

**Step 2: Update renameChannel signature and body**

Replace the existing `renameChannel` method (lines 98-104):

```swift
@discardableResult
func renameChannel(slug: String, name: String, icon: String? = nil, agentName: String? = nil, joinAgentsChannel: Bool? = nil) async throws -> Any? {
    var params: [String: Any] = ["slug": slug, "name": name]
    if let icon { params["icon"] = icon }
    if let agentName { params["agentName"] = agentName }
    if let joinAgentsChannel { params["joinAgentsChannel"] = joinAgentsChannel }
    return try await request("vantage.channels.rename", params: params)
}
```

**Step 3: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 4: Commit**

```bash
git add VantageOC/Services/GatewayAPI.swift
git commit -m "feat: add isAgentsChannel and joinAgentsChannel RPC params"
```

---

### Task 5: Update AppCoordinator Channel Operations

**Files:**
- Modify: `VantageOC/App/AppCoordinatorChannelOps.swift:97-123` (createChannel)

**Step 1: Update createChannel signature**

Replace the method signature (line 98):

```swift
func createChannel(name: String, slug: String, description: String?, icon: String?, soul: String? = nil, agentName: String? = nil, isAgentsChannel: Bool = false, joinAgentsChannel: Bool = false) async {
```

**Step 2: Update the RPC call (line 100)**

```swift
let _ = try await gateway.createChannel(slug: slug, name: name, description: description, icon: icon, soul: soul, agentName: agentName, isAgentsChannel: isAgentsChannel, joinAgentsChannel: joinAgentsChannel)
```

**Step 3: Update the optimistic VantageChannel (lines 102-110)**

Add `isAgentsChannel` to the constructor:

```swift
let channel = VantageChannel(
    slug: slug,
    name: name,
    description: description,
    icon: icon,
    createdAt: Int(Date().timeIntervalSince1970 * 1000),
    unreadCount: 0,
    agentName: agentName,
    isAgentsChannel: isAgentsChannel
)
```

**Step 4: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 5: Commit**

```bash
git add VantageOC/App/AppCoordinatorChannelOps.swift
git commit -m "feat: pass isAgentsChannel and joinAgentsChannel through coordinator"
```

---

### Task 6: Add `hasAgentsChannel` to ChannelStore

**Files:**
- Modify: `VantageOC/App/Stores/ChannelStore.swift:1-56`

**Step 1: Add computed property**

After `totalUnread` (line 25), add:

```swift
/// Whether an agents channel exists in the workspace.
var hasAgentsChannel: Bool {
    channels.contains { $0.isAgentsChannel }
}

/// The slug of the agents channel, if one exists.
var agentsChannelSlug: String? {
    channels.first { $0.isAgentsChannel }?.slug
}
```

**Step 2: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 3: Commit**

```bash
git add VantageOC/App/Stores/ChannelStore.swift
git commit -m "feat: add hasAgentsChannel and agentsChannelSlug to ChannelStore"
```

---

### Task 7: Update CreateChannelSheet with Agents Channel Toggles

**Files:**
- Modify: `VantageOC/Views/Sidebar/CreateChannelSheet.swift:1-233`

**Step 1: Add state variables**

After `@State private var showEmojiPicker = false` (line 15), add:

```swift
@State private var isAgentsChannel = false
@State private var joinAgentsChannel = false
```

Add environment for ChannelStore:

```swift
@Environment(ChannelStore.self) private var channelStore
```

**Step 2: Add "Create as Agents Channel" toggle**

After the agent name field (after line 122), add:

```swift
// Agents channel toggle — mutually exclusive with soul/agent
if !channelStore.hasAgentsChannel {
    Divider().overlay(VantageTheme.divider)

    Toggle(isOn: $isAgentsChannel) {
        VStack(alignment: .leading, spacing: 2) {
            Text("Create as Agents Channel")
                .font(VantageTheme.fontBody)
                .foregroundStyle(VantageTheme.textPrimary)
            Text("A shared channel where per-channel agents collaborate")
                .font(VantageTheme.fontCaption)
                .foregroundStyle(VantageTheme.textMuted)
        }
    }
    .toggleStyle(.switch)
    .tint(VantageTheme.accent)
}

// Join agents channel toggle — only for channels with an agent
if channelStore.hasAgentsChannel && !isAgentsChannel && !agentName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
    Toggle(isOn: $joinAgentsChannel) {
        VStack(alignment: .leading, spacing: 2) {
            Text("Join Agents Channel")
                .font(VantageTheme.fontBody)
                .foregroundStyle(VantageTheme.textPrimary)
            Text("This agent will participate in the shared agents channel")
                .font(VantageTheme.fontCaption)
                .foregroundStyle(VantageTheme.textMuted)
        }
    }
    .toggleStyle(.switch)
    .tint(VantageTheme.accent)
}
```

**Step 3: Hide agent name field when agents channel is toggled on**

Wrap the existing agent name field (lines 116-122) in a conditional:

```swift
if !isAgentsChannel {
    // Agent name
    formField("AGENT NAME", placeholder: "Forge") {
        TextField("Forge", text: $agentName)
            .textFieldStyle(.plain)
            .font(VantageTheme.fontBody)
            .foregroundStyle(VantageTheme.textPrimary)
    }
}
```

**Step 4: Set default icon when agents channel toggled**

Add an `onChange` handler. After the `.frame(width: 420, height: 400)` line (152), add before `.background`:

```swift
.onChange(of: isAgentsChannel) { _, newValue in
    if newValue {
        icon = "🤖"
        agentName = ""
        joinAgentsChannel = false
    }
}
```

**Step 5: Update createAction**

Replace the `createAction()` method (lines 215-232):

```swift
private func createAction() {
    guard isFormValid else { return }
    isSubmitting = true
    errorMessage = nil

    let trimmedAgentName = agentName.trimmingCharacters(in: .whitespacesAndNewlines)
    Task {
        await coordinator?.createChannel(
            name: name.trimmingCharacters(in: .whitespacesAndNewlines),
            slug: slug,
            description: nil,
            icon: icon.isEmpty ? nil : icon,
            soul: nil,
            agentName: trimmedAgentName.isEmpty ? nil : trimmedAgentName,
            isAgentsChannel: isAgentsChannel,
            joinAgentsChannel: joinAgentsChannel
        )
        dismiss()
    }
}
```

**Step 6: Increase frame height to accommodate new toggles**

Change `.frame(width: 420, height: 400)` to `.frame(width: 420, height: 480)`.

**Step 7: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 8: Commit**

```bash
git add VantageOC/Views/Sidebar/CreateChannelSheet.swift
git commit -m "feat: add agents channel toggles to CreateChannelSheet"
```

---

### Task 8: Add Agent Name Badge to ChatBubbleView

**Files:**
- Modify: `VantageOC/Views/Channel/ChatBubbleView.swift:24-112`

**Step 1: Add agent name badge above the bubble**

In the `chatRow` computed property, inside the `VStack(alignment: isUser ? .trailing : .leading, spacing: 2)` block (line 28), add the agent name label BEFORE `bubbleContent` (before line 30):

```swift
VStack(alignment: isUser ? .trailing : .leading, spacing: 2) {
    // Agent attribution badge (agents channel only)
    if let agent = message.agentName {
        Text(agent)
            .font(.system(size: 11, weight: .semibold))
            .foregroundStyle(VantageTheme.accent)
            .padding(.leading, 4)
    }

    // Bubble
    bubbleContent
```

**Step 2: Update accessibility label**

In `bubbleAccessibilityLabel` (line 116-126), update the role detection:

```swift
private var bubbleAccessibilityLabel: String {
    let role: String
    if isUser {
        role = "You"
    } else if let agent = message.agentName {
        role = agent
    } else {
        role = "Assistant"
    }
    let preview = String(message.displayContent.prefix(80))
    let statusSuffix: String
    switch message.status {
    case .sending: statusSuffix = ", sending"
    case .error: statusSuffix = ", failed to send"
    default: statusSuffix = ""
    }
    return "\(role): \(preview)\(statusSuffix)"
}
```

**Step 3: Build to verify**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 4: Commit**

```bash
git add VantageOC/Views/Channel/ChatBubbleView.swift
git commit -m "feat: add agent name badge above chat bubbles in agents channel"
```

---

### Task 9: Final Build + Launch Verification

**Step 1: Clean build**

Run: `xcodebuild -project VantageOC.xcodeproj -scheme VantageOC -configuration Debug clean build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

**Step 2: Launch and smoke test**

```bash
pkill -f VantageOC 2>/dev/null; sleep 1
open /Users/erasei/Library/Developer/Xcode/DerivedData/VantageOC-clgjiyarzaneboedmshyoxesuunr/Build/Products/Debug/VantageOC.app
```

Verify:
- App launches without crash
- Existing channels render normally
- Create Channel sheet opens — toggles appear when expected
- No regressions in chat bubble rendering

**Step 3: Commit any fixups if needed**

---

### Summary of Changes

| File | Change |
|------|--------|
| `Models/Channel.swift` | Add `isAgentsChannel: Bool` field |
| `ViewModels/ChannelViewModel.swift` | Add `agentName: String?` to DisplayMessage, parse from metadata |
| `Services/GatewayAPI.swift` | Add `isAgentsChannel` and `joinAgentsChannel` params to create/rename |
| `App/AppCoordinatorChannelOps.swift` | Pass new params through createChannel |
| `App/Stores/ChannelStore.swift` | Add `hasAgentsChannel` and `agentsChannelSlug` computed properties |
| `Views/Sidebar/CreateChannelSheet.swift` | Add toggles for agents channel creation and agent join |
| `Views/Channel/ChatBubbleView.swift` | Add agent name badge above bubble, update accessibility |

**Server-side dependency:** The server (Eagle) must implement the fan-out, cooldown, roster, and message metadata as specified in `docs/plans/2026-03-13-agents-channel-design.md`. The client changes are safe to land independently — they're additive and backwards-compatible. Until Eagle ships, `isAgentsChannel` will always be `false` from the server, agent attribution badges won't appear (no metadata), and the join toggle won't be visible (no agents channel exists).
