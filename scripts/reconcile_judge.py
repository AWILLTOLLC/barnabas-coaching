#!/usr/bin/env python3
"""
reconcile_judge.py — LLM judgment pass for memory reconciliation candidates.

Reads candidate JSON, calls OpenRouter (kimi-k2.5) with calibration rubric,
and writes judged output JSON.

Usage:
    python3 scripts/reconcile_judge.py --in /tmp/candidates.json --out /tmp/judged.json
    cat /tmp/candidates.json | python3 scripts/reconcile_judge.py > /tmp/judged.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Optional

import urllib.request
import urllib.error

# ── Configuration ────────────────────────────────────────────────────────────
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
JUDGE_MODEL = "moonshotai/kimi-k2.5"
TIMEOUT_SECONDS = 120
MAX_RETRIES = 3

# ── Calibration rubric (from pressure test results) ──────────────────────────
RUBRIC = """
You are a strict judge evaluating candidate memory items extracted from an agent's session transcripts.
Your task: decide whether each candidate is genuinely useful to write to long-term memory.

## Verdict definitions
- **match** — The candidate is genuinely useful: a decision, commitment, state change, revealed preference, correction, or new fact that may be referenced later. The evidence clearly supports this.
- **skip** — The candidate is related/interesting but not worth writing to memory. Examples: transient status, one-off completed task with no lasting impact, a fact that is too minor or already well-known, or a vague commitment without specifics.
- **junk** — False positive / noise. The keyword triggered but the evidence is not actually a useful event (e.g., "no problem" triggered "no" correction pattern; tool output dump; meta-discussion).

## Judgment rules
1. Judge the **evidence text**, not just the candidate type or heuristic confidence.
2. Prefer **skip** over **match** when uncertain. Prefer **junk** over **skip** when the evidence is clearly noise.
3. Corrections are useful ONLY if they identify an actual mistake with specifics ("actually use X, not Y"). Generic "actually" or "no" are junk.
4. State changes are useful ONLY if they name what changed ("enabled feature X"). Generic "started" with no subject is skip or junk.
5. New facts (URLs, emails, versions, prices) are useful ONLY if they relate to a person, project, or system Aaron cares about.
6. Commitments are useful ONLY if they are specific ("will check on Tuesday") or assigned to someone. Vague "I should do that" is skip.
7. Decisions are match if they block an alternative or set a policy. "Let's skip it for now" is a decision. Vague "let's think about it" is skip.

