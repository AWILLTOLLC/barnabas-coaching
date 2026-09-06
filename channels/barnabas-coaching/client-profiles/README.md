# Client Profiles — Barnabas Coaching Signal System

## Overview

This directory stores per-client behavioral signal logs for the Barnabas Coaching system.
It implements the Princeton online RL approach: capture implicit feedback from every coaching
session and use it to improve recommendations over time — without modifying the underlying model.

## How It Works

Every coaching session generates implicit signals:
- A client re-asks a question from a prior session → the recommendation didn't land
- A client reports they implemented something → the recommendation worked
- A client pushes back on a suggestion → wrong fit for this client type or industry
- A client comes back with a win → the advice was actionable and well-timed

We capture these signals instead of discarding them.

## File Structure

Each client gets their own append-only JSONL log:

```
client-profiles/
  <client-id>.jsonl      # e.g., acme-dental.jsonl, cascade-plumbing.jsonl
  README.md              # this file
  SCHEMA.md              # signal schema documentation
```

**Naming convention:** Use the company name, slugified (lowercase, hyphens, no spaces).
- "Acme Dental Group" → `acme-dental-group.jsonl`
- "Cascade Plumbing" → `cascade-plumbing.jsonl`

## Usage

Log a session signal:
```bash
echo '<signal-json>' | python3 scripts/client_signals.py --log <client-id>
```

Review a client's history before a session:
```bash
python3 scripts/client_signals.py --analyze <client-id>
```

Cross-client pattern analysis (run monthly):
```bash
python3 scripts/client_signals.py --summary
```

## The Compounding Effect

The more sessions logged, the more calibrated Barrett becomes for each client.
After 10+ clients, the system will surface:
- Which recommendations have the highest implementation rates
- Which industries need different framing
- Which client types show early churn signals

This is the moat. No other AI consultant is building this.
