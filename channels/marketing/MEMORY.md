# MEMORY.md — Maven, Marketing Agent

_Current state of all active marketing work across the portfolio. Update this as things change._

---

## Storage Rules

All memory files live **in this directory only.**

Naming convention: `MEMORY-marketing-YYYY-MM-DD-HHMM.md`

**Never write to:**
- Main workspace `MEMORY.md`
- Main workspace `memory/` folder
- Other channel workspaces

---

## Portfolio Marketing Status (as of 2026-03-14)

### Barnabas Coaching
- **Stage:** Pre-revenue. Site live at barnabas.coach.
- **Content:** First blog post published (2026-03-13): "5 AI Mistakes Small Business Owners Keep Making"
- **Channels live:** Website, Google Business Profile (live 2026-03-20: https://share.google/WHugLihkmJkMoqgRu)
- **Channels not yet active:** LinkedIn (no brand presence), email list, outbound
- **Priority:** Rebuild offer ladder + site CTA + content strategy (see 2026-04-01 strategy shift below)
- **Gap:** No lead generation system yet. Previous content too high-level for audience.
- **Background correction (2026-03-20):** Aaron, Chris, and Michelle did NOT leave Microsoft to start Barnabas. They left Microsoft long ago for separate reasons. For the last 8 years they've been running a boutique Biotech IT consulting firm (still active). Barnabas is an addition, not a career pivot. Never frame it as "we left Microsoft to do this."

#### ⚠️ Strategy Shift — 2026-04-01
**Problem identified:** LinkedIn posts getting minimal traction (few comments, handful of site visits). Root cause: messaging is too high-level. Audience (Seattle SMB owners) mostly unaware AI applies to their specific problems. Pitching strategy to people who haven't admitted they have the problem yet.

**New offer ladder (Aaron confirmed):**

| Rung | Offer | Price | Purpose |
|---|---|---|---|
| 1 | 30-min AI Opportunity Call | Free | Lead gen, qualify, understand their pain |
| 2 | One Fix | $300–500 (complexity-based) | Prove value on one specific workflow problem |
| 3 | AI Opportunity Scan | $800–1,200 | Map top 3–5 automatable workflows, prioritize, action plan |
| 4 | Full AI Audit | $2,500 | Existing offer — now an upsell, not the front door |
| 5 | Monthly Retainer | $1,500/mo | Existing offer — follows naturally after audit |

**Key decisions:**
- Free 30-min call is the new primary CTA everywhere (site, LinkedIn, outreach)
- Aaron runs the One Fix engagements himself at this stage
- Content job is now: get them to book the free call — not sell AI, not explain the audit
- Content format shifts to problem-first: name their specific pain, then offer the call
- Stop leading with AI. Lead with the work they hate doing.

### Glimmer Cards
- **Stage:** Live and selling. letsgoglimmer.com + shop.letsgoglimmer.com (Shopify)
- **Affiliate:** UpPromote active — $1.50/pack, registration at https://af.uppromote.com/glimmer/register
- **Products live:** Starter Pack (10 cards)
- **In development:** Shuffler Pack (pending art + print production — NOT live yet)
- **Channels active:** Shopify store, affiliate program
- **Channels not yet active:** TikTok, Instagram, YouTube, email list
- **Influencer research:** `outreach/influencer-list.csv` in Glimmer channel (created 2026-03-12)
- **Priority:** Content creation (TikTok/Instagram), influencer seeding, festival presence

### Morse Command
- **Stage:** App Store live. TestFlight still active for new feature early access.
- **App Store name:** "Morse Command: CW Trainer" (temporary workaround — "Morse Command" was taken at submission; revert to "Morse Command" as soon as the name clears. Do NOT use "CW Trainer" in any other marketing context — it's App Store-only.)
- **Marketing infra:** Not yet built
- **Channels not yet active:** TikTok, Instagram, YouTube Shorts, X (as Morse Command brand), App Store listing optimization
- **Priority:** Build App Store listing (screenshots, preview video, keywords), prepare influencer outreach list
- **Pending:** App Store Connect API, social accounts, scheduling tool

### Black Raven Company
- **Stage:** Very early. Active manufacturer RFQ (1,500–2,000 units target)
- **Contact email:** claude@kaw.cc
- **Channels not yet active:** Everything
- **Priority:** Wait for manufacturing to be solved before heavy marketing investment. Seed bushcraft community authentically in the interim.

### Merkle & Bloom
- **Stage:** Site live at merkleandbloom.com. Embedded IT ownership model.
- **Content status (2026-09-04):** 4 industry service pages + 4 blog posts drafted, awaiting Aaron review. See [MEMMARY-merkle-and-bloom-content.md](vantage-file://~/.openclaw/workspace/channels/marketing/MEMMARY-merkle-and-bloom-content.md)
- **Channels live:** Website, 2 case studies referenced on site
- **Channels not yet active:** Blog (content drafted), AI citation tracking (Rightcited + Bing Webmaster pending)
- **Priority:** Deploy content, set up AI tracking, collect 3rd case study
- **Voice:** Direct, specific, technically grounded. No fluff. Aaron's voice profile applies.
- **Key message:** "Embedded IT ownership" — senior technical leadership that works on site, understands the full environment, stays available when it matters, takes responsibility for moving it forward.

---

## Infrastructure Corrections (2026-03-24)

- **Scrapling MCP is available.** Use it first for any URL fetch. Server runs at `127.0.0.1:8473` and is live. mcporter requires explicit config flag to find it:
  ```
  mcporter --config /Users/apollo/.openclaw/workspace/config/mcporter.json call scrapling.get url=<URL> extraction_type=text --output json
  mcporter --config /Users/apollo/.openclaw/workspace/config/mcporter.json call scrapling.fetch url=<URL> extraction_type=text --output json
  mcporter --config /Users/apollo/.openclaw/workspace/config/mcporter.json call scrapling.stealthy_fetch url=<URL> solve_cloudflare=true --output json
  ```
  Without `--config`, mcporter reports "Unknown MCP server 'scrapling'" even though the server is running.
- **X API is a paid tier.** Bearer token in `/Users/apollo/.openclaw/credentials/x_api.json`. Use it for reading posts, threads, and user content before reaching for web scraping. The `read_x_post.py` script is at `channels/marketing/scripts/read_x_post.py` but hardcodes `/root/` — pass the correct credentials path manually if needed.

---

## Ahrefs Integration

- **Access method:** Cookie-based (Cloudflare Turnstile blocks headless login; cookies are IP/session-bound so injection doesn't work either)
- **Credentials:** `/Users/apollo/.openclaw/credentials/ahrefs.json` (login), `/Users/apollo/.openclaw/credentials/ahrefs_cookies.json` (session cookies — expire, need re-export)
- **Practical workflow:** Export CSV from Ahrefs → drop in `ahrefs-exports/` → run `python3 scripts/ahrefs_process.py --latest --business <name>`
- **Intake dir:** `ahrefs-exports/` — see `ahrefs-exports/README.md` for export instructions
- **Processor script:** `scripts/ahrefs_process.py` — auto-detects: Keyword Explorer, Site Explorer Organic Keywords, Content Gap. Outputs `.report.md` alongside the CSV.
- **Cloudflare /crawl endpoint:** Launched March 10, 2026. Useful for crawling public competitor pages (not Ahrefs — requires auth). Worth using for competitive intel on barnabas.coach competitors, Etsy/Amazon listings, bushcraft sites.

## Active Automations

| System | Cron | Status | Notes |
|---|---|---|---|
| Barnabas Reddit Scanner | Daily 4pm PST | ✅ Live | `scripts/barnabas_reddit_scan.py` |
| Competitor Negative Reviews Report | Monday 7am PST | ✅ Live | `scripts/negative_reviews_report.py` — HTML email, App Store reviews only; Etsy/Amazon pending |
| Morse Command ASA Daily Report | Daily 8am PST | ⏸ Paused (2026-04-17) | `scripts/asa_daily_report.py` — cron removed while campaign is paused. Re-add when campaign resumes. |

## Apple Search Ads — Morse Command Campaign

**Credentials:**
- Config: `/Users/apollo/.openclaw/credentials/apple_search_ads.json`
- Private key: `/Users/apollo/.openclaw/agents/marketing/apple_ads_private.pem`
- Public key: `/Users/apollo/.openclaw/agents/marketing/apple_ads_public.pem`

**Account:**
- Org name: Aaron Williams App Store Ads
- Org ID: `21160890`
- Client ID / Team ID: `SEARCHADS.402b03a1-21a7-491f-ad76-e85e0e2f6b4f`
- Key ID: `3e0539f4-1a15-41f8-8180-a28129482ee5`

**Campaign:**
- Name: US Morse Command Campaign
- Campaign ID: `2143622293`
- Ad Group: MCAdGroup1 (ID: `2147335247`)
- App Adam ID: `6759479305`
- Budget: $15/day
- Dates: Apr 2 – Apr 15, 2026 (⏸ paused as of 2026-04-17)
- Targeting: US, iPhone + iPad, ages 25–54, excludes existing app users
- Bidding: Manual CPT
- Keywords: 20 keywords (morse code app, learn morse code, morse code game, cw trainer, ham radio app, etc.)

**Bid history:**
- Apr 1 launch: $1.00 CPT (all keywords) — zero impressions
- Apr 2 08:44 PDT: Raised to **$1.65 CPT** via API (ad group default bid). Zero impressions after 24hrs was the trigger.
- If still zero by end of Apr 2: raise to $2.00

**Auth flow:** OAuth 2.0. Generate JWT from private key → POST to `https://appleid.apple.com/auth/oauth2/token` with scope `searchadsorg` → bearer token valid 1hr. API base: `https://api.searchads.apple.com/api/v5/`

## Content Format Libraries

Created 2026-03-14 by Dru. Each business agent has a `references/content-formats.md` in their own workspace. Agents should load this file before generating any content.

| Agent | File |
|---|---|
| Spark (Glimmer Cards) | `channels/glimmer/references/content-formats.md` |
| Dash (Morse Command) | `channels/morse-command/references/content-formats.md` |
| Barrett (Barnabas Coaching) | `channels/barnabas-coaching/references/content-formats.md` |
| Forge (Black Raven) | `channels/black-raven/references/content-formats.md` |

Contents: brand voice snapshot, audience primer, platform priority stack, 4–6 named post formats per platform (with full templates + concrete examples), and anti-patterns ("what never to do").

Maven does NOT need to re-deliver this content to agents — they own it. Maven's role is strategic updates when something changes (new platform, new campaign direction, lessons learned).

---

## Active Campaigns

| Campaign | Business | Channel | Status | KPIs | Notes |
|---|---|---|---|---|---|
| X Content Pilot | Morse Command | X (@MorseCommand) | 🟡 Week 1 pending Aaron review | Impressions, follows, replies | Weekly batch review model — Aaron approves Sunday, posts schedule automatically |
| **Merkle & Bloom Content Launch** | **Merkle & Bloom** | **Website + AI tracking** | **🟢 8 pieces drafted, awaiting review** | **N/A** | **4 service pages + 4 blog posts ready; Rightcited check pending; Bing Webmaster setup pending** |

---

## Marketing Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-03-25 | Morse Command X pilot launched — weekly batch review model | Aaron reviews + approves post batch on Sundays; Buffer posts on schedule. Low-touch, high-trust after initial 2-week calibration. Template for Barnabas et al once MC pilot holds up. |
| 2026-03-25 | Approval cadence: weekly batch, not per-post | Aaron's time constraint. Agent drafts, Aaron reviews once/week, approves in bulk. |
| 2026-03-14 | Marketing channel created as shared resource for all agents | Centralize marketing knowledge and tactics so each channel agent doesn't reinvent the wheel |
| 2026-03-14 | Agents channel posting via `post_to_agents.py` script, not `message` tool | `message` tool (channel=vantage) can't target agents channel by slug — no bound session. Direct vantage.message RPC via WebSocket works. Script at `scripts/post_to_agents.py`. |
| 2026-03-14 | Reading X posts: use `scripts/read_x_post.py`, NOT web_fetch or browser | web_fetch always fails on x.com (JS-gated). X API v2 with bearer token works. Script handles root tweet + thread. See `references/read-x-posts.md`. |

---

## Shared Resources

### Platform Account Inventory

| Platform | Barnabas | Glimmer | Morse Command | Black Raven |
|---|---|---|---|---|
| TikTok | ❌ | ❌ | ❌ | ❌ |
| Instagram | ❌ | ❌ | ❌ | ❌ |
| YouTube | ❌ | ❌ | ❌ | ❌ |
| LinkedIn | ❌ (personal) | N/A | N/A | N/A |
| X/Twitter | N/A | ❌ | @AlricEdryk (partial) | ❌ |
| Email list | ❌ | ❌ | ❌ | ❌ |

_Update as accounts are created._

### Email Infrastructure
- Outbound address: drubot@posteo.com (for agent-sent outreach)
- Script: `/Users/apollo/.openclaw/workspace/scripts/send_email.py`

### Scraping / Research Infrastructure
- Scrapling MCP: `127.0.0.1:8473` — anti-bot scraping for influencer research and competitive analysis
- X API: `/Users/apollo/.openclaw/credentials/x_api.json` (read/write, authorized as @AlricEdryk)

---

## Playbooks (Reference)

### Influencer Outreach Template (Rave/Festival — Glimmer)
```
Subject: Glimmer Cards — want to send you some?

Hey [Name],

Love what you're doing at [specific show/event content]. I'm Spark from Glimmer Cards — we make
small compliment cards people hand out at shows. The idea: one card, one glimmer, one moment 
someone feels genuinely seen.

Aaron and Lily (the founders) hand these out at raves themselves. It's a real thing, not 
a marketing stunt.

Would love to send you a pack, no strings. If you love them and want to share, amazing. 
If not, enjoy the cards anyway.

Want me to drop your address?

— Spark @ Glimmer Cards
spark@letsgoglimmer.com
```

### Influencer Outreach Template (Ham Radio — Morse Command)
```
Subject: Morse Command — iOS game for CW operators

Hey [Name],

Big fan of your channel — [specific video reference].

I'm Dash from Morse Command. We built an asteroid-style iOS game that teaches Morse via 
the Koch method. It's tactically fun — built for people who actually know what CW is.

Currently in TestFlight, launching on the App Store soon. Want early access? Happy to set 
you up as a tester and hear what you think.

— Dash @ Morse Command
```

### LinkedIn Post Framework (Barnabas Coaching — Aaron's Voice)
```
[Hook: one sentence, specific claim or contrarian take]

[2-3 sentences expanding the point, concrete detail]

[The real insight — what Aaron actually believes after 25 years in tech]

[CTA: subtle. "If this resonates, my DMs are open." or "Full post on the site [link]"]
```

---

## Writing Rules (Aaron's Preferences)

These apply to ALL public-facing copy across every business:

- **No em dashes** — never use `—` in public writing. Rewrite the sentence instead.
- **Always run through unslop** — apply `references/unslop-writing.md` to every piece of copy before delivering. No exceptions.
- **No common AI words/phrases** — this includes but is not limited to: landscape, paradigm, leverage, robust, seamless, ecosystem, holistic, nuanced, compelling, innovative, crucial, essential, delve, navigate (metaphorical), unlock (metaphorical), transformative, game-changing, remarkable, fascinating. See full list in `references/unslop-writing.md`.
- **No slop structures** — no broad world-state openers, no "here's the thing," no "at the end of the day," no dramatic one-sentence kickers. See full list in `references/unslop-writing.md`.

_Set: 2026-03-20_

## Aaron's Voice Profile

Source: Reddit post r/amateurradio (written by Aaron as K1AXP, announcing Morse Command)

**Tone:** Direct, informal, technically specific. Writes like he's talking to a peer, not an audience. No performance. No hype.

**Key traits:**
- Leads with what the thing IS and HOW it works, not why it's amazing
- Specific numbers and mechanics over adjectives ("80 levels, 8 boss battles," "starts at 20 WPM," "Koch method")
- Self-aware humor, brief and dry ("jk, I'm just jealous of anyone that fast!")
- Honest about what it is and isn't ("Current version is 'copy only' but lots more in the works")
- Credit where it's due, genuinely ("Big shoutout to r/hamradio")
- Closes with a community sign-off, not a sales pitch ("73 de K1AXP")
- Short paragraphs. One idea per paragraph. No padding.
- Uses parenthetical asides for texture, not for hedging

**What he does NOT do:**
- No superlatives ("incredible," "amazing," "game-changing")
- No vague benefit statements ("helps you grow," "takes your skills to the next level")
- No throat-clearing before getting to the point
- No fake urgency or FOMO
- No corporate we when he means I
- No job titles. Let the reader fill in the picture themselves.

**Application:** When writing in Aaron's voice (LinkedIn posts, landing pages, site copy, community posts), match this register. Specific over vague. Peer-to-peer over brand-to-customer. Dry humor welcome, sparingly. Let the product speak through its details, not through adjectives about the product.

_Set: 2026-03-20_

---

## Lessons

_(Add entries as they emerge)_

---

_This is the marketing brain. Keep it current._
