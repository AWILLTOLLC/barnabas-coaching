# MEMORY.md — Barrett, Barnabas Coaching Agent

## Memory Storage Rules

All memory files live **in this directory only.**

Naming convention: `MEMORY-barnabas-coaching-YYYY-MM-DD-HHMM.md`

**Never write to:**
- Main workspace `MEMORY.md`
- Main workspace `memory/` folder
- Other channel workspaces

Write a memory file: at end of session, when a decision is made, when you learn something important about a client, or when Aaron corrects you.

---

## Current Business State (as of 2026-03-12)

### Status
- Site is live at barnabas.coach
- No confirmed clients yet — pre-revenue stage
- Aaron is actively building toward first paying client
- Blog section exists but no posts published yet

### Services (live, priced, on site)
- **AI Audit:** $2,500 one-time
  - 7-10 day engagement (updated 2026-03-13; was previously listed as 30-day — corrected by Aaron)
  - Intake interview (90 min, structured)
  - Workflow mapping
  - Written assessment report (jargon-free, owner-readable)
  - Prioritized recommendations
  - Tool & vendor guidance
  - Debrief call (60 min)
- **Coaching Retainer:** $1,500/month, 3-month minimum
  - 2 × 60-min strategy calls/month
  - Async support between calls
  - Tool/vendor recommendations
  - Implementation review
  - Flexible monthly focus
- **Entry point:** Free 30-minute discovery call (no pitch — genuine conversation)

### Site Structure
- `/` — hero, services overview, why Barnabas, Aaron intro teaser, CTA
- `/services` — full AI Audit + Coaching Retainer detail, FAQ
- `/about` — Aaron's full story, career timeline, team section
- `/contact` — discovery call booking
- `/blog` — empty, ready for posts
- `/thanks` — post-form submission page

### Brand Colors
- Navy: `#0E1F3D`
- Gold: `#C08B3A`
- Muted blue: `#8fa6c4`

### Tech Stack
- Framework: Astro (static site)
- Styles: TailwindCSS inline
- Server: barnabas.coach (SSH key auth), Caddy, web root `/home/barnabas/html`
- Deploy: `npm run build` → `rsync -avz --delete dist/ barnabas.coach:/home/barnabas/html/`
- Source: `/Users/apollo/.openclaw/workspace/projects/barnabas-coaching/`

---

## The Team (Established)

- **Aaron Williams** — founder, coach, named expert. 25+ years in tech. Microsoft TPM (MSN Messenger, joined at 24). VoIP infrastructure in late '90s. Accenture. 8-yr trusted advisor to Seattle exec (NDA). 8 years biotech IT. Now AI builder and coach.
- **Chris B.** — co-advisor. VoIP startup co-worker with Aaron in late '90s. TPM at Microsoft (InfoPath, SharePoint). Technical program management depth.
- **Michelle W.** — co-advisor/operations. Founded and led PMO at Washington state's fastest-growing consulting firm (8 PMs + 20 hrs/week billable). Microsoft Legal team simultaneously with Aaron and Chris. Senior PM + systems analyst at Merkle and Bloom (Aaron's S-corp) for 5 years.

**Key narrative hook:** All 3 at Microsoft at the same time, from 3 different functional angles.

---

## Brand Positioning (Established)

- **Not** a vendor, tool reseller, or enthusiast
- An operator who has built and deployed AI systems and can distinguish signal from noise
- Distinguishing claim: honest about what AI *can't* do, including "not yet" and "not worth your time"
- Comparison to VoIP/internet wave: Aaron was there before it had a name. Pattern recognition is the product.
- Target: Seattle SMB owners 5–200 employees who know AI matters but don't know where to start

---

## Pending / Open Items

- [ ] First client acquisition — no leads confirmed as of 2026-03-12
- [x] Blog: first post published 2026-03-13 — "5 AI Mistakes Small Business Owners Keep Making" at /blog/5-ai-mistakes-small-business-owners-keep-making
- [ ] LinkedIn: no active presence set up for the brand yet
- [ ] Photos: team section uses initials avatars as placeholders; swap when photos available
- [x] Discovery call booking system: contact form wired to calendar — confirmed working (tested 2026-03-12)

---

## Lessons / Corrections

### 2026-03-20 — Deploy permissions bug + rsync fix
macOS ships `openrsync` which does NOT support `--chmod`. Homebrew rsync (`/opt/homebrew/bin/rsync`) is installed and must be used explicitly. Always use `/opt/homebrew/bin/rsync -avz --delete --chmod=D755,F644 -e "ssh -i ~/.ssh/id_ed25519"`. On this server (Caddy), directories need `755` and files need `644` or the web server returns Access Denied. Always run a post-deploy curl check: `curl -o /dev/null -s -w "%{http_code}" https://barnabas.coach` — must return 200. If not, fix permissions with `ssh -i ~/.ssh/id_ed25519 barnabas@barnabas.coach "find /home/barnabas/html -type d -exec chmod 755 {} \; && find /home/barnabas/html -type f -exec chmod 644 {} \;"`.

### 2026-03-20 — Seattle landing page
Added `/ai-consulting-seattle` — geo-targeted SEO page. Linked from footer and Services page CTA. Page includes LocalBusiness+Service schema with 5-city areaServed.

### 2026-03-20 — Schema markup added
Added dual-type `LocalBusiness`+`ProfessionalService` schema and `Person` schema for Aaron globally in Layout.astro. GBP sameAs: `https://share.google/MIAykB7sQYifXkmY8`. LinkedIn: `https://linkedin.com/in/kaaronw`. No physical address (virtual business). Aaron's URL points to `/about`.

### 2026-03-20 — SSH key
Server auth uses `~/.ssh/id_ed25519` explicitly. SSH agent may not have identities loaded — always pass `-i ~/.ssh/id_ed25519` to ssh/rsync commands.

## Client Signal System (Behavioral RL)

Infrastructure built 2026-03-13. Grounded in Princeton research (online RL for agents).

**Core principle:** Every coaching session generates implicit signal. We capture it instead of discarding it.
- Client re-asks prior question = our recommendation didn't land → adjust approach
- Client reports implementation = our recommendation worked → reinforce pattern
- Client resists = wrong fit for this client type/industry → note for cross-client learning

**Files:**
- Per-client logs: `client-profiles/<client-id>.jsonl`
- Schema: `client-profiles/SCHEMA.md`
- Script: `scripts/client_signals.py`

**Long-term goal:** After 10+ clients, the system will surface: which advice lands for which industry, which client types need different framing, which recommendations have highest implementation rates. This is differentiated — no other AI consultant is building this.

**Commercial framing for Aaron:** "Our coaching system learns from every client interaction. The longer you work with us, the more calibrated our advice becomes to your specific business context."
