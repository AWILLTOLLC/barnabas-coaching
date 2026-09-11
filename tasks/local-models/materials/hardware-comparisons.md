# Hardware Configuration Comparisons

_Compiled from Ahmad (@TheAhmadOsman) "Local AI 2026 Edition" series — GPU Memory Math (Apr 3), Memory Bandwidth (Apr 7), Inference Engines (May 20). Source links in discussions.md. Cross-checked against our M5 Max/128GB reference build._

---

## The mental model

**Local AI hardware = capacity × bandwidth × software stack**

- **Capacity** decides what fits.
- **Bandwidth** decides how fast it decodes (decode is memory-bandwidth-bound, not compute-bound).
- **Software stack** decides how much of the spec sheet you can actually cash out.

Core formula: `VRAM (GB) ≈ params (B) × (effective bits per weight ÷ 8)`

Then add **10-30% overhead** for KV cache, activations, batching, framework overhead — more for long context or agent workloads.

---

## Memory math per quant

| Format | GB per 1B params |
|---|---|
| FP16/BF16 | ~2.0 |
| FP8/INT8 | ~1.0 |
| Q6_K | ~0.82 |
| Q5_K | ~0.69 |
| Q4_K | ~0.56 |
| Q3_K | ~0.43 |
| Q2_K | ~0.33 |

Shorthand: FP16 = 2× model size, FP8 = 1×, 4-bit = 0.5×.

Worked examples (weights only):

| Model | FP16 | FP8 | 4-bit |
|---|---|---|---|
| 7B | ~14 GB | ~7 GB | ~3.5-4 GB |
| 13B | ~26 GB | ~13 GB | ~6-7 GB |
| 27B (our Quinn class) | ~54 GB | ~27 GB | ~15-16 GB |
| 70B | ~140 GB | ~70 GB | ~35-40 GB |
| 405B | ~810 GB | ~405 GB | ~200+ GB |

**GPU fit table (weights only):**

| VRAM | FP16 | FP8 | 4-bit |
|---|---|---|---|
| 8 GB | ~3B | ~6-7B | ~12-13B |
| 12 GB | ~5B | ~10B | ~18-20B |
| 16 GB | ~7B | ~13B | ~25B |
| 24 GB | ~10-12B | ~20B | ~35-40B |
| 48 GB | ~20-24B | ~40B | ~70-80B |
| 80 GB | ~35-40B | ~70B | ~140B-class |

**Caveats the post adds:**
- **KV cache is the real killer** at long context — budget beyond weights.
- **MoE trap:** "8x7B" ≠ 56B compute; total params → memory, active params → speed.
- **GGUF numbers are runtime-specific** — other frameworks may dequantize and blow past them.

---

## Bandwidth tiers (the number that actually matters)

Decode speed tracks memory bandwidth, not peak compute. Tiers:

| Class | Hardware | GB/s |
|---|---|---|
| 1.8 TB/s | RTX PRO 6000 Blackwell, RTX 5090 | 1792 |
| 800 GB/s | Mac Studio M3 Ultra (up to 512GB unified) | 819 |
| 450-650 GB/s | Mac Studio M4 Max (546), **MacBook Pro M5 Max (460-614 — ours)**, AMD R9700 (640), Tenstorrent Blackhole p150 (512) | |
| 250-300 GB/s | DGX Spark (273), Mac mini M4 Pro (273), Strix Halo / Ryzen AI Max (256) | |
| Thin-and-light | MacBook Air M5 (153), Snapdragon X2 Elite (152-228), Intel Lunar Lake (136), Snapdragon X Elite (135), Mac mini M4 (120) | |

**Discrete GPU reference:**
- RTX 4090: 24GB @ 1008 GB/s
- RTX 5090: 32GB @ 1792 GB/s
- RTX PRO 6000: 96GB @ 1792 GB/s
- AMD RX 7900 XTX: 24GB @ 960; PRO W7900: 48GB @ 864; AI PRO R9700: 32GB @ 640
- Intel Arc Pro B65: 32GB @ ~608; B60: 24GB @ ~456
- Tenstorrent: Wormhole n300 24GB @ 576; Blackhole p150 32GB @ 512 (fully open-source stack, one to watch)

