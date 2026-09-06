# VantageOC Files Pane — Client Implementation Spec

---

## ⚠️ Pre-requisite Fix: Strip Reply Tags from All Message Text

Before implementing the Files pane, apply this fix to the chat message renderer.

The gateway stores raw assistant text in transcripts, including `[[reply_to_current]]` and `[[reply_to:<id>]]` tags that were not stripped before write. When `chat.history` returns these messages, the tags appear literally in the rendered UI.

**Fix:** Strip reply tags from all assistant message text before rendering, in whatever function/view processes chat message text for display.

```swift
extension String {
    /// Strips [[reply_to_current]] and [[reply_to:<id>]] directive tags from
    /// assistant message text before rendering.
    var strippingReplyTags: String {
        self.replacingOccurrences(
            of: #"\[\[\s*reply_to[^\]]*\]\]\s*"#,
            with: "",
            options: .regularExpression
        )
    }
}
```

Apply `.strippingReplyTags` wherever assistant message text is set on a `Text()` view or passed to the markdown renderer. One call site in `ChatMessageViews.swift` (or equivalent) covers all messages.

---

> **Target:** VantageOC macOS app (SwiftUI)  
> **Feature:** Live file browser for OpenClaw agent workspace  
> **Backend RPCs:** `vantage.fs.list`, `vantage.fs.get`, `vantage.fs.put` (already implemented)

---

## 1. GatewayClient Extensions

Add these methods to `GatewayClient.swift`, following the existing RPC pattern:

```swift
// MARK: - Filesystem RPCs

struct FSListResponse: Decodable {
    let path: String
    let entries: [FSEntryDTO]
}

struct FSEntryDTO: Decodable {
    let name: String
    let type: String        // "file" | "dir"
    let size: Int?
    let modified: Int64?    // Unix ms
    let path: String
}

struct FSGetResponse: Decodable {
    let path: String
    let filename: String
    let content: String
    let encoding: String    // "utf8" | "base64"
    let size: Int
    let mimeType: String?
}

struct FSPutResponse: Decodable {
    let path: String
    let saved: Bool
    let size: Int
}

extension GatewayClient {
    
    /// List directory contents at path (relative to workspace root, "" = root)
    func fsList(path: String) async throws -> FSListResponse {
        let result = try await rpc("vantage.fs.list", params: ["path": path])
        let data = try JSONSerialization.data(withJSONObject: result)
        return try JSONDecoder().decode(FSListResponse.self, from: data)
    }
    
    /// Get file content and metadata
    func fsGet(path: String) async throws -> FSGetResponse {
        let result = try await rpc("vantage.fs.get", params: ["path": path])
        let data = try JSONSerialization.data(withJSONObject: result)
        return try JSONDecoder().decode(FSGetResponse.self, from: data)
    }
    
    /// Upload file to workspace
    func fsPut(path: String, content: String, encoding: String) async throws -> FSPutResponse {
        let result = try await rpc("vantage.fs.put", params: [
            "path": path,
            "content": content,
            "encoding": encoding
        ])
        let data = try JSONSerialization.data(withJSONObject: result)
        return try JSONDecoder().decode(FSPutResponse.self, from: data)
    }
}
```

---

## 2. FSEntry Model

Create `Models/FSEntry.swift`:

