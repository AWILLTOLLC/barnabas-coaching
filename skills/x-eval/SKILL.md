---
name: x-eval
version: 1.0.0
description: |
  Evaluate an X/Twitter post the user sends as a link. Use whenever a message
  contains an x.com or twitter.com status URL — especially a bare link with no
  other text, or a link with "evaluate", "check", "is this legit", "thoughts?".
  Fetches the post via the fxTwitter API (no key, no login) and returns a
  structured evaluation: what is claimed, what is verifiable, hype-to-substance
  ratio, author credibility, and a worth-your-time verdict. Reply on the same
  channel the link arrived on.
allowed-tools:
  - Bash
  - WebSearch
  - WebFetch
---

# x-eval: Evaluate X/Twitter posts

A link to an X post is a question: "should I care about this?" Answer it.

## Step 1 — Fetch

Run the bundled fetcher with the URL exactly as received:

```bash
scripts/fetch_tweet.sh "<url>"
```

(Path is relative to this skill's directory.) It returns JSON: author (name,
handle, followers, bio), text, date, engagement metrics, quoted tweet, media
alt-text, poll, article preview. It handles x.com, twitter.com, fxtwitter,
vxtwitter and fixupx forms.

If it errors, say so plainly and stop — do not evaluate a post you could not
read. Never guess at content from the URL slug.

## Step 2 — Corroborate (only when the post makes checkable claims)

If the post asserts facts (a benchmark, a release, a paper result, a number),
spend ONE WebSearch checking the load-bearing claim. Skip this for pure
opinion, jokes, or vibes — do not pad the evaluation with searches it does
not need.

## Step 3 — Evaluate

Judge these five things, briefly:

1. **Claim** — what is actually being asserted, stripped of framing. One
   sentence. If nothing is asserted, say "no claim, this is commentary/humor."
2. **Checkable?** — is the claim verifiable, and did your check confirm it?
   Distinguish "verified", "plausible but unverified", "contradicted", and
   "unfalsifiable".
3. **Hype-to-substance** — screenshots without links, "insane/wild/nobody is
   talking about", engagement-bait structure, missing primary sources all
   raise it. A linked paper, repo, or reproducible demo lowers it.
4. **Author** — follower count, bio, and what they gain from you believing
   this (selling a course/tool/newsletter is relevant context, not automatic
   disqualification).
5. **Age** — check the post date. AI news decays fast; flag anything over a
   few weeks old as possibly stale or already superseded.

## Step 4 — Reply

Reply on the channel the link arrived on. Format, always in this order:

```
🔎 @handle (followers, date)
Claim: <one sentence>
Check: <verified / unverified / contradicted — with the one fact that decides it>
Substance: <low/medium/high + one-line why>
Verdict: <one of: Worth your time / Interesting if X matters to you / Skip / Old news / Misleading>
```

Then at most two sentences of color. Hard cap the whole reply at ~120 words —
the point of this skill is saving the user a read, not replacing one long read
with another. No hedging both ways: pick a verdict.

If the post is a thread opener, evaluate the opener and note "thread — want
the full thread pulled?" rather than fetching every reply preemptively.
