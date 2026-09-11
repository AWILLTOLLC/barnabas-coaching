# Building Local Models, Hardware and Software

Ongoing project. Source of training materials and recommendations for clients who want Aaron to build local model infrastructure (hardware and software).

## Structure

- `current-plan.md` — what we're actively working on, with status. Keep current.
- `discussions.md` — dated log of everything we discussed/evaluated, newest first. Append, don't rewrite.
- `materials/` — client-facing deliverables as they get written (guides, spec sheets, recommendation docs).

## Grounding facts (our own build, used as reference hardware)

- Host: Apple Silicon MacBook Pro, M5 Max, 128GB unified memory, 4TB storage, macOS 26
- Serving: llama.cpp (`llama-server`) via Homebrew, GGUF models in `/Users/apollo/.openclaw/models/`
- Model library: Qwen 27B-class distills (e.g. Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled Q4_K_M "Quinn"), embeddinggemma-300m
- OpenClaw multi-agent stack on top: ~15 agents, gateway, scheduled automations
- Free disk for experiments: ~3.5TB at project start (2026-09-07)

## Client positioning

- Aaron's IT consulting serves biotechs; this project extends into "local AI infra" offerings
- Deliverables likely: hardware spec recommendations, software stack setup, privacy-first alternatives to cloud APIs, cost comparisons
- Standing rule: check https://github.com/ripienaar/free-for-dev before recommending paid tooling