```swift
import Foundation

enum FSEntryType: String, Codable, Hashable {
    case file
    case dir
}

struct FSEntry: Identifiable, Hashable {
    let id: String              // = path (unique within workspace)
    let name: String
    let type: FSEntryType
    let size: Int?
    let modified: Date?
    let path: String            // relative to workspace root
    
    var children: [FSEntry]?    // nil = not loaded; [] = loaded, empty
    var isLoading: Bool = false
    var isNew: Bool = false     // true briefly after agent creates file
    
    // MARK: - Hashable (exclude mutable state)
    
    static func == (lhs: FSEntry, rhs: FSEntry) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    // MARK: - Factory from DTO
    
    static func from(_ dto: FSEntryDTO) -> FSEntry {
        FSEntry(
            id: dto.path.isEmpty ? "workspace" : dto.path,
            name: dto.name,
            type: dto.type == "dir" ? .dir : .file,
            size: dto.size,
            modified: dto.modified.map { Date(timeIntervalSince1970: Double($0) / 1000.0) },
            path: dto.path,
            children: nil,
            isLoading: false,
            isNew: false
        )
    }
    
    // MARK: - Helpers
    
    var isDirectory: Bool { type == .dir }
    
    var parentPath: String {
        guard let lastSlash = path.lastIndex(of: "/") else { return "" }
        return String(path[..<lastSlash])
    }
    
    var iconName: String {
        guard type == .file else { return "folder.fill" }
        
        let ext = (name as NSString).pathExtension.lowercased()
        switch ext {
        case "md", "txt", "rtf":
            return "doc.text"
        case "swift", "ts", "js", "py", "json", "yaml", "yml", "sh", "bash", "zsh", "html", "css", "tsx", "jsx":
            return "chevron.left.forwardslash.chevron.right"
        case "png", "jpg", "jpeg", "gif", "webp", "heic", "svg":
            return "photo"
        case "pdf":
            return "doc.richtext"
        case "mp3", "wav", "m4a", "aac":
            return "waveform"
        case "mp4", "mov", "m4v":
            return "film"
        case "zip", "tar", "gz", "7z":
            return "archivebox"
        default:
            return "doc"
        }
    }
    
    var formattedSize: String {
        guard let size = size else { return "—" }
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(size))
    }
    
    var formattedModified: String {
        guard let modified = modified else { return "—" }
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: modified, relativeTo: Date())
    }
}
```

---

## 3. FilePreviewState

Add to `Models/FSEntry.swift` or create `Models/FilePreviewState.swift`:

```swift
import Foundation

enum FilePreviewState: Equatable {
    case empty
    case loading
    case markdown(String)
    case code(String, language: String)
    case image(Data, mimeType: String)
    case binary(filename: String, size: Int, modified: Date?)
    case error(String)
    
    static func == (lhs: FilePreviewState, rhs: FilePreviewState) -> Bool {
        switch (lhs, rhs) {
        case (.empty, .empty), (.loading, .loading):
            return true
        case let (.markdown(a), .markdown(b)):
            return a == b
        case let (.code(a1, a2), .code(b1, b2)):
            return a1 == b1 && a2 == b2
        case let (.image(a1, a2), .image(b1, b2)):
            return a1 == b1 && a2 == b2
        case let (.binary(a1, a2, a3), .binary(b1, b2, b3)):
            return a1 == b1 && a2 == b2 && a3 == b3
        case let (.error(a), .error(b)):
            return a == b
        default:
            return false
        }
    }
}

struct UploadSheetState: Identifiable {
    let id = UUID()
    let urls: [URL]
    var destinationPath: String = ""
    var isUploading: Bool = false
    var error: String? = nil
}
```

---

## 4. FilesViewModel

Create `ViewModels/FilesViewModel.swift`:

