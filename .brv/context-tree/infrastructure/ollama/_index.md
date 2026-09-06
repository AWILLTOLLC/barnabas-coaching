---
children_hash: 7e7b3d1ed16d433f06cfac58f1c2062a9fb26b3beb62ab36e4a23daaf0a72cfe
compression_ratio: 0.8172043010752689
condensation_order: 1
covers: [local_llm_timeout_bug.md]
covers_token_total: 279
summary_level: d1
token_count: 228
type: summary
---
# Infrastructure: Local LLM Timeout Bug

The OpenClaw gateway currently implements a hardcoded 30-second timeout for LLM calls, which triggers failures during high-latency inference. 

### Key Technical Findings
*   **Root Cause**: Incorrect `num_ctx` configuration in Ollama Modelfiles. Models were defaulting to 262,144 context tokens instead of the 32,768 limit, resulting in excessive memory pressure and inference times exceeding the 30s gateway threshold.
*   **Red Herrings**: Initial diagnostic reports of Discord 401 errors were misidentified; these were secondary to the underlying timeout issue.

### Architectural Rules
*   **Context Management**: Explicitly cap `num_ctx` at 32,768 within all Ollama Modelfiles.
*   **Operational Requirement**: Local LLM models must be pre-warmed to mitigate initial latency spikes.

For further details, refer to the full documentation in local_llm_timeout_bug.md.