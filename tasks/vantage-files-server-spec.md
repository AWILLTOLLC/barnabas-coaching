# VantageOC Files Pane — Server-Side Implementation Spec

**Target file:** `~/.openclaw/extensions/vantage/src/rpc.ts`

This spec provides complete TypeScript implementations for three new RPC methods that expose a sandboxed file browser of the OpenClaw workspace directory.

---

## Security Helpers

Add these at the top of `rpc.ts`, after the existing imports:

```typescript
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

// ── Filesystem Security Helpers ─────────────────────────────────────────────

const WORKSPACE_ROOT = path.resolve(os.homedir(), ".openclaw/workspace");
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const TEXT_EXTENSIONS = new Set([
  ".md", ".txt", ".ts", ".js", ".jsx", ".tsx", ".json", ".py", ".sh",
  ".yaml", ".yml", ".toml", ".csv", ".html", ".css", ".swift", ".env",
  ".mjs", ".cjs", ".rs", ".go", ".rb", ".php", ".sql", ".xml", ".ini",
  ".cfg", ".conf", ".log", ".gitignore", ".dockerignore", ".editorconfig",
]);

const MIME_TYPES: Record<string, string> = {
  ".md": "text/markdown",
  ".txt": "text/plain",
  ".ts": "text/typescript",
  ".tsx": "text/typescript",
  ".js": "text/javascript",
  ".jsx": "text/javascript",
  ".mjs": "text/javascript",
  ".cjs": "text/javascript",
  ".json": "application/json",
  ".py": "text/x-python",
  ".sh": "text/x-shellscript",
  ".yaml": "text/yaml",
  ".yml": "text/yaml",
  ".toml": "text/toml",
  ".csv": "text/csv",
  ".html": "text/html",
  ".css": "text/css",
  ".swift": "text/x-swift",
  ".env": "text/plain",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".zip": "application/zip",
  ".tar": "application/x-tar",
  ".gz": "application/gzip",
};

interface PathValidationResult {
  valid: true;
  absolutePath: string;
  relativePath: string;
} | {
  valid: false;
  error: string;
}

/**
 * Validate and resolve a path relative to WORKSPACE_ROOT.
 * Returns the absolute path if valid, or an error message if not.
 * Catches: directory traversal (../), symlink escape, absolute paths.
 */
function validateWorkspacePath(inputPath: string | undefined | null): PathValidationResult {
  // Normalize empty/null to root
  const relativePath = (inputPath ?? "").trim();
  
  // Block absolute paths
  if (path.isAbsolute(relativePath)) {
    return { valid: false, error: "Absolute paths are not allowed" };
  }
  
  // Resolve to absolute path
  const absolutePath = path.resolve(WORKSPACE_ROOT, relativePath);
  
  // Verify it's within workspace (catches ../ traversal)
  // Must equal WORKSPACE_ROOT or start with WORKSPACE_ROOT + separator
  if (absolutePath !== WORKSPACE_ROOT && !absolutePath.startsWith(WORKSPACE_ROOT + path.sep)) {
    return { valid: false, error: "Path escapes workspace boundary" };
  }
  
  // Check for symlink escape by resolving the real path
  try {
    // For existing paths, verify realpath is also within workspace
    if (fs.existsSync(absolutePath)) {
      const realPath = fs.realpathSync(absolutePath);
      if (realPath !== WORKSPACE_ROOT && !realPath.startsWith(WORKSPACE_ROOT + path.sep)) {
        return { valid: false, error: "Symlink escapes workspace boundary" };
      }
    }
  } catch {
    // Path doesn't exist yet, that's fine for write operations
  }
  
  return { valid: true, absolutePath, relativePath };
}

/**
 * Additional validation for write operations.
 * Blocks writes to credentials/ subdirectory.
 */
function validateWritePath(inputPath: string | undefined | null): PathValidationResult {
  const baseResult = validateWorkspacePath(inputPath);
  if (!baseResult.valid) return baseResult;
  
  // Block credentials directory
  const normalizedRelative = baseResult.relativePath.toLowerCase();
  if (
    normalizedRelative === "credentials" ||
    normalizedRelative.startsWith("credentials/") ||
    normalizedRelative.startsWith("credentials\\")
  ) {
    return { valid: false, error: "Writes to credentials/ are forbidden" };
  }
  
  return baseResult;
}

function getMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  return MIME_TYPES[ext] ?? "application/octet-stream";
}

function isTextFile(filePath: string): boolean {
  const ext = path.extname(filePath).toLowerCase();
  return TEXT_EXTENSIONS.has(ext);
}
```