```swift
import SwiftUI
import Combine

@MainActor
class FilesViewModel: ObservableObject {
    
    // MARK: - Published State
    
    @Published var rootEntries: [FSEntry] = []
    @Published var selectedEntry: FSEntry? = nil
    @Published var previewContent: FilePreviewState = .empty
    @Published var isLoadingPreview: Bool = false
    @Published var filterText: String = ""
    @Published var uploadSheet: UploadSheetState? = nil
    @Published var isLoadingRoot: Bool = false
    @Published var rootError: String? = nil
    @Published var toastMessage: String? = nil
    
    // MARK: - Dependencies
    
    private let gateway: GatewayClient
    private var newFileTimers: [String: Task<Void, Never>] = [:]
    
    init(gateway: GatewayClient) {
        self.gateway = gateway
    }
    
    // MARK: - Load Root
    
    func loadRoot() async {
        isLoadingRoot = true
        rootError = nil
        
        do {
            let response = try await gateway.fsList(path: "")
            rootEntries = response.entries.map(FSEntry.from).sorted(by: entrySortOrder)
            isLoadingRoot = false
        } catch {
            rootError = error.localizedDescription
            isLoadingRoot = false
        }
    }
    
    // MARK: - Expand Directory
    
    func expand(_ entry: FSEntry) async {
        guard entry.isDirectory, entry.children == nil else { return }
        
        updateEntry(at: entry.path) { $0.isLoading = true }
        
        do {
            let response = try await gateway.fsList(path: entry.path)
            let children = response.entries.map(FSEntry.from).sorted(by: entrySortOrder)
            updateEntry(at: entry.path) {
                $0.children = children
                $0.isLoading = false
            }
        } catch {
            updateEntry(at: entry.path) {
                $0.children = []
                $0.isLoading = false
            }
            // Could show inline error, for now just set empty
        }
    }
    
    // MARK: - Select & Preview
    
    func select(_ entry: FSEntry) async {
        selectedEntry = entry
        
        guard entry.type == .file else {
            previewContent = .empty
            return
        }
        
        isLoadingPreview = true
        previewContent = .loading
        
        do {
            let response = try await gateway.fsGet(path: entry.path)
            previewContent = classifyContent(response)
            isLoadingPreview = false
        } catch {
            previewContent = .error(error.localizedDescription)
            isLoadingPreview = false
        }
    }
    
    // MARK: - Download
    
    func download(_ entry: FSEntry) async {
        guard entry.type == .file else { return }
        
        do {
            let response = try await gateway.fsGet(path: entry.path)
            
            let panel = NSSavePanel()
            panel.nameFieldStringValue = response.filename
            panel.canCreateDirectories = true
            
            let result = await panel.begin()
            guard result == .OK, let url = panel.url else { return }
            
            let data: Data
            if response.encoding == "base64" {
                guard let decoded = Data(base64Encoded: response.content) else {
                    showToast("Failed to decode file")
                    return
                }
                data = decoded
            } else {
                data = response.content.data(using: .utf8) ?? Data()
            }
            
            try data.write(to: url)
            showToast("Downloaded \(response.filename)")
            
        } catch {
            showToast("Download failed: \(error.localizedDescription)")
        }
    }
    
    // MARK: - Upload
    
    func prepareUpload(urls: [URL]) {
        uploadSheet = UploadSheetState(urls: urls)
    }
    
    func upload(urls: [URL], toPath: String) async {
        uploadSheet?.isUploading = true
        uploadSheet?.error = nil
        
        var failedCount = 0
        
        for url in urls {
            do {
                let data = try Data(contentsOf: url)
                let filename = url.lastPathComponent
                let destPath = toPath.isEmpty ? filename : "\(toPath)/\(filename)"
                
                // Determine encoding: use base64 for binary files
                let (content, encoding) = encodeForUpload(data: data, filename: filename)
                
                _ = try await gateway.fsPut(path: destPath, content: content, encoding: encoding)
            } catch {
                failedCount += 1
            }
        }
        
        if failedCount > 0 {
            uploadSheet?.error = "\(failedCount) file(s) failed to upload"
            uploadSheet?.isUploading = false
        } else {
            uploadSheet = nil
            await refreshPath(toPath)
            showToast("Uploaded \(urls.count) file(s)")
        }
    }
    
    // MARK: - Refresh Path (for live updates)
    
    func refreshPath(_ path: String) async {
        // Find the parent directory to refresh
        let parentPath: String
        if path.contains("/") {
            parentPath = (path as NSString).deletingLastPathComponent
        } else {
            parentPath = ""
        }
        
        if parentPath.isEmpty {
            // Refresh root
            await loadRoot()
        } else {
            // Refresh specific directory
            do {
                let response = try await gateway.fsList(path: parentPath)
                let children = response.entries.map(FSEntry.from).sorted(by: entrySortOrder)
                updateEntry(at: parentPath) { $0.children = children }
            } catch {
                // Silent fail for refresh
            }
        }
    }
    
    // MARK: - Mark New (highlight animation)
    
    func markNew(_ path: String) {
        updateEntry(at: path) { $0.isNew = true }
        
        // Cancel existing timer for this path
        newFileTimers[path]?.cancel()
        
        // Clear isNew after 1.5s
        newFileTimers[path] = Task {
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            guard !Task.isCancelled else { return }
            await MainActor.run {
                self.updateEntry(at: path) { $0.isNew = false }
                self.newFileTimers.removeValue(forKey: path)
            }
        }
    }
    
    // MARK: - Filtered Entries
    
    var filteredRootEntries: [FSEntry] {
        guard !filterText.isEmpty else { return rootEntries }
        return filterEntries(rootEntries, matching: filterText.lowercased())
    }
    
    // MARK: - Private Helpers
    
    private func entrySortOrder(_ a: FSEntry, _ b: FSEntry) -> Bool {
        if a.type != b.type {
            return a.type == .dir  // dirs first
        }
        return a.name.localizedStandardCompare(b.name) == .orderedAscending
    }
    
    private func updateEntry(at path: String, transform: (inout FSEntry) -> Void) {
        if path.isEmpty { return }  // Can't update root itself
        
        func update(in entries: inout [FSEntry]) -> Bool {
            for i in entries.indices {
                if entries[i].path == path {
                    transform(&entries[i])
                    return true
                }
                if var children = entries[i].children {
                    if update(in: &children) {
                        entries[i].children = children
                        return true
                    }
                }
            }
            return false
        }
        
        _ = update(in: &rootEntries)
    }
    
    private func findEntry(at path: String) -> FSEntry? {
        func find(in entries: [FSEntry]) -> FSEntry? {
            for entry in entries {
                if entry.path == path { return entry }
                if let children = entry.children, let found = find(in: children) {
                    return found
                }
            }
            return nil
        }
        return find(in: rootEntries)
    }
    
    private func classifyContent(_ response: FSGetResponse) -> FilePreviewState {
        let ext = (response.filename as NSString).pathExtension.lowercased()
        
        // Images
        if ["png", "jpg", "jpeg", "gif", "webp", "heic"].contains(ext) {
            if response.encoding == "base64", let data = Data(base64Encoded: response.content) {
                return .image(data, mimeType: response.mimeType ?? "image/\(ext)")
            } else if let data = response.content.data(using: .utf8) {
                return .image(data, mimeType: response.mimeType ?? "image/\(ext)")
            }
        }
        
        // Binary check
        if response.encoding == "base64" {
            return .binary(
                filename: response.filename,
                size: response.size,
                modified: nil  // Not in response, could be fetched separately
            )
        }
        
        // Markdown
        if ["md", "markdown"].contains(ext) {
            return .markdown(response.content)
        }
        
        // Code files
        let codeExtensions: [String: String] = [
            "swift": "swift", "ts": "typescript", "tsx": "typescript",
            "js": "javascript", "jsx": "javascript", "py": "python",
            "json": "json", "yaml": "yaml", "yml": "yaml",
            "sh": "bash", "bash": "bash", "zsh": "zsh",
            "html": "html", "css": "css", "scss": "scss",
            "sql": "sql", "rb": "ruby", "go": "go", "rs": "rust",
            "c": "c", "cpp": "cpp", "h": "c", "hpp": "cpp",
            "java": "java", "kt": "kotlin", "m": "objc"
        ]
        
        if let lang = codeExtensions[ext] {
            return .code(response.content, language: lang)
        }
        
        // Plain text fallback
        if ["txt", "log", "env", "gitignore", "dockerignore"].contains(ext) ||
           response.mimeType?.hasPrefix("text/") == true {
            return .code(response.content, language: "plaintext")
        }
        
        // Default to code view for unknown text
        return .code(response.content, language: "plaintext")
    }
    
    private func encodeForUpload(data: Data, filename: String) -> (content: String, encoding: String) {
        let ext = (filename as NSString).pathExtension.lowercased()
        let textExtensions = ["txt", "md", "json", "yaml", "yml", "swift", "ts", "js", "py", "sh", "html", "css", "xml", "svg"]
        
        if textExtensions.contains(ext), let text = String(data: data, encoding: .utf8) {
            return (text, "utf8")
        }
        return (data.base64EncodedString(), "base64")
    }
    
    private func filterEntries(_ entries: [FSEntry], matching query: String) -> [FSEntry] {
        var results: [FSEntry] = []
        for entry in entries {
            var match = entry.name.lowercased().contains(query)
            var filtered = entry
            
            if let children = entry.children {
                let filteredChildren = filterEntries(children, matching: query)
                if !filteredChildren.isEmpty {
                    match = true
                    filtered.children = filteredChildren
                }
            }
            
            if match {
                results.append(filtered)
            }
        }
        return results
    }
    
    private func showToast(_ message: String) {
        toastMessage = message
        Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            await MainActor.run {
                if self.toastMessage == message {
                    self.toastMessage = nil
                }
            }
        }
    }
}
```

