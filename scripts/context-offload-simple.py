#!/usr/bin/env python3
"""
Simple Context Offload Script
Spawns a subagent to check context and offload if needed.
"""

import subprocess
import sys

CONTEXT_THRESHOLD = 80000  # 80K tokens
OFFLOAD_DIR = "/Users/apollo/.openclaw/workspace/memory/context-offloads"

def main():
    # Spawn a subagent that will check context and offload
    prompt = f"""
You are a context offload monitor. Check the current session status:
- If contextTokens > {CONTEXT_THRESHOLD}, read sessions_history (limit=200)
- Summarize the oldest 50 messages into 12 paragraphs
- Write the summary to {OFFLOAD_DIR}/YYYY-MM-DD-HH-MM.md
- Reply with: "OFFLOADED: {CONTEXT_THRESHOLD} tokens, summary written"
- If contextTokens < {CONTEXT_THRESHOLD}, reply: "OK: context below threshold"
"""
    
    result = subprocess.run(
        ["openclaw", "sessions", "spawn",
         "--task", prompt,
         "--label", "Context Monitor",
         "--runtime", "subagent",
         "--model", "ollama/quinn-q8:ctx128k",
         "--visible", "false",
         "--collect", "true"],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print(result.stdout.strip())
    return 0 if result.returncode == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