---

## RPC Method 1: `vantage.fs.list`

List contents of a directory (non-recursive).

### Request
```typescript
interface FsListRequest {
  path?: string;  // Relative to workspace root; empty/omitted = root
}
```

### Response
```typescript
interface FsListResponse {
  path: string;
  entries: Array<{
    name: string;
    type: "file" | "dir";
    size?: number;      // Bytes, only for files
    modified: number;   // Unix ms timestamp
    path: string;       // Full relative path from workspace root
  }>;
}
```

### Implementation

```typescript
api.registerGatewayMethod("vantage.fs.list", async ({ params, respond }: any) => {
  const { path: inputPath } = params ?? {};
  
  // Validate path
  const validation = validateWorkspacePath(inputPath);
  if (!validation.valid) {
    return respond(false, undefined, { code: "FORBIDDEN", message: validation.error });
  }
  
  const { absolutePath, relativePath } = validation;
  
  // Check directory exists
  try {
    const stat = fs.statSync(absolutePath);
    if (!stat.isDirectory()) {
      return respond(false, undefined, { code: "INVALID_REQUEST", message: "Path is not a directory" });
    }
  } catch (err: any) {
    if (err.code === "ENOENT") {
      return respond(false, undefined, { code: "NOT_FOUND", message: "Directory not found" });
    }
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: err.message ?? "stat failed" });
  }
  
  // Read directory
  let dirEntries: fs.Dirent[];
  try {
    dirEntries = fs.readdirSync(absolutePath, { withFileTypes: true });
  } catch (err: any) {
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: err.message ?? "readdir failed" });
  }
  
  // Filter hidden files and build entry list
  const entries: Array<{
    name: string;
    type: "file" | "dir";
    size?: number;
    modified: number;
    path: string;
  }> = [];
  
  for (const dirent of dirEntries) {
    // Skip hidden files (starting with .)
    if (dirent.name.startsWith(".")) continue;
    
    const entryAbsPath = path.join(absolutePath, dirent.name);
    const entryRelPath = relativePath ? path.join(relativePath, dirent.name) : dirent.name;
    
    try {
      const entryStat = fs.statSync(entryAbsPath);
      
      if (dirent.isDirectory()) {
        entries.push({
          name: dirent.name,
          type: "dir",
          modified: Math.floor(entryStat.mtimeMs),
          path: entryRelPath,
        });
      } else if (dirent.isFile()) {
        entries.push({
          name: dirent.name,
          type: "file",
          size: entryStat.size,
          modified: Math.floor(entryStat.mtimeMs),
          path: entryRelPath,
        });
      }
      // Skip symlinks, sockets, etc.
    } catch {
      // Skip entries we can't stat
    }
  }
  
  // Sort: directories first (alphabetically), then files (alphabetically)
  entries.sort((a, b) => {
    if (a.type !== b.type) {
      return a.type === "dir" ? -1 : 1;
    }
    return a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
  });
  
  respond(true, { path: relativePath, entries });
});
```

---

## RPC Method 2: `vantage.fs.get`

Fetch file content for download or preview.

### Request
```typescript
interface FsGetRequest {
  path: string;  // Required, relative to workspace root
}
```

### Response
```typescript
interface FsGetResponse {
  path: string;
  filename: string;
  content: string;      // UTF-8 string or base64-encoded
  encoding: "utf8" | "base64";
  size: number;         // Bytes
  mimeType: string;
}
```

### Implementation

