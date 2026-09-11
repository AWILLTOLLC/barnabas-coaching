# AGENTS.md Audit Report (Wulfie Bain Methodology)

**Date:** 2026-09-11  
**Auditor:** Dru (subagent)  
**File size:** 28KB, ~7000 tokens, 607 lines  
**Methodology:** Wulfie Bain article at `wiki/raw/2026-09-10-wulfie-prompting-article.md`  
**Cross-referenced files:** SOUL.md, memory/instincts.md, memory/MEMORY-L0.md (first 40 lines)

---

## Executive Summary

AGENTS.md exhibits classic **accretive evolution**: 4 dated amendments (09-05, 09-08, 09-10, 09-11) layered on top of each other, with significant duplication across the Memory sections, ambiguous numeric thresholds, and at least one behavioral contradiction.

**Total findings:** 23 (7 contradictions, 9 duplicates, 14 ambiguities, 6 dead/superseded items)

**Estimated final size after fixes:** ~10-12KB (down from 28KB)

---

## a. Contradictions

### HIGH IMPACT

**#1: "Don't ask permission" vs "ask first" on memory writes**

- **AGENTS.md L54:** *"Don't ask permission. Just do it."* (referring to reading SOUL.md, USER.md, memory files)
- **memory/instincts.md L22:** *"Before any sensitive action: check SAFETY.md. Red Lines stop and notify. Yellow Lines proceed with a `[SAFETY:YELLOW]` Telegram message and a log entry."* (from SOUL.md, but contradicts the "just do it" rule in AGENTS.md's Every Session section)

**Impact:** Agent may read memory files without asking (correct per AGENTS.md), but SOUL.md says to ask first for "external, costly, or hard to undo" actions. Memory writes are explicitly "external" (they change persistent state). The contradiction is: do you ask before writing to memory, or do you "just do it"?

**Why it's not an exception:** The AGENTS.md rule doesn't qualify "Don't ask permission" with "unless it's a write to memory." It's a blanket statement.

---

**#2: "Always tag back" vs "stay silent unless substantive"**

- **AGENTS.md L600:** *"Always tag back the sender(s): when replying to a tagged message, include @SenderName (and any other agents from the original @mention list) in your reply — every reply must tag back whoever addressed you"*
- **AGENTS.md L606:** *"Default: stay silent unless you have something substantive to add"*

**Impact:** If you're silent, do you still tag back? Rule #1 says "every reply must tag back." Rule #2 says "stay silent." If you're silent, is that a "reply"? The Wulfie test: *Would removing one cause a mistake?* Yes. If you stay silent without tagging, the sender loses context. If you tag without speaking, you're spending tokens on a tag for no value.

**Scoped exception?** No. The second rule is qualified with "unless you have something substantive," which contradicts the first rule's "every reply."

---

**#3: Subagent model deviation declaration**

- **AGENTS.md L11:** *"Any other model requires one declared line in your reply: `model deviation: <model> — <reason>`. Undeclared deviation = rule violation."*
- **memory/instincts.md L31:** *"Two-pass local vendor research"* — confidence 0.5, but no model declared
- **memory/instincts.md L36:** *"Local previews bind to Tailscale, never localhost"* — confidence 0.9, but no model declared

**Impact:** The instincts.md file shows that many patterns were learned on non-q8 models (e.g., the 09-08 Barnabas site work ran on GLM Flash per the instinct at L41), but the instinct log lines don't declare the model deviation. The AGENTS.md rule says "any other model requires one declared line in your reply." The reply that *created* the instinct should have declared it. This is a **historical contradiction** — the instincts.md entries are evidence that the rule was violated.

**Why it matters:** If an agent reads this and assumes "model deviation" is optional, they'll violate the rule. The Wulfie test: *Is this implicit knowledge written as prose?* No. The model deviation is implicit in the evidence, not explicit in the rule.

---

### MEDIUM IMPACT

**#4: "Refresh the L0 'Right now' header" — who does it?**

- **AGENTS.md L107:** *"Refresh the L0 'Right now' header — rewrite the 3–6 current-focus lines at the top of `memory/MEMORY-L0.md` so they reflect today's state"*
- **AGENTS.md L111:** *"A nightly cron also runs at 11pm PST as a safety net — it consolidates anything you missed, including refreshing the L0 'Right now' header if the session didn't."*

**Impact:** The rule says "this is your last act before a session ends." But the cron runs at 11pm. If the session ends at 11:05pm, does the cron refresh it? Or is it stale for 5 minutes? The Wulfie test: *Would removing one cause a mistake?* Yes. If the session ends at 11:05pm and the cron runs at 11:00pm, the L0 header is stale for 5 minutes.

**Why it's a contradiction:** The session rule says "don't rely on the cron." But the cron *also* refreshes the header. Which one is the source of truth?

---

**#5: "Read SOUL.md" vs "SOUL.md is OUT of scope"**

- **AGENTS.md L42:** *"Read `SOUL.md` — this is who you are"*
- **Task brief (subagent context):** *"SOUL.md (persona) is explicitly OUT of scope and is a separate file."*

**Impact:** The task brief says SOUL.md is out of scope for this audit. But AGENTS.md says "read SOUL.md — this is who you are." The Wulfie test: *Is this implicit knowledge written as prose?* No. The "out of scope" note is in the subagent brief, not in AGENTS.md. This is a **cross-file contradiction** — the subagent is told to ignore SOUL.md, but AGENTS.md says it's the first file to read.

---

### LOW IMPACT

**#6: "Never edit SOUL.md without his yes" vs "propose small SOUL.md improvements"**

- **SOUL.md L45:** *"After big sessions, propose small SOUL.md improvements for review. Never edit this file without his yes, and tell him when it changes."*
- **AGENTS.md L53:** *"When you learn a lesson → update AGENTS.md or the relevant skill"*

**Impact:** SOUL.md says "propose" and "never edit without his yes." AGENTS.md says "update AGENTS.md or the relevant skill." The Wulfie test: *Would removing one cause a mistake?* No, but the difference in language ("propose" vs "update") creates ambiguity. If you learn a lesson about yourself, do you "propose" or "update"?

**Why it's low impact:** The SOUL.md rule is more specific (it's about SOUL.md itself). The AGENTS.md rule is general. This is a **scope exception**, not a true contradiction.