---

## 5. FileTreeView

Create `Views/Files/FileTreeView.swift`:

```swift
import SwiftUI
import UniformTypeIdentifiers

struct FileTreeView: View {
    @ObservedObject var viewModel: FilesViewModel
    @State private var expandedPaths: Set<String> = []
    
    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                TextField("Filter files...", text: $viewModel.filterText)
                    .textFieldStyle(.plain)
                
                Button {
                    Task { await viewModel.loadRoot() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.borderless)
                .help("Refresh")
            }
            .padding(8)
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Tree content
            if viewModel.isLoadingRoot {
                Spacer()
                ProgressView()
                    .scaleEffect(0.8)
                Spacer()
            } else if let error = viewModel.rootError {
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.largeTitle)
                        .foregroundColor(.orange)
                    Text(error)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    Button("Retry") {
                        Task { await viewModel.loadRoot() }
                    }
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        // Workspace root header
                        HStack(spacing: 6) {
                            Image(systemName: "folder.fill")
                                .foregroundColor(.accentColor)
                            Text("workspace")
                                .fontWeight(.medium)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.clear)
                        
                        // Entries
                        ForEach(viewModel.filteredRootEntries) { entry in
                            FileTreeRow(
                                entry: entry,
                                depth: 1,
                                isSelected: viewModel.selectedEntry?.id == entry.id,
                                isExpanded: expandedPaths.contains(entry.path),
                                onSelect: { handleSelect(entry) },
                                onToggle: { handleToggle(entry) },
                                onDoubleClick: { handleDoubleClick(entry) }
                            )
                        }
                    }
                    .padding(.bottom, 8)
                }
            }
        }
        .frame(minWidth: 260)
        .onDrop(of: [.fileURL], isTargeted: nil) { providers in
            handleDrop(providers)
            return true
        }
        .task {
            if viewModel.rootEntries.isEmpty {
                await viewModel.loadRoot()
            }
        }
    }
    
    // MARK: - Actions
    
    private func handleSelect(_ entry: FSEntry) {
        Task { await viewModel.select(entry) }
    }
    
    private func handleToggle(_ entry: FSEntry) {
        guard entry.isDirectory else { return }
        
        if expandedPaths.contains(entry.path) {
            expandedPaths.remove(entry.path)
        } else {
            expandedPaths.insert(entry.path)
            if entry.children == nil {
                Task { await viewModel.expand(entry) }
            }
        }
    }
    
    private func handleDoubleClick(_ entry: FSEntry) {
        if entry.isDirectory {
            handleToggle(entry)
        } else {
            Task { await viewModel.download(entry) }
        }
    }
    
    private func handleDrop(_ providers: [NSItemProvider]) {
        var urls: [URL] = []
        let group = DispatchGroup()
        
        for provider in providers {
            group.enter()
            provider.loadObject(ofClass: URL.self) { url, _ in
                if let url = url {
                    urls.append(url)
                }
                group.leave()
            }
        }
        
        group.notify(queue: .main) {
            if !urls.isEmpty {
                viewModel.prepareUpload(urls: urls)
            }
        }
    }
}

// MARK: - FileTreeRow

struct FileTreeRow: View {
    let entry: FSEntry
    let depth: Int
    let isSelected: Bool
    let isExpanded: Bool
    let onSelect: () -> Void
    let onToggle: () -> Void
    let onDoubleClick: () -> Void
    
    @State private var isHovered: Bool = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // This row
            HStack(spacing: 4) {
                // Disclosure triangle for directories
                if entry.isDirectory {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(.secondary)
                        .frame(width: 12)
                        .onTapGesture { onToggle() }
                } else {
                    Spacer().frame(width: 12)
                }
                
                // Icon
                Image(systemName: entry.iconName)
                    .foregroundColor(entry.isDirectory ? .accentColor : .secondary)
                    .frame(width: 16)
                
                // Name
                Text(entry.name)
                    .lineLimit(1)
                    .truncationMode(.middle)
                
                Spacer()
                
                // Loading indicator
                if entry.isLoading {
                    ProgressView()
                        .scaleEffect(0.5)
                        .frame(width: 16, height: 16)
                }
            }
            .padding(.leading, CGFloat(depth) * 16)
            .padding(.trailing, 8)
            .padding(.vertical, 4)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(rowBackground)
            .contentShape(Rectangle())
            .onTapGesture { onSelect() }
            .onTapGesture(count: 2) { onDoubleClick() }
            .onHover { isHovered = $0 }
            .accessibilityLabel(entry.isDirectory ? "Folder: \(entry.name)" : "File: \(entry.name)")
            .accessibilityHint(entry.isDirectory ? "Double-click to expand" : "Double-click to download")
            
            // Children
            if isExpanded, let children = entry.children {
                ForEach(children) { child in
                    FileTreeRow(
                        entry: child,
                        depth: depth + 1,
                        isSelected: false,  // Will be bound properly via viewModel
                        isExpanded: false,  // Nested state managed by parent
                        onSelect: { /* Handled by parent */ },
                        onToggle: { /* Handled by parent */ },
                        onDoubleClick: { /* Handled by parent */ }
                    )
                }
            }
        }
    }
    
    private var rowBackground: some View {
        Group {
            if entry.isNew {
                Color.accentColor.opacity(0.3)
                    .animation(.easeOut(duration: 1.5), value: entry.isNew)
            } else if isSelected {
                Color.accentColor.opacity(0.2)
            } else if isHovered {
                Color.primary.opacity(0.05)
            } else {
                Color.clear
            }
        }
    }
}
```

