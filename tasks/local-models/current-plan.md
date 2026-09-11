# Current Plan — Building Local Models, Hardware and Software

_Working list. Update status as items move. Completed items move to Discussions log with a date._

## Active

1. **MLX-LM side-by-side evaluation** (started 2026-09-07)
   - `mlx-lm` installed via uv (18 CLI tools incl. `mlx_lm.server`)
   - Model: `mlx-community/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit` downloading to `/Users/apollo/.openclaw/models/mlx/` (~16GB)
   - Remaining: sanity generate test → start `mlx_lm.server` on spare port → speed benchmark vs llama.cpp (same prompt, tok/s) → verdict on format friction vs speed

2. **Voice stack decision** (pending)
   - Voice-IN: already solved (Talk mode, push-to-talk, iMessage voice notes)
   - Voice-OUT options: (1) hosted TTS (ElevenLabs/OpenAI) — best quality, costs; (2) local Kokoro/VoiceStudio — free/private, heavier; (3) evaluating https://github.com/jamiepine/voicebox
   - Recommendation so far: option 1 first, local only if heavy daily use / privacy need

3. **AgentShield security audit** (running)
   - Scanner from github.com/affaan-m/ECC against workspace + openclaw.json
   - Findings to feed into ERRORS.md / hardening backlog

4. **ECC continuous-learning comparison** (running)
   - Compare ECC's instincts/hooks implementation vs our signals.jsonl → instincts.md pipeline
   - Deliverable: 2-4 concrete pipeline improvements

## Queued (client-material backlog)

- **Hardware spec guide**: what to buy at 3 price points (e.g. Mac Mini M-series 32GB / 64GB / 128GB Mac Studio class) for local serving; VRAM-unified-memory sizing rules of thumb (model size × quant + context KV)
- **Cost comparison doc**: local vs hosted API economics, incl. break-even analysis
- **Privacy pitch**: why local for biotech/regulated clients
- **Long-context serving guide**: KV cache quantization, prompt caching, context windows on 128GB
- **Multi-model serving**: one box, several models, OpenAI-compatible routing (llama-server slots, port-per-model)

## Done

- Serving runtime comparison (2026-09-07): llama.cpp top pick, MLX-LM runner-up; ExLlamaV2/V3, vLLM, SGLang, TensorRT-LLM, NVIDIA Dynamo ruled out on Apple Silicon — see discussions.md
- Whisper (speech-to-text) local setup proven: `whisper-cpp` 1.9.2, base.en GGML, ~53min audio transcribed in ~26s on M5 Max
