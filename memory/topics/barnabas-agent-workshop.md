<!-- project: github.com/AWILLTOLLC/barnabas-coaching -->
# Barnabas "Agent Foundations Working Session" — deck knowledge
Source: https://barnabas.coach/agent-foundations-workshop.html (read 2026-09-10). One-page deck/workshop Aaron delivers; homepage: barnabas.coach. Companion tool: /agent-configurator.html ("AI Agent Builder" — generates SOUL/AGENTS/USER files). Related: /creel (Creel & OpenClaw Services).

## Positioning
- "Agent Foundations Working Session" — 7 blocks (A–G), interrupt anytime. Tagline: "If something sounds like magic, say so. All of it is mechanism."
- Two hats: day job = Merkle & Bloom (Principal Consultant, embedded IT ownership for biotech/GxP labs; a client grew 6→60 people under his environment; local+private AI, full agent audit trail, graph engineering). Barnabas = "the same work, scaled down" for individuals/small businesses.
- Standard the deck holds: every number measured on his own hardware or vendor docs; worked example is his own agent, running 200 days; unverified things are labeled.

## Block A — The stack (4 layers)
1. Model — text predictor, no memory/hands/clock.
2. Chatbot = Model + Textbox (forgets everything).
3. Harness — triggers, tools, memory, identity, guardrails, logs. "Almost everything that changed what's possible happened at layer 3."
4. Agent = Model + Harness — one job, one identity, on your accounts, without you.
- Sorting question: "If someone tells you about their agent, ask which harness they run." No answer = layer 2 with a costume. Test: can it act when nobody is typing?
- Vocabulary taught: token (~¾ word, page ≈ 700), turn, prompt (everything handed to model, not just your typed text), conversation vs session (session spans channels/background in a harness), context window, compaction, reasoning/effort (charged like output).
- Harness = 6 parts: Trigger, Tools, Memory, Identity ("files, not vibes"), Guardrails (enforced outside the model's judgment), Logs ("without this you have a rumor").

## Block B — Cost
- Context window is "a desk, not an inbox." Long sessions go shallow before they error.
- Every turn re-sends the whole conversation: turn 10 ≈ 10k tokens, turn 100 ≈ 100k. Tool results are the accelerant (8k tokens re-sent every turn after).
- Pricing tiers: $20 fine for one agent; ~$100 realistic business tier; OpenRouter = pay per token, 5.5% top-up fee, per-key spend caps (a plan stops you, credits don't — cap it yourself); local = no allowance; hybrid = what he runs (cheap cloud default, local subagent for narrow jobs).
- Same job, 8 prices table (email 500 tok / competitor study 500k tok): GPT-6 Astra $0.017/$14.40; Claude Fable 5.1 $0.017/$8.20; GPT-5.6 Sol $0.0068/$5.76; Claude Opus 5 $0.0085/$4.10; Sonnet 5 $0.0034/$1.64; GPT-5.6 Luna $0.0004/$0.31; GLM 5.3 Flash $0.0001/$0.05; Qwen3.8 27B local $0.
- Local isn't slow: M5 Max Qwen3.8-27B @ 90.4 tok/s vs cloud Sonnet/GLM ~62–63. OpenAI doubles input pricing >270k tokens.

## Block C — Options (3 categories)
1. Custom agent harnesses (OpenClaw, Hermes) — you run, any model incl. local, always listening, widest channels.
2. Assistant apps w/ agent features (Claude Desktop, Codex, Grok Bot) — tenant, pull/schedule only, no inbound.
3. Rented vertical agents (CloseBot, Meta Business AI) — walled garden, right for one high-volume job; most can fire webhooks out → wire into your own harness.
- "Rent the vertical for the job that pays for itself; build in a harness for what's specific to you; wire the first into the second."

## Block D — Channels
- Channel = architecture decision. Criteria: threading, privacy, reliability, reach.
- Table: Telegram (~5 min, consensus start), Discord (~30 min, best multi-agent), Slack (team audit trail), Signal (E2EE, painful setup, no threads), iMessage (bridge runs on your Mac = trust boundary), WhatsApp (reverse-engineered, ban risk, breaks when Meta changes), MS Teams (no attachments!), SMS (max reach min capability), Email (underrated, not private).
- Threading matters less with domain owners — separate sessions absorb it. Web interface is where heavy work happens; chat is from your pocket.

## Block E — Memory (his most original material)
- Hermes bets on constraint (hard caps, refuses writes until consolidation); OpenClaw bets on capture (hybrid search, nightly consolidation/"dreaming", origin tracking). Neither recalls reliably across months without a stronger backend (e.g. Supermemory, MIT, single binary).
- Gap 1 nobody solves: checking memory is a habit, not a mechanism — nothing in the pipeline forces search-before-answer. Real incident: his agent searched, right answer appeared, asked the question anyway. Fix = grounding by construction (move the fact into always-loaded context), runtime hooks don't exist yet.
- Gap 2: agents never record their own performance (rewritten drafts, repeated questions, bad delegations). Nothing writes down "how it did."
- His 3-tier memory: Tier 0 always-loaded (SOUL/USER/AGENTS), Tier 1 index (MEMORY-L0 + "Right now" header, MEMORY.md — where credentials live, never what they are), Tier 2 on demand (topics/, daily logs, DECISIONS/ERRORS/instincts; local embedding search).
- Supersede rule: old entries get edited with "> superseded DATE by: <fact>", not deleted. Stale and current never sit side by side looking equally true.
- Open problem he names: two live sources disagree (topic file vs wiki vs import) — search ranking decides, and ranking rewards phrasing, so the stalest entry can win by using your exact words.

## Block F — Orchestration
- Options: you're the router / one Chief of Staff / CoS spawns on demand. CoS wins: context accrues in one place, you describe outcomes not tools.
- Routing: config decides where possible (deterministic, free); model decides only when config runs out. "Most people build the model-decides version because it feels smarter."
- Domain owners on purpose: learning compounds, credentials stay scoped, cost knowable, debuggable, has a voice. Spawned helpers evaporate and inherit too much.
- Delegation caps: 2–3 helpers at a time, one level deep, helpers can't create helpers, every run has a timeout. (Evidence: Claude Code shipped 3 limits in one week last July; OpenClaw has depth/child limits.)
- Coordination via shared work queue (Kanban/Workboard), not agent-to-agent chat. Small scale: shared files + append-only log = audit trail.
- Shape: persistent CoS + few standing domain owners w/ scoped creds + capped helpers + cheap model routing / expensive model thinking.

## Block G — Behaviour
- Skills = 3 tiers (name+description always loaded / instructions on demand / references deeper). Description > contents — it decides whether the skill ever opens.
- Humanizer: ~30 patterns, no API key, on every essentials list. Caveats: many versions, none beat AI detectors.
- Ponytail: stops overbuilding — ladder from "does this need to exist" → stdlib → built-in → installed → one-liner → then write new. Invoke by name or it sits there.
- Identity files table: SOUL.md (who's talking, values/tone/boundaries, 200–300 words), IDENTITY.md (external presentation), AGENTS.md (per-project procedures/hard rules), USER.md (durable facts about you), TOOLS.md (tool policy/approvals), MEMORY.md (accrued facts). Standard mistake: workflow in SOUL, preferences in AGENTS. Identity travels; rules are scoped.
- Shorter files work better (Anthropic guidance): test = "would removing this cause a mistake?" Diagnostics: keeps breaking a rule = file too long; asks what file answers = ambiguous wording.
- Rules layers: 1) instruction files (advisory), 2) tool gates/hooks (deterministic code before the tool), 3) harness/sandbox (outside agent entirely), 4) governance/audit (weakest). Proof: 3 rules as instructions = 2/3 broken (unverified payment confirmed, 15 guests vs max 10); same 3 as gates = 3/3 held. "Instruction files are for preferences. The harness is for rules."
- Five lessons from 200 days: two channels two permission levels (web = elevated, iMessage = reduced; also doubles as memory test); numeric criteria beat adjectives ("very tiny" failed, counters work); let it finish then ask why (error analysis → DECISIONS/nightly pass); "you're right I'll fix that" means nothing (no mechanism behind promises); bloat kills instructions.

## Cross-links to my own setup
- The deck describes the actual architecture I run (tiers, supersede rule, instincts gating, orchestration rule) — the workshop is Aaron teaching his own house style.
- The Barnabas mistake (2026-09-10, answered Black Raven/Glimmer instead of Barnabas) is literally deck Gap 1: "searched or could have, answered from what was in front of it anyway." Instinct written: unknown-name = mandatory memory_search.