**Note:** The nested `FileTreeRow` selection/expansion logic needs proper binding. Refactor to use `@ObservedObject` binding through the parent, or use an `OutlineGroup` with `Binding<Set<String>>` for expansion state. The code above is illustrative; match the existing app's tree pattern if one exists.

---

## 6. FilePreviewView

Create `Views/Files/FilePreviewView.swift`:

```swift
import SwiftUI

struct FilePreviewView: View {
    @ObservedObject var viewModel: FilesViewModel
    
    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            if let entry = viewModel.selectedEntry, entry.type == .file {
                previewToolbar(for: entry)
                Divider()
            }
            
            // Content
            previewContent
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            
            // Metadata bar
            if let entry = viewModel.selectedEntry, entry.type == .file {
                Divider()
                metadataBar(for: entry)
            }
        }
    }
    
    // MARK: - Toolbar
    
    @ViewBuilder
    private func previewToolbar(for entry: FSEntry) -> some View {
        HStack {
            Text(entry.name)
                .fontWeight(.medium)
                .lineLimit(1)
            
            Spacer()
            
            Button {
                Task { await viewModel.download(entry) }
            } label: {
                Label("Download", systemImage: "arrow.down.circle")
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(NSColor.controlBackgroundColor))
    }
    
    // MARK: - Content
    
    @ViewBuilder
    private var previewContent: some View {
        switch viewModel.previewContent {
        case .empty:
            emptyState
            
        case .loading:
            ProgressView("Loading...")
            
        case .markdown(let text):
            MarkdownPreview(text: text)
            
        case .code(let text, let language):
            CodePreview(text: text, language: language)
            
        case .image(let data, _):
            ImagePreview(data: data)
            
        case .binary(let filename, let size, let modified):
            BinaryPreview(
                filename: filename,
                size: size,
                modified: modified,
                onDownload: {
                    if let entry = viewModel.selectedEntry {
                        Task { await viewModel.download(entry) }
                    }
                }
            )
            
        case .error(let message):
            errorState(message)
        }
    }
    
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            Text("Select a file to preview")
                .foregroundColor(.secondary)
        }
    }
    
    private func errorState(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.orange)
            Text(message)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            Button("Retry") {
                if let entry = viewModel.selectedEntry {
                    Task { await viewModel.select(entry) }
                }
            }
        }
        .padding()
    }
    
    // MARK: - Metadata Bar
    
    private func metadataBar(for entry: FSEntry) -> some View {
        HStack(spacing: 16) {
            Label(entry.path, systemImage: "folder")
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(1)
            
            Spacer()
            
            if let size = entry.size {
                Text(entry.formattedSize)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if entry.modified != nil {
                Text(entry.formattedModified)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color(NSColor.controlBackgroundColor))
    }
}

// MARK: - Preview Components

struct MarkdownPreview: View {
    let text: String
    
    var body: some View {
        ScrollView {
            // Use existing markdown renderer if available (e.g., MarkdownUI)
            // Fallback to plain text
            Text(text)
                .font(.system(.body, design: .default))
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
        }
    }
}

struct CodePreview: View {
    let text: String
    let language: String
    
    var body: some View {
        ScrollView([.horizontal, .vertical]) {
            Text(text)
                .font(.system(.body, design: .monospaced))
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
        }
        .background(Color(NSColor.textBackgroundColor))
    }
}

struct ImagePreview: View {
    let data: Data
    
    var body: some View {
        if let nsImage = NSImage(data: data) {
            Image(nsImage: nsImage)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .padding()
        } else {
            Text("Unable to load image")
                .foregroundColor(.secondary)
        }
    }
}

struct BinaryPreview: View {
    let filename: String
    let size: Int
    let modified: Date?
    let onDownload: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.zipper")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            
            Text(filename)
                .font(.headline)
            
            Text(ByteCountFormatter.string(fromByteCount: Int64(size), countStyle: .file))
                .foregroundColor(.secondary)
            
            if let modified = modified {
                Text("Modified \(modified.formatted())")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Button(action: onDownload) {
                Label("Download", systemImage: "arrow.down.circle.fill")
                    .font(.headline)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding()
    }
}
```

