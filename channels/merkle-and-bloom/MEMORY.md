# MEMORY.md

## Ownership (2026-09-08)

- **Vera owns the Merkle & Bloom website/domain admin** — assigned directly by Aaron. Domain, hosting, deploys, site content updates. (Avery remains analyst/sparring partner only.) — Merkle and Bloom

_Current state of all active work. Update this as things change._

---

## Web Stack Inventory (2026-09-08)

_Inventoried live via API. Credentials: `~/.openclaw/credentials/cloudflare.json` (api_token) and `~/.openclaw/credentials/github.json` (org,token,username). Never echo values._

### Cloudflare — account "Github@erasei.com's Account" (id 5c68e7493917ba789644831da2432fdb)
- **Zone merkleandbloom.com: PENDING, 0 DNS records.** Created 2026-09-02. Nameservers never pointed at Cloudflare; nothing resolves yet.
- **Pages project `merkleandbloom`:** serves merkleandbloom.pages.dev + www.merkleandbloom.com. Production branch main. Source: null → **direct upload, no git integration.**
- Pages project `glimmer-cards-web`: letsgoglimmer.com — Glimmer Cards (Lily's business), adjacent, not M&B core.
- No Workers. **barnabas.coach and morsecommand.com are NOT in Cloudflare** — still on their own hosts with rsync/Caddy deploys.

### GitHub — user AugustCrane, org AWILLTOLLC
- AWILLTOLLC/barnabas-coaching — public, active (pushed 2026-09-06) <!-- project: github.com/AWILLTOLLC/barnabas-coaching -->
- AWILLTOLLC/glimmer-cards-web — private, static since Mar 2026
- No repo exists for the merkleandbloom.com site.

### Flags (need Aaron decisions)
1. **merkleandbloom.com is not live:** zone pending, no DNS records, registrar for the domain unknown. To go live: confirm registrar → change nameservers to Cloudflare → create root/www records → bind Pages domain.
2. **M&B site has no git repo:** Pages deploys are direct upload, unversioned. Recommend a repo in AWILLTOLLC.
3. **barnabas.coach + morsecommand.com outside my control** (rsync + third-party DNS). Migrate DNS into Cloudflare? Requested 2026-09-08.

---

## Company Overview

**Merkle and Bloom** — Aaron's S-corp. Has EIN. DUNS number requested via Apple (Feb 2026, pending approval).

Active products:
1. **Morse Command** — iOS game, App Store launch pending
2. **Barnabas Coaching** — AI advisory service, live and building pipeline
3. **IT Consulting** — primary income, biotech clients, not a growth focus

Team beyond Aaron: **Chris B.** (TPM, ex-Microsoft) and **Michelle W.** (Director of PMO, ex-Microsoft Legal). All three overlapped at Microsoft — this is the Barnabas credibility anchor.

---

## Morse Command — Current State

**Product:** Asteroid-style iOS game teaching Morse code via Koch method (character-by-character fluency building). TestFlight: published Feb 21, 2026.

**Target audience:** Ham radio operators, preppers/survivalists, military, veterans, emergency comms.

**Launch status:** TestFlight live. App Store submission pending.

**Marketing vision — planned but not yet live:**
- Content factory: short-form video (TikTok, Reels, YouTube Shorts, X) — 3 posts/day, auto-scheduled
- Influencer outreach: ham radio YouTubers + prepper channels — email scrape at scale
- Daily KPI reports to Aaron via Telegram (downloads, revenue, traffic sources)
- App Store review triage + support escalation automation

**Pending setup items:**
- [ ] App Store Connect API credentials
- [ ] Social accounts (TikTok, Instagram, YouTube Shorts, X) for Morse Command brand
- [ ] Postbridge or Buffer account for scheduling
- [ ] Influencer outreach pipeline (Scrapling + email script)
- [ ] KPI report cron (after App Store Connect is live)

**Site:** morsecommand.com — SSH: mc@morsecommand.com, web root: /home/mc/

---

## Barnabas Coaching — Current State

**Service:** AI coaching for Seattle-area SMBs (10–200 people)

**Offerings:**
- AI Audit — $2,500 one-time (map current state, identify gaps, deliver roadmap)
- Coaching Retainer — $1,500/month (2 calls + async support)

**Site:** barnabas.coach (live, Astro static site)
- Local: `projects/barnabas-coaching/`
- Deploy: `npm run build` → rsync → barnabas.coach:/home/barnabas/html

**Pipeline:** Track here when clients are added.

| Stage | Company | Contact | Value | Notes |
|---|---|---|---|---|
| (empty — populate as pipeline builds) | | | | |

**Team tasks:** Track here when assigned.

| Task | Owner | Status | Notes |
|---|---|---|---|
| (empty — populate as tasks are assigned) | | | |

---

## IT Consulting — Current State

Primary income. Biotech clients. Aaron manages directly.

No active growth initiatives — it's the runway while Barnabas and Morse Command scale.

Flag to Aaron if he mentions a new client, a renewal risk, or capacity constraints.

---

## Decisions Log

_Significant decisions with rationale. Prevents re-litigating._

| Date | Decision | Rationale |
|---|---|---|
| (none yet) | | |

---

## Open Questions / Blockers

| Item | Status | Owner |
|---|---|---|
| App Store Connect API setup | Not started | Aaron / Dru to initiate |
| merkleandbloom.com zone activation + DNS | Blocked — registrar unknown, needs Aaron | Vera |
| barnabas.coach + morsecommand.com DNS migration to Cloudflare | Needs Aaron decision | Vera to execute |
| Barnabas Coaching — first paid client | Pending pipeline build | Aaron |
| Morse Command App Store submission | Pending | Aaron |
| DUNS number via Apple | Pending (requested Feb 2026) | Aaron |
