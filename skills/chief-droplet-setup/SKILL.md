---
name: "chief-droplet-setup"
description: "SSH into and review a fresh customer OpenClaw droplet: connection stability (UFW limit, fail2ban, ssh.socket), hardening review, Chief template deployment."
---

# Chief Droplet Setup

SSH access to a fresh customer OpenClaw droplet, host hardening review, and connection-stability fixes. Use when connecting to a customer OpenClaw droplet, when SSH sessions drop or port 22 refuses connections, or when running the first-run review (specs, process owner, integrity).

## First connection

1. Use the dedicated key `~/.ssh/id_ed25519_barnabas_droplet` with `-o IdentitiesOnly=yes`. Never copy the operator's personal key; a dedicated key is revocable independently.
2. Confirm the droplet IP with Aaron before connecting. Never infer it from other files or sources.
3. Test with one short command (`ssh -i <key> root@IP 'echo PING-OK'`) before any multi-command survey.

## Connection stability

Rapid consecutive SSH connections trip UFW's `limit 22/tcp` and fail2ban; rapid retries from the agent make it worse. When sessions drop or port 22 refuses:

1. Have the operator whitelist the home IP (the Mac's public IP, from `curl -s ifconfig.me` on the Mac, not on the droplet):
   - `ufw allow from <HOME_IP> to any port 22 proto tcp`
   - `fail2ban-client set sshd addignoreip <HOME_IP>` and persist it in `/etc/fail2ban/jail.d/ignoreip.local` (`[DEFAULT]` / `ignoreip = 127.0.0.1/8 <HOME_IP>`), then `systemctl restart fail2ban`.
2. Switch off Ubuntu 24.04 socket-activated SSH (drops idle sessions): `systemctl disable --now ssh.socket && systemctl enable --now ssh.service`, and add keepalives in `/etc/ssh/sshd_config.d/keepalive.conf` (`ClientAliveInterval 30`, `ClientAliveCountMax 6`).
3. On the agent side, never hammer: run ssh in background writing to a temp file (`ssh ... 'commands' > /tmp/out.txt 2>&1`), poll it, and space retries 20-30s inside a bounded loop. Parallel or immediate sequential connections get refused.
4. If a long multi-command survey is killed mid-run while short commands succeed, split the survey into 2-3 short ssh connections instead of one long one.

## Host review checklist

Run as short separate connections once SSH is stable:

- Specs and OS: `nproc`, `free -h`, `df -h /`, `grep PRETTY /etc/os-release`.
- Swap: `swapon --show`. Small droplets ship without swap; add a 2GB swapfile (fallocate, chmod 600, mkswap, swapon, fstab entry) before any npm or apt work.
- Process owner: `ps aux | grep openclaw`. OpenClaw must run as a non-root user (DO images use `openclaw`). If it runs as root, stop and create a dedicated user before further work.
- Integrity: `ufw status` (expect 80/443 allow, 22 limit), `fail2ban-client status sshd` (expect zero bans), `last -n 5`, and `dmesg | grep -i oom | tail` for OOM kills.
- Versions: droplet images may ship Node 22 while current OpenClaw needs Node >=24 (NodeSource setup_24.x). Install Node BEFORE any OpenClaw update.
- Service topology: the DO image runs the gateway as a system-level unit `/etc/systemd/system/openclaw.service` (`User=openclaw`, ExecStart `/usr/bin/openclaw gateway --port ...`), not a user-level service. Health-check it with `systemctl is-active openclaw.service` and `ss -tlnp | grep 18789`; a CLI `openclaw gateway status` may say "Runtime: stopped" because it looks at the user bus — that is cosmetic, trust the unit and the listening port.

## Deploying the Chief template

1. Template files live in `template-chief-of-staff/templatefiles/` in the main agent workspace. Bundle first: `tar -czf /tmp/chief-template.tar.gz` from inside `templatefiles/` with the relative paths `AGENTS.md IDENTITY.md SOUL.md USER.md DECISIONS.md ERRORS.md FULLINSTRUCTIONS.md memory/`, then scp the tarball — one connection, one extract (`tar -xzf /tmp/chief-template.tar.gz -C /home/openclaw/.openclaw/workspace`), instead of a per-file `scp -r` that multiplies connections on a rate-limited host.
2. Before extracting, back up the image's default workspace files (`tar -czf /root/workspace-defaults-backup-$(date +%Y%m%d).tar.gz -C <workspace>` of the shipped AGENTS/SOUL/IDENTITY/USER/HEARTBEAT/TOOLS/BOOTSTRAP.md) so template-vs-default diffs stay possible. Extract, then delete `BOOTSTRAP.md` — the DO image's bootstrap file contradicts the template identity and the agent would follow it first.
2. Immediately `chown -R openclaw:openclaw /home/openclaw/.openclaw/workspace` — root-owned files break the gateway's reads.
3. Verify with `openclaw gateway status` and by listing the workspace as the `openclaw` user.
4. Never include `openclaw.json` in the template: model keys and channel config are per-customer. Ship a config template with placeholders the install step fills.

## Updating OpenClaw on DO-image droplets (2026.9.x+)

The DO image's gateway breaks three ways on a version jump. Fix in this order, all with the service stopped (`systemctl stop openclaw.service`), then `systemctl start openclaw.service` and verify active + listening on 18789:

1. Update via npm, never `openclaw update`: the doctor step reads the image's custom systemd unit as a "foreign" service (it only trusts services it installed itself) and permanently refuses maintenance. Command: `npm install -g --allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs openclaw@latest`.
2. Boot may fail with "Legacy ... requires migration" for `workspace/.openclaw/workspace-state.json`, `workspace/openclaw-workspace-state.json`, and `agents/main/sessions/sessions.json`. `openclaw doctor --fix` is the sanctioned tool but refuses on foreign services — on a FRESH droplet (no real conversations), archive these to `/root/legacy-migration-backup/` and restart. Never hand-delete them on a droplet with real usage.
3. The image's Caddy reverse proxy connects over IPv6 `::1`; `gateway.trustedProxies` shipping only `127.0.0.1` causes `proxy_attribution_required` errors in the web UI. Patch `openclaw.json`: add `"::1"` to `gateway.trustedProxies`, and add `gateway.auth.trustedProxy = { allowLoopback: true, requiredHeaders: [], userHeader: "x-forwarded-user" }` (the schema requires `userHeader` even when unused — omitting it fails validation and blocks boot). Diagnose by grepping the gateway log for "unattributable proxy-shaped traffic from <address>" — the address tells you which trustedProxies entry is missing.

## Gateway RPC and crash-loop recovery on customer droplets

1. `/opt/openclaw-cli.sh` may reject its own `--token` injection ("does not recognize option"). When it does, call the gateway directly: token lives at `/home/openclaw/.openclaw/gateway-token.txt`, endpoints `GET /status`, `/health`, and `POST /rpc` on `127.0.0.1:18789` with `Authorization: Bearer <token>`. REST-style paths like `/v1/...` return 404.
2. If a customer reports all tool calls failing, check `/home/openclaw/.openclaw/logs/stability/` first: `gateway.startup_failed` with `SessionStoreMigrationRequiredError` (agents/main/sessions/sessions.json) causes a crash loop, then the restart-loop breaker trips and suppresses channel/provider auto-start. Fix by running `openclaw doctor --fix` as the `openclaw` user, then `systemctl restart openclaw.service`, and confirm active + listening. Note the breaker message is the symptom; the startup_failed JSON names the real cause.
3. Journal files may be absent (`No journal files were found` from journalctl) on these droplets — rely on `~/.openclaw/logs/` and stability bundles, not journalctl.
4. SSH may refuse connections intermittently every few minutes even after the UFW/fail2ban whitelist fix (droplet uptime unaffected). Wrap every remote call in a bounded retry loop (sleep 30 between tries, max 3-4) instead of assuming the host is down on the first refusal.

## Fixing degraded memory vector recall on customer droplets

Symptom: `openclaw memory index` reports "chunks_vec not updated — no vector dimensions resolved. Vector recall degraded." Cause: `memory.search` unset, so no embedding provider resolves. Fix:

1. Read the knobs first: `docs/reference/memory-config.md` (embedded in the openclaw install under `docs/reference/`) documents provider adapters; `openclaw memory --help` lists the index/status subcommands.
2. Prefer riding the provider key the droplet already has (e.g. `openclaw config set memory.search.provider openrouter` and `memory.search.model openai/text-embedding-3-small`, 1536 dims) — no new credential. Embeddings bill per token on that key; `provider: "none"` is the free FTS-only alternative, only when the customer declines embeddings.
## First model-provider key on a customer droplet (post-key setup)

After the customer's API key is wired (add-provider-keys.sh pattern: staged 0600 file → SecretRef via `openclaw config set`), two failure modes appear and are fixed in this order:

1. "Primary model down, fallback engaged" in the TUI: a bare install's default model is `openai/gpt-*` with no key. The customer's OpenRouter key proves fine (`openclaw agent --agent main --model openrouter/<model> -m "Reply with exactly: PROVIDER-PROOF-OK"`) but the default route doesn't use it. Fix: `openclaw config set agents.defaults.model.primary openrouter/<chosen-model>` as the `openclaw` user.
2. TUI shows "unauthorized: gateway token mismatch" when run as root: the first-run script persists `gateway.auth.token` in the openclaw user's config only, and root's CLI has no token. Run the TUI/probes as the gateway user instead: `sudo -u openclaw openclaw tui`. Do not mirror tokens into root config.

If the script's final cleanup (removing the staged key file) did not run, its internal probe failed — verify the route manually per (1) before touching the key. The staged key file may remain on disk; config reads the file path at runtime, so never move it, and only delete it after a successful manual proof.
