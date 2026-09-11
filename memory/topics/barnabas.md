# Barnabas Coaching — L2 Detail

## Business

- Brand: Barnabas Coaching. Aaron as named expert. Domain: barnabas.coach (live).
- Target: Seattle-area SMBs, 10–200 people.
- Services: AI Audit $2,500 one-time; Coaching Retainer $1,500/month (2 calls + async).

## Deploy Stack

- Framework: Astro static site → `projects/barnabas-coaching/`
- Build: `npm run build`
- Deploy: `rsync -avz --delete dist/ barnabas.coach:/home/barnabas/html`

## Team

- **Aaron** — founder/coach
- **Chris B.** — TPM, Microsoft background
- **Michelle W.** — Director of PMO, Microsoft Legal; also Merkle and Bloom PM
- All 3 were at Microsoft simultaneously — core narrative hook for credibility.

## Buzz (Block/Jack Dorsey) — candidate offering infra

- https://github.com/block/buzz — free, Apache 2.0, self-hostable Nostr-based workspace: Slack/GitHub/workflows in one, AI agents as channel members with own keys + signed audit log.
- Not a harness (OpenClaw/Claude Code run agents); Buzz is the workplace they plug into via buzz-cli + ACP (supports Claude Code, Codex, Goose). OpenClaw not natively supported; would need custom glue.
- Status as of 2026-09-08: young (launched ~2026-07-21), desktop client only (v0.5.23), mobile/push "being wired up", 1.5k open issues.
- Position: NOT for our own stack (OpenClaw covers it). Candidate for Barnabas clients: self-hosted "AI team member with a paper trail" — data sovereignty pitch for biotechs. Revisit ~Nov 2026 once mobile + workflow gates stabilize.
- Runbook shape: small server w/ Docker (docker-compose ships relay+Postgres+Redis), subdomain = workspace, keypair identities, start ONE agent w/ ONE job (morning brief → human 👍), scope agents by channel membership, 90-min staff training, ~$3-5k setup + $500-1k/mo retainer. Pilot framing: 60-day proof.
- Aaron testing it himself — reminder set for noon 2026-09-08.

## Aaron's Credibility Bullets

- VoIP routing code, late '90s
- TPM for MSN Messenger at age 24
- Accenture consultant (built Microsoft training programs)
- Director of IT for prominent Seattle exec (NDA)
- 8 years biotech IT consulting
- Built Morse Command with AI
