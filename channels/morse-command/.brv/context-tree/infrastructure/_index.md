---
children_hash: 2ab6c14a844f1efb9bfe5437345a63b98978d22c0e0ca8a576b8ef95d7e53976
compression_ratio: 0.9226804123711341
condensation_order: 2
covers: [monitoring/_index.md]
covers_token_total: 194
summary_level: d2
token_count: 179
type: summary
---
### Monitoring Overview
This domain tracks Morse/CW content through automated pipelines designed to bypass external API limitations.

#### X Post Monitoring (x_post_monitoring.md)
The system utilizes Nitter RSS feeds to track relevant social media activity, circumventing X API cost constraints. 

* **Pipeline**: Nitter RSS → `scripts/monitor_x_posts.py` → FastMail JMAP.
* **Logic**: Posts are processed by a scoring script; only those meeting a threshold of ≥ 8 trigger an email notification.
* **Constraints**: 
    * Daily execution at 7am PT via cron.
    * `@Ham_Radio_World` is currently excluded from monitoring.
* **Dependencies**: Requires consistent availability of Nitter RSS and FastMail JMAP services.