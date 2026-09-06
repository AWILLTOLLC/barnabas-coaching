# Client Signal Schema

Each line in a `<client-id>.jsonl` file is a valid JSON object conforming to this schema.

## Schema

```json
{
  "timestamp": "ISO-8601",
  "session_number": 1,
  "client_id": "string",
  "client_type": "audit|retainer",
  "industry": "string",
  "company_size": "1-10|11-50|51-200",
  "session_type": "discovery|audit|retainer|check-in",
  "recommendations_given": ["rec1", "rec2"],
  "implementations_reported": ["what they actually did"],
  "re_questions": ["questions they re-asked from prior session"],
  "resistance_patterns": ["what they pushed back on and why"],
  "wins_reported": ["successes they came back to report"],
  "implicit_score": 0.0,
  "signal_type": "implementation|re_query|resistance|win|churn_risk",
  "notes": "qualitative context"
}
```

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO-8601 datetime of the session |
| `session_number` | int | Sequential session count for this client (1-indexed) |
| `client_id` | string | Slugified company name matching the filename |
| `client_type` | enum | `audit` (one-time $2,500) or `retainer` ($1,500/mo) |
| `industry` | string | Client's industry (e.g., "dental", "plumbing", "retail") |
| `company_size` | enum | Employee count band: `1-10`, `11-50`, or `51-200` |
| `session_type` | enum | `discovery`, `audit`, `retainer`, or `check-in` |
| `recommendations_given` | array | List of recommendations made in this session |
| `implementations_reported` | array | What the client said they actually implemented |
| `re_questions` | array | Questions they re-asked from a prior session |
| `resistance_patterns` | array | What they pushed back on and why |
| `wins_reported` | array | Successes they reported back |
| `implicit_score` | float | Composite signal score for this session (see scoring below) |
| `signal_type` | enum | Primary signal type for this entry |
| `notes` | string | Qualitative context Barrett wants to remember |

## Signal Scoring

Individual signals combine to produce `implicit_score`:

| Signal | Score | Meaning |
|--------|-------|---------|
| `implementation` | +1.0 | Client reported implementing a recommendation |
| `win` | +1.0 | Client came back with a concrete win |
| `re_query` | -0.8 | Client re-asked something from a prior session |
| `resistance` | -0.3 | Client pushed back on a recommendation |
| `churn_risk` | -1.5 | Cancellation mention, frustration, lack of engagement |

A session with 2 implementations and 1 re-query scores: `(2 × 1.0) + (1 × -0.8) = 1.2`

## Notes

- `implementations_reported` is the most valuable signal — it means advice landed AND was actionable
- `re_questions` are supervision signals: they tell you what to explain differently next time
- `resistance_patterns` grouped across clients reveal structural issues with certain recommendations
- `churn_risk` should trigger immediate review of what's not working for that client
