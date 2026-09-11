---
source: https://barnabas.coach/agent-configurator.html
fetched: 2026-09-11
type: website
---

<<<EXTERNAL_UNTRUSTED_CONTENT id="3a719cbbb6b093f3">>>
Source: Web Fetch
---
[B](https://barnabas.coach)
 Barnabas Coaching

 Agent Configurator

 1

 Soul

 2

 Identity

 3

 Export

 4

 Preview

 Barnabas Coaching · Agent Setup

# Build an agent that thinks
the way you need it to.

 Every high-performance agent starts with two files. A soul defines how it relates to you. An identity defines how it thinks. Pick one of each.

 Start Configuring →

 🎲 Randomize everything

 Step 1 · Relationship Type

## Choose how your Agent talks to you

 Agent Name* Browse names →

 Name is required before selecting a soul.

 Agent Emoji

 🤖

 🎲 Name & Emoji

 Step 2 · Cognitive Character

## Choose how your Agent thinks

 Select a soul first to see compatibility.

 Step 3 · Hook it up to your agent

### Install your agent's personality

 You've built two files. Now put them where your agent platform reads them. Pick where this agent will run — the page shows only that platform's setup.

 Where is this agent going to run?

 OpenClawself-hosted gateway agent
 HermesNous Research agent

#### What you just built

 SOUL.md is your agent's personality and values — how it thinks, speaks, and behaves. IDENTITY.md is its name, emoji, and role description. Together they're the difference between a generic chatbot and your agent.

#### Where these files go

 OpenClaw reads both files from the agent's workspace folder: ~/.openclaw/workspace/channels/your-agent-name/. The steps below create that folder and install the files.

#### Setup steps

 Run these in order. Click Copy on each box, paste it into your terminal, and press Enter.

#### Verify it worked

- Your agent greets you in the voice you picked — that's your SOUL.md talking.

- Ask it "who are you?" — it should describe itself using the identity you built (name, role, personality), not a generic assistant answer.

- Run openclaw agents list — your agent's name appears with a workspace path.

#### Troubleshooting

- Agent still sounds generic. The file didn't land where OpenClaw reads it. Double-check the path — ~/.openclaw/workspace/channels/your-agent-name/SOUL.md — then restart the gateway.

- "command not found: openclaw" — the OpenClaw CLI isn't installed or isn't on your PATH. Install OpenClaw first (see openclaw.ai/docs).

- Copy button pastes the wrong thing. Some terminals paste on right-click, others with Cmd+V (Mac) or Ctrl+V (Windows/Linux). Paste into a plain text editor first to check what you got.

- You edited the files in Step 4 but the agent didn't change. The copy buttons always grab your latest edits, but the agent only re-reads files on restart. Copy again and restart the gateway.

#### What you just built

 SOUL.md is your agent's personality and values — how it thinks, speaks, and behaves. Hermes uses a single SOUL.md as the agent's complete identity — there's no separate identity file, so we've folded your agent's name and emoji into the top of the file for you.

#### Put it into Hermes Desktop

#### Verify it worked

- Start a new session in the Hermes Desktop app — the very first reply should match the personality you chose.

- Ask it "who are you?" — it should describe itself using the name and role you built, not the default "You are Hermes Agent" answer.

#### Troubleshooting

- Agent still sounds like default Hermes. The SOUL field is empty or the save didn't take — an empty SOUL makes Hermes fall back to its built-in identity. Reopen the agent's profile, confirm your text is there, then start a new chat.

- Edits in Step 4 aren't showing up. Your agent reads its SOUL when a chat starts, so start a new chat after saving changes.

- Hermes scans the SOUL file for prompt-injection patterns. Keep it focused on personality and voice — meta-instructions about tools or files belong elsewhere and may be flagged.

 Step 4 · Preview & Export

 Agent

 SOUL.md
 IDENTITY.md

 Editable — changes are reflected in your exported files.

 Editable — changes are reflected in your exported files.

 📋 Copy SOUL.md

 📋 Copy IDENTITY.md

 ⬇ Download .zip

### Agent Names

 Click any name to use it. These are starting points — edit freely.

 ✕
<<<END_EXTERNAL_UNTRUSTED_CONTENT id="3a719cbbb6b093f3">>>