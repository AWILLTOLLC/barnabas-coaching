---
children_hash: 85e24f1acb4b44122e6e6da268347df923d8228e0c1cda407b00dd031d5c982c
compression_ratio: 0.837979094076655
condensation_order: 1
covers: [context.md, safeharbor_project.md]
covers_token_total: 574
summary_level: d1
token_count: 481
type: summary
---
# Domain: projects/safe_harbor

SafeHarbor is a secure infrastructure project designed to run AI agents within isolated macOS virtual machines, bypassing Docker dependencies in favor of native virtualization.

### Architectural Overview
The system utilizes the **macOS Virtualization.framework** (requiring macOS 13+) to host an **Alpine Linux guest** environment. The architecture shifted on 2026-03-14 from a GatewayClient/WebSocket model to a direct **SafeHarborVM/VSockConnection** design.

*   **Host-Guest Communication:** IPC is strictly handled via **vsock JSON-RPC 2.0** on port 5000, connecting the Swift host to a Node.js guest sidecar.
*   **Runtime Environment:** The guest runs TypeScript code compiled via **esbuild**.
*   **Data & Persistence:** Uses **SQLite** via the **GRDB** stack (Swift) on the host. Shared data is exposed to the guest via **9p filesystem mounts**.
    *   `/agents/`: Configuration files.
    *   `/data/burrow.db`: SQLite database mapping.
*   **Security:** API keys are passed exclusively via environment variables at VM boot.
*   **Key Paths:** Application data resides in `~/Library/Application Support/SafeHarbor/`.

### Key Components & Technologies
*   **Core Frameworks:** macOS Virtualization.framework, Alpine Linux, Node.js.
*   **Build Tools:** esbuild (TypeScript to JS compilation).
*   **Persistence Layer:** GRDB (Swift), SQLite, 9p mounts.
*   **Primary Reference:** `reports/burrow-server-build-plan.md`.

### Relationships and Rules
*   **Rule 1:** All host-guest communication must use **vsock**.
*   **Rule 2:** Guest runtime requires **esbuild** for TypeScript compilation.
*   **Rule 3:** API keys are restricted to **boot-time environment variables**.

### Entry References
*   **context.md**: High-level conceptual overview and infrastructure stack.
*   **safeharbor_project.md**: Detailed technical specifications, build plan, and extraction of core facts.