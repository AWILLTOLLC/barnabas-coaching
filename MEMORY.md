# MEMORY.md — L1 Overview (Active Context)

_L0 index: `memory/MEMORY-L0.md`. Full detail: `memory/topics/<name>.md`. Raw logs: `memory/YYYY-MM-DD.md`._

---

## Standing Order: Dru = Orchestrator (2026-09-05)

Aaron's rule, stored in AGENTS.md, applies every session. Tasks matching an agent's domain → delegate to that agent and relay results. Other tasks → subagent on local q8 by default; OpenRouter model when clearly better (authority granted). Only VERY SMALL tasks stay inline.

### Agent Ownership Map

## Dru (main)
- **Dru (main)** — **Chief of Staff** (promoted from "personal AI assistant" by Aaron, 2026-09-08): orchestrator, right hand, agent team lead, system config, gateways, this instance
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
- **Fern** — Lily's agent (isolated workspace, Quinn Q8)
- **Larry** — general assistant (gemma4 deleted; model TBD)

## House Sale (Active)

- Selling current house → moving to Fremont apartment (3620 Phinney Ave N, Apt 412, Seattle 98103).
- Pre-sale: ~$10k downstairs bathroom remodel in progress. Anton (realtor friend) advising.
- Dumpster (clean-out, 2026-09-08): ✅ BOOKED with Rubatino Refuse Removal (Everett) — delivery Fri 2026-09-11, 8am–12pm. P&T Industries phone disconnected 9/9 (vendor possibly out of business); DTG Recycle (425) 549-3000 as future backup; 10 yd $378–500, 20 yd $585–635; no permit if driveway.
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

## Chief-of-Staff Template + DO Droplets (Active, 2026-09-09/10)

> Droplet 134.209.217.142 superseded 2026-09-10: Aaron deleted it; Jeff relaunch on new droplet.

