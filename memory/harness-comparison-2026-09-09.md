# Agent Harness Comparison: OpenClaw vs Hermes vs OpenCode vs OpenHands

*Researched 2026-09-09. Sources: vendor docs, GitHub, DeepWiki/ICLR paper for OpenHands. Note: two repos have moved — OpenCode is now `github.com/anomalyco/opencode`, and OpenHands moved from `All-Hands-AI` to the `OpenHands` org (`github.com/OpenHands/openhands`).*

---

## 1. OpenClaw (baseline, for contrast)

- **Repo:** https://github.com/openclaw/openclaw (~389k stars, custom "NOASSERTION" license — not pure OSS)
- **Premise:** A always-on personal agent runtime, not a coding agent. "The AI that really does things. Any OS. Any Platform." Local docs at `/opt/homebrew/lib/node_modules/openclaw/docs/` (incl. `agent-runtime-architecture.md`, `openclaw-agent-runtime.md`).
- **Architecture:** A persistent **gateway** daemon hosts many named agents. Each agent has a **workspace** (files on disk) that acts as its brain — AGENTS.md, SOUL.md, USER.md, memory tiers (L0 index / L1 overview / L2 topic files), decisions/errors ledgers. Sessions are ephemeral executors against that durable workspace; context resets are expected and designed around. A **heartbeat** mechanism wakes agents on a schedule; sessions can be spawned as subagents (depth-limited) or routed between agents via a shared channels bus.
- **Memory/persona:** The strongest of the four here. SOUL.md (identity) + IDENTITY.md + tiered memory protocol (L0/L1/L2), daily notes, instinct extraction, orchestration logs. Files are the source of truth; everything is human-editable markdown.
- **Session continuity:** Context resets are a *feature* — the workspace/memory files reload each session (per AGENTS.md protocol). Multi-day continuity comes from the file brain, not transcript persistence.
- **Extensibility:** Plugins, MCP, skills (SKILL.md), custom tools, channels (iMessage/Discord/Telegram/webchat), nodes (phones/other hosts).
- **Deployment:** Self-hosted daemon on your Mac/VPS, multi-channel, multi-device via nodes; Control UI dashboard.
- **Optimized for:** 24/7 personal/operational agents across messaging channels — exactly your 16+ agent fleet.

## 2. Hermes Agent (Nous Research)

