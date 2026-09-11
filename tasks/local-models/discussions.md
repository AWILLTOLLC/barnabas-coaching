# Discussions Log — Building Local Models, Hardware and Software

_Append-only, newest first. One entry per discussion with date, outcome, and any numbers._

---

## 2026-09-07 — Ahmad (@TheAhmadOsman) Local AI 2026 series digested (3 articles)

All good data distilled into `materials/hardware-comparisons.md`. Sources:
- GPU Memory Math (Apr 3, 2026): https://x.com/TheAhmadOsman/status/2040103488714068245 — 721k views
- Memory Bandwidth (Apr 7, 2026): https://x.com/TheAhmadOsman/status/2041331757329285589 — 510k views
- Inference Engines (May 20, 2026): https://x.com/TheAhmadOsman/status/2057183854444843202 — 1.24M views

Key takeaways beyond what we already had:
- Bandwidth tiers: our M5 Max sits at 460-614 GB/s (serious workstation tier); RTX 5090-class is 3-4x faster but capacity-capped at 32GB
- Memory math: VRAM ≈ params × (bits÷8), +10-30% for KV cache/activations; Q4_K ≈ 0.56 GB/1B
- MoE trap: total params → memory, active params → speed
- His engine verdicts match our shootout for Mac (MLX native + llama.cpp GGUF), but his map is broader: vLLM = production default, SGLang for long-context/MoE/routing, ExLlamaV3 for 2-4 GPU consumer boxes
- **Notable flag: he says "DO NOT USE Ollama"** (convenience-only, not production-grade). We run Quinn via Ollama locally — fine for our personal use, but worth reconsidering for any client deployment; llama-server or vLLM would be the client-grade answer
- Author credibility: r/LocalLLaMA GPU moderator, founder OsmanticAI, 73.8k followers; series is well-regarded (500k-1.2M views per piece)

---

## 2026-09-07 — Serving runtime shootout (8 candidates)

**Question:** which local model serving stack for our M5 Max / 128GB?

**Evaluated:** llama.cpp, MLX/MLX-LM, ExLlamaV2, ExLlamaV3, vLLM, SGLang, TensorRT-LLM, NVIDIA Dynamo.

**Ruled out on Apple Silicon:**
- ExLlamaV2 — CUDA-only, no Metal support planned (issue open ~2 yrs)
- ExLlamaV3 — CUDA 12.4+ only
- TensorRT-LLM — NVIDIA-only toolchain
- NVIDIA Dynamo — multi-GPU datacenter orchestrator
- SGLang — no Apple Silicon support (maintainers, Feb 2026)
- vLLM — experimental MLX bridges only, underperform native Metal

**Finalists:**
- **llama.cpp (llama-server)** — winner for us: native GGUF, native Metal, OpenAI-compatible API, KV-cache quantization (`-ctk q8_0 -ctv q8_0`), parallel slots, launchd serviceable. ~150 tok/s.
- **MLX-LM** — runner-up: fastest raw generation on Apple Silicon (~230 tok/s, arXiv 2511.05502), OpenAI-compatible server since v0.18, but MLX safetensors format requires re-downloading/reconverting models.

**Client takeaway (draft):** llama.cpp is the pragmatic default for GGUF libraries; MLX is the throughput upgrade when a single hot model justifies a format copy. Everything CUDA is a non-starter on Mac; if a client has NVIDIA GPUs, that flips the whole table.

**Decision:** stay on llama.cpp; test MLX for the hot local model. → tracked in current-plan.md #1.

## 2026-09-07 — Local speech-to-text baseline established

- `whisper-cpp` (whisper-cli 1.9.2) via Homebrew; ggml-base.en model
- Performance datapoint: 53 min of audio transcribed in ~26s wall clock on M5 Max (Metal + 8 threads)
- Lesson: convert source media to 16kHz mono WAV first (`ffmpeg -i in.mp4 -vn -ar 16000 -ac 1 -f wav out.wav`) — MP4 direct input flaked
- Client takeaway: transcription is effectively free and instant on Apple Silicon; useful for meeting-notes and voice-note workflows

## 2026-09-07 — Voice in/out strategy (initial)

- Voice-IN: solved already via OpenClaw Talk mode / push-to-talk / iMessage voice notes
- Voice-OUT: hosted TTS (option 1: quality, per-char cost) vs fully-local TTS (option 2: Kokoro / VoiceStudio — free, private, heavier install, weaker ceiling, no true barge-in)
- Preliminary rec: hosted first, local when usage justifies
- Voicebox (jamiepine/voicebox) under evaluation — see current-plan.md #2

## 2026-09-07 — Project created

Created this project as the standing home for local-model infrastructure work and future client training materials. Initial context: our own M5 Max/128GB build as reference hardware; llama.cpp vs MLX shootout; whisper baseline; voice stack decision pending.
