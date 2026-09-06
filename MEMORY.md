# MEMORY.md — L1 Overview (Active Context)

_L0 index: `memory/MEMORY-L0.md`. Full detail: `memory/topics/<name>.md`. Raw logs: `memory/YYYY-MM-DD.md`._

---

## Standing Order: Dru = Orchestrator (2026-09-05)

Aaron's rule, stored in AGENTS.md, applies every session. Tasks matching an agent's domain → delegate to that agent and relay results. Other tasks → subagent on local q8 by default; OpenRouter model when clearly better (authority granted). Only VERY SMALL tasks stay inline.

### Agent Ownership Map

- **Dru (main)** — orchestrator, chief of staff, system config, gateways, this instance
- **Maven (marketing)** — marketing for all three businesses, content, SEO, competitor reports
- **Quinn (qwen)** — Discord community agent (Reality Changers), general assistant
- **LittleJohn** — research and reports (crypto, Robinhood chain, web research)
- **Frankie** — text-to-image generation (FLUX.2 Max via image_generate)
- **Forge (black-raven)** — Black Raven Company ops
- **Spark (glimmer)** — Glimmer Cards ops
- **Dash (morse-command)** — Morse Code Defense / X post monitoring
- **Barrett (barnabas-coaching)** — Barnabas AI coaching content
- **Vera (merkle-and-bloom)** — Merkle & Bloom ops
- **Creel** — operator dashboard tooling
- **Avery** — analyst/sparring partner, evidence-based reviews
- **Scout** — scouting/research
- **Forward** — general agent on local q8
- **Larry** — general assistant (gemma4 deleted; model TBD)

## House Sale (Active)

- Selling current house → moving to Fremont apartment (3620 Phinney Ave N, Apt 412, Seattle 98103).
- Pre-sale: ~$10k downstairs bathroom remodel in progress. Anton (realtor friend) advising.
- First buyer fell through. Capital post-sale: ~$300–500k + ~$400k retirement.
- Contractor: Eagle Remodel & Construction (Doru, Everett, (206) 495-8587) — quote pending.
- Backups: Footprints Bath and Tile Northwest (Everett), SMY Home Improvement (Lynnwood).

## Lily

- Aaron's girlfriend and intended future wife. Glimmer Cards co-founder. Core presence in all planning.
- Spends ~95% of personal time with her. The only person Aaron fully opens up to. She's curious, updates beliefs on new information — intellectually compatible.

## Aaron — Personal Context

- 47. Self-described loner with a rich inner life. Plenty of social acquaintances, but Lily is the only deep relationship outside family.
- Came from a religious background; dismantled dogmatic beliefs that stopped serving him. Sees the same zealotry pattern in Seattle's social justice culture — holds people at emotional distance for it.
- Leans conservative but open-minded and genuinely curious. Values personal accountability and belief-updating.
- Plans to leave Seattle in 2028. Not building new friendships there intentionally.
- Looking for a church community at his new location (had one before the move).

## The Three Businesses

### IT Consulting (primary income)
- Biotech clients. AI Coach service (Barnabas Coaching) running alongside it.

### Black Raven Company
- Handmade scotch eye augers. Active manufacturer search (started 2026-03-01).
- RFQ: `BlackRavenAuger_RFQ.docx`. Contact email: claude@kaw.cc. Target: 1,500–2,000 units @ $8–15/unit.
- Non-China preferred (Taiwan, India, Vietnam, Mexico, Eastern Europe, USA). QIMA QC planned.
- Task tracker: `tasks/blackraven-rfq/todo.md`.

### Glimmer Cards (with Lily)
- Rave compliment cards. Brand new, wants to grow.
- Site: letsgoglimmer.com (CF Pages, glimmer-cards-web.pages.dev). Shop: shop.letsgoglimmer.com (Shopify, phsjm0-jp.myshopify.com).
- GitHub: AWILLTOLLC/glimmer-cards-web. My account: AugustCrane (PAT at `/Users/apollo/.openclaw/credentials/github.json`).
- CF creds: `/Users/apollo/.openclaw/credentials/cloudflare.json` (account: 5c68e7493917ba789644831da2432fdb).
- Local project: `/Users/apollo/.openclaw/workspace/projects/glimmer-cards-web/`

## Merkle and Bloom (S-corp)

