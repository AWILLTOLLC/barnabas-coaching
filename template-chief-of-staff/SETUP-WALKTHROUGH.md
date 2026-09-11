# SETUP-WALKTHROUGH.md — Per-Customer Runbook

_For the installer. One pass per customer, start to finish. Estimated time: 30 to 45 minutes plus onboarding conversation._

## What you need before starting

- A DigitalOcean account with billing set up
- An SSH key pair on your laptop (or willingness to create one)
- The OpenClaw droplet image or a snapshot with OpenClaw pre-installed and configured
- `template-chief-of-staff/FULLINSTRUCTIONS.md` from this package

---

## Step 1: Create the droplet

1. DigitalOcean → Create → Droplets.
2. **Region:** closest to the customer.
3. **Image:** bare Ubuntu 24.04 LTS — the default path (droplet #1's DO marketplace image proved unstable; see LESSONS-LEARNED.md). The marketplace image remains a supported secondary path.
4. **Size:** 2 to 4 GB RAM is plenty for one agent instance. Start small; resize later if needed.
5. **Authentication:** SSH key. Do not use a password.
6. Note the droplet's public IP.

## Step 2: SSH in and seed the agent

All commands run from your laptop unless noted.

**First, run the first-run script on the droplet.** It now handles both bare Ubuntu 24.04 images and the DO OpenClaw marketplace image (auto-detected by the presence of the `openclaw.service` unit): OS upgrade, Node 24 LTS, OpenClaw via npm, `openclaw` user + systemd unit on bare images, legacy-state archiving on marketplace images, a persisted gateway auth token, and gateway verification.

```bash
# from your laptop
scp template-chief-of-staff/first-run.sh root@<DROPLET_IP>:/root/first-run.sh
ssh root@<DROPLET_IP> 'bash /root/first-run.sh'
```

Things the script handles that you should know about (learned the hard way on droplets #1 and #2):

- **It does NOT run `openclaw update`.** The DO image's custom unit makes the updater's doctor refuse, permanently. Updates go through `npm install -g openclaw@latest` on both image types.
- **Marketplace images ship legacy state files** (`workspace-state.json`, legacy `sessions.json`) that newer gateways refuse to boot with until migrated. The script archives them to `/root/legacy-migration-backup/` — harmless on a fresh droplet, never do that on a droplet with real usage.
- **Onboarding before the unit:** `openclaw doctor` refuses to run when a gateway systemd unit already exists, so the script initializes config BEFORE writing the unit, with a minimal local-mode fallback config if onboarding produces nothing.
- **Auth token is persisted.** Without `gateway.auth.token` the gateway mints a new runtime token each start and pairing breaks. Retrieve it with:
  `sudo -u openclaw openclaw config get gateway.auth.token`
- **Bare-image re-runs are safe** — detection is by unit file, not user, so re-running the script skips onboarding/unit creation and just verifies the gateway.
- **No SSH here.** Bare images expose SSH by default with no hardening; do the UFW/fail2ban pass before handing the droplet to a customer (see `FULLINSTRUCTIONS.md` security section).

Then seed the agent:

```bash
# 1. Connect
ssh root@<DROPLET_IP>

# 2. Verify OpenClaw is alive (on the droplet)
openclaw --version
systemctl is-active openclaw.service
ss -tlnp | grep 18789

# 3. Push the workspace template (full tarball, not just FULLINSTRUCTIONS.md)
#    Built from templatefiles/ in this package — see the rebuild script.
scp template-chief-of-staff/chief-template.tar.gz root@<DROPLET_IP>:/tmp/
ssh root@<DROPLET_IP> 'tar -xzf /tmp/chief-template.tar.gz -C /home/openclaw/.openclaw/workspace/ && rm -f /home/openclaw/.openclaw/workspace/BOOTSTRAP.md && chown -R openclaw:openclaw /home/openclaw/.openclaw'
```

On DO-image droplets the workspace lives at `/home/openclaw/.openclaw/workspace/` and the gateway runs as the `openclaw` user via the system unit `openclaw.service` — not as root, and not as a user-level service. Adjust the path only if a future image changes this. Do not modify `openclaw.json` (per-customer model config, see Step 3.5).

4. Back on the droplet, or via the webchat UI, send the agent exactly one message:

> Read FULLINSTRUCTIONS.md in your workspace and follow it.

5. Open the customer's access to the webchat/Control UI. Follow `OWNER-ACCESS-WALKTHROUGH.html` for the exact sequence. Do not invent pairing flags: the Control UI is served by the gateway at `http://<host>:18789/`; sign-in uses the persisted `gateway.auth.token` (`sudo -u openclaw openclaw config get gateway.auth.token`); a first connection from a new browser needs one-time device pairing (`sudo -u openclaw openclaw dashboard` prints a single-use pairing link, or `devices list` → `devices approve <requestId>`). Confirm the URL works from the customer's own browser before moving on.

## Step 2.5: Model provider

A fresh install has **no model provider configured**, and its default model is a placeholder (`openai/gpt-5.6-sol`) routing to a provider with no key — so **every agent turn fails** with `No route-compatible authentication source is configured for openai` until both are fixed. Key collection happens on the 1:1 customer call (never email/chat; the Management Key never goes on a droplet — see `OWNER-ACCESS-WALKTHROUGH.html`).

1. On the call, have the customer create an OpenRouter account, add credits, and generate an API key.
2. Paste it directly (hidden prompt; the key is never echoed, logged, or sent anywhere):

```bash
bash /root/add-provider-keys.sh    # run as root on the droplet
```

   Wait for `PROVIDER-PROOF-OK` — the script stages the key at mode 600, wires it into config as a SecretRef, proves the route, then removes the staged file.
3. Point the default model at the configured provider, using the provider-qualified ID (display names don't resolve in TUI `/model` swaps either):

```bash
sudo -u openclaw openclaw config set agents.defaults.model.primary openrouter/z-ai/glm-5.3-flash
```

4. Prove the agent answers: `sudo -u openclaw openclaw agent --message "Reply with exactly: ALIVE-OK"`.

## Step 3: Onboarding conversation

Sit with the customer (call or in person) while the agent runs its first-boot protocol. Your part:

- Tell the agent: "This is [customer name], your new owner. Introduce yourself and get the basics from them."
- Let the agent ask its questions: name, business, timezone, boundaries.
- Prompt the customer to give one or two real current priorities so the agent has something real in its "Right now" header on day one.

The agent should end this step having written USER.md, created today's daily note, and updated MEMORY-L0.md. Watch it happen; do not take it on faith.

## Step 4: Verification checklist

- [ ] Agent replied with an introduction and asked for name/business/timezone
- [ ] USER.md filled in with the customer's answers, no placeholders left for known facts
- [ ] `memory/` directory exists with MEMORY-L0.md and today's daily note
- [ ] MEMORY-L0.md has a populated "Right now" header
- [ ] DECISIONS.md and ERRORS.md exist as empty scaffolds
- [ ] Agent correctly answered one question about something the customer just told it (memory write worked)
- [ ] Webchat reachable from the customer's browser (not just yours)

## Step 5: Post-setup options

Tell the customer these exist but don't set them up unless asked:

- **More channels:** Telegram, WhatsApp, and similar can be connected later, each with its own setup steps in the installed docs.
- **Scheduled maintenance:** the nightly consolidation and weekly pattern automations from FULLINSTRUCTIONS.md (11pm local / weekly), configured after the first week of real usage.
- **Where the template lives:** FULLINSTRUCTIONS.md stays in the agent's workspace permanently as reference. The source package (all three files) lives in your own copy of `template-chief-of-staff/`; keep it updated as you learn from each customer.
- **Updates:** check `openclaw docs` for the update procedure on the image; schedule updates with the customer rather than patching mid-conversation.

---

## Troubleshooting

**Gateway not running.** Run `systemctl status openclaw.service` and `ss -tlnp | grep 18789`. If stopped, start it with `systemctl start openclaw.service` and check `journalctl -u openclaw.service`. Do not hand-edit config to "fix" it.

**"Update available" banner won't clear.** Run `npm install -g --allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs openclaw@latest` as root, then `systemctl restart openclaw.service`. Do NOT use `openclaw update` on DO-image droplets — its doctor step permanently fails against the image's custom service unit (see Step 2).

**Gateway won't boot after update: "Legacy ... requires migration".** A leftover DO-image state file is blocking boot. Stop the service, move the named file to `/root/legacy-migration-backup/` (first-run.sh already does this for the known ones), restart. On a fresh droplet these files hold only bootstrap scaffolding; never do this on a droplet with real usage — those stores hold sessions and state.

**`openclaw doctor --fix` refuses: "service ownership ... could not be verified".** Expected on DO-image droplets; the doctor only trusts services it installed itself. Don't fight it — verify health with `systemctl is-active openclaw.service`, `ss -tlnp | grep 18789`, and `openclaw gateway status` instead.

**Agent asks you (the installer) instead of the customer.** Remind it: "Your owner is [customer name]. Direct your questions to them," and note it for the template if it happens more than once.

**Anything else.** Check `openclaw docs` first. If the docs are silent, note the gap for the template package rather than improvising on the customer's machine.

**Agent didn't pick up FULLINSTRUCTIONS.md.** Verify the file landed with `ls -la /home/openclaw/.openclaw/workspace/`. Then resend the exact trigger message. If still silent, check the workspace path matches where the agent actually reads (see `openclaw docs` on workspace layout).
