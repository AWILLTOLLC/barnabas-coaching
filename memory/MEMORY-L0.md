# MEMORY-L0 — Quick Index
<!-- Dru: Chief of Staff (promoted 2026-09-08) -->

## Right now (updated 2026-09-09)
<!-- 3-6 lines of current focus; refresh during nightly consolidation -->
- **Chief template product: droplet deployed & hardened.** Jeff's DO droplet (134.209.217.142) running OpenClaw 2026.9.3 with sanitized Chief workspace; all DO-image pitfalls fixed & encoded in first-run.sh. Full log: `memory/topics/chief-template-droplet.md`. Open: model/API-key per customer, Jeff pairing, first-boot message.
- Barnabas agent-configurator: Steps 3/4 swapped + verified (17/17 jsdom checks); NOT deployed — Aaron/Barrett deploys.
- Buzz offering: pitch approved & emailed to Aaron (Posteo SMTP works); next: local Mac test env (`projects/buzz-offering/TEST-ENV.md`).
- Loop engineering plan drafted (`tasks/loop-engineering-plan.md`) — awaiting Aaron's go on phases.
- Graph engineering digest saved (`memory/topics/graph-engineering.md`) — revisit flagged.

_Scan this first. Expand to `MEMORY.md` (L1) or `memory/topics/<name>.md` (L2) only for relevant topics._

## 🔴 Urgent / Watch

| Topic | One-liner | Expand |
|---|---|---|
| **Chief Template** | Chief-of-Staff agent template product (Agent Workshop); Jeff = first customer; droplet live at 134.209.217.142, hardened | `memory/topics/chief-template-droplet.md` |
| **Standing Order** | Dru = orchestrator of all agents. Delegate domain tasks to owned agents, else subagent on local q8; OpenRouter models when clearly better. Relay results. | MEMORY.md → Standing Order |
| Malta 2026 | Oct 2–16 w/ Lily; tickets ✅, accommodation ✅; **SEA→FCO flight status** — need confirmation ⚠️ | `memory/topics/malta.md` |
| Morning Brief 9/9 | ✅ **Dumpster BOOKED (9/9): Rubatino delivery Friday 9/11, 8am–12pm window, Mukilteo clean-out.** (P&T phone disconnected — vendor offline; Rubatino was the backup pick.) | below |
| Creel | Native macOS OpenClaw client (no plugin); replaced VantageOC (retired 2026-03-18) | `channels/creel/` |
| House Sale | Selling → Fremont apt; bathroom remodel in progress; ~$300-500k capital post-sale | `MEMORY.md` |
| Black Raven RFQ | Active manufacturer search since 2026-03-01; non-China preferred; quote pending | `MEMORY.md` |

## 🟡 Active / Ongoing

| Topic | One-liner | Expand |
|---|---|---|
| Robinhood Meme-Scout | Robinhood Chain meme-coin scout + GMGN monitor (built 9/4-9/5); **monitors KILLED 9/5**, launchd plist quarantined to ~/.openclaw/disabled-launchagents/ | `memory/topics/robinhood-meme-scout.md` |
| Barnabas Coaching | AI coaching biz for Seattle SMBs; site live; team of 3 (Aaron + Chris + Michelle) | `memory/topics/barnabas.md` |
| Glimmer Cards | Rave compliment cards w/ Lily; CF Pages + Shopify; wants to grow | `MEMORY.md` |
| Morse Code Defense | iOS game on TestFlight; marketing automation not yet built — Aaron waiting on Dru | `memory/topics/morse.md` |
| SafeHarbor | AI agents in isolated Alpine Linux VM on macOS; vsock JSON-RPC; SQLite via GRDB; active dev | `MEMORY.md` |
| IT Consulting | Primary income; biotech clients; feeds Barnabas Coaching pipeline | `MEMORY.md` |

## ⚪ Stable / Reference

| Topic | One-liner | Expand |
|---|---|---|
| Lily | Aaron's girlfriend, cherished; Glimmer Cards co-founder; treat as core presence | `MEMORY.md` |
| Infrastructure | Tailscale, daily briefing, backups, CalDAV, iMessage — all stable | `MEMORY.md` |
| iMessage (Dru→Aaron) | Primary out-of-band contact channel; use for anything outside an active conversation | `MEMORY.md` |
| Music | Christian Löffler; Anjunadeep wheelhouse; for Nectar Lounge briefing flags | `MEMORY.md` |
| Hard Rules | Never restart gateway without permission; verify subagent API claims; no ghost writes | `MEMORY.md` |
| Skills (Main) | humanizer, content-engine, search-first, openclaw-ios-chat, ponytail suite — auto-loaded | `MEMORY.md` |
| Graph Engineering | Saved repo digest (KG 9-stage pipeline + task-graph patterns as a Claude skill); revisit flagged | `memory/topics/graph-engineering.md` |
| Knowledge Bases | Situational Awareness SQLite DB + **free-for-dev** (check before any build recommendation) | `MEMORY.md` |
| Workspace Git | Initialized 2026-03-09; openclaw.json hardened | `MEMORY.md` |
| LittleJohn | Research agent (🏹, Qwen Q8); workspace at `agents/littlejohn/` | `memory/topics/littlejohn.md` |
| Fern Agent | Lily's agent, isolated workspace, Quinn Q8 | `agents/fern/` |
| Memory Fixes | Provenance search + instinct reconciliation | `scripts/` |
| X2Claw | ~~Chrome extension for X→agents~~ — **DON'T USE**, Aaron didn't like it | `projects/x2claw/` (deleted) |
- Barnabas Agent Workshop deck digest → memory/topics/barnabas-agent-workshop.md (stack/cost/channels/memory/orchestration/behaviour)
- Raw-sources wiki layer → wiki/raw/ (immutable sources; conventions: wiki/SCHEMA.md)
