---
name: stop-slop
version: 1.0.0
description: |
  Remove AI writing patterns from prose. Use when drafting, editing, or reviewing
  text to eliminate predictable AI tells. Based on Hardik Pandya's stop-slop framework.
  Covers banned phrases, structural clichés, active voice, adverb removal, and scoring.
allowed-tools:
  - Read
  - Write
  - Edit
---

# Stop Slop

Eliminate predictable AI writing patterns from prose.

## Core Rules

1. **Kill all adverbs.** No -ly words. See [references/phrases.md](references/phrases.md) for the full list.

2. **Cut filler phrases.** Remove throat-clearing openers, emphasis crutches, vague declaratives. See [references/phrases.md](references/phrases.md).

3. **Break formulaic structures.** Avoid binary contrasts, negative listings, dramatic fragmentation, rhetorical setups, false agency. See [references/structures.md](references/structures.md).

4. **Active voice.** Every sentence needs a human subject doing something. No passive constructions. No inanimate objects performing human actions ("the complaint becomes a fix" → "someone fixed the complaint").

5. **Be specific.** No vague declaratives ("The reasons are structural"). Name the specific thing. No lazy extremes ("every," "always," "never") doing vague work.

6. **Put the reader in the room.** No narrator-from-a-distance voice. "You" beats "People." Specifics beat abstractions.

7. **Vary rhythm.** Mix sentence lengths. Two items beat three. End paragraphs differently. **No em dashes.**

8. **No Wh- sentence starters.** Never start a sentence with What, When, Where, Which, Who, Why, or How. Restructure.

9. **Trust readers.** State facts directly. Skip softening, justification, hand-holding.

10. **Cut pull-quotes.** If it sounds like a screenshot caption or LinkedIn banger, rewrite it as a plain statement.

## Quick Pre-Send Checklist

- Any adverbs? Kill them.
- Any passive voice? Find the actor, make them the subject.
- Inanimate thing doing a human verb ("the decision emerges")? Name the person.
- Sentence starts with a Wh- word? Restructure it.
- Any "here's what/this/that" throat-clearing? Cut to the point.
- Any "not X, it's Y" contrasts? State Y directly.
- 3 consecutive sentences match length? Break one.
- Paragraph ends with punchy one-liner? Vary it.
- Em-dash anywhere? Remove it.
- Vague declarative ("The implications are significant")? Name the specific implication.
- More than 2 items in a list? Drop one or collapse two.
- Sentence sounds quotable/shareable? Rewrite as a plain statement.

## Scoring

Rate 1-10 on each dimension. Below 35/50: revise.

| Dimension | Question |
|-----------|----------|
| Directness | Statements or announcements? |
| Rhythm | Varied or metronomic? |
| Trust | Respects reader intelligence? |
| Authenticity | Sounds human? |
| Density | Anything cuttable? |

## Reference Files

- [references/phrases.md](references/phrases.md) — banned phrases, adverbs, throat-clearing openers
- [references/structures.md](references/structures.md) — structural patterns to avoid

## Source

Based on [stop-slop by Hardik Pandya](https://github.com/hardikpandya/stop-slop). MIT License.