```typescript
api.registerGatewayMethod("vantage.fs.get", async ({ params, respond }: any) => {
  const { path: inputPath } = params ?? {};
  
  if (!inputPath) {
    return respond(false, undefined, { code: "INVALID_REQUEST", message: "path is required" });
  }
  
  // Validate path
  const validation = validateWorkspacePath(inputPath);
  if (!validation.valid) {
    return respond(false, undefined, { code: "FORBIDDEN", message: validation.error });
  }
  
  const { absolutePath, relativePath } = validation;
  
  // Check file exists and is a file
  let stat: fs.Stats;
  try {
    stat = fs.statSync(absolutePath);
    if (!stat.isFile()) {
      return respond(false, undefined, { code: "INVALID_REQUEST", message: "Path is not a file" });
    }
  } catch (err: any) {
    if (err.code === "ENOENT") {
      return respond(false, undefined, { code: "NOT_FOUND", message: "File not found" });
    }
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: err.message ?? "stat failed" });
  }
  
  // Check file size
  if (stat.size > MAX_FILE_SIZE) {
    return respond(false, undefined, {
      code: "FILE_TOO_LARGE",
      message: `File exceeds maximum size of ${MAX_FILE_SIZE / 1024 / 1024}MB`,
    });
  }
  
  // Read file
  let content: string;
  let encoding: "utf8" | "base64";
  
  try {
    if (isTextFile(absolutePath)) {
      content = fs.readFileSync(absolutePath, "utf8");
      encoding = "utf8";
    } else {
      const buffer = fs.readFileSync(absolutePath);
      content = buffer.toString("base64");
      encoding = "base64";
    }
  } catch (err: any) {
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: err.message ?? "read failed" });
  }
  
  respond(true, {
    path: relativePath,
    filename: path.basename(absolutePath),
    content,
    encoding,
    size: stat.size,
    mimeType: getMimeType(absolutePath),
  });
});
```

---

## RPC Method 3: `vantage.fs.put`

Write a file to workspace (for drag-and-drop upload from operator).

### Request
```typescript
interface FsPutRequest {
  path: string;           // Required, relative to workspace root
  content: string;        // UTF-8 string or base64-encoded
  encoding?: "utf8" | "base64";  // Defaults to "utf8"
}
```

### Response
```typescript
interface FsPutResponse {
  path: string;
  saved: true;
  size: number;  // Bytes written
}
```

### Implementation

```typescript
api.registerGatewayMethod("vantage.fs.put", async ({ params, respond }: any) => {
  const { path: inputPath, content, encoding = "utf8" } = params ?? {};
  
  if (!inputPath) {
    return respond(false, undefined, { code: "INVALID_REQUEST", message: "path is required" });
  }
  if (content === undefined || content === null) {
    return respond(false, undefined, { code: "INVALID_REQUEST", message: "content is required" });
  }
  if (encoding !== "utf8" && encoding !== "base64") {
    return respond(false, undefined, { code: "INVALID_REQUEST", message: "encoding must be 'utf8' or 'base64'" });
  }
  
  // Validate path (with write-specific checks)
  const validation = validateWritePath(inputPath);
  if (!validation.valid) {
    return respond(false, undefined, { code: "FORBIDDEN", message: validation.error });
  }
  
  const { absolutePath, relativePath } = validation;
  
  // Ensure parent directory exists
  const parentDir = path.dirname(absolutePath);
  try {
    fs.mkdirSync(parentDir, { recursive: true });
  } catch (err: any) {
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: `Failed to create directory: ${err.message}` });
  }
  
  // Prepare content
  let buffer: Buffer;
  try {
    if (encoding === "base64") {
      buffer = Buffer.from(content, "base64");
    } else {
      buffer = Buffer.from(content, "utf8");
    }
  } catch (err: any) {
    return respond(false, undefined, { code: "INVALID_REQUEST", message: `Invalid content encoding: ${err.message}` });
  }
  
  // Check size before writing
  if (buffer.length > MAX_FILE_SIZE) {
    return respond(false, undefined, {
      code: "FILE_TOO_LARGE",
      message: `Content exceeds maximum size of ${MAX_FILE_SIZE / 1024 / 1024}MB`,
    });
  }
  
  // Write file
  try {
    fs.writeFileSync(absolutePath, buffer);
  } catch (err: any) {
    return respond(false, undefined, { code: "INTERNAL_ERROR", message: `Write failed: ${err.message}` });
  }
  
  respond(true, {
    path: relativePath,
    saved: true,
    size: buffer.length,
  });
});
```

