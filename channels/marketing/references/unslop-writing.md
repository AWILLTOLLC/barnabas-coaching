# Unslop — Anti-AI-Slop Writing Profile
_Source: github.com/mshumer/unslop — writing.md profile, adapted for Maven/marketing use._
_Loaded automatically when drafting any copy: blog posts, GBP descriptions, landing pages, LinkedIn posts, emails, ad copy._

---

## Phrases — Never Use These

Not even close variants:

- "In today's [adjective] landscape/world/era"
- "In an increasingly [adjective] world"
- "It's not just about X — it's about Y"
- "Here's the thing"
- "Here's why that matters"
- "Let's dive in" / "Let's dive deeper" / "Let's unpack this"
- "At its core"
- "At the end of the day"
- "It's worth noting that"
- "This is where things get interesting"
- "The short answer is" / "The long answer is"
- "But here's the catch"
- "Think about it this way"
- "This isn't just [X] — it's [grander version of X]"
- "The reality is"
- "What does this mean for [audience]?"
- "Spoiler alert:"
- "Let that sink in"
- "The bottom line"
- "In other words"
- "Make no mistake"
- "It goes without saying"
- "The question isn't whether X, but Y"
- "X is more than just Y — it's Z"
- "This raises an important question"
- "To put it simply"
- "Perhaps most importantly"
- "The good news is" / "The bad news is"

---

## Words — Never Use These

- landscape, paradigm, leverage, robust, seamless, ecosystem, holistic, nuanced, compelling, innovative, crucial, essential, fundamental
- "delve" or "delve into"
- "navigate" used metaphorically (navigate challenges, navigate complexity)
- "unlock" used metaphorically (unlock potential, unlock growth)
- "double-edged sword"
- "at the intersection of X and Y"

---

## Structural Patterns — Avoid

- Don't open with a broad sweeping claim about "the world" or "the industry" before narrowing to the point. Start with the actual point.
- Don't use: "[Broad claim]. But [complication]. Here's [resolution]."
- Don't close by restating the thesis in grander terms than the piece warrants.
- Don't default to: intro hook → context → 3–5 body sections → takeaway → CTA. Vary it.
- Don't add a "The future of X" section near the end.
- Don't use "Final thoughts" or "Key takeaways" as section headers.
- Don't number points unless the reader actually needs them in order.
- Don't use rhetorical questions as transitions.

---

## Tonal Patterns — Avoid

- Don't hedge every claim with "might," "could potentially," "it remains to be seen." Either commit or don't make the claim.
- Don't perform enthusiasm. Not everything is fascinating, remarkable, game-changing, or transformative.
- Don't address the reader as "you" in every paragraph.
- Don't write with false-authority voice — treating opinion as settled consensus.
- Don't end paragraphs with one-sentence dramatic kickers meant to sound profound.

---

## The Standard

Write like a specific human with a specific voice — not like a median of all writing on the internet.

If you notice yourself about to use any pattern above, stop. Find a different way.

---

## Running unslop for New Domains

To generate a domain-specific profile (e.g., "B2B consulting emails" or "rave brand copy"):

```bash
git clone https://github.com/mshumer/unslop.git
cd unslop
python3 -m venv .venv && source .venv/bin/activate
python3 unslop.py --domain "B2B consulting landing pages" --count 50 --concurrency 5
```

Output lands in `./unslop-output/skill.md` — that's the file to keep and add here.