- Aaron's S-corp (game dev + other). EIN acquired. DUNS via Apple pending (2026-02-21).
- Morse Code Defense: iOS game on TestFlight. Marketing automation not yet built — Aaron waiting on Dru.
- Detail + marketing plan: `memory/topics/morse.md`.


## Barnabas Coaching (Active)

- AI coaching for Seattle SMBs. barnabas.coach live. $2,500 audit / $1,500/mo retainer.
- Team: Aaron (founder) + Chris B. (TPM) + Michelle W. (PMO Director). All ex-Microsoft.
- Full team bios, credibility bullets, deploy instructions: `memory/topics/barnabas.md`.

## Workspace Skills (Custom, Auto-Loaded)

- **humanizer** — strip AI writing tells; canonical style pass for all prose
- **content-engine** — platform-native content; primary use: Glimmer Cards + Black Raven social
- **search-first** — research-before-coding; auto-apply on any dev task
- **openclaw-ios-chat** — native iOS chat client skill

## Creel — Active Development

- Native macOS operator dashboard. Talks directly to OpenClaw gateway API. No plugin layer.
- Replaced VantageOC (retired 2026-03-18). Vantage plugin deleted. Channel workspace: `channels/creel/`.
- Agent ID: `creel`. Agent name: Creel. Emoji: 🎣.
- **Channel agent names:** Main=Dru, Black Raven=Forge, Glimmer Cards=Spark, Morse Command=Dash, Barnabas Coaching=Barrett, Merkle and Bloom=Vera, Creel=Creel, Marketing=Maven.
- **Marketing channel:** Created 2026-03-14. Shared marketing brain for all channels. Workspace: `channels/marketing/`. Files: SOUL.md (portfolio knowledge + marketing playbooks), MEMORY.md, AGENTS.md, TOOLS.md, USER.md.
- **Content format libraries** created 2026-03-14: `channels/glimmer/references/content-formats.md`, `channels/morse-command/`, `channels/barnabas-coaching/`, `channels/black-raven/` — brand voice, audience, platform stack, named post formats + templates.

## SafeHarbor — Active Development (2026-03-14)

Aaron's project to run AI agents in an isolated macOS VM. Architecture finalized:
- **VM:** Alpine Linux via Virtualization.framework (macOS 13+, no Docker)
- **Runtime:** Single Node.js sidecar (TypeScript → JS via esbuild)
- **IPC:** vsock JSON-RPC 2.0 on port 5000 (Swift host ↔ Node.js guest)
- **Persistence:** SQLite via GRDB + 9p filesystem mounts
- **App Support:** `~/Library/Application Support/SafeHarbor/`
- **Guest mounts:** `/agents/` (configs), `/data/burrow.db` (SQLite)
- **API key:** passed as env var at VM boot
- Build plan: `reports/burrow-server-build-plan.md` (working title "Burrow" — rename pending)
- Naming theme: lobster/crustacean (SafeHarbor or Haven leaning)
- Replaces VantageOC's gateway integration layer long-term

## Operational Lessons

- **Transcript poisoning:** If responses double/triple, check session transcript — not delivery infra.
- **Session key:** Always use canonical `'agent:main:main'`, not `'main'`.
- **VantageOC test command:** `agent test X Y` — spawns X top-level agents × Y sub-agents.

## Workspace Git

- Git initialized 2026-03-09. `.gitignore` added. Workspace is a tracked repo.
- openclaw.json hardened: `compaction.memoryFlush`, `reserveTokensFloor: 40000`, `memorySearch.enabled`, `cache.enabled`.

## Communication Channels

- **iMessage is Dru's primary out-of-band contact channel to Aaron** (set up 2026-09-03). Use it for anything Aaron needs to know outside the bounds of an active conversation — proactive updates, completed background work, alerts, blockers — rather than waiting for him to check back.
- Sends via `imsg` CLI from a dedicated Apple ID (`apollo@morsecommand.com`) signed into Messages on the apollo-1 gateway host, to Aaron's `mac@kaw.cc`.
- `channels.imessage` config: `dmPolicy: allowlist`, `allowFrom: ["mac@kaw.cc"]` only, `groupPolicy: disabled`. Locked down deliberately — no one else can reach the agent via this channel.
- Host permissions required (macOS, non-obvious): Full Disk Access + Automation (Messages) both granted to the actual `imsg` binary path (`/opt/homebrew/Cellar/imsg/<version>/bin/imsg`), not a symlink. `imsg` is unsigned — grant via Finder `Cmd+Shift+G` to paste the path directly, since `/opt` is hidden and unsigned binaries don't show up in the normal picker. These grants are version-pinned and will need re-adding after `brew upgrade imsg` or `brew upgrade node`.