---

## Error Response Format

All three methods use consistent error responses:

```typescript
// Success
respond(true, { ...payload });

// Error
respond(false, undefined, { code: string, message: string });
```

### Error Codes

| Code | HTTP Equivalent | When |
|------|-----------------|------|
| `INVALID_REQUEST` | 400 | Missing required params, invalid encoding, not a file/dir |
| `FORBIDDEN` | 403 | Path traversal, symlink escape, credentials/ write attempt |
| `NOT_FOUND` | 404 | File or directory doesn't exist |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB limit |
| `INTERNAL_ERROR` | 500 | Filesystem errors, unexpected failures |

---

## Integration Checklist

Add to `src/rpc.ts`:

### 1. Add imports at the top (after existing imports)

```typescript
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
```

**Note:** Check if these are already imported elsewhere in the file. The existing code uses `require("node:fs")` inline in some methods. For consistency with modern patterns, add the imports at the top and use them throughout.

### 2. Add security helpers after imports

Add the entire "Security Helpers" section from above, starting with `const WORKSPACE_ROOT = ...` through the `isTextFile` function.

### 3. Add RPC registrations inside `registerVantageRpcMethods()`

Add a new section comment and the three methods:

```typescript
// ── Workspace filesystem ────────────────────────────────────────────────

api.registerGatewayMethod("vantage.fs.list", async ({ params, respond }: any) => {
  // ... implementation
});

api.registerGatewayMethod("vantage.fs.get", async ({ params, respond }: any) => {
  // ... implementation
});

api.registerGatewayMethod("vantage.fs.put", async ({ params, respond }: any) => {
  // ... implementation
});
```

Place this section after the existing "Agent config files" section (after `vantage.agent.config.set`).

### 4. Build and test

```bash
cd ~/.openclaw/extensions/vantage
npm run build
# Restart gateway to pick up changes
openclaw gateway restart
```

### 5. Manual verification

```bash
# Test list (root)
curl -X POST http://localhost:3033/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"vantage.fs.list","params":{}}'

# Test list (subdirectory)
curl -X POST http://localhost:3033/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"vantage.fs.list","params":{"path":"tasks"}}'

# Test get
curl -X POST http://localhost:3033/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"vantage.fs.get","params":{"path":"SOUL.md"}}'

# Test put
curl -X POST http://localhost:3033/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"vantage.fs.put","params":{"path":"test-upload.txt","content":"Hello from operator"}}'

# Test security (should fail)
curl -X POST http://localhost:3033/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"vantage.fs.get","params":{"path":"../../../etc/passwd"}}'
```

---

## Security Audit Checklist

Before deploying, verify:

- [ ] `validateWorkspacePath` rejects `../` traversal
- [ ] `validateWorkspacePath` rejects absolute paths (`/etc/passwd`)
- [ ] `validateWorkspacePath` rejects symlinks pointing outside workspace
- [ ] `validateWritePath` rejects `credentials/` and `credentials/anything`
- [ ] All three methods return `FORBIDDEN` error (not throw) for security violations
- [ ] Error messages don't leak filesystem structure
- [ ] File size limit enforced on both read and write
- [ ] Hidden files (`.git`, `.env`, etc.) excluded from listings

---

## TypeScript Types (Optional)

If you want to add explicit types to `src/types.ts`:

```typescript
// ── Filesystem types ────────────────────────────────────────────────────

export interface FsEntry {
  name: string;
  type: "file" | "dir";
  size?: number;
  modified: number;
  path: string;
}

export interface FsListRequest {
  path?: string;
}

export interface FsListResponse {
  path: string;
  entries: FsEntry[];
}

export interface FsGetRequest {
  path: string;
}

export interface FsGetResponse {
  path: string;
  filename: string;
  content: string;
  encoding: "utf8" | "base64";
  size: number;
  mimeType: string;
}

export interface FsPutRequest {
  path: string;
  content: string;
  encoding?: "utf8" | "base64";
}

export interface FsPutResponse {
  path: string;
  saved: true;
  size: number;
}
```