**Reading the tiers:**
- <150 GB/s → edge/assistants/small models only; not multi-agent territory
- 250-300 GB/s → unified memory gets interesting
- 450-650 GB/s → serious workstation tier
- 800+ GB/s → expensive, powerful, fun

**Positioning by vendor:**
- **NVIDIA** → fastest raw decode when the model fits
- **Apple Ultra (M3 Ultra)** → biggest one-box memory; wins on "one silent box with stupid amounts of memory"; loses on raw tok/s and concurrency
- **Strix Halo** → first real x86 unified-memory play (up to 128GB, ~96GB usable, 256 GB/s)
- **DGX Spark** → coherent-memory CUDA developer appliance, not a bandwidth monster (273 GB/s; NVFP4 support)
- **Tenstorrent** → fully open-source stack wildcard
- **Multi-GPU ≠ linear**: interconnect, topology, sync overhead, software maturity all tax you

---

## Inference engine decision guide (his one-pager)

| Situation | Engine |
|---|---|
| Laptop / edge / odd hardware | llama.cpp |
| Mac-first workflows | MLX / MLX-LM |
| Single RTX local inference | ExLlamaV2 |
| 2-4+ NVIDIA GPUs | ExLlamaV3 |
| General production serving | vLLM |
| Long-context / MoE / routing | SGLang |
| NVIDIA max performance | TensorRT-LLM |
| Cluster orchestration | NVIDIA Dynamo |

**Workload → bottleneck mapping:**
- Short prompt, long answer → decode dominates → bandwidth + batching
- Long prompt, short answer → prefill dominates → attention kernels, chunked prefill
- Many users → scheduler quality (continuous batching, cache paging, fairness)
- Long context → KV cache → paged attention, KV quantization, offload
- MoE → expert routing → expert parallelism, grouped GEMMs
- Multi-node → interconnect → NVLink/RDMA, pipeline vs tensor parallelism (pipeline wins without NVLink, per vLLM docs)

**Hardware strategy recipes:**
- CPU-only server → llama.cpp (OpenVINO on Intel Xeon)
- Mac → MLX native / llama.cpp for GGUF
- Single RTX → ExLlamaV2; vLLM if serving multiple users
- Dual/quad RTX → ExLlamaV3; vLLM/SGLang if serving matters
- 8×H100 node → vLLM or SGLang; TensorRT-LLM if NVIDIA-only; Dynamo at multi-node
- AMD MI300+ → vLLM/SGLang on ROCm (don't assume NVIDIA numbers transfer)
- Browser/mobile → MLC LLM / ONNX Runtime GenAI

**Benchmark properly (his rules):** never single-user tok/s only; test your real prompt/output distribution and concurrency; separate prefill from decode; report p50/p95/p99; measure memory headroom at target context; test cache reuse; re-test after upgrades.

**His spiciest take:** "DO NOT USE Ollama" — production means security, observability, backpressure, routing; Ollama is convenience-only. Also notes MLX-LM's own server "not recommended for production" (basic security checks only), and llama.cpp RPC backend is proof-of-concept/fragile.

---

## Fit to our reference build (M5 Max, 128GB, 460-614 GB/s)

- We sit in the "serious workstation tier" band: 27B-class Q4 (15-16GB weights) fits trivially; 70B Q4 (~40GB) fits with room; long-context agent workloads are our KV-cache-heavy case.
- The post's Mac-first verdict (MLX native + llama.cpp GGUF) matches our 2026-09-07 shootout conclusion.
- Client pitch angle: on a 24GB RTX box you top out at ~35-40B in 4-bit; on a 128GB Mac the constraint becomes bandwidth-adjusted decode speed, not fit. Different machines buy different bottlenecks.
