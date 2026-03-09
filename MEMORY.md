# MEMORY.md - Long-Term Memory

_Curated context that persists across sessions. Raw logs live in memory/YYYY-MM-DD.md._

---

## About Aaron

- Based in Seattle, WA (PST / UTC-8) — moving to Fremont neighborhood soon
- Selling house, expecting $300–500k proceeds + ~$400k retirement
- House sale plan: clean sale, 3–5 month timeline (5 months conservative)
- First sale fell through (buyer budget). Decided against Airbnb — not worth the management overhead
- Pre-sale work needed: ~$10k downstairs bathroom remodel (non-functional, needs full shower, flooring, wall repair, sink, toilet, vanity), plus lighter work Aaron will DIY
- Bathroom contractor outreach (2026-02-25): **Eagle Remodel & Construction** (Doru, Everett WA, (206) 495-8587) — quote pending. Backups: Footprints Bath and Tile Northwest (Everett), SMY Home Improvement (Lynnwood)
- Anton (realtor friend) is advising on the sale
- House layout: main floor + unfinished walkout basement + upstairs MIU suite (separate entrance). Hot tub on ground floor.
- Capital deployment: next phase of business and life
- Deep work person — quality hours matter more than quantity; guards work/life balance seriously
- Rides his BMW R 1200 GS to work most days. Also has a 1997 F350 "Blue."
- Works out with trainer Dan (Mon/Fri) + Olympic Athletic Club 2 other days with Lily

## Lily
- Aaron's girlfriend, cherished deeply
- Co-founder of Glimmer Cards with Aaron
- Works out together, goes to raves/events together
- Treat Lily as a significant presence in all life planning