## Infrastructure (Stable)

- **Host:** macOS 26.3.1 (arm64), M5 Pro Max MacBook Pro — 128GB unified memory, 4TB storage. Migrated from Ubuntu container (2026-03-18).
- **Tailscale:** gateway host is `apollo-1` (IP `100.65.203.16`). Dashboard over HTTPS: `https://apollo-1.tailb4a099.ts.net` (Tailscale Serve enabled 2026-08-17: gateway.tailscale.mode=serve, resetOnExit=true, proxies to 127.0.0.1:18789). `aarons-macbook-pro` (100.94.67.96) is Aaron's separate remote Mac. Control UI needs a secure context (https or 127.0.0.1) or device-identity fails with "could not connect" — plain http on the tailscale IP won't work.
- **Nightly memory cron:** 11pm PST, ID: 2a848c7f-2d2c-4e73-8dfe-d7adc248cb72.
- **Daily briefing:** `scripts/daily_briefing.py` — dormant, no scheduler wired up.
- **iCloud CalDAV:** mac@kaw.cc, app password at `/Users/apollo/.openclaw/credentials/icloud.json`. Amazon emails → drubot@posteo.com.
- **Backups:** daily 9am PST. Script: `/Users/apollo/backups/backup-openclaw.sh`. 14-day retention.

## Music Preferences (Nectar Lounge Briefings)

- Loves: Christian Löffler. Wheelhouse: melodic/organic electronic, Anjunadeep, deep house, melodic techno, progressive, downtempo.
- Likely loves: Above & Beyond, Lane 8, Yotto, Dosem, Elderbrook, Monolink, Ben Böhm, Bonobo, Jon Hopkins, RÜFÜS DU SOL, Tale of Us, Four Tet, Floating Points, ODESZA, Tycho.
- Briefing: ⭐ known faves, ✅ genre-matched; show ALL non-disliked events.

## Knowledge Bases

- **Situational Awareness** (Aschenbrenner, June 2024): SQLite FTS5 at `data/situational-awareness.db`. Search: `python3 scripts/search_situational_awareness.py "query"`. **Do NOT load full text into context.**
- **free-for-dev** — Before recommending any paid infra/tooling, check https://github.com/ripienaar/free-for-dev first. 119k-star repo cataloguing free tiers for cloud, databases, CI/CD, hosting, APIs, monitoring, email, auth, and more. Aaron's standing rule: always check here before making build recommendations.

---

## Errors / Hard Rules

- **Never restart the gateway without explicit permission.** Even if fix is obvious. Ask first. (Violated 2026-03-09.)
- **Claude Code / subagents can invent APIs.** Verify any `api.*` calls against real SDK before trusting.
- **Don't trust subagent file-write claims.** Verify with Read after. Two Opus subagents claimed to write and didn't.

## Malta Trip 2026 (Active — Oct 2–16)

- Aaron + Lily. Anjunadeep Malta Oct 8–11.
- Festival tickets ✅ (confirmed 2026-04-01). Malta accommodation ✅.
- **SEA→FCO Alaska 787 flight: status unknown.** Launched April 28. It's now late June — needs confirmation ASAP. Trip is ~99 days out.
- Rome Oct 3–5: Donna Camilla Savelli hotel (request garden-facing). FCO→MLA Ryanair Oct 6.
- Open: ETIAS (~€7 each), Colosseum + Vatican advance booking.
- Detail: `memory/topics/malta.md`

## Archive (Completed / Stable)

- Glimmer Cards VPS migration → CF Pages complete (2026-03-06). Old VPS can be cancelled.
- OpenClaw Studio (2026-03-02): Tailscale setup on Aaron's Mac — notes in daily files if needed.
- Mission Control (builderz-labs): Aaron interested, not yet set up.
- DUNS via Apple: requested 2026-02-21, awaiting.
- X API setup: complete. Credentials: `/Users/apollo/.openclaw/credentials/x_api.json`. See TOOLS.md for usage.
- Dru online since 2026-02-20. SOUL.md last updated 2026-02-27.
