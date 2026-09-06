---
children_hash: 0d37bf99b2450d3f6716e2e20e2721098cbd63f5d326a096d1b30998b759dd35
compression_ratio: 0.6308068459657702
condensation_order: 2
covers: [content_strategy/_index.md, context.md, patterns/_index.md, workspace/_index.md]
covers_token_total: 1227
summary_level: d2
token_count: 774
type: summary
---
# Workspace Conventions and Operational Patterns (d2)

This domain establishes the foundational strategies, behavioral standards, and technical orchestration patterns governing the agent workspace and content delivery systems.

### Content Strategy and Format Libraries
A unified framework developed by **Maven** (2026-03-14) ensures brand consistency across channel agents (**Spark, Dash, Barrett, Forge**).
*   **Library Structure**: Integrates brand voice, audience primers, and platform priorities. Specifications are localized in `channels/<channel-name>/references/content-formats.md` for Glimmer, Morse Command, Barnabas Coaching, and Black Raven.
*   **Operational Flow**: Maven defines formats; channel agents execute; **Spark** provides mandatory test result feedback via **@Maven** tagging to iterate playbooks.
*   **Reference**: See `content_strategy/_index.md` for component details and `content_strategy/content_format_libraries.md` for template definitions.

### Agent Interaction and Writing Standards
Strict linguistic and structural constraints define all workspace communications to ensure brevity and technical compatibility.
*   **Response Protocol**: Implements a strict single-reply policy following tool execution. Agents must avoid redundant narration or trailing summaries to prevent message cycles (see `patterns/learned_patterns.md` and `workspace/_index.md`).
*   **Stylistic Constraints**: Prohibits em dashes (favoring commas/colons) and standard emojis (favoring inline Heroicon SVGs).
*   **Logging**: All heartbeat logs must be recorded in JSONL format.
*   **Reference**: See `patterns/learned_patterns.md` for specific writing rules.

### Long-Running Task Orchestration
A technical framework for managing complex compute jobs (6–8 hours) through state persistence and resource awareness.
*   **Architectural Flow**: Tasks are decomposed into a Directed Acyclic Graph (DAG) with per-node token cost estimates. Execution state is persisted to `tasks/<project>/todo.json` for resilience (see `patterns/long_running_task_orchestration.md`).
*   **Resource Management**: Utilizes `Anthropic` rate limit headers for real-time budget tracking and staggered subagent launches to maintain stability.
*   **Reference**: See `patterns/long_running_task_orchestration.md` for DAG specifications and budget logic.

### Workspace Operational Policies
Core rules governing infrastructure and tool selection.
*   **Web Operations**: `scrapling` is the primary tool for web fetching; `web_fetch` is reserved strictly for fallback.
*   **Infrastructure**: Manual gateway restarts are prohibited without explicit authorization.
*   **Reference**: See `workspace/workspace_rules.md` for fetch logic and infrastructure constraints.

### Structural Overview
*   **content_strategy/**: Channel-specific format libraries and feedback loops.
*   **patterns/**: Interaction standards and DAG-based task orchestration.
*   **workspace/**: Tool usage policies and infrastructure safety rules.
*   **context.md**: High-level domain overview covering writing style, UI, and agent behavior.