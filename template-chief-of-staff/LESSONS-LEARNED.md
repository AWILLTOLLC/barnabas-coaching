# LESSONS-LEARNED.md — error log from both droplets

_Complete record of every failure, root cause, and where the fix now lives. Read before deviating from SETUP-WALKTHROUGH.md. Pair with `OWNER-ACCESS-WALKTHROUGH.html` (the access-grant runbook) and `DROPLET-BUILD-LOG.md` (the raw build record)._

## Droplet #1 — DO marketplace image, 134.209.217.142 (2026-09-09/10)

**What happened:** the DO OpenClaw marketplace droplet was unstable through the whole session — gateway crash loops and repeated `SessionStoreMigrationRequiredError` after upgrades, compounded by the image's custom systemd unit that permanently blocks `openclaw update` (doctor classifies the unit as "foreign" and refuses maintenance) and legacy state files that block boot until migrated.

**Root cause:** the image ships a pre-built unit + legacy state that fight the current gateway's migration and ownership model.

**Fix / where baked in:** first-run.sh archives legacy state files and works on both image types, but the **template now targets bare Ubuntu 24.04 as the default path** (Step 1 of SETUP-WALKTHROUGH.md; README). Marketplace image remains a supported-but-secondary path. The full fix gauntlet for droplet #1 is in DROPLET-BUILD-LOG.md §"The gauntlet of fixes" (Node version, npm-only updates, legacy-state archiving, `trustedProxies` needing `127.0.0.1` **and** `::1`, don't trust `gateway status` on image droplets).

## Droplet #2 — bare Ubuntu 24.04, 143.198.151.243 (2026-09-10)

Customer Jeff, agent named **Rambo**. Errors 1–9 below all come from this run.

**1. Fresh bare install has no model provider.**
- *What happened:* first-run.sh never covered model auth; the agent couldn't run a single turn: `No route-compatible authentication source is configured for openai`.
- *Root cause:* model-provider wiring was treated as a per-customer open item, but the installer path had no scripted step for it.
- *Fix:* `add-provider-keys.sh` — hidden-prompt key entry, 0600 staging, SecretRef wiring via `openclaw config set`, `PROVIDER-PROOF-OK` route probe, staged-key cleanup.
- *Baked in:* SETUP-WALKTHROUGH.md Step 2.5; OWNER-ACCESS-WALKTHROUGH.html §1/§3a.

**2. The fresh-install default model is a placeholder.**
- *What happened:* every default-model turn failed even after the provider key was in — the shipped default (`openai/gpt-5.6-sol`) routes to a provider with no key.
- *Root cause:* default model points at a provider that isn't configured.
- *Fix:* set the default to a model on the configured provider, with the provider-qualified ID:
  `sudo -u openclaw openclaw config set agents.defaults.model.primary openrouter/z-ai/glm-5.3-flash`
- *Baked in:* SETUP-WALKTHROUGH.md Step 2.5; OWNER-ACCESS-WALKTHROUGH.html §1 pre-flight + §5 troubleshooting.

**3. `openclaw doctor --fix` refuses when a systemd unit already exists** ("Gateway service ownership could not be verified").
- *Root cause:* the doctor only trusts services it installed itself; onboarding (which runs doctor) after unit creation is refused forever on that config.
- *Fix:* **onboarding must precede unit creation.** first-run.sh initializes config before writing the unit.
- *Baked in:* first-run.sh ordering; SETUP-WALKTHROUGH.md Step 2 notes.

**4. `set -e` + `systemctl is-active` returning `activating` mid-boot aborts the script.**
- *Root cause:* `is-active` returns non-zero for `activating`, and the script ran under `set -e`.
- *Fix:* replaced with a retry loop (10s intervals) that waits for the gateway to settle.
- *Baked in:* first-run.sh (10s gateway wait loop).

**5. Without a persisted `gateway.auth.token`, pairing breaks across restarts.**
- *Root cause:* token mode with no configured token mints an ephemeral runtime token each start — unrecoverable, so browsers can't re-auth.
- *Fix:* first-run.sh persists `gateway.auth.token` (mode 600). Retrieve with `sudo -u openclaw openclaw config get gateway.auth.token`.
- *Baked in:* first-run.sh; SETUP-WALKTHROUGH.md Step 2 notes; OWNER-ACCESS-WALKTHROUGH.html §1/§5.

**6. Running `openclaw tui`/CLI as root → "unauthorized: gateway token mismatch".**
- *Root cause:* root's config lacks the token; the gateway config belongs to the `openclaw` user.
- *Fix:* always `sudo -u openclaw openclaw tui` (and `sudo -u openclaw` for every gateway CLI call).
- *Baked in:* OWNER-ACCESS-WALKTHROUGH.html §1/§2/§5; SETUP-WALKTHROUGH.md examples.

**7. Bare-vs-marketplace detection by user existence misdetects on re-runs.**
- *Root cause:* on a re-run the `openclaw` user already exists regardless of image, so user-based detection flips paths.
- *Fix:* detect by unit file presence instead.
- *Baked in:* first-run.sh (unit-file-based detection).

**8. TUI `/model` swaps need the provider-qualified model ID.**
- *What happened:* display names don't resolve; e.g. use `openrouter/z-ai/glm-5.3-flash`, not "GLM".
- *Baked in:* SETUP-WALKTHROUGH.md Step 2.5; OWNER-ACCESS-WALKTHROUGH.html §1/§2.

**9. Model-provider credential collection moved to the human 1:1 call.**
- *What happened:* "whose key, whose bill" (droplet #1 open item) had no process; credentials must never travel by email/chat, and the Management Key must never live on a droplet.
- *Fix:* installer runs setup to a defined checkpoint; on the call the customer creates the OpenRouter account, adds credits, generates the key, and the installer pastes it directly via `add-provider-keys.sh` (hidden prompt). Management Key stays in the operator's password manager.
- *Baked in:* SETUP-WALKTHROUGH.md Step 2.5; OWNER-ACCESS-WALKTHROUGH.html (whole runbook is built on this split); README new-build checklist.

## Process changes (not errors, but changed how we ship)

- **Installer-runbook split:** setup-to-checkpoint (installer) and key collection + access grant (1:1 call) are separate phases with separate docs: SETUP-WALKTHROUGH.md vs OWNER-ACCESS-WALKTHROUGH.html.
- **Customer agent naming is per-customer** (this run: "Rambo") while template docs stay generic (default "Chief") — the workspace template is not rebuilt per customer; IDENTITY.md naming happens on the droplet during setup.
- **Two droplets, two images:** marketplace instability pushed the default path to bare Ubuntu 24.04; first-run.sh stays image-agnostic and detects by unit file.
- **Cron template validated:** SETUP-CRONS.md's 9-job set deployed successfully on the old droplet before deletion; treat it as proven, deploy after the customer's first real week.
