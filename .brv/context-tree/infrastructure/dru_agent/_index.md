---
children_hash: 17b6b891c81b8c98e83cb55cdd219f9737a68c27a9df5e2f9d153631ab707ba9
compression_ratio: 0.7078651685393258
condensation_order: 1
covers: [dru_agent_hard_rules.md]
covers_token_total: 356
summary_level: d1
token_count: 252
type: summary
---
# Dru Agent Hard Rules Summary

This entry establishes critical operational constraints for the Dru agent, focusing on gateway stability, git integrity, and communication protocols.

## Operational Constraints
- **Gateway Management**: Restarting the gateway requires explicit permission from Aaron.
- **Web Fetching**: Use `scrapling` as the default fetcher to avoid `undici` TLS-related crashes associated with `web_fetch`.
- **Public Communication**: Ghost-writing public posts on behalf of Aaron is strictly prohibited without prior approval.

## Security and Integrity Protocols
- **Subagent Interaction**: All API claims from subagents must be verified before execution.
- **Git Safety**: Force-pushing, branch deletion, and history rewriting are forbidden.
- **Environment Security**: Pushing environment variables to codebases is prohibited without authorization.

For granular details on specific safety implementations and rule enforcement, refer to the full `dru_agent_hard_rules.md` documentation.