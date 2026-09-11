# Chief Template — Setting Up Common Channels (Jeff setup)

Wire the customer's chat channel after the gateway is live and the default model is set (Step 2.5). Everything below runs on the droplet via SSH as root — the customer never touches a terminal. All `openclaw` CLI calls run as the `openclaw` user:

```bash
sudo -u openclaw openclaw …
```

(Root gets `unauthorized: gateway token mismatch` — same rule as everywhere else.)

Docs version: OpenClaw 2026.9.3.

## Decision table

| Channel | Privacy | New app for customer? | Number needed? | Ban/ToS risk | Setup time |
|---|---|---|---|---|---|
| **WhatsApp** ⭐ recommended | DMs E2EE between phone contacts, but the linked gateway receives the **full account message stream** | No | No (gateway links to existing account) | Yes — unofficial automation (Baileys); spam-like patterns risk a ban | ~15 min (QR scan) |
| **Signal** | Real E2EE; bot is its own identity — customer's personal account is cryptographically unreachable | Likely no (most have it) | Yes — dedicated bot number, one-time SMS/voice verify | No | ~30–45 min (number sourcing + register) |
| **Matrix** | E2EE supported with verification | **Yes** — Element (phone + desktop) | **No** — username only, no phone anywhere | No | ~30 min + homeserver choice |

Not covered in detail here (server-visible to the provider — fine for public/low-sensitivity use only): **Telegram, Discord, Slack**. **iMessage** is macOS-only and cannot run on the Ubuntu droplet; bridging through the operator's Mac is an architectural decision to avoid for customer droplets.

---

## 1. WhatsApp (recommended default)

The gateway registers as a **linked device** on the customer's existing WhatsApp account — no second number, no new app.

### Steps

1. Install the plugin:

   ```bash
   sudo -u openclaw openclaw plugins install @openclaw/whatsapp
   ```

2. **Set access policy BEFORE linking** (customer's number, `+1XXXXXXXXXX` — usually the phone's SIM number, same as iMessage; confirm in WhatsApp → Settings → profile):

   ```bash
   sudo -u openclaw openclaw config set channels.whatsapp.dmPolicy pairing
   sudo -u openclaw openclaw config set channels.whatsapp.allowFrom '["+1XXXXXXXXXX"]'
   ```

3. Link via QR (QR-only — there is no code path):

   ```bash
   sudo -u openclaw openclaw channels login --channel whatsapp
   ```

   The customer just scans: **WhatsApp → Settings → Linked devices → Link a device.** Deliver the QR by screen-share, or screenshot + email it. QRs expire in ~20 s–2 min — rerun the command for a fresh QR as many times as needed.

4. Verify and test:

   ```bash
   sudo -u openclaw openclaw channels status   # expect linked / running
   ```

   Then have the customer DM the bot from their phone and confirm a reply.

### Trade-offs (customer must knowingly accept)

- **Pros:** zero new apps, real-time, familiar.
- **Cons:** unofficial automation (Baileys) — a ban is possible on spam-like patterns. More importantly, the linked device receives the **full message stream of the whole account** — all chats, contacts, and groups — not just bot conversations. Policy filters (`dmPolicy`, `allowFrom`) are software, not cryptographic walls. A customer who wants the "digest all my convos" use case is making a deliberate, informed choice — say it out loud on the call and get a yes.
- **Groups:** if the customer wants the gateway to observe groups, set `channels.whatsapp.groupPolicy` / `groupAllowFrom` and stage groups deliberately — never `allowall`.

---

## 2. Signal (most private)

The bot is its own Signal identity on a **dedicated number**. Do **not** run it on the customer's personal Signal account — loop protection makes the bot ignore messages from its own account.

The gateway talks to `signal-cli` (native JSON-RPC/SSE daemon, or the `bbernhard/signal-cli-rest-api` container). Full reference: `/opt/homebrew/lib/node_modules/openclaw/docs/channels/signal.md` — read it and follow it for exact commands.

### Steps (summary — follow signal.md for detail)

1. Install the plugin:

   ```bash
   sudo -u openclaw openclaw plugins install @openclaw/signal
   ```

2. Source a dedicated number that can receive SMS or voice verification once (Twilio ~$1/mo, or an eSIM). After setup there is **no SMS traffic** — all messaging is Signal E2EE over data.

3. Install `signal-cli` on the gateway host (native build per signal.md), then register and verify:

   ```bash
   signal-cli -a +<BOT_PHONE_NUMBER> register        # add --captcha '<URL>' if required
   signal-cli -a +<BOT_PHONE_NUMBER> verify <CODE>
   ```

   Captchas: generate at `https://signalcaptchas.org/registration/generate.html`, copy the `signalcaptcha://…` target, register from the same external IP as the browser, and verify immediately.