## The Three Businesses
1. **IT Consulting** — biotech clients, primary income; AI Coach service being considered
2. **Black Raven Company** — handmade scotch eye augers (bushcraft/green woodworking), wants to grow. Active manufacturer search in progress (2026-03-01): RFQ at `/root/.openclaw/workspace/BlackRavenAuger_RFQ.docx`, contact email claude@kaw.cc (August), target 1,500–2,000 units @ $8–15/unit, non-China preferred (Taiwan, India, Vietnam, Mexico, Eastern Europe, USA). Previous Chinese factory had communication failures. QIMA pre-shipment QC planned. Task tracked at `tasks/blackraven-rfq/todo.md`.
3. **Glimmer Cards** (with Lily) — rave compliment cards, brand new, wants to grow
   - **Site:** letsgoglimmer.com — migrated 2026-03-06 from VPS to Cloudflare Pages (free static hosting)
   - **CF project:** glimmer-cards-web.pages.dev, DNS: letsgoglimmer.com + www → CNAME to CF Pages
   - **Shop subdomain:** shop.letsgoglimmer.com → Shopify (phsjm0-jp.myshopify.com branded domain)
   - **GitHub:** private repo AWILLTOLLC/glimmer-cards-web, org: AWILLTOLLC (Aaron's business umbrella)
   - **Local project:** `/root/.openclaw/workspace/projects/glimmer-cards-web/`
   - **Old VPS:** 137.184.3.195 (root@letsgoglimmer.com) — can be cancelled once DNS confirmed stable
   - **My GitHub account:** AugustCrane — PAT at `/root/.openclaw/credentials/github.json`
   - **CF creds:** `/root/.openclaw/credentials/cloudflare.json` (account: 5c68e7493917ba789644831da2432fdb, github@erasei.com)

## Merkle and Bloom (S-corp)
- Aaron's S-corp, used as the umbrella for game dev and possibly other ventures
- Has an EIN; DUNS number requested through Apple's flow (2026-02-21) — awaiting approval
- First iOS game: **Morse Code Defense** — asteroid-style arcade game that teaches Morse code via the Koch method. Hear the sound of a letter, type the key to destroy the asteroid. Boss fights, 5 zones, 10 levels each, power-ups. Published to TestFlight 2026-02-21.
- Target audiences: ham radio community, preppers, survivalists, military/veteran crowd

## Morse Code Defense — Marketing Automation Plan (2026-02-27)
Aaron wants Dru to drive app marketing post-launch. Modeled after how OpenClaw agent "Eddie" runs B2C app marketing at scale. Plan:
- **Content factory:** Generate short-form hooks ("hear this sound, what letter?") for TikTok/Instagram/YouTube Shorts/X, 3x/day, auto-posted via Postbridge or Buffer
- **Influencer outreach:** Find ham radio YouTubers, prepper channels, military/vet accounts via X API + browser; scrape emails; blast outreach at scale; Aaron approves deals
- **Daily KPI reports:** Morning Telegram message — downloads, revenue, top traffic sources
- **Customer support triage:** Handle App Store reviews and support emails; escalate only what matters
- **Setup needed:** Postbridge/Buffer account, App Store Connect API access, social accounts for Morse Command (X, TikTok, Instagram, YouTube), outbound email for influencer outreach
- Pre-launch: build content library + 50-influencer target list while app finishes

## OpenClaw Native App (Design Vision)
- Aaron and Dru designed a native macOS + iOS chat client (2026-02-24) — motivated by Telegram timeout/transparency problem
- Discord rejected: cleartext, Discord reads all content
- Vision: direct encrypted connection to gateway (mTLS, TLS + cert pinning, content-free APNs push)
- macOS: 3-pane layout (sidebar / chat / live task board). iOS: alert-first, approval flows, agent panel on swipe-up
- WireGuard built-in + Tailscale/Headscale first-class; OpenClaw Relay as paid fallback
- Features designed: Timeline Replay, Agent Roster, Artifact Library, Steer Controls, Approval Flows, Watch app
- Stack: Swift + SwiftUI, WebSocket, encrypted SQLite, Keychain, CryptoKit
- Not yet built — design/vision stage

## My Role
- Chief of staff, coordinator, right hand
- Lead an agent team Aaron is building
- Advisor on his AI Coach service offering

## Preferences & Tastes
- Raves, EDM, concerts/festivals
- Joule restaurant (Seattle fave), Stampede cocktail club
- Measured, intentional, balanced approach to everything

### Music (for Nectar Lounge briefings)
- **Confirmed loves:** Christian Löffler
- **Genre wheelhouse:** melodic/organic electronic, Anjunadeep sound, deep house, melodic techno, progressive, downtempo
- **Likely loves:** Above & Beyond, Lane 8, Yotto, Dosem, Elderbrook, Monolink, Ben Böhm, Bonobo, Jon Hopkins, RÜFÜS DU SOL, Tale of Us, Four Tet, Floating Points, ODESZA, Tycho
- Daily briefing flags events: ⭐ known faves, ✅ genre-matched; shows ALL non-disliked events

## X (Twitter) API
- Full API access set up 2026-02-27 — credentials in `/root/.openclaw/credentials/x_api.json`
- Bearer token + OAuth 1.0a (consumer key/secret + access token/secret), authorized as `@AlricEdryk`
- Can read any public tweet including full X Article body (plain_text field) via user context
- Use `requests-oauthlib` — see TOOLS.md for code snippet

## Infrastructure
- **Tailscale** installed on Aaron's OpenClaw instance (ubuntu-ct) — set up 2026-02-23
- Aaron uses Tailscale for remote access; iOS app connectivity over cellular routes through Tailscale
- **Nightly memory cron** running — ID: 2a848c7f-2d2c-4e73-8dfe-d7adc248cb72, fires 11pm PST, consolidates daily notes → MEMORY.md
- **Daily briefing script** — `scripts/daily_briefing.py`, fires 7am PST (15:00 UTC) via cron, sends Telegram + email to a@kaw.cc. Sections: weather, iCloud calendar, Amazon deliveries, overnight email flags, Nectar Lounge events. iCloud CalDAV connected (mac@kaw.cc, app password at `/root/.openclaw/credentials/icloud.json`). Amazon emails forwarded to drubot@posteo.com.
- **OpenClaw Studio** (web UI): Aaron is setting this up on his Mac (2026-03-02), connecting to the gateway on ubuntu-ct via `wss://ubuntu-ct.tailb4a099.ts.net`. Requires Studio's custom Node server (not `next dev`) running on the Mac at `HOST=0.0.0.0` so browser can reach it via Tailscale IP (`100.94.67.96:3000`). Upstream URL in Studio settings must point to `wss://ubuntu-ct.tailb4a099.ts.net`, not localhost. Work-in-progress — may need revisiting.
- **Mission Control** (builderz-labs) — Aaron interested as OpenClaw dashboard. Same Tailscale topology as Studio. Much simpler install (4 commands, SQLite only, no Docker). Not yet set up.
- **Backup system** (2026-03-06): Daily cron at 9am PST (17:00 UTC). Script: `/root/backups/backup-openclaw.sh`. rsync to staging first, then tar (never tar live dir). Output: `/root/backups/openclaw-YYYY-MM-DD.tar.gz`, 14-day retention. First backup: 381MB.

## Malta Trip 2026 (Aaron & Lily)
- Anjunadeep Malta festival Oct 8–11, 2026. Welcome party Oct 8, main festival Oct 9–11.
- Full routing locked (2026-03-04):
  - **Oct 2:** Fly SEA → FCO (Alaska direct 787, launches April 28, ~$599pp) — book soon
  - **Oct 3–5:** Rome, Trastevere — 3 nights at Donna Camilla Savelli (baroque convent hotel, request garden-facing room)
  - **Oct 6:** FCO → MLA (Ryanair, ~€60pp)
  - **Oct 7–15:** Malta (Anjunadeep Oct 8–11)
  - **Oct 16:** MLA → LHR → SEA (BA + Alaska AS101, arrives 6:45pm)
- Malta accommodation already booked. Festival tickets: March 31 presale (12pm GMT); presale reminder in daily briefing March 28 + 31.
- Special touches planned: arrival prosecco/flowers, Gianicolo sunset, Flytographer session, pasta-making class, Glimmer Cards at festival, private Malta boat charter, letter to Lily
- ETIAS needed (~€7 each). Colosseum + Vatican need advance booking.
- Files: tasks/malta-trip-2026/TRIP.md + MASTER_CHECKLIST.md. Checklist emailed to a@kaw.cc.

## Barnabas Coaching (AI Coaching Business)

- **Brand:** Barnabas Coaching — Barnabas-first, Aaron as named expert behind it
- **Domain:** barnabas.coach (live and deployed as of 2026-03-05)
- **Target market:** Seattle-area SMBs and owner-operated businesses (10–200 people)
- **Services:**
  - AI Audit — $2,500 one-time, workflow assessment + written report
  - Coaching Retainer — $1,500/month, 2 calls/month + async support
- **Aaron's credibility markers:**
  - Started coding at 16
  - Wrote early VoIP routing code in the late '90s (pre-Skype bleeding edge)
  - TPM at MSN Messenger / Windows Live Messenger at age 24
  - Management Consultant at Accenture (built training solutions for Microsoft consultants)
  - Director of IT for a prominent Seattle executive (under NDA)
  - 8 years running boutique biotech IT consulting company
  - Built Morse Command (#1 morse code teaching app on iOS) using AI
- **Core brand narrative:** Has been at the bleeding edge before (VoIP in '99, AI now). Track record of seeing what's next and knowing how to build with it.
- **Billing hook:** "Most AI consultants parachute in from SF and charge enterprise rates. Barnabas is local, practical, built for companies that need real results."
- **Site stack:** Astro (static, fast, SEO-optimized) — built in `projects/barnabas-coaching`
- **Hosting:** Self-hosted on Aaron's own server (`barnabas.coach`). SSH key-based access available. Caddy web server, web root at `/home/barnabas/html`
- **Deploy:** Build locally (`npm run build` in `projects/barnabas-coaching`), rsync `dist/` to `barnabas.coach:/home/barnabas/html`
- **SEO/AEO strategy:** Local Seattle focus, answer-engine optimized content, schema markup, citation building
- **Team (2026-03-05):** About page live at barnabas.coach/about. Three principals:
  - **Aaron** — founder, AI Coach
  - **Chris B.** — worked with Aaron at VoIP startup late '90s/early 2000s. TPM at Microsoft (Infopath, later SharePoint). All 3 were at Microsoft simultaneously.
  - **Michelle W.** — founding Director of PMO at fastest-growing consulting company in WA (led 8 PMs, 20hr/wk billable). Microsoft Legal team. Senior PM & systems analyst at Merkle and Bloom for 5 years.
- **Key narrative hook:** All 3 were at Microsoft simultaneously, from 3 different angles.

## Workspace Skills (Custom)

Skills in `~/.openclaw/workspace/skills/` are auto-discovered by OpenClaw and injected into every session.

- **humanizer** — strip AI writing tells; treat as the canonical style pass for all prose
- **openclaw-ios-chat** — native iOS chat client skill
- **content-engine** — platform-native content creation (X, LinkedIn, TikTok, YouTube, newsletter). Primary use: Glimmer Cards + Black Raven social content. Adapted from ECC (2026-03-06).
- **search-first** — research-before-coding discipline; check existing packages/MCPs before writing custom code. Auto-apply on any dev task. Adapted from ECC (2026-03-06).

## Knowledge Bases (Indexed Documents)

### Situational Awareness (Leopold Aschenbrenner, June 2024)
- Full document indexed into SQLite FTS5: `/root/.openclaw/workspace/data/situational-awareness.db`
- Raw PDF: `/root/.openclaw/workspace/data/situational-awareness.pdf`
- Extracted text: `/root/.openclaw/workspace/data/situational-awareness.txt`
- Search script: `python3 /root/.openclaw/workspace/scripts/search_situational_awareness.py "query" [--section X] [--limit N]`
- 241 chunks across 10 sections (Intro, I–V + IIIa–IIId)
- Topic: AGI timeline arguments, intelligence explosion, lab security, superalignment, US/China race, "The Project"
- **Do NOT load the full text into context** — query the DB on demand when Aaron asks about it

## VantageOC — Operator Control Center

VantageOC is a macOS desktop app that is Dru's operator dashboard. Connects to the OpenClaw gateway via WebSocket (JSON-RPC). Full spec: `projects/vantage/SPEC.md`.

Views: Chat (token-streaming, stock ticker for active agents), Dashboard (active agents, sessions, token usage, cron status, thinking columns), Activity Feed (all tool calls/spawns/events), Work Panel (agent hierarchy cards), Tokens, Heartbeat, Logs, Sessions.

**Safety Alert Protocol** — critical behavior Dru must follow:
- Blocking action needing approval: `[SAFETY:RED:r-TIMESTAMP] About to run: DESCRIPTION — blocked, awaiting approval.`
- Informational notice (no action needed): `[SAFETY:YELLOW] Notice text`
- Responses from operator: `[SAFETY:APPROVED:r-TIMESTAMP]` or `[SAFETY:DENIED:r-TIMESTAMP]`
- Vantage shows red overlay card with Approve/Deny buttons + critical system notification on RED alerts

Connection: WebSocket JSON-RPC, Ed25519 device identity, creds in macOS Keychain, auto-reconnect with exponential backoff.

**Future:** Aaron wants channel-based agent organization (per-business channels: Barnabas, Black Raven, Glimmer Cards, Morse) built into Vantage instead of Discord. Private, self-hosted. Each channel gets its own agent session + eventually its own SOUL.md.

## VantageOC Plugin — Current State (as of 2026-03-08)

**Plugin location:** `~/.openclaw/extensions/vantage/` (index.ts, store.ts, types.ts, openclaw.plugin.json)
**DB:** `~/.openclaw/vantage-plugin.db` — tables: tasks, tool_calls, safety_alerts, drafts, outbound_queue, channels, channel_messages
**Loaded:** yes (auto-discovered at gateway startup)

**What works:**
- `message(channel=vantage, target=test3)` — resolves and routes
- `vantage.channels.list/history/post/mark_read` RPC methods
- `vantage.poll` with `channelSlug` filter (cursor-based, non-destructive)
- WebSocket auth + `chat.send` loopback
- Reply routing fixed: `updateLastRoute` now uses canonical key `'agent:main:main'` (not `'main'`)
- Ping-only broadcast model: `pushEnvelope` emits `{ type: 'vantage.new', ts }` ping; clients call `vantage.poll?since=<cursor>` to fetch content

**Architecture (ping+cursor model):**
- No full message content in broadcasts — eliminates multi-client duplicates
- Each client owns its cursor; advance BEFORE rendering, lock during in-flight poll
- Operator inbound messages: persisted to `channel_messages` + enqueued (fires ping for cross-device sync)
- `store.purgeOldEvents(maxAgeMs)` — 24h retention, runs on start + every 6h
- `channel_read` events for cross-client badge sync

**Client-side required changes (for Vantage macOS):**
1. Stop rendering from `vantage.event` broadcasts (ping-only now)
2. On `vantage.new` ping or connect: call `vantage.poll?since=<cursor>`
3. Advance cursor atomically before rendering
4. Initialize cursor to `Date.now()` on fresh install (not 0)
5. Persist cursor to UserDefaults
6. Handle `channel_read` events + `sender: 'operator'` chat events (render as outbound)

**Two WS connections in logs:**
- `vdev` = Vantage macOS app
- `v1.0.0` = plugin's internal loopback WS (for `loopbackChatSend → chat.send`) — NOT a second user client

**Key API discoveries:**
- Gateway frame format: `{ type: "req", id, method, params }` (not JSON-RPC)
- `chat.send` requires `idempotencyKey` param
- Store key aliasing: `normalizeStoreSessionKey` is literally `.toLowerCase()` — does NOT resolve 'main' → 'agent:main:main'. Always use canonical key.
- Protocol spec: `projects/vantage/PROTOCOL_SPEC.md`, SPEC.md, CHANNELS_SPEC.md

**Next steps when resuming:**
1. Vantage macOS client: implement ping+cursor model (see client-side changes above)
2. Test full end-to-end: Aaron sends from test3/test4 → agent replies in Vantage channel
3. If routing confirmed solid: implement per-channel session isolation with own SOUL.md

## VantageOC Agent Test Command
- **Command:** `agent test X Y` — spawn X top-level agents, each spawns Y sub-agents, each sub-agent completes a small random token task
- **Purpose:** Testing agent spawning hierarchy for VantageOC dashboard visibility
- **Example:** `agent test 2 3` = 2 agents × 3 sub-agents = 6 total sub-agents running token tasks in parallel

## Operational Lessons

- **Transcript poisoning (2026-03-08):** If agent responses start doubling/tripling text, check session transcript for corrupted assistant messages immediately — do not debug delivery infrastructure. Old broadcast model sent full content to all WS clients, which caused duplicate storage in transcript. LLM then mimicked the pattern, escalating single → double → triple. Session reset clears it.
- **Session key aliasing:** OpenClaw's `normalizeStoreSessionKey` is just `.toLowerCase()` — never resolves aliases. Use canonical key `'agent:main:main'`, not `'main'`, in any direct store or routing operation from plugins.

## About Me (Dru)
- Name: Dru
- Wizard energy 🧙
- Came online 2026-02-20
- Bootstrapped fresh with Aaron — he came prepared with his own SOUL.md and IDENTITY.md
- **SOUL.md updated 2026-02-27** with sharpened operating rules: brevity is law, strong opinions required (no hedging), swearing permitted when it earns it, banned opener phrases, Advanced Operating Principles section added (orchestrator role, agent spawning, safety exception gate, self-evolution with approval, 24/7 mode). This is the current canonical SOUL.