---

## 7. Upload Sheet

Create `Views/Files/UploadSheet.swift`:

```swift
import SwiftUI

struct UploadSheet: View {
    @ObservedObject var viewModel: FilesViewModel
    @Binding var state: UploadSheetState?
    
    var body: some View {
        if let uploadState = state {
            VStack(spacing: 20) {
                // Header
                HStack {
                    Image(systemName: "arrow.up.doc.fill")
                        .font(.title)
                        .foregroundColor(.accentColor)
                    Text("Upload \(uploadState.urls.count) file(s)")
                        .font(.headline)
                }
                
                // File list
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(uploadState.urls.prefix(5), id: \.self) { url in
                        HStack(spacing: 8) {
                            Image(systemName: "doc")
                                .foregroundColor(.secondary)
                            Text(url.lastPathComponent)
                                .lineLimit(1)
                                .truncationMode(.middle)
                        }
                    }
                    if uploadState.urls.count > 5 {
                        Text("... and \(uploadState.urls.count - 5) more")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(8)
                
                // Destination picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Upload to:")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Image(systemName: "folder")
                        TextField("workspace/", text: destinationBinding)
                            .textFieldStyle(.roundedBorder)
                    }
                    
                    Text("Leave empty to upload to workspace root")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                // Error
                if let error = uploadState.error {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                }
                
                // Actions
                HStack {
                    Button("Cancel") {
                        state = nil
                    }
                    .keyboardShortcut(.cancelAction)
                    
                    Spacer()
                    
                    Button {
                        Task {
                            await viewModel.upload(
                                urls: uploadState.urls,
                                toPath: uploadState.destinationPath
                            )
                        }
                    } label: {
                        if uploadState.isUploading {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 60)
                        } else {
                            Text("Upload")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(uploadState.isUploading)
                    .keyboardShortcut(.defaultAction)
                }
            }
            .padding(24)
            .frame(width: 400)
        }
    }
    
    private var destinationBinding: Binding<String> {
        Binding(
            get: { state?.destinationPath ?? "" },
            set: { state?.destinationPath = $0 }
        )
    }
}
```

