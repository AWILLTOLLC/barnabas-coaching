---
name: adversarial-code-review
description: Adversarial code review of a diff or PR — surface real bugs the author would actually want to fix, with a high bar and no theater. Use when the user asks to "review this", "review the diff", "review my changes", "review this PR", "any bugs in this?", "adversarial review", "tear this apart", "code review", or similar. Also use proactively before opening a PR or after a substantial set of changes.
source: https://initialcommit.co/library/skills/adversarial-code-review
---

# Adversarial Code Review

You are reviewing a code change as if you'll be the one paged at 3am when it breaks. Your job is to surface real bugs — not perform thoroughness. A review with two genuine findings beats a review with twelve performative ones.

The author already knows what they wrote. They're asking you to find what they missed.

## Step 1: Understand the intent

Before reading a single line of the diff, find out what the change is *supposed* to do. Read the PR description, commit messages, and any linked issue. If those are thin, read the most recent commit body in full.

You're building a hypothesis: "the author claims this change does X." The single richest adversarial finding is **the code doesn't match the stated intent** — a renamed flag the author forgot to flip, a "fix" that only handles 2 of the 3 cases described, a refactor that quietly changes behavior. You can't spot that mismatch if you don't know the intent first.

If intent is genuinely unrecoverable (no description, terse commit), say so in the final report and review on structural grounds only.

## Step 2: Get the diff

Use git:

```bash
# Committed changes vs target branch
MERGE_BASE=$(git merge-base origin/${TARGET_BRANCH:-main} HEAD)
git diff $MERGE_BASE HEAD

# Plus any uncommitted work
git diff HEAD
```

Read both. The committed diff shows the proposed change; the uncommitted diff shows work in progress. Treat them as one review surface.

If `TARGET_BRANCH` is ambiguous, check what branch the repo defaults to (`git remote show origin | grep 'HEAD branch'`) before guessing.

## Step 3: Decide what counts as a bug

A finding is worth flagging only if **all** of these are true:

1. **It meaningfully impacts correctness, performance, security, or maintainability.** Not style. Not "I would have written it differently."
2. **It's discrete and actionable** — one specific thing, with one specific fix. Not "the whole approach feels off."
3. **It was introduced in this change.** Pre-existing bugs are out of scope unless the change makes them materially worse.
4. **The author would fix it if you pointed it out.** If a reasonable engineer would shrug and say "yeah, intentional" or "fine for this codebase" — it's not a finding.
5. **You can prove it, not just speculate.** "This might break something elsewhere" is not a finding unless you can name the other code that's provably affected.
6. **It doesn't demand a level of rigor absent from the rest of the codebase.** Don't ask for exhaustive input validation in a personal scripts repo. Match the bar of the surrounding code.
7. **It's not just an intentional design choice you happen to disagree with.** Read the diff in context before assuming the author was wrong.

If nothing clears this bar, the right answer is: **no findings**. Say so plainly. A clean review is a real outcome, not a failure to look hard enough.

## Step 4: What to look for

### Logic and correctness

- Does the code actually do what the intent says it should?
- Changed conditional: does the new branch ever execute? The old one?
- Null/undefined/empty: can the new code encounter a value it doesn't handle?
- Race conditions: can two things happen in an unexpected order?
- Off-by-one: loops, slices, pagination — does the boundary case work?
- Error handling: is the new code swallowing errors it shouldn't, or not handling errors it can encounter?
- Input validation: can a caller pass something the new code doesn't expect?

### State and side effects

- Does the change mutate something shared that other code depends on?
- Is state initialized before it's read? Cleaned up when it should be?
- Does a failure leave partial state that the next call will trip over?
- Transaction boundaries: if two things should succeed or fail together, are they wrapped?

### Performance

- N+1 queries: does the new code query inside a loop?
- Blocking the event loop: synchronous I/O or heavy compute on the main thread?
- Memory: does the change allocate unbounded collections, keep references alive, or leak?

### Security

- Injection: is user input reaching a query, shell, or template unescaped?
- Auth: is the new endpoint/surface gated by the right permissions?
- Secrets: are keys, tokens, or passwords logged, committed, or sent to a client?

## Output format

```markdown
## Adversarial Review

**Intent:** [one-sentence summary of what the change claims to do]

### Findings

**1. [Finding title]**
**Location:** `path/to/file:line`
**What:** [concrete description of the bug]
**Fix:** [specific, actionable fix]
**Severity:** [critical | high | medium | low]

### Summary
[X findings: Y critical, Z high, …]
```

If no findings: "**No findings.** This diff is clean by the adversarial bar."