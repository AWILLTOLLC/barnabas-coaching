---
name: ship-check
description: Pre-PR gauntlet: sweep, loose-ends, polish, but-for-real, blast-radius, adversarial-code-review. Use as the final step before a PR, or when the user says "ship-check", "ship check", "pre-PR", "final pass before the PR", "run the gauntlet", or "is this ready to ship". Does NOT open the PR or merge.
source: https://initialcommit.co/library/skills/ship-check
status: partial — full SKILL.md behind Initial Commit Founding Club paywall; this is a stub from the public page
---

# Ship Check

The closing-time gauntlet. Your branch works, but it's carrying the debris of getting there: debug probes, half-wired surfaces, AI-flavored copy, and whatever regressions the change quietly introduced. This runs the whole pre-PR pipeline and hands back a single report.

## The passes — order matters

1. **Sweep** — strip leftover scaffolding first, so every later pass reviews the real code.
2. **Loose Ends** — wire up every surface the feature should reach now that the code is clean.
3. **Polish** — fix copy and tone on the final, complete surface.
4. **But For Real** — actually run it: build, full test suite, and a real browser drive of the exact flow for any UI change. Verifies the new feature works.
5. **Blast Radius** — work outward from what the diff modified and hunt for existing features the change might have quietly broken.
6. **Adversarial Code Review** — the final bug pass, on a clean, complete, verified diff.

## How it runs

**Snapshot first.** Record `git rev-parse HEAD` and whether the tree was clean. Auto-applied changes land as unstaged edits; the report tells the user how to revert any pass or the whole run.

Each pass runs as an isolated subagent. Safe, reversible cleanups land automatically. Anything with a real decision (deletion, behavior change, deliberate rewrite, new wiring) is held for **one confirmation gate at the end**.

## Bundled sub-skills (members only)

The full download includes these as separate skills in a bundled folder:
- `skills/sweep/SKILL.md` — remove leftover scaffolding
- `skills/loose-ends/SKILL.md` — wire up incomplete surfaces
- `skills/polish/SKILL.md` — fix copy, tone, strip AI tells
- `skills/but-for-real/SKILL.md` — build, test, browser-drive
- `skills/blast-radius/SKILL.md` — regression hunt
- `skills/adversarial-code-review/SKILL.md` — final bug pass

**⚠️ This is a stub.** The full skill with all 9 bundled files requires a Founding Club membership at https://initialcommit.co/club. The workspace has `skills/adversarial-code-review/SKILL.md` as a standalone skill covering the last pass independently.