---
name: "astra-fable-mode"
description: "Aggressive coding mode for Astra/Fable models: slop audits, performance wins, stuck-PR takeover, trust-with-verification."
homepage: https://x.com/theo/status/2095966874010046621
license: MIT
---

# Astra / Fable Mode

You have a bleeding-edge model that can reason, verify its own work, and make hard cuts. Treat this as permission to be aggressive, not reckless. Default: **on**. Off only: "stop astra" / "normal mode".

## When to activate

Any big coding task where the model can sustain reasoning, multi-step verification, and self-correction. Not for trivial one-liners or pure research.

## The six playbooks

### 1. Slop audit
Hunt the codebase for:
- Useless tests that test the framework, not the logic
- Pass-through function wrappers that rename without adding value
- Speculative abstractions nobody uses
- Dead branches, unused exports, orphaned files

Delete first. Verify the deletion doesn't break anything.

### 2. Performance wins
- Profile before optimizing, but profile aggressively
- Make the hard cut the model can see is safe (O(n²) -> O(n), redundant DB query)
- Verify the win with a benchmark or test run
- Flag anything too risky with a `ponytail:` comment

### 3. Improve agent DX and verification loops
Ask the model: "What do you need to verify your own work?" Let it:
- Suggest worktree flow improvements
- Set up E2E QA tooling it can invoke
- Install debug access it needs
- Propose test harnesses for self-checking

Don't guess. Ask.

### 4. Audit open PRs and issues
Before writing new code, sweep the backlog:
- Close stale/invalid PRs with a one-liner
- Merge easy-win PRs that just need sign-off
- Close duplicate or fixed issues

### 5. Let it merge
Default to merge, not suggest. Branch -> PR -> auto-merge through staging.
- Self-review every PR with evidence (test output, diff analysis)
- Tag human only on real ambiguity
- Merge when CI and staging pass

Safety gate: staging pipeline, not yolo to prod.

### 6. Takeover stuck work
Got a branch where agents run in circles? Start fresh:
- Throw away the existing attempt
- Old approach is dead weight, don't salvage
- Ship the fix in one clean pass

## Rules

- **Verify everything.** No change ships without evidence it works.
- **Trust deletion**, but verify. The model is better than a human at spotting unnecessary code.
- **Scope to the task.** Don't refactor the whole repo unprompted.
- **Start fresh on takeover.** The old branch is a sunk cost.

## Boundaries

- No user data or config file deletion without asking
- No force-push or git history rewrite
- No shipping to production without staging gate
- Flag uncertain deletions instead of silently keeping
