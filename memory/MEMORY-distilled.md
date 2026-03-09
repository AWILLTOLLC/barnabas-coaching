# MEMORY.md - Distilled Long-Term Memory

_Active context only. Raw logs in memory/YYYY-MM-DD.md. Full original: MEMORY.md._

---

## House Sale (Active)

- Selling current house → moving to Fremont apartment. 3–5 month timeline.
- First buyer fell through. Decided against Airbnb.
- Pre-sale work: ~$10k downstairs bathroom remodel (non-functional, needs full gut).
- Contractor outreach (2026-02-25): **Eagle Remodel & Construction** (Doru, Everett, (206) 495-8587) — quote pending. Backups: Footprints Bath and Tile Northwest (Everett), SMY Home Improvement (Lynnwood).
- Anton (realtor friend) advising. House: main floor + unfinished walkout basement + upstairs MIU suite + hot tub.
- Capital post-sale: ~$300–500k proceeds + ~$400k retirement → deploy into next business phase.

## Lily

- Aaron's girlfriend, cherished. Co-founder of Glimmer Cards. Treat as significant presence in all planning.

## The Three Businesses

### 1. IT Consulting (primary income)
- Biotech clients. AI Coach service (Barnabas Coaching) being built alongside it.

### 2. Black Raven Company
- Handmade scotch eye augers. **Active manufacturer search** (started 2026-03-01).
- RFQ: `/root/.openclaw/workspace/BlackRavenAuger_RFQ.docx`. Contact email: claude@kaw.cc (August).
- Target: 1,500–2,000 units @ $8–15/unit. Non-China preferred (Taiwan, India, Vietnam, Mexico, Eastern Europe, USA).
- Previous Chinese factory had communication failures. QIMA pre-shipment QC planned.
- Task tracker: `tasks/blackraven-rfq/todo.md`.

### 3. Glimmer Cards (with Lily)
- Rave compliment cards. Brand new, wants to grow.
- **Site:** letsgoglimmer.com — on Cloudflare Pages (glimmer-cards-web.pages.dev). DNS stable.
- **Shop:** shop.letsgoglimmer.com → Shopify (phsjm0-jp.myshopify.com).
- **GitHub:** AWILLTOLLC/glimmer-cards-web. My account: AugustCrane (PAT at `/root/.openclaw/credentials/github.json`).
- **CF creds:** `/root/.openclaw/credentials/cloudflare.json` (account: 5c68e7493917ba789644831da2432fdb).
- **Local project:** `/root/.openclaw/workspace/projects/glimmer-cards-web/`

## Merkle and Bloom (S-corp)

- Aaron's S-corp (game dev + other). Has EIN. DUNS via Apple pending (2026-02-21).
- **Morse Code Defense** — asteroid-style iOS game teaching Morse via Koch method. Published to TestFlight 2026-02-21.
- Target: ham radio, preppers, survivalists, military/vets.
- **Marketing automation plan** (Aaron wants Dru to drive post-launch):
  - Content factory: short-form hooks for TikTok/Instagram/YouTube Shorts/X, 3x/day, auto-posted
  - Influencer outreach: find ham radio YouTubers + prepper/vet channels, scrape emails, blast at scale
  - Daily KPI reports via Telegram (downloads, revenue, traffic sources)
  - App Store review triage + support escalation
  - **Setup needed:** Postbridge/Buffer, App Store Connect API, social accounts for Morse Command

## Malta Trip 2026 (Aaron & Lily) — Action Items Pending

- **Anjunadeep Malta:** Oct 8–11, 2026.
- **Full routing locked:** SEA→FCO Oct 2 (Alaska direct 787, ~$599pp, launches April 28 — book soon) → Rome Trastevere Oct 3–5 (Donna Camilla Savelli, request garden-facing) → FCO→MLA Oct 6 (Ryanair, ~€60pp) → Malta Oct 7–15 → MLA→LHR→SEA Oct 16 (BA+Alaska AS101, arrives 6:45pm).
- Malta accommodation: booked. Festival tickets: **March 31 presale (12pm GMT) — flag in briefing March 28 + 31.**
- Special touches: arrival prosecco/flowers, Gianicolo sunset, Flytographer session, pasta-making class, Glimmer Cards at festival, private Malta boat charter, letter to Lily.
- ETIAS needed (~€7 each). Colosseum + Vatican: advance booking required.
- Files: `tasks/malta-trip-2026/TRIP.md` + `MASTER_CHECKLIST.md`.

## Barnabas Coaching (Active Business)

- **Brand:** Barnabas Coaching. Aaron as named expert. Domain: barnabas.coach (live).
- **Target:** Seattle-area SMBs, 10–200 people.
- **Services:** AI Audit $2,500 one-time; Coaching Retainer $1,500/month (2 calls + async).
- **Stack:** Astro static site → `projects/barnabas-coaching`. Deploy: `npm run build` → rsync `dist/` to `barnabas.coach:/home/barnabas/html`.
- **Team:** Aaron (founder/coach), Chris B. (TPM Microsoft background), Michelle W. (Director of PMO, Microsoft Legal, Merkle and Bloom PM). All 3 were at Microsoft simultaneously — core narrative hook.
- **Aaron's credibility:** VoIP routing code late '90s, TPM MSN Messenger at 24, Accenture consultant (built Microsoft training), Director of IT for prominent Seattle exec (NDA), 8 years biotech IT, built Morse Command w/ AI.