4. Configure the channel (guided, non-interactive flags available):

   ```bash
   sudo -u openclaw openclaw channels add --channel signal --signal-number +<BOT_PHONE_NUMBER>
   ```

   Set `channels.signal.dmPolicy: "pairing"` and `allowFrom` with the customer's number (E.164).

5. Customer pairs: install/keep the Signal app, text the bot number, then approve on the server:

   ```bash
   sudo -u openclaw openclaw pairing approve signal <PAIRING_CODE>
   ```

6. Verify:

   ```bash
   sudo -u openclaw openclaw channels status --probe
   ```

### Trade-offs

- **Pros:** real E2EE; the customer's personal account/chats are cryptographically unreachable (a hard privacy boundary, not a policy filter); no ToS problem; no ban risk.
- **Cons:** sourcing + verifying a dedicated number (one-time SMS); customer must keep the Signal app; slightly more setup ceremony.

---

## 3. Matrix (no phone number at all)

The bot account is just a username on a homeserver — no phone number, SMS, or eSIM anywhere in the stack.

### Steps

1. Install the plugin:

   ```bash
   sudo -u openclaw openclaw plugins install @openclaw/matrix
   ```

2. Create the bot account on a homeserver — `matrix.org` is free to start; self-host Synapse/Conduit on the droplet later for a fully customer-owned stack.

3. Configure `channels.matrix` (`homeserver` + `accessToken`, or `homeserver` + `userId` + `password`; wizard: `sudo -u openclaw openclaw channels add`), restart the gateway. Full reference: `/opt/homebrew/lib/node_modules/openclaw/docs/channels/matrix.md`.

4. The customer creates **their own** Matrix account (username only, no phone), installs **Element** (phone + desktop), and DMs the bot. Set `channels.matrix.dm.policy: "pairing"` and `dm.allowFrom` with the customer's exact `@user:server` ID (case-sensitive).

5. Enable E2EE and complete key verification (wizard does the bootstrap, or `openclaw matrix encryption setup`).

### Trade-offs

- **Pros:** no phone number anywhere; open protocol, no vendor; self-hostable homeserver = customer-owned stack end to end.
- **Cons:** customer must install Element (a new app); heavier setup ceremony (homeserver choice, E2EE key verification).

---

## After the channel is live

The template ships two report-y cron jobs with `delivery.mode = none` — their output goes nowhere. Once the customer has a chat channel, switch both to announce with an explicit target so the nightly reports actually reach them:

- **nightly-memory-consolidation** (job 1 in SETUP-CRONS.md, 23:00 local)
- **memory-survival-test** (job 7, 07:00 local)

Use `automations edit` with the documented announce flags:

```bash
sudo -u openclaw openclaw automations edit <job-id> \
  --announce --channel <channel> --to <target>
```

- `<channel>` = the plugin id (`whatsapp`, `signal`, `matrix`).
- `<to>` = the customer's DM target: WhatsApp/Signal use the E.164 number (`+1XXXXXXXXXX`); Matrix uses the exact `room:!room:server` / user form — Matrix IDs are case-sensitive.
- On a multi-channel host the explicit `--channel` is required. If delivery-target validation rejects the edit, check `openclaw openclaw automations edit --help` (or `docs/automation/cron-jobs.md`) for current flags — do not invent keys.
- Verify: `sudo -u openclaw openclaw automations get <job-id>`, then force-run once (`run`, runMode=force) and confirm the report lands in the customer's chat.

Note: DM pairing-store approvals do **not** count as automation recipients — the explicit `delivery.to` (or an `allowFrom` entry) is required for proactive nightly sends.

## Customer talking points (say these out loud on the call)

| Channel | What the customer must knowingly accept |
|---|---|
| WhatsApp | The linked gateway receives the **full account message stream** (all chats/contacts/groups, not just bot conversations) + ToS/ban risk from unofficial automation. Policy filters are software, not cryptographic walls. |
| Signal | A dedicated bot number must be sourced and verified once (one-time SMS); the customer keeps the Signal app. |
| Matrix | A new app (Element) to install; E2EE key verification ceremony. |

Get an explicit "yes, I understand" for the chosen channel before finishing setup.

## Troubleshooting quickies

| Symptom | Fix |
|---|---|
| QR expired / never scanned | Rerun `sudo -u openclaw openclaw channels login --channel whatsapp` for a fresh QR. |
| WhatsApp shows not linked | Run `channels login` again, then `openclaw channels status` until linked/running. |
| Customer DMs but bot is silent | Check `allowFrom` / pairing approval (`openclaw pairing list`), **and** check the default model — a fresh install has placeholder `openai/gpt-5.6-sol`, which fails every agent turn until set to a configured provider model (Step 2.5 of SETUP-WALKTHROUGH.md). |
| Signal DM silent | Confirm `signal-cli` is registered (`channels status --probe`), then pairing-approved. |
| Nightly reports never arrive | Jobs 1/7 still on `delivery.mode: none` — see "After the channel is live" above. |