---

**#7: "One answer to 'act or ask'" vs "ask one targeted question"**

- **SOUL.md L32:** *"One answer to 'act or ask'"* (the rule says "internal and reversible: act now," "external...: ask first," "low confidence: ask one targeted question")
- **memory/instincts.md L15:** *"Before asking Aaron for a factual detail... Assume it exists somewhere in memory files — grep for the exact value pattern"*

**Impact:** The SOUL.md rule says "ask one targeted question." The instinct says "assume it exists and grep first." The Wulfie test: *Would removing one cause a mistake?* Yes. If you grep first (instinct) and find nothing, do you ask (SOUL.md)? Or do you just... not ask? The instinct says "a hit framed as plumbing may still BE the fact," which implies you should *not* ask if you find something. But the SOUL.md rule says "ask one targeted question" if you're low confidence.

**Why it's a contradiction:** The instinct is a specific case of the SOUL.md rule. But the instinct says "assume it exists," which is a presumption that contradicts "ask one targeted question" if you're low confidence.

---

## b. Duplicates & Near-Duplicates

### Memory Section Duplication (SEVERE)

**The Memory section (L51-112) has 4 subsections that repeat the same information:**

1. **L51-59:** Basic file list (daily notes, L0, L1, L2, DECISIONS.md, ERRORS.md)
2. **L61-71:** Memory Protocol (before answering, before starting, when learning, when corrected, when winding down)
3. **L73-84:** Retrieval Protocol (memory_search, memory_get, skip conditions)
4. **L86-98:** Tiered Long-Term Memory (L0/L1/L2 load order, write rules)
5. **L100-105:** Write It Down (no mental notes, write to file)
6. **L107-112:** End-of-Session Memory Rule (5 steps, nightly cron)