## Output format
Return ONLY a JSON array, one object per candidate, in the SAME ORDER as input:
[
  {"id": "candidate-id-1", "verdict": "match|skip|junk", "rationale": "one-sentence reason"},
  ...
]
Do not include markdown, commentary, or explanation outside the JSON array.
"""


# ── Key resolution ───────────────────────────────────────────────────────────

def resolve_api_key() -> Optional[str]:
    """Find OPENROUTER_API_KEY without ever logging its value."""
    # 1. Environment variable
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    state_dir = Path(os.environ.get("OPENCLAW_STATE_DIR", "/Users/apollo/.openclaw"))

    # 2. OpenClaw config JSON — auth profiles
    config_path = state_dir / "openclaw.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            profiles = cfg.get("auth", {}).get("profiles", {})
            for name, prof in profiles.items():
                if not isinstance(prof, dict):
                    continue
                if prof.get("provider") == "openrouter" or "openrouter" in name.lower():
                    # SecretRef or direct key
                    api_key_val = prof.get("apiKey")
                    if isinstance(api_key_val, str) and len(api_key_val) > 20:
                        return api_key_val
                    if isinstance(api_key_val, dict):
                        # SecretRef resolution — try common paths
                        secret_path = api_key_val.get("$secret") or api_key_val.get("secretRef") or api_key_val.get("path")
                        if secret_path:
                            sp = Path(secret_path).expanduser()
                            if sp.exists():
                                return sp.read_text().strip()
        except Exception:
            pass

    # 3. Main agent auth store SQLite
    db_path = state_dir / "agents" / "main" / "agent" / "openclaw-agent.sqlite"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute("SELECT store_key, store_json FROM auth_profile_store").fetchall()
            conn.close()
            for store_key, store_json in rows:
                if not isinstance(store_json, str):
                    continue
                if "openrouter" not in store_key.lower() and "openrouter" not in store_json.lower():
                    continue
                try:
                    data = json.loads(store_json)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and v.startswith("sk-or") and len(v) > 20:
                            return v
                        if isinstance(v, dict):
                            for kk, vv in v.items():
                                if isinstance(vv, str) and vv.startswith("sk-or") and len(vv) > 20:
                                    return vv
        except Exception:
            pass

    # 4. Legacy auth JSON files (migrated)
    for auth_file in (state_dir / "agents" / "main" / "agent").glob("auth*.json*"):
        try:
            data = json.loads(auth_file.read_text())
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str) and v.startswith("sk-or") and len(v) > 20:
                        return v
                    if isinstance(v, dict):
                        for kk, vv in v.items():
                            if isinstance(vv, str) and vv.startswith("sk-or") and len(vv) > 20:
                                return vv
        except Exception:
            pass

    # 3. Gateway authProfiles store (proven path — same as openrouter_credits.py)
    db_path = os.path.expanduser("~/.openclaw/state/openclaw.sqlite")
    if os.path.exists(db_path):
        try:
            import sqlite3
            db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            row = db.execute(
                "select value_json from config_machine_state where state_key='authProfiles.store'"
            ).fetchone()
            db.close()
            if row:
                profiles = json.loads(row[0]).get("profiles", {})
                for name, prof in profiles.items():
                    if isinstance(prof, dict) and prof.get("provider") == "openrouter" and prof.get("type") == "api_key" and prof.get("key"):
                        return prof["key"]
        except Exception:
            pass

    return None


# ── OpenRouter call ──────────────────────────────────────────────────────────

def judge_candidates(candidates: List[dict], api_key: str) -> List[dict]:
    """Call OpenRouter once for a batch of candidates."""
    # Build prompt: rubric + candidate list
    prompt_parts = [RUBRIC.strip(), "", "## Candidates to judge:"]
    for i, c in enumerate(candidates, 1):
        prompt_parts.append(f"[{i}] id={c['id']} type={c['type']}")
        prompt_parts.append(f"    evidence: {c['evidence'][:300]}")
        prompt_parts.append("")

    prompt_text = "\n".join(prompt_parts)

    payload = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": "You are a strict memory-quality judge."},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0.1,
        "max_tokens": 16000,
    }

    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://openclaw.local",
            "X-Title": "reconcile-judge",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    msg = result["choices"][0].get("message", {})
    content = msg.get("content")
    if not content or not content.strip():
        # Some models put the answer in reasoning_content or return empty content on tool-less prompts
        content = msg.get("reasoning_content") or msg.get("reasoning") or ""
    if not content.strip():
        raise ValueError(f"Judge returned empty content; finish_reason={result['choices'][0].get('finish_reason')}; keys={list(result['choices'][0].get('message', {}).keys())}")
    # Strip markdown fences
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    verdicts = json.loads(content)
    if not isinstance(verdicts, list):
        raise ValueError("Expected JSON array from judge")

    # Ensure same count and populate missing IDs
    if len(verdicts) != len(candidates):
        raise ValueError(f"Verdict count mismatch: {len(verdicts)} vs {len(candidates)}")

    for i, v in enumerate(verdicts):
        v.setdefault("id", candidates[i]["id"])
        v.setdefault("verdict", "unjudged")
        v.setdefault("rationale", "")
    return verdicts


def fallback_verdicts(candidates: List[dict], reason: str) -> List[dict]:
    return [
        {"id": c["id"], "verdict": "unjudged", "rationale": reason}
        for c in candidates
    ]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Memory reconcile judge")
    parser.add_argument("--in", dest="input_file", help="Input candidates JSON file")
    parser.add_argument("--out", help="Output judged JSON file (default stdout)")
    args = parser.parse_args()

    # Read input
    if args.input_file:
        raw = Path(args.input_file).read_text()
    else:
        raw = sys.stdin.read()

    try:
        candidates = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid input JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(candidates, list):
        print("ERROR: Input must be a JSON array", file=sys.stderr)
        sys.exit(1)

    if not candidates:
        # Empty input — nothing to judge
        result = []
        if args.out:
            Path(args.out).write_text(json.dumps(result))
        else:
            print(json.dumps(result))
        return

    api_key = resolve_api_key()
    if not api_key:
        verdicts = fallback_verdicts(candidates, "API key not found — no judge available")
    else:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                verdicts = judge_candidates(candidates, api_key)
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt
                    print(f"WARN: Judge attempt {attempt} failed ({e}), retrying in {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                else:
                    print(f"WARN: Judge failed after {MAX_RETRIES} attempts: {e}", file=sys.stderr)
                    verdicts = fallback_verdicts(candidates, f"API failure: {e}")

    # Merge verdicts back with candidate metadata for downstream use
    judged = []
    for c, v in zip(candidates, verdicts):
        judged.append({
            "id": c["id"],
            "verdict": v.get("verdict", "unjudged"),
            "rationale": v.get("rationale", ""),
            "candidate_type": c.get("type"),
            "evidence": c.get("evidence"),
            "source_ref": c.get("source_ref"),
            "ts": c.get("ts"),
        })

    output = json.dumps(judged, indent=2)
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