- **Repo:** https://github.com/NousResearch/hermes-agent (~244k stars, MIT)
- **Docs:** https://hermes-agent.nousresearch.com/docs/ (the URLs without `/docs/` prefix 404; current paths are under `/docs/guides/...` and `/docs/user-guide/features/...`)
- **Premise:** "The agent that grows with you" — a CLI-first personal agent that lives in `~/.hermes` (or `$HERMES_HOME`), talks on messaging platforms, runs cron jobs, and accumulates memory across sessions. Closest philosophical sibling to OpenClaw.
- **Architecture:** Single-agent process per *profile* (Hermes home). Session = CLI run / messaging-platform conversation; the agent is a tool-loop over an LLM with a Tool Gateway, skills system, LSP integration, plugins, and cron automation. Explicit guide exists for **delegation & parallel work** (docs/guides/delegation-patterns) and a **"Mixture of Agents"** feature — multi-agent exists but is lighter-weight than OpenClaw's named-agent fleet. There's even a documented **"Migrate from OpenClaw"** guide — they see OpenClaw users as their audience.
- **Memory/persona (verified):**
  - `~/.hermes/SOUL.md` is **slot #1 of the system prompt** — injected verbatim after prompt-injection scanning and truncation, fully *replacing* the built-in default identity. Loaded **only from HERMES_HOME**, never cwd (personality is per-instance, deliberately immune to cwd drift). Auto-seeded on first run; never overwritten; empty file → built-in fallback. No IDENTITY.md concept — confirmed.
  - Persistent memory is **deliberately bounded**: `~/.hermes/memories/MEMORY.md` (2,200 chars ≈ 800 tokens, agent's notes) + `USER.md` (1,375 chars ≈ 500 tokens, your profile). Frozen snapshot injected at session start; agent self-edits via a memory tool. One agent per Hermes home — concurrent writers compound entries.
  - Also reads AGENTS.md for project instructions, plus `.cursorrules`/`.cursor/rules/*.mdc`.
- **Session continuity:** Strong by design — memory files + Curator feature + optional vector/provided memory (Memory Providers, Honcho Memory) survive restarts. But budget-capped (~1,300 tokens of memory total vs tiered files' freedom).
- **Extensibility:** MCP (documented guide), plugins + plugin catalog, skills (like OpenClaw's), ACP for IDE embedding (VS Code, Zed, JetBrains), Python library mode, tool search. Messaging: Telegram, Teams, voice mode, even agent email addresses.
- **Deployment:** Local CLI, server, **Hermes Cloud** (managed, controllable via MCP), batch processing with trajectory capture (eval-friendly — clearly Nous's research bent).
- **License/maturity:** MIT; backed by Nous Research; very active; ~244k stars.
- **Differentiators vs the field:** Closest OpenClaw analog; hardcoded memory budgets (anti-drift by design); Nous model ecosystem pull (Nemotron etc.); research/eval orientation.

## 3. OpenCode (Anomaly Innovations, f.k.a. SST)

- **Repo:** **https://github.com/anomalyco/opencode** — the canonical one (opencode.ai redirects here; ~206k stars, MIT). The rename: the company is Anomaly Innovations (terminal.shop / NeoVim people); repo moved from `sst/opencode` to `anomalyco/opencode`. `sst/opencode` is legacy.
- **Premise:** "The open source coding agent" built for the terminal — a direct Claude Code competitor, not an always-on agent. TUI, desktop app, IDE extension, and headless CLI.
- **Architecture:** **Client/server**. A server process owns all AI interaction/state; clients (TUI, desktop, web, IDE) attach over HTTP/SDK. Sessions, messages, files, events are all server API resources (see https://opencode.ai/docs/server/). State lives under the project/global data dirs; config is `opencode.json` (global + project scopes).
- **Memory/persona:** No SOUL.md concept. Context comes from **AGENTS.md** (generated by `/init`, committed to git), plus Rules files, per-agent prompt files. Agents are config, not personas: **primary agents** (Build — full tools; Plan — read-only permissioned) and **subagents** (General, Explore, Scout, Compaction, Title, Summary), each with custom prompt, model, temperature, max-steps, permissions. Defined in JSON or markdown.
- **Session continuity:** Sessions are persisted server-side and resumable; **compaction agent** auto-summarizes long context (one of the built-in subagents). But no cross-session memory/brain — a new session starts fresh with AGENTS.md only. Weakest fit for continuity concerns.
- **Extensibility:** The richest dev-facing surface of the four: **MCP servers**, **Agent Skills**, custom tools (TypeScript), **plugins** (event hooks), LSP servers, formatters, themes, keybinds, commands, permissions/policies, SDK, and an [Ecosystem](https://opencode.ai/docs/ecosystem/) page. 75+ LLM providers; **Zen** = curated model list.
- **Deployment:** Runs locally against your codebase (Docker image exists, WSL on Windows). Server can be remote (client/server split is a first-class design goal). No sandboxed-runtime story — it edits your real repo with a permission system (ask/allow per tool).
- **License/maturity:** MIT; Anomaly Innovations; extremely active; ~206k stars — the de-facto "Claude Code but open" of 2026.
- **Differentiators:** Best interactive coding UX (Tab to switch Build/Plan, plan-then-build workflow); permission/policy system per agent; IDE+TUI parity via one server.

## 4. OpenHands (formerly OpenDevin)

- **Repo:** **https://github.com/OpenHands/openhands** (org moved from All-Hands-AI; ~134k stars, MIT)
- **Docs:** https://docs.openhands.dev/ (use https://docs.openhands.dev/llms.txt as index)
- **Premise:** A **platform/SDK for software-engineering agents** — "AI-Driven Development." Origin story is SWE-bench (ICLR 2025 paper: "OpenHands: An Open Platform for Software-Engineering Agents"). Now: "Run OpenHands, Claude Code, Codex, Gemini, or any ACP-compatible agent across local, remote, and cloud backends" — i.e., it's becoming a harness *for* other agents too.
- **Architecture:** The most engineered of the four. Core loop (per ICLR paper + DeepWiki): **EventStream** (immutable append-only event bus) + **State** (conversation history, stats) + **AgentController** (step-function agent loop) + **Runtime** (sandboxed execution) + persistence (FileConversationStore) + Socket.IO web session. The new **Software Agent SDK** (arXiv 2511.03690) formalizes it: `Conversation()` factory → **LocalConversation** (in-process) or **RemoteConversation** (HTTP/WebSocket to an agent-server) over `ConversationState` + `EventLog`. Same code, swap workspace type to move local↔cloud.
- **Runtime/sandbox:** Actions (run bash, edit files, browse) execute in a **Docker-sandboxed runtime** (local Docker or remote runtime at runtime.all-hands.dev). This is its signature safety model — agent code never runs loose on the host.
- **Memory/persona:** No SOUL.md. Persona/system prompt is per-agent config (Agent Hub for community agent recipes + microagents — repo-triggered knowledge files). Condensers/compression manage long context. Closest to "config, not character."
- **Session continuity:** Conversations are first-class durable objects — event log persisted, resumable, pause/resume lifecycle, stuck-detection. Continuity is *within* a conversation's event stream; no built-in cross-session memory brain like OpenClaw/Hermes.
- **Extensibility:** **Full MCP support everywhere** (CLI `~/.openhands/mcp.json`, SDK programmatic, Local GUI, Cloud — SSE/SHTTP/stdio); agent hub; microagents; SDK is the extensibility story; ACP-compatible agents can be hosted *by* it.
- **Deployment:** CLI, local GUI (VS Code/VNC/browser views into the sandbox), **OpenHands Cloud**, enterprise; also embeddable as a Python library. Delegation mode: cloud handles GitHub issues end-to-end.
- **License/maturity:** MIT; All Hands AI (company, VC-backed, ICLR-published); ~134k stars; heavy release cadence on the SDK.
- **Differentiators:** Sandboxed runtime + event-sourced state + cloud/local symmetry; the only one designed as an SDK others build on; strongest for autonomous, unattended, batch/eval workloads.

---

## Comparison Table

| | **OpenClaw** | **Hermes** | **OpenCode** | **OpenHands** |
|---|---|---|---|---|
| **Optimized for** | Always-on personal/ops agents on messaging channels | Personal agent that "grows with you"; messaging + cron + evals | Interactive terminal coding | Autonomous SWE agents, sandboxed, batch/cloud |
| **Architecture** | Gateway daemon, many named agents, workspace-as-brain | Single agent per profile (HERMES_HOME) | Client/server; TUI/desktop/IDE clients | EventStream + State + Docker runtime; SDK with Local/Remote conversations |
| **Persona/memory** | SOUL.md + IDENTITY.md + L0/L1/L2 tiered memory files | SOUL.md (slot #1, verbatim, HERMES_HOME only) + MEMORY.md/USER.md (hard ~1,300-token caps) + Curator/Honcho | None — AGENTS.md + agent config prompts | None — agent config, microagents, condensers |
| **Session continuity** | Context resets by design; file brain reloads | Strong: bounded memory snapshot each session start | Sessions resumable; auto-compaction; no cross-session memory | Event-log persistence, resumable conversations; no cross-session memory |
| **Extensibility** | Plugins, MCP, skills, channels, nodes | MCP, plugins, skills, ACP, Python lib | MCP, skills, custom tools, plugins, SDK, LSP — widest dev surface | MCP (all platforms), agent hub, SDK |
| **Deployment** | Self-hosted daemon (Mac/VPS), nodes, Control UI | Local CLI, server, Hermes Cloud | Local-first; server can be remote | Local Docker sandbox, remote runtime, Cloud, GUI |
| **Sandboxing** | Host-level (your machine, permission prompts) | Host-level | Permission system on real repo | ✅ Docker sandbox / remote runtime |
| **Multi-agent** | ✅ First-class (16+ named agents, subagents, inter-agent channel) | Light (delegation, MoA) | Primary + subagents in one session | SDK/ACP — hosts other agents; cloud delegation |
| **License / stars** | Custom (NOASSERTION) / ~389k | MIT / ~244k | MIT / ~206k | MIT / ~134k |
| **Backing** | Steipete + community | Nous Research | Anomaly Innovations | All Hands AI (VC-backed) |

## Who Wins Where

**OpenClaw wins** at exactly what Aaron runs: persistent multi-agent fleets on real messaging channels, file-based memory that survives any reset, heartbeats/proactive behavior, cross-device nodes. No competitor has an equivalent to tiered memory + orchestration logging + inter-agent channels. Its weaknesses: no sandboxing (agents run on the host), memory discipline is *protocol* (agent judgment) rather than *enforced* (Hermes hard-caps), and the custom license matters if productizing.

**Hermes wins** if you want OpenClaw's soul with enforced discipline: hard memory budgets prevent context bloat and drift, the plugin/skills ecosystem is AI-lab-quality, batch mode with trajectory capture is the best eval harness of the four, and Nous's model stack is native. Its one-agent-per-home rule makes a 16-agent fleet mean 16 profiles — no shared gateway. Notably it publishes a "Migrate from OpenClaw" guide; worth reading for their take on bounded memory vs L0/L1/L2.

**OpenCode wins** for interactive daily coding in a terminal — the plan→build workflow, permission-gated Plan agent, auto-compaction, and client/server letting you pair from desktop/IDE/web against one session. It's a tool, not a colleague: no memory, no autonomy, no channels.

**OpenHands wins** for unattended/production SWE automation: Docker-sandboxed execution is the right default when agents modify code without you watching, event-sourced state gives full auditability, and the local↔cloud conversation symmetry plus ACP (hosting Claude Code/Codex as agents) makes it the best "agent infrastructure" bet. SWE-bench pedigree shows in delegation/cloud mode for issue-to-PR automation.

**One-line summary:** OpenClaw is the *household* (persistent persona, many agents, channels), Hermes is a leaner single-resident personal agent with enforced memory hygiene, OpenCode is the best *interactive coding terminal*, and OpenHands is the best *sandboxed agent platform/SDK*. For this stack, OpenClaw stays the orchestrator; OpenHands is the one worth piloting for sandboxed repo work that shouldn't touch the host.

## Sources

- OpenCode docs: https://opencode.ai/docs/ · https://opencode.ai/docs/agents/ · https://opencode.ai/docs/server/
- Hermes: https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes · https://hermes-agent.nousresearch.com/docs/user-guide/features/personality · https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- OpenHands: https://docs.openhands.dev/sdk/arch/conversation.md · https://docs.openhands.dev/overview/model-context-protocol.md · [ICLR 2025 paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/a4b6ad6b48850c0c331d1259fc66a69c-Paper-Conference.pdf) · [SDK paper](https://arxiv.org/html/2511.03690v1) · [DeepWiki](https://deepwiki.com/All-Hands-AI/OpenHands)
- OpenCode DeepWiki: https://deepwiki.com/sst/opencode
- OpenClaw local docs: `/opt/homebrew/lib/node_modules/openclaw/docs/`
- GitHub stats via GitHub API, 2026-09-09.
