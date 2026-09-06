---
children_hash: 680be37e500f898aeec65a3b149a9eb4b18ee3ae87a36bee65c9e78a6ca91025
compression_ratio: 0.8605442176870748
condensation_order: 2
covers: [seo/_index.md]
covers_token_total: 294
summary_level: d2
token_count: 253
type: summary
---
# AI Search Optimization (Level d2)

The AI Search Optimization domain governs content discoverability and structural integrity for AI-driven search engines and crawlers. This domain is defined by the core strategies outlined in `ai_search_optimization.md`.

## Architectural Decisions
- Crawler Accessibility: Full integration enabled via `robots.txt` allowlists and the deployment of `llms.txt` to guide AI discovery.
- Schema Strategy: Implementation of structured data across key assets:
  - `FAQPage` schema on `/faq/` (12 Q&As).
  - `Article` schema on `/koch-method/` (2000-word primary resource).
  - `EducationalApplication` schema on `index.html`.
- Metadata Management: Continuous synchronization of `sitemap.xml` with site updates.

## Governance and Standards
- Identity: All published content and associated schemas must explicitly designate AWILLTO LLC as the publisher.
- Resource Focus: The Koch Method page acts as the foundational long-form educational resource within the site architecture.