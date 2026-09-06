---
children_hash: 6575d1075bd7d68b688fd620361de97dae98e7893ba2ea7da6c5f30b5865dac9
compression_ratio: 0.9510869565217391
condensation_order: 1
covers: [workspace_rules.md]
covers_token_total: 184
summary_level: d1
token_count: 175
type: summary
---
# Workspace Rules Summary (d1)

This domain defines the core operational policies for tool usage and communication within the workspace.

### Operational Policies
*   **Web Fetching**: Primary fetch operations must utilize `scrapling`, with `web_fetch` reserved strictly as a fallback mechanism.
*   **Infrastructure Management**: Manual restarts of the gateway are prohibited without explicit permission.

### Communication Protocol
*   **Response Handling**: Adheres to a strict single-reply policy following tool execution to prevent double-posting and redundant message cycles.

### Reference Entries
*   **workspace_rules.md**: Detailed fetch logic, gateway constraints, and interaction rules.