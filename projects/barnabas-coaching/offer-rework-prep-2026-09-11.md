# Barnabas offer rework — brainstorm prep (2026-09-11, from Aaron via iMessage)

Queued discussion, no action yet, nothing reflected on the site.

## Context (Aaron's words, decoded)
- Realtors really want to move to leveraging 4+ agents.
- Bleeding edge (Anton) already has agents; leading edge (Jeff) are there now. Big topic in realtor circles — they "hear but don't see."
- The Barnabas website today *talks*, it doesn't *show*. That's the fix.
- Considering offer rework: instead of the audit/retainer (originally shaped for small biotechs), move to a hosted OpenClaw instance + retainer.

## Pre-session prep — three discussion areas

### (a) Show-don't-tell site
- Current state: barnabas.coach describes the service; no live demo.
- Ideas to bring: a live agent demo widget on the homepage; a public "watch an agent work" page (redacted real transcripts of agents doing realtor tasks: listing follow-ups, lead triage, CRM updates); case-study cards with before/after time savings; an "agent fleet dashboard" screenshot wall; the openclaw-user-guide.html already in the repo could become a public show page.
- framingley the demo as "hear but don't see" reversed: the page itself IS the demo.

### (b) Hosted OpenClaw instance + retainer offer
- Kill/retire the audit + retainer shape (biotech-shaped) → "your own hosted OpenClaw instance, managed by Barnabas, plus a retainer for ongoing agent development."
- Pricing/positioning questions for discussion: what's in the hosted tier (instance, channels setup, agent roster, template package), what's in the retainer (monthly agent building, prompt refinement, new channel setup).
- Contrast: audit = one-time snapshot; hosted instance = recurring infrastructure + ongoing relationship. Aligns with realtor ask: "agents plural, working daily."

### (c) Infrastructure requirements before offering a live production env
- Backups for both OpenClaw AND the droplet (currently no automated droplet backups on Rambo? verify).
- Per-customer isolation: one droplet per customer vs shared host with per-agent isolation. Suggest: one droplet per customer initially (simple, clean blast radius, matches Chief-droplet-setup skill).
- Secrets management (per-customer credentials, never on-droplet management key — existing rule).
- Monitoring/alerting (gateway heartbeat, cron failure alerts — the same nightly checks Dru runs for Aaron).
- Update path (openclaw update policy per customer), config-push workflow (already queued as discussion topic #1 — feeds directly into this).
- Cost model: droplet monthly cost + OpenClaw license + support hours → floor price for the hosted tier.

## Cross-links
- Gateway config-push workflow discussion (queued) is a prerequisite for (c).
- Session-reconcile cron design draft is relevant to (c) — reliable memory across resets is a production promise.
- Jeff's droplet (Chief template) is effectively the pilot of the hosted offer.