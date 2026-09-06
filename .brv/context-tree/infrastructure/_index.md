---
children_hash: 3f8e05670ff3cd6bd51c71a0c9244101f89ee1efed1a9aff0cce94ab01d35fe1
compression_ratio: 0.487964989059081
condensation_order: 2
covers: [context.md, dru_agent/_index.md, ollama/_index.md, workspace_config/_index.md, workspace_config/tailscale_serve_control_ui.md]
covers_token_total: 914
summary_level: d2
token_count: 446
type: summary
---
# Infrastructure Domain Summary

The Infrastructure domain encompasses the technical, operational, and workspace-specific policies governing OpenClaw. It is organized into three primary operational pillars:

### Dru Agent Operational Constraints
Focuses on gateway stability and communication integrity.
* **Gateway Management**: Restarting the gateway requires explicit authorization from Aaron.
* **Fetch Protocols**: `scrapling` is the mandatory default fetcher; `web_fetch` is restricted to fallback use due to `undici` TLS instability.
* **Communication**: Public ghost-writing for Aaron is strictly prohibited.
* **Security**: Git history rewriting, force-pushing, and unauthorized environment variable injection are forbidden. Subagent API claims require mandatory verification.
* Refer to `dru_agent_hard_rules.md` for full implementation details.

### Local LLM & Inference Infrastructure
Addresses performance optimization and timeout mitigation for local models.
* **Timeout Bug**: High-latency inference failures were traced to `num_ctx` misconfiguration (defaulting to 262,144 tokens). 
* **Resolution**: All Ollama Modelfiles must now explicitly cap `num_ctx` at 32,768. 
* **Operational Rule**: Local models must be pre-warmed to avoid initial latency spikes.
* Refer to `local_llm_timeout_bug.md` for diagnostic history and technical resolution.

### Workspace & Business Configuration
Defines the operational foundation and business logic.
* **Infrastructure Foundation**: Repository management and gateway management rules (initialized 2026-03-09).
* **Business Logic**: IT consulting for biotech clients serves as the primary revenue driver.
* Refer to `workspace_and_infrastructure.md` and `context.md` for workspace rules and operational environment definitions.