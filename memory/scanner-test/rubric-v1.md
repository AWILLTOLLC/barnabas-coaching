# Scanner Rubric v1 — Judgment Criteria for "Useful" Events

## Purpose
The scanner ingests session deltas and surfaces **candidates** for memory consolidation. A candidate is anything that *might* be useful — decisions, commitments, state changes, preferences, corrections, or new facts about people/projects. The rubric filters out noise: small talk, transient status updates, one-off completed tasks with no lasting impact.

## Core Criteria — Mark as Candidate IF:

1. **Decision** — A choice was made that affects future action or blocks alternatives. Keywords: `decided`, `let's`, `go with`, `pick`, `choose`, `opt for`, `skip`, `skip it`, `not doing`, `dropping`.
2. **Commitment** — A promise to do something later, assign a task, or delegate. Keywords: `will do`, `going to`, `need to`, `should`, `remember to`, `todo`, `follow up`, `schedule`, `set a reminder`, `book`.
3. **State Change** — A condition changed (enabled/disabled, started/stopped, installed/uninstalled, added/removed). Keywords: `enabled`, `disabled`, `started`, `stopped`, `installed`, `uninstalled`, `deleted`, `removed`, `added`, `created`, `renamed`, `moved`.
4. **Preference Revealed** — Aaron expressed a taste, constraint, or boundary. Keywords: `prefer`, `like`, `don't like`, `want`, `don't want`, `okay with`, `fine with`, `not okay`, `avoid`, `skip`.
5. **Correction** — A mistake was identified and fixed. Keywords: `wrong`, `actually`, `no`, `not quite`, `missed`, `error`, `bug`, `fix`, `should have`, `instead`.
6. **New Fact** — Information about a person, project, tool, or system that may be referenced later. Keywords: names, URLs, versions, specs, prices, dates, contacts, credentials, IDs.

## Not Useful — Skip These:

- Small talk / greetings / chit-chat
- Transient status (e.g., "running now", "checking")
- One-off completed tasks with no lasting impact
- Meta-discussion about the conversation itself
- Repeated affirmations without new info
- Tool output dumps (unless a specific line matters)
- "Thinking out loud" without commitment

## Edge Cases (10+ examples with the call)

1. **"Let's skip the cron for now"** → **USEFUL** (decision: state change, blocks alternative)
2. **"I'll think about it"** → **SKIP** (transient, no commitment)
3. **"Actually, I meant X, not Y"** → **USEFUL** (correction)
4. **"Great, that works"** → **SKIP** (affirmation without new info)
5. **"Remember to check on this tomorrow"** → **USEFUL** (commitment/reminders)
6. **"The server is down"** → **SKIP** (transient status, unless followed by action)
7. **"Barrett prefers email over iMessage"** → **USEFUL** (preference + fact about person)
8. **"Fixed the bug"** → **SKIP** (one-off, unless bug details matter)
9. **"We're using Posteo SMTP now, not ProtonMail"** → **USEFUL** (state change + new fact)
10. **"This is a cool idea"** → **SKIP** (opinion without action)
11. **"Aaron's email is mac@kaw.cc"** → **USEFUL** (new fact about person)
12. **"Dru is now Chief of Staff"** → **USEFUL** (state change + title change)
13. **"The script ran successfully"** → **SKIP** (transient status)
14. **"Let's archive this project"** → **USEFUL** (decision + state change)
15. **"I need to rotate the API key"** → **USEFUL** (commitment)
16. **"The dashboard shows 10 sessions"** → **SKIP** (transient status from tool output)
17. **"OpenRouter key stored as OPENROUTER_MANAGEMENT_KEY"** → **USEFUL** (new fact + credential)
18. **"Aaron ordered a Tello SIM"** → **USEFUL** (commitment/action taken)
19. **"The gateway restarted at 19:50"** → **SKIP** (transient status, unless root-cause analysis follows)
20. **"Vera owns merkleandbloom.com"** → **USEFUL** (fact about person + ownership change)

## Heuristic Detection Rules (for deterministic scan)

- **Decision phrases:** `let's [verb]`, `decided to`, `going with`, `skip it`, `not doing`, `dropping`, `keeping`, `archiving`
- **Commitment phrases:** `will [verb]`, `going to [verb]`, `need to [verb]`, `should [verb]`, `remember to`, `todo`, `follow up on`, `schedule [verb]`, `set a reminder for`
- **State change phrases:** `enabled`, `disabled`, `started`, `stopped`, `installed`, `uninstalled`, `deleted`, `removed`, `added`, `created`, `renamed`, `moved to`, `changed to`
- **Preference phrases:** `prefer [X]`, `don't like [X]`, `like [X]`, `okay with [X]`, `not okay with [X]`, `avoid [X]`, `skip [X]`, `want [X]`, `don't want [X]`
- **Correction phrases:** `actually`, `no`, `not quite`, `wrong`, `should have`, `instead of`, `missed`, `error`, `bug`, `fix`, `that's not`
- **Fact statements:** Any line with URLs (`http[s]://`), email addresses (`@`), version numbers (`v[0-9]`), version ranges, prices (`$[0-9]`), dates (ISO or common formats), names of people/tools/projects, credential patterns (`KEY`, `TOKEN`, `SECRET`)

## Output Format for Candidates

Each staged candidate must include:
- `timestamp`: ISO timestamp from transcript
- `source`: Transcript file + line number
- `candidate_type`: decision | commitment | state_change | preference | correction | new_fact
- `evidence_line`: The exact line that triggered the candidate
- `confidence`: 0.0-1.0 (heuristic confidence based on keyword match strength)
- `summary`: 1-2 sentence summary of what happened
