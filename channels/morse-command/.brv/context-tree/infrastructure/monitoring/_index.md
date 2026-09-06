---
children_hash: 30dd7514763c8d325410c90c23766c5e224ea88cbe6cb3328d1d7d101deadbea
compression_ratio: 0.4212218649517685
condensation_order: 1
covers: [x_post_monitoring.md]
covers_token_total: 311
summary_level: d1
token_count: 131
type: summary
---
### X Post Monitoring (x_post_monitoring.md)
Monitors Morse/CW content via Nitter RSS to bypass X API limitations.

* **Workflow**: Nitter RSS → `scripts/monitor_x_posts.py` (score ≥ 8) → FastMail JMAP → Email notification.
* **Operations**: Cron-scheduled daily at 7am PT.
* **Dependencies**: Reliable Nitter RSS and FastMail JMAP access.
* **Technical Constraints**: Avoids X API 402 errors; `@Ham_Radio_World` currently unsupported.
* **Key Rules**: Score ≥ 8 required for notification; daily schedule strictly enforced.