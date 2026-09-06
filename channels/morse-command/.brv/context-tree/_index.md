---
children_hash: e0042aa415012028f994a7f046b52889d365661fef432898c50f6cc32233deb2
compression_ratio: 0.591726618705036
condensation_order: 3
covers: [infrastructure/_index.md, marketing/_index.md]
covers_token_total: 556
summary_level: d3
token_count: 329
type: summary
---
# Knowledge Structural Summary (Level d3)

## Infrastructure: Monitoring
The infrastructure domain focuses on automated Morse/CW content tracking, bypassing external API constraints through Nitter RSS integration.
* **Core Pipeline**: Nitter RSS feeds ingested by `scripts/monitor_x_posts.py` and routed via FastMail JMAP.
* **Logic & Constraints**: Automated daily execution (7am PT); notifications triggered by a scoring threshold (≥ 8). `@Ham_Radio_World` is explicitly excluded from monitoring.
* **Drill-down**: See `infrastructure/monitoring/x_post_monitoring.md` for pipeline specifications.

## Marketing: AI Search Optimization
The marketing domain governs content discoverability for AI-driven search crawlers, emphasizing structured data and standardized metadata.
* **Architectural Decisions**: 
    * Crawler Accessibility: Managed via `robots.txt` and `llms.txt`.
    * Schema Mapping: `FAQPage` (12 Q&As), `Article` (Koch Method), and `EducationalApplication` (index).
    * Resource Foundation: The `koch-method.html` resource serves as the primary long-form educational asset.
* **Governance**: AWILLTO LLC is mandated as the publisher for all content and schema data.
* **Drill-down**: See `marketing/seo/ai_search_optimization.md` for specific implementation details and synchronization protocols.