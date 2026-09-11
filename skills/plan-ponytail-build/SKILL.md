---
name: "plan-ponytail-build"
description: "Review implementation plans with ponytail before building. Cuts over-engineering, saves time."
---

# plan-ponytail-build

**Review implementation plans with ponytail before building.** Cuts over-engineering, saves time.

## When
- Multi-step work (3+ steps, 30+ minutes)
- Building tools, scripts, or extensions
- Before any significant code implementation

## Steps

### 1. Write plan to file
- Create `tasks/<name>/PLAN.md` in workspace
- Include: goal, scope, files to create/update, build steps, timeline, success criteria
- Be specific but lean

### 2. Review with ponytail
- Run `skill_workshop` with `ponytail-review`
- Read the skill file at `~/.openclaw/skills/ponytail-review/SKILL.md`
- Apply review findings: delete dead code, shrink abstractions, remove YAGNI
- Goal: cut 50%+ of lines, save 75%+ of time

### 3. Revise plan
- Write revised plan to `PLAN-REVIEWED.md`
- Include ponytail findings: "Lines to cut: X, Time saved: Y"
- Keep only essential steps

### 4. Build with subagent
- Spawn subagent with revised plan
- Pass `PLAN-REVIEWED.md` as context
- Set 30-minute constraint (not original estimate)

### 5. Test end-to-end
- Run full workflow
- Verify success criteria
- Fix if needed

### 6. Ship
- Commit changes
- Document for others

## Why
- Prevents over-engineering before it happens
- Cuts scaffolding, not core logic
- Saves 2-3 hours per build
- Makes builds faster, simpler, more maintainable

## Example
❌ **Without ponytail:**
- Plan: 3 hours, 4 phases, GitHub repo, separate config files, agent API
- Build: 3 hours
- Result: 200 lines of scaffolding

✅ **With ponytail:**
- Plan: 30 minutes, 4 steps, inline config, no repo
- Build: 30 minutes
- Result: 20 lines of scaffolding

## Notes
- Ponytail finds: dead code, stdlib re-inventions, YAGNI abstractions, shrinkable loops
- Don't apply fixes immediately, just list them
- End with "net: -N lines possible" or "Lean already. Ship."
- If ponytail says "Lean already. Ship.", trust it and build
