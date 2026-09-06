# MEMORY — Morse Command (Consolidated)
**Last updated:** 2026-03-30 12:43 PDT
**Supersedes:** All prior MEMORY-morse-command-*.md files (2026-03-11 through 2026-03-13)

---

## App Status

- **App:** Morse Command — asteroid-style iOS game, Koch method Morse training
- **Apple ID:** 6759479305
- **App Store URL:** https://apps.apple.com/us/app/morse-code-defense/id6759479305
- **App Store listing:** "Morse Command: CW Trainer" (temp title — target is "Morse Command" once name conflict resolved)
- **Publisher:** AWILLTO LLC (Aaron's S-corp)
- **Price:** $4.99 paid, no IAP, no subscription, no ads
- **Platform:** iOS only
- **Status as of 2026-03-13:** Submitted to App Store for review. Ready for Distribution (approved 2026-03-16). Pending Paid Apps Agreement processing (tax/banking docs submitted ~2026-03-16, expected live within 24-48h from then).

## Name Dispute

- "Morse Command" name taken by squatter app (id6751498289, developer Aytac Mamiyeva, released 2025-08-28, 1 star, 1 review, never updated, v1.0)
- Temp workaround: title changed to "Morse Command: CW Trainer"
- Canonical brand remains "Morse Command"
- Apple IP infringement report submitted 2026-03-20 via apple.com/legal/internet-services/itunes/appstorenotices/
- Next: follow up ~2 weeks after submission; parallel tracks = USPTO trademark (~$350) + direct developer outreach

## Agent Identity

- **Name:** Dash (assigned by Aaron 2026-03-13) — named after the Morse dah
- Aaron's other agents: Forge (Black Raven Augers), Spark (Glimmer Cards)

---

## Infrastructure

### Website — morsecommand.com
- SSH: `mc@morsecommand.com` (key auth, Caddy, web root `/home/mc/`)
- Deploy: `rsync -avz --delete <local>/ mc@morsecommand.com:~/`
- Stack: single-page static HTML, no framework
- Design system: Orbitron/Inter/JetBrains Mono fonts; `--green-primary: #4ADE80` brand color
- Live pages: index.html, /privacy.html, /support.html, /press-kit.html
- /robots.txt, /sitemap.xml live
- Plausible Analytics script added (needs Plausible account at plausible.io to activate)
- Email waitlist form uses Formspree (needs Aaron to create account + swap in `YOUR_FORM_ID`)
- `apple-itunes-app` meta tag still has `YOUR_APP_ID` placeholder — needs real App Store ID
- Press contacts: support@morsecommand.com, press@morsecommand.com (need forwarding set up)

### App Store Connect API
- Credentials: `/Users/apollo/.openclaw/credentials/appstore_connect.json`
- Key ID: `U52M27K4YB` | Issuer ID: `69a6de78-11e6-47e3-e053-5b8c7c11a4d1`
- Private key: `/Users/apollo/.openclaw/credentials/AuthKey_U52M27K4YB.p8`
- Script: `scripts/asc_client.py` (run with `/tmp/asc-venv/bin/python3`)
- Venv: `/tmp/asc-venv` (PyJWT + cryptography)
- Vendor number: `85612226`
- Working: customer reviews, app info, sales/download reports ✅

### Outreach Email
- Address: dash@morsecommand.com (FastMail)
- API token: `/Users/apollo/.openclaw/credentials/fastmail_dash.json`
- Volume target: ~1,000/day during blast campaigns

### X API
- Credentials: `/Users/apollo/.openclaw/credentials/x_api.json`
- Auth: OAuth 1.0a as @AlricEdryk
- Use: read-only monitoring / competitive research
- X handle for app: @MorseCommand (registered 2026-03-25 by Aaron)
- X posting: Maven generates weekly posts; Aaron schedules via Buffer — no API posting by Dash

---

## Outreach Rules (confirmed by Aaron 2026-03-13)

- **No appearances** — no podcast guest spots, interviews, live sessions (at least for now)
- **One-way outreach only** — announce app, offer promo codes, point to App Store
- **Aaron handles inbound** — direct questions to aaron@morsecommand.com
- **Send as Dash, not Aaron** — Dash is an employee of Morse Command; can mention Aaron as creator
- **Tone:** light-hearted, friendly, masculine — like a guy at a hamfest
- **Signoff:** `73, Dash @ Morse Command`
- **Approved templates:**
  - `outreach/templates/template-hamradio-creator.txt` ✅
  - `outreach/templates/template-prepper-military.txt` ✅
  - `outreach/templates/template-cw-org-partnership.txt` ✅
  - Podcast pitch template: dropped

---

## Influencer Pipeline (Summary)

Full database: `tasks/influencer-pipeline.md` — Sweep 3 complete (2026-03-11 17:15 UTC)

**Totals in database:**
- YouTube: 33+ channels
- TikTok: 25+ accounts
- Instagram: 28+ accounts
- Twitter/X: 9 accounts
- Podcasts: 12
- Blogs/web: 3
- CW/Morse learning communities: 5
- Reddit communities: 6
- Forums: QRZ.com, eHam.net, SurvivalistBoards (168K members)
- Streaming: Twitch (HamNCheddar: 20.3K)
- International orgs: JARL (Japan), DARC (Germany), RSGB (UK), LABRE (Brazil), URE (Spain), SRR (Russia)

**Tier 1 priority targets:**
1. Ham Radio Crash Course (Josh Nass KI6NAZ) — 407K YT, 47K IG — #1 target
2. Ham Radio 2.0 (Jason KC5HWB) — 192K YT
3. The Tech Prepper (Gaston) — 165K YT + 31.8K IG, ham+prepper exact overlap
4. K4SWL (Thomas Witherspoon) — THE CW-on-air creator, POTA focus
5. DX Commander (Callum M0MCX) — #1 community recommendation, British ham
6. OH8STN Julian — off-grid emcomm, CW operator, ~55K YT

**Strategic audience pools (high priority):**
- **POTA (Parks on the Air):** 84K+ registered operators, CW dominant, growing 22% YoY — single biggest untapped channel
- **LCWO.net:** Koch method CW learner site — EXACT method as Morse Command
- **LICW (Long Island CW Club):** online Zoom CW classes, international
- **CWops:** serious CW operators club
- **QRZ.com:** 800K+ callsigns, active CW megathread
- **SurvivalistBoards.com:** 168K members, 11.8M posts, direct placement possible

**International opportunities:**
- Japan 2026 = 100th anniversary of Japanese amateur radio (JARL + Osaka Expo 8K3EXPO) — localization timing opportunity
- RSGB / British Science Week Morse-athon (was live 2026-03-11) — UK outreach
- DARC (Germany): 44K members, only 1.8K IG — email/newsletter channel dominant

---

## Launch Strategy

- **Phase 1 (English-native):** On App Store approval — ham radio forums, prepper/survivalist communities, military/vet networks, English-native influencers
- **Phase 2 (Localization):** After Phase 1 settles — prioritize Japanese first (timing opportunity)

**Launch day posting targets (Aaron confirmed):**
- Product Hunt (primary — launches 12:01am PT)
- Peerlist
- Uneed (submit 2-3 days before)
- Fazier
- MicroLaunch

---

## Pending / Blocked Items

- [ ] App Store Connect API → daily KPI reports still not flowing (needs live sales data)
- [ ] Formspree form ID — Aaron needs to create account and swap `YOUR_FORM_ID` in index.html
- [ ] Plausible Analytics — Aaron needs to create account at plausible.io
- [ ] press@morsecommand.com / support@morsecommand.com — need forwarding setup
- [ ] `apple-itunes-app` meta tag — needs real App Store ID in index.html
- [ ] Product Hunt hunter — need to line up before launch
- [ ] Press kit URL live (morsecommand.com/press-kit — page exists, needed for outreach emails)
- [ ] Scrape missing contact emails (16 contacts in launch-contacts.csv)
- [ ] CWops contact email (cwops.org)
- [ ] LICW official contact email
- [ ] TikTok, Instagram, YouTube accounts — still pending creation
- [ ] Aaron approves community posts → `outreach/community-posts.md` (BLOCKING outreach)
- [ ] Paid Apps Agreement finalization — needed for revenue to flow

---

_Consolidated from 8 prior memory files. Old files can be deleted._