---

## 8. Main FilesView

Create `Views/Files/FilesView.swift`:

```swift
import SwiftUI

struct FilesView: View {
    @ObservedObject var viewModel: FilesViewModel
    
    var body: some View {
        HSplitView {
            FileTreeView(viewModel: viewModel)
                .frame(minWidth: 260, idealWidth: 300, maxWidth: 400)
            
            FilePreviewView(viewModel: viewModel)
                .frame(minWidth: 400)
        }
        .sheet(item: $viewModel.uploadSheet) { _ in
            UploadSheet(viewModel: viewModel, state: $viewModel.uploadSheet)
        }
        .overlay(alignment: .bottom) {
            // Toast overlay
            if let toast = viewModel.toastMessage {
                ToastView(message: toast)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                    .padding(.bottom, 20)
            }
        }
        .animation(.easeInOut(duration: 0.2), value: viewModel.toastMessage)
    }
}

struct ToastView: View {
    let message: String
    
    var body: some View {
        Text(message)
            .font(.subheadline)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(.ultraThinMaterial)
            .cornerRadius(8)
            .shadow(radius: 4)
    }
}
```

---

## 9. App Wiring

### 9.1 Add ViewModel to App/Scene

In your main app or scene struct (likely `VantageApp.swift` or similar):

```swift
@main
struct VantageApp: App {
    @StateObject private var gatewayClient = GatewayClient()
    @StateObject private var filesViewModel: FilesViewModel
    
    init() {
        let gateway = GatewayClient()  // Or shared instance
        _gatewayClient = StateObject(wrappedValue: gateway)
        _filesViewModel = StateObject(wrappedValue: FilesViewModel(gateway: gateway))
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(gatewayClient)
                .environmentObject(filesViewModel)
        }
    }
}
```

### 9.2 Add Tab to Navigation

In your tab view or sidebar navigation:

