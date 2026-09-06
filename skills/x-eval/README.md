# x-eval

Send your OpenClaw agent a link to an X/Twitter post, get back a structured
verdict: what's claimed, whether it checks out, hype-to-substance, and
"worth your time / skip". Built for the AI-news firehose.

## Install

```bash
clawhub install x-eval
```

That's the whole skill. Any X status link you send your agent — on whatever
channel you already use (Telegram, Discord, iMessage, ...) — comes back
evaluated. Replies land on the same channel the link arrived on, so every
operator keeps their own setup.

- Fetches via the public fxTwitter API: no X account, no API key, no scraping.
- One web search to corroborate checkable claims, none for opinions and jokes.
- Verdict capped at ~120 words. The point is saving you a read.

## Optional: one-hotkey capture on macOS

Skip the copy-link/switch-app/paste loop entirely. Installs a command that
grabs the frontmost browser tab (Safari, Chrome, Brave, Edge, Arc, Vivaldi,
Dia) and sends it to your agent:

```bash
bash ~/path/to/skills/x-eval/capture/install.sh
```

Then bind it to a hotkey in the Shortcuts app (the installer prints the
3-step recipe). Look at tweet → hit ⌥⌘E → verdict arrives on your channel.

On a phone no extra software is needed: X share sheet → your messaging app →
your agent.

### Remote gateway

Capture works fine when your Gateway runs on another host — the CLI is just a
client, and the agent turn executes wherever the Gateway lives. Point the CLI
at it once:

```bash
openclaw config set gateway.remote.url wss://your-gateway-host:18789
openclaw config set gateway.remote.token <token>
```

Reach the host however you already do (Tailscale, or an SSH tunnel:
`ssh -N -L 18789:127.0.0.1:18789 user@gateway-host`). Use `config set`, not
environment variables — the Shortcuts hotkey runs in a bare shell that
doesn't load your dotfiles.

## How the evaluation works

The skill fetches author, text, metrics, quote tweet, media and poll data,
then judges five things: the actual claim, verifiability, hype-to-substance
ratio, author incentives, and post age (AI news goes stale in weeks). Format
is fixed so verdicts stay scannable in a chat.

## Files

- `SKILL.md` — the skill (trigger + rubric)
- `scripts/fetch_tweet.sh` — fxTwitter fetch + URL normalization
- `capture/x-eval-capture` — Mac frontmost-tab capture
- `capture/install.sh` — capture installer

MIT.
