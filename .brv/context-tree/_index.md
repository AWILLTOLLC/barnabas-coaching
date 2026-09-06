---
children_hash: 493c63865ba6ee41451e5c9772d4d30035c4593c40c0267de38aaef608723ba9
compression_ratio: 0.33134328358208953
condensation_order: 3
covers: [conventions/_index.md, infrastructure/_index.md, projects/_index.md]
covers_token_total: 2010
summary_level: d3
token_count: 666
type: summary
---
# Workspace and Project Infrastructure Overview (d3)

This structural summary integrates the foundational operation frameworks, infrastructure constraints, and active project initiatives.

### Operational Frameworks and Conventions
* **Content Strategy**: A unified framework (Maven, 2026-03-14) governs brand voice for agents Spark, Dash, Barrett, and Forge. Library specifications reside in `channels/<channel>/references/content-formats.md`. Feedback loops are enforced via @Maven tagging.
* **Communication Rules**: Strict single-reply policy post-tool execution. Prohibits redundant narration and trailing summaries. Stylistic requirements mandate comma/colon usage over em dashes and Heroicon SVGs over standard emojis.
* **Task Orchestration**: Complex jobs utilize DAG-based decomposition with per-node token cost estimates. Tasks are persisted to `tasks/<project>/todo.json` for resilience and tracked via `Anthropic` rate limit headers.
* **Refer to**: `conventions/content_strategy/`, `conventions/patterns/`, and `conventions/workspace/`.

### Infrastructure and Gateway Policy
* **Gateway Operations**: Gateway restarts require explicit authorization. Public ghost-writing for Aaron is prohibited. Force-pushing and unauthorized environment variable injection are forbidden.
* **Fetch Protocols**: `scrapling` is the mandatory fetcher; `web_fetch` is restricted to fallback due to `undici` TLS instability.
* **Inference Optimization**: Local Ollama Modelfiles must cap `num_ctx` at 32,768 to mitigate latency-related timeout bugs.
* **Refer to**: `infrastructure/dru_agent/`, `infrastructure/ollama/`, and `infrastructure/workspace_config/`.

### Active Project Portfolio
* **Professional & Business**:
    * **Barnabas Coaching**: AI consultancy for Seattle SMBs.
    * **Black Raven**: Hardware procurement focusing on non-Chinese scotch eye augers.
    * **Glimmer Cards**: Shopify/Cloudflare-based rave compliment card project.
* **Software Development**:
    * **Creel**: Native macOS OpenClaw client (replacing VantageOC as of 2026-03-18).
    * **Morse Code Defense**: iOS game on TestFlight; finalizing marketing automation.
    * **SafeHarbor**: Secure AI execution using `Virtualization.framework` and Alpine Linux. Employs `vsock` JSON-RPC for IPC and GRDB/SQLite for persistence.
* **Logistics & Relocation**:
    * **House Sale**: Fremont relocation (3620 Phinney Ave N) with ~$500k projected yield.
    * **Malta 2026**: Travel logistics for Oct 2026. Primary trigger: Anjunadeep Malta presale (March 31, 2026). Mandatory ETIAS filing required.
* **Refer to**: `projects/` domain for specific project paths and architectural decisions.