## Workspace Skills (Custom, Auto-Loaded)

- **humanizer** — strip AI writing tells; canonical style pass for all prose
- **openclaw-ios-chat** — native iOS chat client skill
- **content-engine** — platform-native content creation; primary use: Glimmer Cards + Black Raven social
- **search-first** — research-before-coding; auto-apply on any dev task

## VantageOC — Active Development

- Operator dashboard macOS app. Plugin: `~/.openclaw/extensions/vantage/` (index.ts, store.ts, types.ts, openclaw.plugin.json).
- DB: `~/.openclaw/vantage-plugin.db`. Loaded (auto-discovered at gateway startup).
- **Architecture:** ping+cursor model. `pushEnvelope` emits `{ type: 'vantage.new', ts }` ping; clients call `vantage.poll?since=<cursor>`.
- **Reply routing:** `updateLastRoute` uses canonical key `'agent:main:main'` (not `'main'`).
- Full spec: `projects/vantage/SPEC.md`, `PROTOCOL_SPEC.md`, `CHANNELS_SPEC.md`.

**Next steps:**
1. Vantage macOS client: implement ping+cursor model (stop rendering from `vantage.event`; on `vantage.new` → call `vantage.poll?since=<cursor>`; advance cursor atomically; persist to UserDefaults; init cursor to `Date.now()` on fresh install).
2. Test end-to-end: Aaron sends from test3/test4 → agent replies in Vantage channel.
3. If routing solid: implement per-channel session isolation with own SOUL.md.

**Safety Alert Protocol:**
- Blocking: `[SAFETY:RED:r-TIMESTAMP] About to run: DESCRIPTION — blocked, awaiting approval.`
- Informational: `[SAFETY:YELLOW] Notice text`
- Operator responses: `[SAFETY:APPROVED:r-TIMESTAMP]` or `[SAFETY:DENIED:r-TIMESTAMP]`

**Future:** Channel-based agent org (per-business channels: Barnabas, Black Raven, Glimmer Cards, Morse) built into Vantage. Private, self-hosted.

## Operational Lessons

- **Transcript poisoning:** If responses double/triple text, check session transcript for corrupted assistant messages — do NOT debug delivery infra. Old broadcast model caused duplicate storage; LLM mimicked escalation. Session reset clears it.
- **Session key aliasing:** `normalizeStoreSessionKey` is just `.toLowerCase()`. Never resolves aliases. Always use canonical key `'agent:main:main'`, not `'main'`.
- **VantageOC test command:** `agent test X Y` — spawns X top-level agents × Y sub-agents for dashboard visibility testing.

## Infrastructure (Stable, Brief)

- **Tailscale:** on ubuntu-ct. Gateway: `wss://ubuntu-ct.tailb4a099.ts.net`.
- **Nightly memory cron:** 11pm PST, cron ID: 2a848c7f-2d2c-4e73-8dfe-d7adc248cb72.
- **Daily briefing:** `scripts/daily_briefing.py`, 7am PST (15:00 UTC). Telegram + email (a@kaw.cc). Sections: weather, iCloud calendar, Amazon deliveries, email flags, Nectar Lounge events.
- **iCloud CalDAV:** mac@kaw.cc, app password at `/root/.openclaw/credentials/icloud.json`. Amazon emails forwarded to drubot@posteo.com.
- **Backup:** daily 9am PST (17:00 UTC). Script: `/root/backups/backup-openclaw.sh`. Output: `/root/backups/openclaw-YYYY-MM-DD.tar.gz`, 14-day retention.

## Music Preferences (Nectar Lounge Briefings)

- **Confirmed loves:** Christian Löffler
- **Genre wheelhouse:** melodic/organic electronic, Anjunadeep sound, deep house, melodic techno, progressive, downtempo
- **Likely loves:** Above & Beyond, Lane 8, Yotto, Dosem, Elderbrook, Monolink, Ben Böhm, Bonobo, Jon Hopkins, RÜFÜS DU SOL, Tale of Us, Four Tet, Floating Points, ODESZA, Tycho
- Briefing flags: ⭐ known faves, ✅ genre-matched; shows ALL non-disliked events

## Knowledge Bases

- **Situational Awareness** (Leopold Aschenbrenner, June 2024): SQLite FTS5 at `/root/.openclaw/workspace/data/situational-awareness.db`. Search: `python3 scripts/search_situational_awareness.py "query"`. 241 chunks, 10 sections. Topics: AGI timelines, intelligence explosion, lab security, superalignment, US/China race. **Do NOT load full text into context** — query DB on demand.

---

## Archive (Completed / One-Time / Stable)

- Glimmer Cards VPS migration (2026-03-06): migrated from 137.184.3.195 to CF Pages — complete. Old VPS can be cancelled.
- OpenClaw Studio (2026-03-02): setup attempted on Aaron's Mac via Tailscale. Notes in original MEMORY.md if needed.
- Mission Control (builderz-labs): Aaron interested as dashboard, not yet set up.
- DUNS number requested through Apple flow (2026-02-21): awaiting approval.
- Dru came online 2026-02-20. SOUL.md last updated 2026-02-27 with current canonical operating rules.
- OpenClaw Native App (macOS + iOS chat client): design/vision stage only — not built.
- X API setup: complete, credentials in `/root/.openclaw/credentials/x_api.json`. See TOOLS.md for usage.
