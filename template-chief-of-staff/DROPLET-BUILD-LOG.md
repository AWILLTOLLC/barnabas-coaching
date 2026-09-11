# Chief-of-Staff Template & Droplet — Full Build Log

<!-- project: github.com/AWILLTOLLC/barnabas-coaching -->
_Created 2026-09-09. Product: "Chief of Staff" OpenClaw template (from Agent Workshop). First test customer: Jeff. Aaron sells pre-configured droplets: sanitized agent template on a DigitalOcean OpenClaw marketplace image._

## Package contents (`template-chief-of-staff/`)

- `FULLINSTRUCTIONS.md` — agent-facing first-boot instructions (verify + onboarding model, not self-build)
- `SETUP-WALKTHROUGH.md` — installer runbook, per-customer, 30–45 min. Includes DO-image troubleshooting section.
- `SANITIZATION-CHECKLIST.md` — forbidden-strings list + verification steps
- `first-run.sh` — run as root on fresh droplet. apt upgrade → Node 24 (NodeSource) → npm update of OpenClaw → archive legacy state → restart/verify gateway. Syntax-checked.
- `build-template.sh` — rebuilds `chief-template.tar.gz` from `templatefiles/` with a hard sanitization grep gate (forbidden strings: Dru, Aaron, Williams, Lily, Barnabas, kaw.cc, wizard, 🧙, hermes_quickguide, 100.65.203.16, tailb4a099, apollo, Fremont, Phinney, Black Raven, Glimmer, biotech, erasei). Refuses to build if any trip.
- `templatefiles/` — the sanitized workspace: SOUL.md, IDENTITY.md (agent name "Chief"), USER.md, AGENTS.md, DECISIONS.md, ERRORS.md, FULLINSTRUCTIONS.md, memory/{MEMORY-L0.md, instincts.md, daily-note-TEMPLATE.md}
- `chief-template.tar.gz` — built output, ships in the package.

## Template decisions (2026-09-09, Aaron-approved)

- Agent default name: **Chief**; business-agnostic (zero Barnabas content)
- Template = sanitized copy of Dru's workspace files, NOT a copy of Dru (no wizard persona, no memory content, no logs, no session DBs)
- Boot scope: webchat/Control UI only
- Delivery: pre-seeded workspace files (tar), not agent self-configuration (saves customer tokens)
- First-boot trigger message: *"Read FULLINSTRUCTIONS.md in your workspace and follow it."*

## DO droplet deployment (Jeff's test box)

**Droplet:** 134.209.217.142, hostname `BlankAgent`, Ubuntu 24.04.4, 2 vCPU / 3.8GB RAM / 116GB disk / 2GB swap (swap added during session). OpenClaw runs as `openclaw` user via system unit `/etc/systemd/system/openclaw.service`, gateway on 127.0.0.1:18789. Caddy (image-shipped) terminates TLS on 80/443 and reverse-proxies to `localhost:18789`. CLI wrapper `/opt/openclaw-cli.sh` injects gateway token for RPC commands. Workspace: `/home/openclaw/.openclaw/workspace/`.

**Access:** Aaron whitelisted home IP 174.127.233.74 in UFW (`allow from ... to any port 22 proto tcp comment 'Aarons-Macs'`) + fail2ban ignoreip + persistent `/etc/fail2ban/jail.d/ignoreip.local`. SSH: `ssh -i ~/.ssh/id_ed25519_barnabas_droplet -o IdentitiesOnly=yes root@134.209.217.142`. Note: rapid back-to-back SSH connections trip UFW LIMIT even when whitelisted — space connections out or batch into one call.

**Deployed:** full template tarball extracted into workspace, DO defaults backed up to `/root/workspace-defaults-backup-20260909.tar.gz`, BOOTSTRAP.md removed, all chowned openclaw:openclaw. Gateway healthy, Chief awaiting model config + Jeff pairing + first-boot message.

## The gauntlet of fixes (2026-09-09/10) — all baked into first-run.sh + walkthrough

