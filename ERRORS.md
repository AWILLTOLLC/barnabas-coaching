# ERRORS.md - Anti-Repeat System

_Every mistake logged here is a mistake that doesn't have to happen twice. Be specific. Unlogged mistakes repeat._

---

## Format

```
### [YYYY-MM-DD] What went wrong (short title)
**What happened:** Description of the mistake
**Why it happened:** Root cause
**Correct pattern:** What to do instead
**Prevention rule:** One-line rule to remember
```

---

## Log

### [2026-03-06] Backup script tarred live .openclaw directory, killed gateway
**What happened:** Ran `tar -czf` on `/root/.openclaw` while gateway was actively using session/db files. Gateway stopped responding. Aaron had to restore the backup.
**Root cause:** Tarring a live directory with active SQLite DBs and session files causes file contention and I/O starvation.
**Prevention rule:** Never tar the live .openclaw directory directly. Copy to staging first, then archive. Or use rsync with --exclude for active session files. Always test backup scripts during low-activity periods, not immediately after being asked.

### [2026-03-06] Chronic double-posting in every reply
**What happened:** Wrote text both before AND after tool calls in the same turn, every single time. Aaron called it out multiple times across the session.
**Why it happened:** Narrating setup before tools, then summarizing results after. Both fired in the same reply.
**Correct pattern:** Pick one: either write nothing before tools and one sentence after if needed, OR one sentence before tools and nothing after. Never both.
**Prevention rule:** If I wrote text before a tool call, my mouth is shut after it. No exceptions.