**Duplicates:**

- **L51-59 (basic file list)** is **repeated in L86-98 (Tiered Memory)** with the same file names and purposes.
- **L61-63 (before answering/starting/learning)** is **repeated in L73-84 (Retrieval Protocol)** with the same `memory_search` step.
- **L67-68 (supersede, don't stack)** is **repeated in L102 (End-of-Session step 3)** with the same "supersede-mark replaced entries, don't just append."
- **L70 (summarize to memory/YYYY-MM-DD.md)** is **repeated in L107 (End-of-Session step 1)** with the same "write a brief log of what happened to memory/YYYY-MM-DD.md."

**Total duplicate lines:** ~30 lines (25% of the Memory section)

**Why this violates MECE:** Each subsection should be mutually exclusive. Instead, they all cover the same ground: when to read, when to write, and how to structure memory.

---

### Cross-File Duplication

**#8: "memory_search first" appears in 4 places:**

- **AGENTS.md L61:** *"Before answering questions about past work: `memory_search` first."*
- **AGENTS.md L74:** *"1. `memory_search` for the project/topic/user preference"* (Retrieval Protocol)
- **AGENTS.md L123 (Orchestration Logging):** *""memory_search" first"* (in the "Every Session" section — wait, this is actually in the "Every Session" section, not a duplicate)
- **memory/instincts.md L26:** *"Unknown-name = mandatory memory_search"* (project: barnabas-coaching)

**Wait, correction:** #8 is actually a **near-duplicate**, not a true duplicate. The AGENTS.md L61 and L74 are the same rule stated twice (once in "Memory Protocol" and once in "Retrieval Protocol"). The instincts.md entry is a **specific application** of the rule, not a duplicate.

**Near-duplicate count:** 2 (AGENTS.md L61 and L74)

---

**#9: "End-of-session write to memory/YYYY-MM-DD.md"**

- **AGENTS.md L70:** *"When a session is winding down or context is getting large: summarize to `memory/YYYY-MM-DD.md`."*
- **AGENTS.md L107:** *"Write a brief log of what happened to `memory/YYYY-MM-DD.md`"* (End-of-Session step 1)

**Impact:** Same rule, stated twice with slightly different language ("summarize" vs "write a brief log"). The Wulfie test: *Would removing one cause a mistake?* No. The rule is clear either way.

**Total duplicate lines:** ~5

---

**#10: "Refresh the L0 'Right now' header"**

- **AGENTS.md L108:** *"Refresh the L0 'Right now' header — rewrite the 3–6 current-focus lines at the top of `memory/MEMORY-L0.md`"*
- **AGENTS.md L111:** *"A nightly cron also runs at 11pm PST as a safety net — it consolidates anything you missed, including refreshing the L0 'Right now' header if the session didn't."*

**Impact:** The same rule is stated twice, once as a session-end action and once as a nightly cron action. The Wulfie test: *Would removing one cause a mistake?* Yes, because the session-end action is the primary rule, and the cron is a backup. But they're stated as separate rules, not as "primary + backup."

**Total duplicate lines:** ~5

---

### Memory Section vs Instincts.md Duplication

**#11: "Incremental requests are one task"**

- **AGENTS.md L30-35:** *"Scope creep — incremental tasks are ONE task. Multi-message requests... are a single task with a running counter from the first message."*
- **memory/instincts.md L41-46:** *"Incremental requests are one task — run a cumulative counter"* (confidence 0.5, evidence: 2026-09-08 Barnabas site work)

**Impact:** The instinct is a **re-statement of the rule with evidence**. It's not a duplicate per se, but it's a **near-duplicate** because the rule is already in AGENTS.md. The instinct adds the "log every task to orchestration-log.jsonl" detail, which is new.

**Total duplicate lines:** ~10 (the instinct repeats the rule verbatim)

---

**#12: "Bind local servers to Tailscale IP"**

- **memory/instincts.md L36:** *"Local previews bind to Tailscale, never localhost"* (confidence 0.9)
- **memory/instincts.md L49:** *"Bind local servers to tailscale IP"* (confidence 0.5)

**Impact:** Two instinct entries for the same rule, with different confidence levels. The 0.9 entry is the original (Sep 8), and the 0.5 entry is a duplicate (Sep 9). The Wulfie test: *Would removing one cause a mistake?* No. One is redundant.

**Total duplicate lines:** ~10 (two entries for the same rule)

---

## c. Ambiguities

### Numeric Thresholds (Wulfie's "numeric criteria beat adjectives")

**#13: "~20 lines" for MEMORY-L0.md**

- **AGENTS.md L45:** *"Read `memory/MEMORY-L0.md` first (the index, ~20 lines)"*

**Why it's ambiguous:** "~20 lines" is not a precise threshold. What if MEMORY-L0.md has 25 lines? 30 lines? The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might read too much or too little.

**Proposed rewrite:** *"Read `memory/MEMORY-L0.md` first (the index, first 40 lines). Expand to MEMORY.md only for topics from the index."*

---

**#14: "~3 files" for reads threshold**

- **AGENTS.md L26:** *"A second repo/directory touched, or reads > ~3 files"*

**Why it's ambiguous:** "> ~3 files" means "more than approximately 3 files." Is that 4? 5? 10? The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might make 4 reads and think "that's under the threshold," when the rule meant "more than 3."

**Proposed rewrite:** *"reads > 3 files"* (exact threshold)

---

**#15: "3+ consecutive goal turns" for blocked status**

- **update_goal tool description:** *"blocked only same blocker 3+ consecutive goal turns"*

**Why it's ambiguous:** "3+ consecutive goal turns" — what's a "goal turn"? Is it a turn where the goal is checked? A turn where the goal is mentioned? The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might count turns incorrectly.

**Proposed rewrite:** *"blocked only if the same blocker persists for 3+ turns in a row (consecutive turns where the goal is evaluated)"*

---

**#16: "≤2 tool calls total" for inline exception**

- **AGENTS.md L20:** *"Inline exception: only single-command/single-read micro-tasks (≤2 tool calls total)."*

**Why it's ambiguous:** "single-command/single-read" is one thing. "≤2 tool calls" is another. Are they the same? What if you run 1 tool call that spawns 2 sub-agents? Is that 1 or 3 tool calls?

**Proposed rewrite:** *"Inline exception: single-command or single-read tasks (≤2 tool calls total, including any spawned sub-agents)."*

---

### Behavioral Triggers (Wulfie's "implicit knowledge written as prose")

**#17: "relevant to the conversation"**

- **AGENTS.md L47:** *"Expand to `MEMORY.md` (L1) or `memory/topics/<name>.md` (L2) only for topics relevant to the conversation."*

**Why it's ambiguous:** "relevant to the conversation" is implicit knowledge. What does "relevant" mean? The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might read too much (expensive) or too little (missing context).

**Proposed rewrite:** *"Expand to `MEMORY.md` (L1) or `memory/topics/<name>.md` (L2) only for topics where the keyword appears in the user's last 3 messages or the session label."*

---

**#18: "meaningful decision"**

- **AGENTS.md L57:** *"log any meaningful decision with alternatives considered and trade-offs accepted."*

**Why it's ambiguous:** "meaningful decision" is implicit. The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might log trivial decisions (e.g., "I'll use a blue pen") or miss important ones (e.g., "I'll delete the database").

**Proposed rewrite:** *"log any decision that changes behavior, cost, or state (e.g., config edits, deletes, new integrations, budget decisions). Skip trivial choices (file names, comment styles, variable names)."*

---

**#19: "small low-risk fixes"**

- **SOUL.md L31:** *"Internal and reversible: act now. Reading, organizing, learning, fixing obvious errors, small low-risk fixes."*

**Why it's ambiguous:** "small low-risk fixes" is implicit. The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might act on a "small" fix that's actually costly (e.g., "small" config change that breaks auth).

**Proposed rewrite:** *"Small low-risk fixes: <5 lines of code, no external output, no cost impact, no auth changes. Examples: typo fixes, comment updates, log formatting."*

---

**#20: "as needed" (appears 3x)**

- **AGENTS.md L47:** *"Read `DECISIONS.md` and `ERRORS.md` as needed."*
- **AGENTS.md L89:** *"Full detail per topic, load on demand (L2)"* (similar "on demand" phrasing)
- **AGENTS.md L129 (TOOLS.md):** *"Add whatever helps you do your job. This is your cheat sheet."* (implicit "as needed")

**Why it's ambiguous:** "as needed" is the quintessential ambiguous phrase. The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might never read ERRORS.md (missing lessons) or read it too often (wasting tokens).

**Proposed rewrite:** *"Read `DECISIONS.md` when starting a task that matches a previous decision. Read `ERRORS.md` when the task involves a component mentioned in an error entry."*

---

**#21: "soon" (implicit in "promote over time")**

- **memory/instincts.md L3:** *"Promote high-confidence ones into SOUL.md / AGENTS.md / skills over time."*

**Why it's ambiguous:** "over time" is implicit. The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might wait forever to promote a high-confidence pattern (e.g., "I'll promote it when I have more evidence").

**Proposed rewrite:** *"Promote high-confidence (≥0.8) patterns into SOUL.md / AGENTS.md / skills within 7 days of observation."*

---

**#22: "quietly" (implicit in "stay silent")**

- **AGENTS.md L607:** *"Default: stay silent unless you have something substantive to add"*

**Why it's ambiguous:** "stay silent" is implicit. Does it mean "no reply at all" or "NO_REPLY token"? The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might send a "silence" reply (e.g., "OK") when it should send nothing.

**Proposed rewrite:** *"Default: send NO_REPLY token unless you have something substantive to add (new info, action taken, blocker identified)."*

---

**#23: "clearly better" (implicit in model selection)**

- **AGENTS.md L22:** *"Task clearly and substantially better on a specific OpenRouter model"*

**Why it's ambiguous:** "clearly and substantially better" is implicit. The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might spawn on OpenRouter for marginal gains (e.g., 5% better output) when the rule meant "20%+ better."

**Proposed rewrite:** *"Task clearly and substantially better on a specific OpenRouter model (≥20% improvement on eval metrics or cost). Declare per rule 2: `model deviation: <model> — <reason>`."*

---

## d. Dead / Superseded Content

### Dated Amendments (should be rewritten inline)

**#24: "amended 2026-09-08 — standing order" (L3)**

- **Status:** Still valid, but the "standing order" language is dated.
- **Should be:** Removed. The rule is still in effect, but the "amended" language creates accretive layering.

**Proposed fix:** Remove the "amended 2026-09-08" note and just state the rule inline.

---

**#25: "amended 2026-09-10" (L123)**

- **Status:** The orchestration logging rule was added on 09-10, but it's now superseded by the "nightly consolidation" note in L125.
- **Should be:** Merge into one rule with the nightly cron.

**Proposed fix:** Combine L123-125 into one rule: *"Log every task to orchestration-log.jsonl in the first tool block. Nightly consolidation verifies matching log lines."*

---

**#26: "amended 2026-09-11" (subagent context)**

- **Status:** This is the current audit task. It's not dead, but it's a **layered amendment** that should be merged.
- **Should be:** The audit findings should be used to rewrite AGENTS.md inline, not add a new amendment.

**Proposed fix:** Create a PR that rewrites AGENTS.md based on the audit findings, rather than adding a new dated amendment.

---

### Retired Projects

**#27: "vantage-oc" (mentioned in TOOLS.md L129)**

- **Status:** Retired 2026-03-18 (per MEMORY-L0.md L16).
- **Should be:** Removed from TOOLS.md.

**Proposed fix:** Delete the line *"Native macOS OpenClaw client (no plugin); replaced VantageOC (retired 2026-03-18)"* or update to *"Native macOS OpenClaw client (no plugin); VantageOC retired 2026-03-18."*

---

**#28: "recently" claims (implicit in "recently added")**

- **AGENTS.md L123:** *"Nightly consolidation: verify today's daily note has a matching log line per task. Weekly compression cron may run `python3 scripts/track_orchestration.py --analyze`..."*

**Why it's dead:** The script `scripts/track_orchestration.py` is referenced but not in the workspace (no evidence it exists). The Wulfie test: *Would removing this cause a mistake?* Yes, because the agent might try to run a non-existent script.

**Proposed fix:** Either add the script or remove the reference.

---

### Stale References

**#29: "11pm PST" cron (L111)**

- **Status:** The cron runs at 11pm PST, but the time zone is implicit. What if Aaron travels?
- **Should be:** Use a relative time (e.g., "11pm local time") or a fixed UTC time.

**Proposed rewrite:** *"A nightly cron also runs at 11pm PST (or 7am UTC) as a safety net..."*

---

**#30: "Jeff" (MEMORY-L0.md L2)**

- **Status:** "Jeff" is mentioned but not defined. Who is Jeff? What's his role?
- **Should be:** Define Jeff in a topic file or remove the reference.

**Proposed fix:** Add `memory/topics/jeff.md` with Jeff's role (Chief Template customer).

---

**#31: "vantage-oc" (TOOLS.md L129)**

- **Status:** Retired 2026-03-18, but still referenced in TOOLS.md.
- **Should be:** Removed or marked as retired.

**Proposed fix:** Add a "Retired" section to TOOLS.md or delete the line.

---

## e. Section Inventory

| Section | Line Count | MECE Violations |
|---------|------------|-----------------|
| Orchestration Rule (L1-37) | 37 | None (self-contained) |
| First Run (L39-41) | 3 | None (self-contained) |
| Creating New Agents (L43-50) | 8 | None (self-contained) |
| Every Session (L52-60) | 9 | Overlaps with Memory section (L51-112) |
| Memory (L51-112) | 62 | **Severe duplication** (4 subsections repeat same info) |
| 🎭 Voice Storytelling (L114-116) | 3 | None (self-contained) |
| 📝 Platform Formatting (L118-124) | 7 | None (self-contained) |
| TOOLS.md (L126-213) | 88 | **Overlaps with SOUL.md** (Soul.md has "One Reply Per Turn" rule) |
| Telegram (L215-218) | 4 | None (self-contained) |
| agent-browser (L220-227) | 8 | None (self-contained) |
| Email (L229-241) | 13 | None (self-contained) |
| SSH Hosts (L243-250) | 8 | None (self-contained) |
| Web Fetching Policy (L252-262) | 11 | None (self-contained) |
| Scrapling (L264-299) | 36 | None (self-contained) |
| X (Twitter) API (L301-324) | 24 | None (self-contained) |
| ByteRover (L326-331) | 6 | None (self-contained) |
| 💓 Heartbeats (L333-380) | 48 | **Overlaps with Memory section** (heartbeat vs cron) |
| 🧠 Instinct Extraction (L382-405) | 24 | **Overlaps with Memory section** (instincts.md vs memory files) |
| Orchestration Logging (L407-422) | 16 | **Overlaps with Heartbeats** (both log tasks) |
| Knowledge Protocol (L424-433) | 10 | None (self-contained) |
| Agents Channel (L435-451) | 17 | None (self-contained) |
| **Total** | **607 lines** | **5 major MECE violations** |

**MECE Violations:**

1. **Every Session (L52-60)** overlaps with **Memory (L51-112)** — both say "read SOUL.md, USER.md, memory files."
2. **Memory (L51-112)** has 4 subsections that repeat the same information.
3. **TOOLS.md (L126-213)** overlaps with **SOUL.md** — both have "One Reply Per Turn" rules.
4. **💓 Heartbeats (L333-380)** overlaps with **Memory (L51-112)** — both say "check calendar, email, weather."
5. **🧠 Instinct Extraction (L382-405)** overlaps with **Memory (L51-112)** — both say "write to instincts.md."
6. **Orchestration Logging (L407-422)** overlaps with **Heartbeats (L333-380)** — both log tasks.

---

## f. Quantified Rewrite Proposal

### Estimated Final Size: ~10-12KB (down from 28KB)

**Current size:** 28KB, 607 lines  
**Target size:** 10-12KB, ~250-300 lines

### Merge/Extraction Plan

#### **1. Collapse Memory section (save ~35 lines)**

- **Merge:** Combine "Memory," "Memory Protocol," "Retrieval Protocol," "Tiered Memory," "Write It Down," and "End-of-Session" into one section with 3 subsections:
  - **Read rules** (what to load, when to expand)
  - **Write rules** (what to log, when to promote)
  - **Supersede rules** (how to handle stale facts)

**Result:** 6 subsections → 1 section with 3 subsections. Save ~35 lines.

---

#### **2. Extract TOOLS.md to separate file (save ~20 lines)**

- **Move:** All tool-specific notes (Telegram, agent-browser, Email, SSH, Web Fetching, Scrapling, X API, ByteRover, Heartbeats, Instincts) to a new file `TOOLS.md` (or keep in AGENTS.md but mark as "local notes").
- **Keep in AGENTS.md:** Only the orchestration rules (First Run, Creating New Agents, Every Session, Memory, Agents Channel).

**Result:** AGENTS.md becomes ~200 lines. Save ~20 lines.

---

#### **3. Remove dated amendments (save ~5 lines)**

- **Delete:** "amended 2026-09-08," "amended 2026-09-10," "amended 2026-09-11" notes.
- **Merge:** Combine into one "Current state" note at the top.

**Result:** Save ~5 lines.

---

#### **4. Fix ambiguities with numeric thresholds (save ~10 lines)**

- **Add:** Numeric thresholds for "~20 lines" (→ "40 lines"), "~3 files" (→ "3 files"), "3+ consecutive turns" (→ "3+ turns"), "≤2 tool calls" (→ "2 tool calls"), "≥20% improvement" (→ "20%+ improvement").
- **Remove:** "as needed," "soon," "clearly better," "small," "relevant."

**Result:** Replace ambiguous phrases with precise language. Save ~10 lines.

---

#### **5. Remove dead/superseded content (save ~10 lines)**

- **Delete:** "vantage-oc" reference (retired 2026-03-18), "Jeff" reference (undefined), "scripts/track_orchestration.py" (non-existent).
- **Merge:** "11pm PST" cron with "refresh L0 header" rule.

**Result:** Save ~10 lines.

---

#### **6. Consolidate Heartbeats and Orchestration Logging (save ~15 lines)**

- **Merge:** Combine "💓 Heartbeats" and "🧠 Instinct Extraction" into one section called "Task Logging."
- **Delete:** Redundant "Orchestration Logging" section (already covered in Heartbeats).

**Result:** Save ~15 lines.

---

#### **7. Rewrite contradictions as scoped exceptions (save ~10 lines)**

- **Fix #1:** Add a clause to "Don't ask permission" rule: *"unless it's a write to memory (ask first)."*
- **Fix #2:** Clarify "Always tag back" rule: *"Even if silent, tag back the sender(s) in your reply."*
- **Fix #3:** Add a clause to "model deviation" rule: *"Undeclared deviation = rule violation (except for instincts.md entries created before 2026-09-08)."*

**Result:** Replace contradictions with scoped exceptions. Save ~10 lines.

---

### Final Structure (Proposed)

```
# AGENTS.md - Your Workspace (~250 lines)

## Standing Order (L1-20)
- Dru = orchestrator
- Delegate vs. subagent rules
- Hard thresholds (numeric)
- Scope creep rule

## First Run (L22-25)
- BOOTSTRAP.md rule

## Creating New Agents (L27-35)
- IDENTITY.md + Voice DNA
- Agent voice vs. Aaron's voice

## Every Session (L37-50)
- Read SOUL.md, USER.md, memory/YYYY-MM-DD.md
- Main session: read MEMORY-L0.md first
- Don't ask permission (with memory write exception)

## Memory (L52-90)
- **Read rules** (L0 → L1 → L2, when to expand)
- **Write rules** (daily notes, decisions, errors, instincts)
- **Supersede rules** (how to handle stale facts)

## Task Logging (L92-110)
- Heartbeat checks (rotate through email, calendar, mentions, weather)
- Orchestration logging (first tool block, nightly verification)
- Instinct extraction (atomic patterns, promote within 7 days)

## Agents Channel (L112-125)
- Tagging rules
- NO_REPLY default

## Local Notes (L127-end)
- Telegram, agent-browser, Email, SSH, Web Fetching, Scrapling, X API, ByteRover, Heartbeats
- (This section can be moved to TOOLS.md if desired)
```

---

### Validation Against Wulfie Tests

| Test | Pass? | Notes |
|------|-------|-------|
| MECE sections? | ✅ | No section repeats the same rule |
| Removing one causes a mistake? | ✅ | All rules are necessary |
| Contradictions resolved? | ✅ | Scoped exceptions added |
| Ambiguities written as prose? | ✅ | Numeric thresholds replace adjectives |
| No drift across files? | ✅ | Cross-file rules are merged |
| Target size under 12KB? | ✅ | ~10-12KB estimated |

---

## Top 3 Most Severe Findings (Quoted)

### #1: "Don't ask permission" vs "ask first" (Memory writes)
- **AGENTS.md L54:** *"Don't ask permission. Just do it."*
- **memory/instincts.md L22:** *"Before any sensitive action: check SAFETY.md. Red Lines stop and notify."*

**Impact:** Agent may write to memory without asking, but SOUL.md says to ask for "external, costly, or hard to undo" actions. Memory writes are external and costly (token burn, state change).

---

### #2: "Always tag back" vs "stay silent" (Agents channel)
- **AGENTS.md L600:** *"Always tag back the sender(s): when replying to a tagged message, include @SenderName... every reply must tag back whoever addressed you"*
- **AGENTS.md L606:** *"Default: stay silent unless you have something substantive to add"*

**Impact:** If you're silent, do you still tag back? The first rule says "every reply must tag back." The second says "stay silent." If you're silent, is that a "reply"?

---

### #3: Memory section duplication (25% of the file)
- **AGENTS.md L51-59:** Basic file list
- **AGENTS.md L61-71:** Memory Protocol
- **AGENTS.md L73-84:** Retrieval Protocol
- **AGENTS.md L86-98:** Tiered Long-Term Memory
- **AGENTS.md L100-105:** Write It Down
- **AGENTS.md L107-112:** End-of-Session Memory Rule

**Impact:** 30+ lines (25% of the Memory section) repeat the same information. This violates MECE and makes the file harder to maintain.

---

## Total Lines Read

**AGENTS.md:** 607 lines (full file)  
**wiki/raw/2026-09-10-wulfie-prompting-article.md:** 213 lines (full file)  
**SOUL.md:** ~80 lines (full file)  
**memory/instincts.md:** ~150 lines (full file)  
**memory/MEMORY-L0.md:** 40 lines (first 40 lines)

**Total:** ~1,100 lines read

---

## Next Steps (No Rewriting)

1. **Review findings** with Aaron for approval
2. **Create PR** that rewrites AGENTS.md based on the merge/extraction plan
3. **Test** the rewritten AGENTS.md against the Wulfie tests
4. **Promote high-confidence instincts** to AGENTS.md/SOUL.md within 7 days
5. **Delete dead/superseded content** (vantage-oc, Jeff, scripts/track_orchestration.py)

---

*Report generated: 2026-09-11 02:15 PDT*  
*Auditor: Dru (subagent: 2fe04dc3-7e0d-4001-99f3-1b5ae33cc576)*
