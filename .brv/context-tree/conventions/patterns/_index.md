---
children_hash: 2c6da72b658e65854f96077dc97c7f6289d32a355c4964374b799b6a0fec6662
compression_ratio: 0.974155069582505
condensation_order: 1
covers: [context.md, learned_patterns.md, long_running_task_orchestration.md]
covers_token_total: 503
summary_level: d1
token_count: 490
type: summary
---
# Domain: Patterns

This domain establishes the behavioral, structural, and operational conventions for the agent workspace, focusing on interaction styles and the orchestration of complex, long-running processes.

## Agent Interaction and Writing Standards
Guidelines for content generation and tool-use responses emphasize brevity and specific formatting constraints.
*   **Response Structure**: Agents must provide exactly one reply following tool execution, avoiding the redundancy of both a preceding narration and a trailing summary (see **learned_patterns.md**).
*   **Punctuation and Assets**: The use of em dashes is prohibited in all writing, favoring commas, periods, colons, or parentheses. Visual elements must utilize inline SVGs (Heroicons) rather than standard emojis (see **learned_patterns.md**).
*   **Logging**: All heartbeat logs are required to be recorded in JSONL format.

## Long-Running Task Orchestration
A structured framework for managing compute jobs spanning 6–8 hours through state persistence and budget awareness.
*   **Architecture and Flow**: Tasks are decomposed into a Directed Acyclic Graph (DAG) where each node includes a token cost estimate. Execution state is persisted to `tasks/<project>/todo.json` to ensure resilience against session restarts (see **long_running_task_orchestration.md**).
*   **Resource Management**: Orchestration relies on the `Anthropic` rate limit response headers to track budgets and manage rolling windows.
*   **Operational Rules**:
    *   Mandatory DAG decomposition with per-node cost estimates.
    *   Staggered subagent launches to maintain stability.
    *   Continuous budget tracking via headers.

## Reference Entries
*   **context.md**: General overview of workspace patterns.
*   **learned_patterns.md**: Detailed writing constraints and interaction rules.
*   **long_running_task_orchestration.md**: Technical specifications for DAG-based job management and state persistence.