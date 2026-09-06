# Bookmarks

Curated links with metadata for topic-based recall. Add via Aaron, indexed by Dru.

---

## Format

Each bookmark has:
- **URL** — original link
- **Author** — who posted/wrote it
- **Date** — when it was posted
- **Title/Summary** — what it's about
- **Topics** — searchable tags
- **Notes** — anything worth calling out

---

## Entries

### [2026-03-16] Nvidia Nemotron-3 Super — AI Agent Model

- **URL:** https://x.com/minchoi/status/2033216384159690805
- **Author:** Min Choi (@minchoi)
- **Posted:** 2026-03-15
- **Summary:** Nvidia dropped Nemotron-3 Super: 120B parameters, 12B active (MoE architecture), open source. Built specifically for AI agents. Includes setup + workflow walkthrough.
- **Topics:** `ai-models` `nvidia` `open-source` `ai-agents` `llm` `moe` `nemotron`
- **Notes:** Mixture-of-Experts, 12B active params means efficient inference at massive scale. Relevant to Barnabas Coaching AI stack research and general agent infra awareness.

### [2026-03-16] Paperclip — Open-source Orchestration for Zero-Human Companies

- **URL:** https://x.com/dotta/status/2029239759428780116
- **Author:** dotta (@dotta)
- **Posted:** 2026-03-04
- **GitHub:** https://github.com/paperclipai/paperclip
- **Summary:** Open-source orchestration layer for running autonomous businesses. Includes org charts, goal alignment, task ownership, budgets, and agent templates. Bootstrap with `npx paperclipai onboard`.
- **Topics:** `ai-agents` `orchestration` `autonomous-business` `open-source` `multi-agent` `agent-infra` `startups`
- **Notes:** Directly relevant to Barnabas Coaching AI stack and the broader agent team Aaron is building. Zero-human company framing is the extreme end of what Barnabas is coaching clients toward.

### [2026-03-16] Alibaba CoPaw — Open-source Personal AI Assistant Framework

- **URL:** https://x.com/dr_cintas/status/2032869686828810270
- **Author:** Alvaro Cintas (@dr_cintas)
- **Posted:** 2026-03-14
- **GitHub:** https://github.com/agentscope-ai/CoPaw
- **Summary:** Alibaba's open-source personal AI assistant framework (by AgentScope). Long-term memory, runs locally with Ollama, works with free models like Qwen. Self-hosting, skills system, multi-chat-app support. Described as a mix of OpenClaw + Claude Code.
- **Topics:** `ai-agents` `open-source` `self-hosting` `local-llm` `ollama` `alibaba` `agent-infra` `long-term-memory` `personal-assistant`
- **Notes:** Competitor/complement to OpenClaw. Interesting for SafeHarbor architecture research and for Barnabas Coaching when recommending self-hosted agent stacks to clients.

### [2026-03-16] Run Nvidia Nemotron-3 Super Locally via Ollama

- **URL:** https://x.com/juliangoldieseo/status/2033133060125069341
- **Author:** Julian Goldie SEO (@JulianGoldieSEO)
- **Posted:** 2026-03-15
- **Summary:** Practical walkthrough for running Nvidia Nemotron-3 Super (120B, MoE) locally via Ollama. Zero internet, zero API costs, zero fees. Aimed at solopreneurs using AI agents.
- **Topics:** `ai-agents` `nvidia` `nemotron` `local-llm` `ollama` `self-hosting` `solopreneur` `tutorial`
- **Notes:** Companion to the Min Choi Nemotron bookmark. More practical/setup-focused. Relevant for Barnabas Coaching clients who want to run agents without cloud API costs.

### [2026-03-16] SwiftUI UI Patterns — Codex Agent Skill

- **URL:** https://x.com/dimillian/status/2033123144450392507
- **Author:** Thomas Ricouard (@Dimillian)
- **Posted:** 2026-03-15
- **GitHub:** https://github.com/Dimillian/Skills/blob/main/swiftui-ui-patterns/SKILL.md
- **Summary:** A Codex agent skill that encodes SwiftUI UI patterns with examples, so coding agents produce clean, idiomatic SwiftUI. Built and maintained by Thomas Ricouard (known for open-source iOS apps like Ice Cubes).
- **Topics:** `swiftui` `ios` `codex` `agent-skills` `swift` `ui-patterns` `coding-agent` `apple`
- **Notes:** Directly relevant to the OpenClaw iOS chat client work and any SafeHarbor macOS/iOS UI. Good reference for how to structure agent skills for platform-specific coding patterns.

### [2026-03-16] Huihui Qwen3.5-4B Claude Opus Abliterated — Uncensored Local Model

- **URL:** https://x.com/support_huihui/status/2033237638380143079
- **Author:** huihui.ai (@support_huihui)
- **Posted:** 2026-03-15
- **HuggingFace:** https://huggingface.co/huihui-ai/Huihui-Qwen3.5-4B-Claude-4.6-Opus-abliterated
- **Summary:** Uncensored version of Qwen3.5-4B distilled with Claude Opus reasoning, created via abliteration (refusal removal). 4B params — runs on consumer hardware. Part of huihui-ai's series of uncensored/abliterated local models.
- **Topics:** `local-llm` `open-source` `uncensored` `abliteration` `qwen` `reasoning` `distillation` `small-models`
- **Notes:** Interesting for SafeHarbor local inference experiments. Small enough to run in a VM. Abliteration = removes safety refusals while keeping capabilities — useful for agent workflows that need unrestricted tool use.

### [2026-03-16] The Spec Is the New Code — Guide to Spec Driven Development

- **URL:** https://x.com/juliandeangeiis/status/2033303156340240481
- **Author:** Julián (@juliandeangeIis)
- **Posted:** 2026-03-15
- **Summary:** Long-form article on Spec Driven Development (SDD) for AI coding agents. Core argument: agents fail not because models are weak but because instructions are ambiguous. SDD = Specify → Plan → Task → Implement. The whole ecosystem (GitHub Spec Kit 77k stars, OpenAI Symphony, Ralph Loop, Claude Code plan mode) is converging on this pattern independently.
- **Topics:** `ai-agents` `coding-agents` `spec-driven-development` `agent-harness` `prompt-engineering` `software-engineering` `methodology` `claude-code`
- **Notes:** Directly relevant to how we scope SafeHarbor builds and Barnabas Coaching AI workflows. The "ambiguity problem" framing is a clean way to explain to clients why their AI coding isn't working. Worth reading in full.

---

_Last updated: 2026-03-16_
