# Chief-of-Staff Template Package

Pre-configured OpenClaw droplet offering ("Chief of Staff" agent template, from the Agent Workshop). Build a new customer droplet in 30–45 min using these files. Default path: **bare Ubuntu 24.04** (two-droplet learning, 2026-09-09/10: the DO marketplace image proved unstable — see LESSONS-LEARNED.md).

## Contents

| File | Purpose |
|---|---|
| `SETUP-WALKTHROUGH.md` | **Start here.** Per-customer runbook: create droplet → run first-run.sh → configure → onboard. Includes troubleshooting section. |
| `CHANNELS.md` | Setting up common channels: WhatsApp (recommended), Signal, Matrix — decision table, install/link steps, cron delivery switch, customer talking points, troubleshooting. |
| `first-run.sh` | Run as root on a fresh droplet. Image-agnostic (bare Ubuntu 24.04 default, DO marketplace secondary; detects by unit file). apt upgrade, Node 24, npm-installs OpenClaw (NOT `openclaw update` — see build log), onboarding BEFORE unit write, persists `gateway.auth.token` (mode 600), 10s gateway wait + verification. |
| `add-provider-keys.sh` | Run as root on the droplet during the 1:1 call. Hidden-prompt OpenRouter key entry → 0600 staging → SecretRef wiring → `PROVIDER-PROOF-OK` route probe → staged-file cleanup. Never prints or logs the key. |
| `build-template.sh` | Rebuilds `chief-template.tar.gz` from `templatefiles/`. Refuses to build if sanitization gate trips. |
| `chief-template.tar.gz` | The sanitized workspace tarball extracted to the droplet. Rebuild after editing `templatefiles/`. |
| `templatefiles/` | Source of the workspace: SOUL.md, IDENTITY.md ("Chief"), USER.md, AGENTS.md, DECISIONS.md, ERRORS.md, FULLINSTRUCTIONS.md, memory scaffolding. |
| `FULLINSTRUCTIONS.md` | Agent-facing first-boot instructions. Trigger message: *"Read FULLINSTRUCTIONS.md in your workspace and follow it."* |
| `SANITIZATION-CHECKLIST.md` | Forbidden-strings list + verification steps before shipping. |
| `SETUP-CRONS.md` | 9-job cron template (nightly memory consolidation, index rebuild, dreaming promotion, context offload, context guard, weekly signal compression, survival test, skill collection review, heartbeat). Deployed successfully on droplet #1. |
| `OWNER-ACCESS-WALKTHROUGH.html` | Installer runbook for granting the customer gateway access: pre-flight, key collection on the 1:1 call, Control UI sign-in + pairing, verification, troubleshooting. |
| `LESSONS-LEARNED.md` | Complete error log from both droplets — what happened, root cause, fix, where baked in. Read before deviating. |
| `DROPLET-BUILD-LOG.md` | Raw build record: droplet #1 (134.209.217.142, marketplace image) and droplet #2 (143.198.151.243, bare Ubuntu). Read before deviating from the walkthrough. |

## New build checklist

1. Create a bare Ubuntu 24.04 droplet (region near customer). Marketplace image = secondary path only.
2. SSH in, run `first-run.sh` (backgrounded; it takes several minutes).
3. Extract `chief-template.tar.gz` into `/home/openclaw/.openclaw/workspace/`, chown openclaw:openclaw.
4. Model provider: customer's OpenRouter key via `add-provider-keys.sh` (collected on the 1:1 call — never email/chat), then set the default model to a provider-qualified ID (Step 2.5 of the walkthrough).
5. Grant the customer access per `OWNER-ACCESS-WALKTHROUGH.html` (gateway token + one-time pairing in the customer's own browser).
6. Send the first-boot trigger message, verify Chief responds per FULLINSTRUCTIONS.md.

## Known non-negotiables

- Sanitization gate must pass — no Dru/Aaron/Barnabas/kaw.cc/wizard/erasei strings in shipped files.
- Never `openclaw update` on DO-image droplets; npm only.
- `gateway.trustedProxies` needs both `127.0.0.1` and `::1` (Caddy connects over IPv6) — already in first-run.sh.
- Always run gateway CLI as `sudo -u openclaw openclaw …` — as root you get `unauthorized: gateway token mismatch`.
- A fresh install has no provider and a placeholder default model — wire the key (`add-provider-keys.sh`) and set the default model (Step 2.5) before the customer's first turn.
- Never collect model-provider credentials by email/chat; paste them on the 1:1 call via `add-provider-keys.sh`. The Management Key stays in the operator's password manager.
