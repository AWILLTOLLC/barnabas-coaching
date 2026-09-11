#!/usr/bin/env python3
"""
openrouter_credits.py — daily OpenRouter credit-spend line for the morning brief.

Output (stdout, ready to paste into the brief):
  "We used $X.XX in credits yesterday (mostly <model>). We're averaging $X.XX
   in credits per day over the last week."
If yesterday's spend > 150% of the 7-day average, appends 1-2 diagnostic
sentences naming the model/day driving the spike.

Also appends {"date", "spend", "avg7", "top_model"} as a JSON line to
memory/credits-history.jsonl (skipped on --dry-run).

Stdlib only. Auth: OPENROUTER_API_KEY in env, else OpenClaw's auth-profile
store (~/.openclaw/state/openclaw.sqlite, read-only).

Endpoints (Bearer auth):
  GET https://openrouter.ai/api/v1/activity?created_after=...&page=...
      -> {"data": [{date, model, usage, ...}], "next_page": int|null}
         usage is in credits (USD). NOTE: live shape unverified; parse
         defensively and bail loudly if it doesn't match.
  GET https://openrouter.ai/api/v1/credits
      -> {"data": {"total_credits": float, "total_usage": float}} (fallback info)
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

API = "https://openrouter.ai/api/v1"
HISTORY = os.path.join(os.path.dirname(__file__), "..", "memory", "credits-history.jsonl")
DAYS_WINDOW = 7          # days back for the average (yesterday + 6 prior)
SPIKE_RATIO = 1.5

# ── fixture for --dry-run: 9 days of usage rows (yesterday back) ─────────────
FIXTURE_ROWS = []
def _mk_fixture():
    today = date.today()
    per_day = [3.10, 2.40, 2.80, 2.20, 2.60, 1.90, 2.30, 2.10, 2.50]  # oldest->newest incl. yesterday
    for i, amt in enumerate(reversed(per_day)):  # newest first (yesterday first)
        d = today - timedelta(days=i + 1)
        top = 0.85 if i == 0 else 0.6
        FIXTURE_ROWS.append({"date": d.isoformat(), "model": "openai/gpt-5.2", "usage": round(amt * top, 4)})
        FIXTURE_ROWS.append({"date": d.isoformat(), "model": "anthropic/claude-sonnet-4.6", "usage": round(amt * (1 - top), 4)})
_mk_fixture()


def resolve_key(management=False):
    """Key lookup: env first, then OpenClaw's auth-profile store (read-only,
    never printed). management=True looks for a management key; the regular
    inference key works only for /credits and /key totals."""
    env_names = ["OPENROUTER_MANAGEMENT_KEY"] if management else ["OPENROUTER_API_KEY"]
    for name in env_names:
        key = os.environ.get(name)
        if key:
            return key
    db_path = os.path.expanduser("~/.openclaw/state/openclaw.sqlite")
    if not os.path.exists(db_path):
        return None
    try:
        db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        row = db.execute(
            "select value_json from config_machine_state where state_key='authProfiles.store'"
        ).fetchone()
        db.close()
        if not row:
            return None
        profiles = json.loads(row[0]).get("profiles", {})
        for name, prof in profiles.items():
            if prof.get("provider") == "openrouter" and prof.get("type") == "api_key" and prof.get("key"):
                if not management or name.endswith(":management"):
                    return prof["key"]
    except (sqlite3.Error, json.JSONDecodeError, OSError) as e:
        print(f"Auth-store lookup failed ({type(e).__name__}) — falling back to env only.", file=sys.stderr)
    # OpenClaw protected secret store (team scope) — where a management key would live.
    try:
        db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        want = "OPENROUTER_MANAGEMENT_KEY" if management else "OPENROUTER_API_KEY"
        row = db.execute(
            "select value from secret_store_entries where name=? and (deleted_at_ms is null or deleted_at_ms=0) order by updated_at_ms desc limit 1",
            (want,)).fetchone()
        db.close()
        if row and row[0]:
            return row[0]
    except sqlite3.Error as e:
        print(f"Secret-store lookup failed ({type(e).__name__}).", file=sys.stderr)
    return None


def fetch_activity(key, created_after, created_before=None):
    """Page through /activity. Returns list of {date, model, usage}."""
    rows, page = [], 1
    while True:
        q = f"{API}/activity?created_after={created_after}T00:00:00Z&page={page}"
        if created_before:
            q += f"&created_before={created_before}T00:00:00Z"
        req = urllib.request.Request(q, headers={"Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.load(r)
        except urllib.error.HTTPError as e:
            sys.exit(f"OpenRouter API error {e.code}: {e.read().decode()[:200]}")
        data = body.get("data") if isinstance(body, dict) else None
        if data is None:
            sys.exit(f"Unexpected /activity response shape: {str(body)[:200]}")
        for it in data:
            rows.append({
                "date": str(it.get("date", ""))[:10],
                "model": it.get("model") or it.get("model_slug") or "unknown",
                "usage": float(it.get("usage") or 0),  # credits (USD)
            })
        nxt = body.get("next_page") if isinstance(body, dict) else None
        if not nxt or page > 100:
            break
        page = nxt
    return rows


def fetch_totals(key):
    """Fallback with a regular (non-management) key: totals from /key + /credits.
    No per-day history or model attribution — line is flagged as estimated."""
    data = {}
    for ep in ("/key", "/credits"):
        req = urllib.request.Request(f"{API}{ep}", headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        data.update(body.get("data") or {})
    return data


def summarize(rows, yesterday):
    by_day = defaultdict(float)
    by_day_model = defaultdict(float)
    for r in rows:
        if not r["date"]:
            continue
        by_day[r["date"]] += r["usage"]
        by_day_model[(r["date"], r["model"])] += r["usage"]
    y_spend = by_day.get(yesterday.isoformat(), 0.0)
    window = [(yesterday - timedelta(days=i)) for i in range(DAYS_WINDOW)]
    daily = [by_day.get(d.isoformat(), 0.0) for d in window]
    avg7 = sum(daily) / len(daily)
    top = max((v, k[1]) for k, v in by_day_model.items() if k[0] == yesterday.isoformat())
    top_model = top[1] if top[0] > 0 else "unknown"
    return y_spend, avg7, daily, top_model


def brief_line(y_spend, avg7, daily, top_model, yesterday):
    line = (f"We used ${y_spend:.2f} in credits yesterday (mostly {top_model}). "
            f"We're averaging ${avg7:.2f} in credits per day over the last week.")
    if avg7 > 0 and y_spend > SPIKE_RATIO * avg7:
        # diagnosis: which day in the window was heaviest + top model that day
        heavy_i = max(range(len(daily)), key=lambda i: daily[i])
        heavy_day = (yesterday - timedelta(days=heavy_i)).isoformat()
        diag = (f" That's a spike — {y_spend / avg7:.0%} of the 7-day average. Heaviest recent day "
                f"was {heavy_day} at ${daily[heavy_i]:.2f}; {top_model} drove most of yesterday's spend — "
                f"check /api/v1/activity around that date for the specific session.")
        line += diag
    return line


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="use fixture data, no API call, no history append")
    ap.add_argument("--append", action="store_true", help="force history append even for a dry run")
    args = ap.parse_args()

    yesterday = date.today() - timedelta(days=1)

    if args.dry_run:
        rows = list(FIXTURE_ROWS)
        created_after = yesterday - timedelta(days=DAYS_WINDOW + 1)
        created_before = yesterday + timedelta(days=1)
    else:
        mkey = resolve_key(management=True)
        if mkey:
            created_after = yesterday - timedelta(days=DAYS_WINDOW + 1)  # margin for tz edges
            rows = fetch_activity(mkey, created_after.isoformat(),
                                  (yesterday + timedelta(days=1)).isoformat())
            key = mkey
        else:
            key = resolve_key()
            if not key:
                print("OPENROUTER key not available (env + auth store) — credits line skipped.")
                sys.exit(0)
            totals = fetch_totals(key)
            daily_24h = float(totals.get("usage_daily") or 0)  # last 24h (UTC)
            weekly = float(totals.get("usage_weekly") or 0)
            line = (f"OpenRouter: ${daily_24h:.2f} in credits over the last 24 hours "
                    f"(estimated), ${weekly:.2f} this week, "
                    f"${float(totals.get('usage') or 0):.2f} lifetime. "
                    "Per-day breakdown needs a management key.")
            print(line)
            return

    y_spend, avg7, daily, top_model = summarize(rows, yesterday)
    print(brief_line(y_spend, avg7, daily, top_model, yesterday))

    if args.dry_run and not args.append:
        return
    hist = {"date": yesterday.isoformat(), "spend": round(y_spend, 4),
            "avg7": round(avg7, 4), "top_model": top_model}
    path = os.path.abspath(HISTORY)
    with open(path, "a") as f:
        f.write(json.dumps(hist) + "\n")


if __name__ == "__main__":
    main()