- New product: pre-configured OpenClaw droplet with "Chief" template agent (Dru is the template). Business-agnostic, sanitized (strip names/persona/memory/logs — template, not copy).
- Workshop 2026-09-09: 8 attendees. Jeff = first test customer.
- **Rambo droplet (Jeff, customer #1), relaunched 2026-09-10:** bare Ubuntu 24.04 at 143.198.151.243. first-run.sh now image-agnostic (unit-file detection, onboarding-before-unit, persisted gateway.auth.token, retry loop); SETUP-WALKTHROUGH Step 2 rewritten. add-provider-keys.sh: hidden-prompt OpenRouter key → SecretRef → PROVIDER-PROOF-OK probe; Aaron collects keys on 1:1 customer calls (process change). Jeff's gateway: openrouter/z-ai/glm-5.3-flash default (Aaron's choice). TUI must run as `sudo -u openclaw` (root gets token mismatch). Sanitized 9-job cron set deployed; report jobs delivery.mode=none until channel exists.
- Channel: Jeff wants WhatsApp (knowingly accepts full-account tap / ToS risk); QR emailed, awaiting scan. Fallback analysis: Signal needs dedicated number, Matrix needs none. CHANNELS.md template written. Old droplet deleted by Aaron.
- Tailscale rule: customer droplet joins the *customer's* tailnet, node-shared to Aaron — never auth to Aaron's tailnet. Auth URLs are one-time tokens, never paste in chat.
- **Dedicated ops phone incoming:** Tello physical SIM ordered (eSIM unsupported on Galaxy A16 4G) for a dedicated number for Dru; Samsung A16 dual-SIM, data SIM slot 1.
- Template package v2: OWNER-ACCESS-WALKTHROUGH.html, LESSONS-LEARNED.md, CHANNELS.md. Full log: `memory/topics/chief-template-droplet.md`.
- Key fixes still encoded in first-run.sh + SETUP-WALKTHROUGH: Node 22→24 prerequisite; `openclaw update` broken on DO image (npm install -g with allow-scripts); legacy state files block boot post-upgrade; trustedProxies needs ::1 (IPv6) + userHeader. SSH flakiness = UFW LIMIT + fail2ban; Aaron's IP 174.127.233.74 whitelisted.

## Backup + Credits Automation (2026-09-08/09)

- System crontab backup: 3:30am daily, 2.3G tarball, 7d/30d retention. Memory-survival test deployed (8:30am PT iMessage report).
- OpenRouter credits tracker: `scripts/openrouter_credits.py` + cron `openrouter-credits-brief-line` (7am PT). Key = OPENROUTER_MANAGEMENT_KEY (management key; Aaron rotating after transcript-fragment leak 2026-09-08). Doubles as silent-model-swap tripwire — GLM V4 Turbo default mistake cost $4.81 in one day (308% of avg).
- Barnabas blog batch shipped 2026-09-08/09 (commits 58373ed..edd79d3): 200-day post, "Bits hit the fan" post-mortem, Tips & Tricks post, 5-Mistakes update. Pending: **Aaron to rotate GitHub PAT**.
- Harness study overnight plan (2026-09-09): all 5 steps done, deliverables `overnight-step{1..5}-*.md`. Headline: enforcement is advisory, not mechanical — only code in the path enforces. Subagents again claimed file-writes that never happened (verify-then-report rule added). Phase 1 protocol edits await Aaron go/no-go.
- Anton's Barnabas site ideas parked: `projects/barnabas-coaching/IDEAS-anton-2026-09-09.md` (visitor quiz, warmth, auto-typing textbox, 15%-started progress bar). Aaron wants to work through later.

## Merkle and Bloom (S-corp)

- Website/domain admin owned by **Vera** (assigned by Aaron 2026-09-08; Avery stays analyst/sparring partner, not domain ops).
- Aaron's S-corp (game dev + other). EIN acquired. DUNS via Apple pending (2026-02-21).
- Morse Code Defense: iOS game on TestFlight. Marketing automation not yet built — Aaron waiting on Dru.
- Detail + marketing plan: `memory/topics/morse.md`.


## Barnabas Coaching (Active)

- AI coaching for Seattle SMBs. barnabas.coach live. $2,500 audit / $1,500/mo retainer.
- Team: Aaron (founder) + Chris B. (TPM) + Michelle W. (PMO Director). All ex-Microsoft.
- Full team bios, credibility bullets, deploy instructions: `memory/topics/barnabas.md`.

## Workspace Skills (Custom, Auto-Loaded)
- **Robinhood meme-scout / GMGN monitor** (built 2026-09-04/05 via LittleJohn on q8): TikTok private-API scout skill + GMGN token monitor at `projects/robinhood-meme-scout/`. **Monitors KILLED 2026-09-05** at Aaron's order; launchd plist `com.apollo.gmgn-monitor` quarantined to `~/.openclaw/disabled-launchagents/`. Details, restart steps, decisions: `memory/topics/robinhood-meme-scout.md`.

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

## Fern Agent (Lily's Agent)

- Agent ID: `fern`. Isolated workspace: `~/.openclaw/workspace/agents/fern/`.
- Model: Quinn Q8 local. Zero access to Aaron's workspace/memory.
- Lily connects via Tailscale (her own account: lily.z.myers@gmail.com) → gateway at `https://apollo-1.tailb4a099.ts.net`.
- `identityScopes` maps Lily to `operator.read + operator.write` (no admin).
- Hard boundary enforced in Fern's AGENTS.md: never read outside workspace, redirect Lily's questions about Aaron's stuff to Aaron/Dru.

## Memory System Fixes (2026-09-06)

- **Provenance-weighted search** (`scripts/provenance_search.py`): trust tiers rank results by source reliability. Topics/wiki (1.0) > MEMORY.md (0.9) > daily notes (0.8) > situational-awareness (0.7) > dreaming (0.6) > ByteRover (0.5) > imports (0.4). Fixes "first result wins on conflict" bug.
- **Instinct reconciliation** (`scripts/reconcile_instincts.py`): cross-references instincts against correction signals + error log. Demotes contradicted instincts, flags zero-validation high-confidence ones. Runs weekly via cron alongside compress_signals.py.

## Communication Channels

- **iMessage is Dru's primary out-of-band contact channel to Aaron** (set up 2026-09-03). Use it for anything Aaron needs to know outside the bounds of an active conversation — proactive updates, completed background work, alerts, blockers — rather than waiting for him to check back.
- Sends via `imsg` CLI from a dedicated Apple ID (`apollo@morsecommand.com`) signed into Messages on the apollo-1 gateway host, to Aaron's `mac@kaw.cc`.
- `channels.imessage` config: `dmPolicy: allowlist`, `allowFrom: ["mac@kaw.cc"]` only, `groupPolicy: disabled`. Locked down deliberately — no one else can reach the agent via this channel.
- Host permissions required (macOS, non-obvious): Full Disk Access + Automation (Messages) both granted to the actual `imsg` binary path (`/opt/homebrew/Cellar/imsg/<version>/bin/imsg`), not a symlink. `imsg` is unsigned — grant via Finder `Cmd+Shift+G` to paste the path directly, since `/opt` is hidden and unsigned binaries don't show up in the normal picker. These grants are version-pinned and will need re-adding after `brew upgrade imsg` or `brew upgrade node`.

## Infrastructure (Stable)

- **Host:** macOS 26.3.1 (arm64), M5 Pro Max MacBook Pro — 128GB unified memory, 4TB storage. Migrated from Ubuntu container (2026-03-18).
  - **Standing order (2026-09-08): any locally started server/node must bind to the tailscale IP (100.65.203.16), never localhost-only** — Aaron's daily driver M1 MacBook is on the tailnet and cannot reach localhost on this host. Applies every time, not just when asked.
- **Tailscale:** gateway host is `apollo-1` (IP `100.65.203.16`). Dashboard over HTTPS: `https://apollo-1.tailb4a099.ts.net` (Tailscale Serve enabled 2026-08-17: gateway.tailscale.mode=serve, resetOnExit=true, proxies to 127.0.0.1:18789). `aarons-macbook-pro` (100.94.67.96) is Aaron's separate remote Mac. Control UI needs a secure context (https or 127.0.0.1) or device-identity fails with "could not connect" — plain http on the tailscale IP won't work.
- **Nightly memory cron:** 11pm PST, ID: 2a848c7f-2d2c-4e73-8dfe-d7adc248cb72.
- **Daily briefing:** `scripts/daily_briefing.py` — dormant, no scheduler wired up.
- **Context offload cron:** 5-min, ID `8dca72e1-d26f-49a5-b703-819bd1e4f1f3`, runs `scripts/context-offload.py` (rebuilt 2026-09-10 after original was truncated to "pending", see ERRORS.md): compacts idle sessions >80K tokens, writes records to `memory/context-offloads/`. Job delivery config still announce/"last" (gateway refuses it every run, silently) — needs a one-time interactive patch to delivery mode none + failureAlert→iMessage.
- **iCloud CalDAV:** mac@kaw.cc, app password at `/Users/apollo/.openclaw/credentials/icloud.json`. Amazon emails → drubot@posteo.com.
- **Backups:** daily 9am PST. Script: `/Users/apollo/backups/backup-openclaw.sh`. 14-day retention.

## Music Preferences (Nectar Lounge Briefings)

- Loves: Christian Löffler. Wheelhouse: melodic/organic electronic, Anjunadeep, deep house, melodic techno, progressive, downtempo.
- Likely loves: Above & Beyond, Lane 8, Yotto, Dosem, Elderbrook, Monolink, Ben Böhm, Bonobo, Jon Hopkins, RÜFÜS DU SOL, Tale of Us, Four Tet, Floating Points, ODESZA, Tycho.
- Briefing: ⭐ known faves, ✅ genre-matched; show ALL non-disliked events.

## Graph Engineering (Saved 2026-09-08)

- Repo digest at `memory/topics/graph-engineering.md` (codejunkie99/graph-engineering, MIT, 486★). Aaron wants to revisit.
- Claude skill: 9-stage KG pipeline (SEU grad course translated) + task-graph orchestration patterns. DeepMind×MIT finding: parallel teams win ~80% only on splittable work; sequential work always loses with teams.
- Relevance: evidence for our delegation rules; candidate skill install for structuring cross-agent knowledge.

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
- **Agent Foundations Workshop deck** (barnabas.coach/agent-foundations-workshop.html): Aaron's 7-block workshop (stack/cost/options/channels/memory/orchestration/behaviour) — full digest + cost tables + 200-day lessons in `memory/topics/barnabas-agent-workshop.md`. Companion: /agent-configurator.html (Agent Builder tool), /creel (Creel & OpenClaw services).
> superseded 2026-09-11 by: Creel page removed from barnabas.coach (OpenClaw 2.0 made Creel unnecessary; Aaron not maintaining it currently). Creel remains an internal project at rest. Commit 9253806, deployed live, /creel 404s.
- Raw sources: wiki/raw/ (immutable, append-only LOG.md); compile-into-wiki conventions: wiki/SCHEMA.md