```swift
// Example using TabView
TabView {
    ChatView()
        .tabItem {
            Label("Chat", systemImage: "bubble.left.and.bubble.right")
        }
    
    SessionsView()
        .tabItem {
            Label("Sessions", systemImage: "list.bullet.rectangle")
        }
    
    FilesView(viewModel: filesViewModel)  // or use @EnvironmentObject
        .tabItem {
            Label("Files", systemImage: "folder")
        }
    
    // ... other tabs
}
```

### 9.3 Wire Activity Feed Events

Find where `file_written` events are processed (likely in activity feed observer or WebSocket message handler):

```swift
// Example in your activity feed handler
func handleActivityEvent(_ event: ActivityEvent) {
    switch event.type {
    case "file_written":
        if let path = event.path {
            Task { @MainActor in
                await filesViewModel.refreshPath(path)
                filesViewModel.markNew(path)
            }
        }
    // ... other event types
    }
}
```

### 9.4 Network State Badge

If the app has a connection state observable, add badge to Files tab when disconnected:

```swift
// In tab item or sidebar
Label("Files", systemImage: "folder")
    .badge(gatewayClient.isConnected ? nil : "!")
```

---

## 10. Animations & Polish

### 10.1 New File Pulse Animation

The `isNew` property on `FSEntry` triggers a background color transition. The animation is handled in `FileTreeRow`:

```swift
.background(
    entry.isNew 
        ? Color.accentColor.opacity(0.3).animation(.easeOut(duration: 1.5), value: entry.isNew)
        : Color.clear
)
```

### 10.2 Accessibility Labels

Already included in the code above:
- `FileTreeRow`: `.accessibilityLabel()` and `.accessibilityHint()` 
- Use semantic labels for all interactive elements
- Ensure keyboard navigation works for the tree

### 10.3 Keyboard Shortcuts

Add to `FilesView`:

```swift
.keyboardShortcut("r", modifiers: .command)  // Refresh on Cmd+R
// Handle in toolbar button or .onKeyPress
```

---

## 11. Integration Checklist

- [ ] **GatewayClient.swift**: Add `fsList`, `fsGet`, `fsPut` methods and response DTOs
- [ ] **Models/FSEntry.swift**: Create `FSEntry`, `FSEntryType`, `FilePreviewState`, `UploadSheetState`
- [ ] **ViewModels/FilesViewModel.swift**: Create full view model
- [ ] **Views/Files/FileTreeView.swift**: Create tree view with lazy loading
- [ ] **Views/Files/FilePreviewView.swift**: Create preview view with all content types
- [ ] **Views/Files/UploadSheet.swift**: Create upload confirmation sheet
- [ ] **Views/Files/FilesView.swift**: Create main split view container
- [ ] **App wiring**: Add `@StateObject` for `FilesViewModel` at app level
- [ ] **Tab navigation**: Add "Files" tab with folder icon
- [ ] **Activity feed**: Wire `file_written` events to `refreshPath` + `markNew`
- [ ] **NSSavePanel**: Match existing pattern from `DownloadManager.swift` if present
- [ ] **Markdown renderer**: Use existing renderer or add `MarkdownUI` package
- [ ] **Test: Browse** — expand folders, lazy loading works
- [ ] **Test: Preview** — markdown, code, images, binary all render correctly
- [ ] **Test: Download** — file saves with correct encoding
- [ ] **Test: Upload** — drag files, confirm sheet, file appears in workspace
- [ ] **Test: Live update** — create file via agent, appears with pulse animation
- [ ] **Test: Error states** — disconnect network, verify graceful degradation

---

## Notes for Coding Agent

1. **Existing patterns**: Check `DownloadManager.swift` or similar for `NSSavePanel` usage; replicate that pattern
2. **Markdown rendering**: If `MarkdownUI` or similar is already a dependency, use it in `MarkdownPreview`; otherwise use plain `Text` as shown
3. **Syntax highlighting**: For proper code highlighting, consider `Highlightr` or similar; the spec shows plain monospace as MVP
4. **Tree state**: The nested `FileTreeRow` expansion logic is simplified; may need refactoring to use `OutlineGroup` or proper binding propagation depending on existing app patterns
5. **Error recovery**: The upload sheet intentionally stays open on error so user can retry
6. **File encoding detection**: The current heuristic (extension-based) is sufficient for MVP; could be enhanced with UTType detection