1. **Node too old for `openclaw update`** (image ships Node 22; OpenClaw needs >=24.16 <25 or >=26.1). Fix: NodeSource 24.x install BEFORE updating OpenClaw.
2. **`openclaw update` permanently fails on DO-image droplets.** The image's custom systemd unit runs the gateway as the `openclaw` user; the updater's doctor classifies it as a "foreign" service (source check: `gatewayServiceCommandUsesRoot` → `kind: "foreign"` → refuses maintenance) and can never verify ownership. **Fix: update via `npm install -g --allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs openclaw@latest` as root, then restart the service.** Never use `openclaw update` on these droplets.
3. **Gateway refuses to boot after upgrade: "Legacy workspace setup state requires migration"** (and then "Legacy session store requires migration" — cascades). Doctor would migrate but is blocked by (2). On a FRESH droplet the legacy files hold only bootstrap scaffolding (no real data) — safe to archive. **Fix: stop service, `mv` the named files to `/root/legacy-migration-backup/`, restart.** Known files: `workspace/.openclaw/workspace-state.json`, `workspace/openclaw-workspace-state.json`, `.openclaw/agents/main/sessions/sessions.json`, `workspace/.attested`. NEVER do this on a droplet with real usage (those stores hold sessions/state).
4. **Web UI error `proxy_attribution_required`** after upgrading to 2026.9.x. Two-part fix in `/home/openclaw/.openclaw/openclaw.json`:
   - `gateway.trustedProxies` must contain BOTH `127.0.0.1` AND `::1` — Caddy connects to the gateway over IPv6 loopback, so IPv4-only trust leaves it "unattributable proxy-shaped traffic from ::1". This was the actual break.
   - The `gateway.auth.trustedProxy` block requires `userHeader` (string) as a mandatory field when present — schema validation fails boot without it. Patch used: `{"allowLoopback": true, "requiredHeaders": [], "userHeader": "x-forwarded-user"}` (inert while auth.mode stays local/token).
   - Backup of pre-fix config: `/root/openclaw.json.bak-proxy-fix` on the droplet.
5. **Don't trust `openclaw gateway status` "Runtime: stopped"** on DO droplets — it reports the user-level systemd view, which isn't how the image runs the gateway. Verify with `systemctl is-active openclaw.service` + `ss -tlnp | grep 18789`.

## Model/provider open item

> superseded 2026-09-10: resolved on droplet #2 — customer's OpenRouter key is collected at the 1:1 call via `add-provider-keys.sh`; default model set to `openrouter/z-ai/glm-5.3-flash`. See LESSONS-LEARNED.md #2/#9.

Chief's `openclaw.json` on the droplet still has the image's default model config; per-customer API key/billing decision (whose key, whose bill) is unresolved — deliberately left for the Jeff setup session.

## Droplet #2 (bare Ubuntu, 2026-09-10)

**Droplet:** 143.198.151.243, bare Ubuntu 24.04 (no marketplace image). Customer: Jeff. Agent name: **Rambo** (per-customer naming happens on the droplet; template default stays "Chief"). Gateway as `openclaw` user, `127.0.0.1:18789`.

`first-run.sh` went through **3 test rounds**; every fix below is baked into the script + walkthrough (full root-cause table in LESSONS-LEARNED.md).

**Round 1 — first bare install.** Script ran end to end but the agent couldn't complete a single turn: a fresh bare install ships **no model provider**, and the default model is a placeholder (`openai/gpt-5.6-sol`) routing to a provider with no key → `No route-compatible authentication source is configured for openai`. Also surfaced: `openclaw doctor --fix` refuses while a systemd unit exists ("Gateway service ownership could not be verified").
Fixes: onboarding moved BEFORE unit write; `add-provider-keys.sh` created (hidden prompt → 0600 staging → SecretRef → `PROVIDER-PROOF-OK` probe → cleanup); default model set via `sudo -u openclaw openclaw config set agents.defaults.model.primary openrouter/z-ai/glm-5.3-flash`.

**Round 2 — boot + re-run stability.** Two aborts: (a) `set -e` killed the script when `systemctl is-active` returned `activating` mid-boot → replaced with a 10s-interval retry wait loop; (b) bare-vs-marketplace detection by user existence misdetects on re-runs (the user exists either way) → detection switched to unit-file presence. Token persistence confirmed as mandatory: with no `gateway.auth.token` the gateway mints an unrecoverable runtime token each start, breaking pairing on every restart → token persisted (mode 600).

**Round 3 — clean verification.** Full re-run from scratch on the bare image: Node 24 + openclaw via npm, `openclaw` user + systemd unit, persisted token, onboarding before unit, gateway verified (`systemctl is-active` + `ss -tlnp | grep 18789`), provider proof OK, agent answering. Confirmed the root-terminal lesson: `openclaw tui`/CLI as root fails with `unauthorized: gateway token mismatch` — all gateway CLI calls run as `sudo -u openclaw`.

**Access grant** documented as `OWNER-ACCESS-WALKTHROUGH.html`: installer runs setup to a defined checkpoint, then the 1:1 call covers OpenRouter key collection + Control UI sign-in/one-time pairing in Jeff's own browser + first message to Rambo (FULLINSTRUCTIONS first boot: asks name/business/timezone, writes USER.md, daily note, L0 header). Process lessons: key collection lives in the human 1:1 call (never email/chat; Management Key stays in the operator's password manager). `SETUP-CRONS.md`'s 9-job cron template had already deployed successfully on droplet #1 before that droplet was deleted.

## Session survival notes

- `openclaw doctor --fix` is useless on DO-image droplets; health-check with `systemctl` + `ss` instead.
- Droplet journald has no persistent logs; gateway file logs at `/tmp/openclaw/openclaw-YYYY-MM-DD.log`.
- For the walkthrough/first-run.sh as shipped: these fixes are already encoded — don't re-derive.
- UFW whitelisting bypasses UFW LIMIT but NOT rapid-connection refusals observed via ssh.socket; keep SSH commands batched and short.