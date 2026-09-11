---
source: /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/tasks/lessons.md
fetched: 2026-09-11
type: internal-doc
---
# Lessons

## 2026-09-10 — LLM thesis quality (user correction)
**Mistake:** Alert theses called every non-cat coin a "cat meta derivative" (model treated the shared launchpad + a meta narrative in CONTEXT as evidence) and called every coin's liquidity "thin" (no baseline to judge against). Also cited our own scout score as the coin's "strongest fact" (circular).
**Rules:**
1. Never put a narrative in an LLM prompt's context that shouldn't apply universally — gate it IN CODE (criteria.json `metas` keyword match), don't rely on prompt instructions to a 27B model.
2. Any qualitative judgment the LLM makes (thin/standard/strong) must come with a pre-computed, data-derived verdict from scout.db peers — the model copies the verdict, it doesn't judge.
3. Facts that are shared across all coins (launchpad) or self-referential (our score) must be explicitly labeled non-evidence in the prompt.
4. When the user reports a systemic output flaw, check the db for the true distribution before deciding what "normal" is (band liq/MC: fresh median 10.6% [p25 7.9, p75 14.9], estab median 4.5%, from 4 days / ~5,200 coins).
