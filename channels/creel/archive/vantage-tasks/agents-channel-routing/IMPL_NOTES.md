# Implementation Notes — Agents Channel @Mention Routing

**Implemented by:** Eagle (coder subagent)  
**Date:** 2026-03-14  
**Build status:** ✅ Clean

---

## Summary

Implemented three changes per the spec:

### 1. `agents-channel.ts` — New Functions

**`normalizeAgentName(name: string): string`**
- Converts to lowercase, strips all non-alphanumeric characters
- Used for case-insensitive, punctuation-insensitive matching
- e.g., `"Black Raven"` → `"blackraven"`, `"morse-command"` → `"morsecommand"`

**`buildReplyToList(mentions: string[], roster: RosterEntry[], excludeSlug: string): string[]`**
- Returns array of names for `[reply-to: ...]` prefix
- Always includes `"Aaron"` first (operator)
- Includes other tagged agents (resolved to canonical names), excluding:
  - The recipient agent (via `excludeSlug`)
  - `@all`
  - `@aaron` (already included as first element)

### 2. `rpc.ts` — `vantage.message` Handler Updates

**Operator-only / unknown mention detection:**
- After extracting mentions, checks if ANY mention matches a roster entry OR `@all`
- If mentions exist but NONE match → skip fan-out entirely (returns `fanned: 0`)
- This handles:
  - `@Aaron` only (operator self-talk)
  - `@FakeAgent` (unknown mentions with no valid targets)

**Reply-to injection:**
- For each fan-out target, builds reply-to list via `buildReplyToList()`
- Injects `[reply-to: @Aaron @OtherAgents]` prefix into the message
- Format: `[agents-channel][reply-to: @Aaron @Maven] Operator: @Eagle @Maven what do you think?`

### 3. `rpc.ts` — `vantage.channels.delete` Handler Updates

**Roster cleanup on channel deletion:**
- Before deleting the channel, checks for an agents channel
- If found, removes the deleted channel's agent from the roster
- Calls `invalidateRosterInjection()` to force re-injection on next message

---

## Files Changed

| File | Changes |
|------|---------|
| `src/agents-channel.ts` | Added `normalizeAgentName()`, `buildReplyToList()` |
| `src/rpc.ts` | Updated imports; added operator-only detection + reply-to injection in `vantage.message`; added roster cleanup in `vantage.channels.delete` |

## Files NOT Changed (per spec)

- `src/types.ts`
- `src/store.ts`
- `src/index.ts`
- `openclaw.plugin.json`
- `~/.openclaw/openclaw.json`

---

## Testing Notes

No unit tests added (spec didn't require them). Manual testing recommended:

1. **Tag single agent:** `@Eagle what's the build status?` → only Eagle receives
2. **Tag multiple agents:** `@Eagle @Maven coordinate on this` → both receive, each sees `[reply-to: @Aaron @OtherAgent]`
3. **Tag @all:** `@all team update` → all agents receive
4. **Tag @Aaron only:** `@Aaron note to self` → no agents receive (`fanned: 0`)
5. **Unknown @mention:** `@FakeAgent hello` → no agents receive (no match, no @all)
6. **Delete channel:** delete a channel that was in the roster → verify roster entry is removed

---

## Edge Cases Handled

- Empty mentions → full broadcast (existing behavior)
- `@all` present → full broadcast (existing behavior)
- Only `@Aaron` → skip fan-out
- Unknown mentions only → skip fan-out
- Self-mention by agent (e.g., `@Eagle` in Eagle's reply) → not affected (llm_output doesn't re-fan-out)

---

## Gateway Restart

**NOT performed.** Per operating rules, Aaron must approve gateway restarts. The changes are compiled to `dist/` and will take effect on next gateway restart.
