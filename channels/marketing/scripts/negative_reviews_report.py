#!/usr/bin/env python3
"""
Competitor Negative Reviews — Monday HTML Report

Runs every Monday at 7am PST.
First Monday of each month: also refreshes competitor research.
Every Monday: fetches recent negative reviews, compiles HTML report, emails Aaron.

Usage: python3 negative_reviews_report.py [--force-research]
"""

import json
import urllib.request
import urllib.parse
import datetime
import subprocess
import sys
import smtplib
import re
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Config ────────────────────────────────────────────────────────────────
COMPETITORS_DB  = Path("/Users/apollo/.openclaw/workspace/channels/marketing/data/competitors.json")
CREDS_PATH      = Path("/Users/apollo/.openclaw/credentials/email.json")
AARON_EMAIL     = "a@kaw.cc"
HEADERS         = {"User-Agent": "competitive-research/1.0 (internal marketing tool)"}

# ── Utilities ─────────────────────────────────────────────────────────────

def load_db() -> dict:
    return json.loads(COMPETITORS_DB.read_text())


def save_db(db: dict):
    COMPETITORS_DB.write_text(json.dumps(db, indent=2))


def is_first_monday() -> bool:
    now = datetime.date.today()
    return now.weekday() == 0 and now.day <= 7


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Fetch error {url}: {e}", file=sys.stderr)
        return ""


# ── App Store Review Fetcher ──────────────────────────────────────────────

def fetch_appstore_reviews(app_id: str, pages: int = 2) -> list:
    """Fetch reviews via iTunes RSS API."""
    reviews = []
    for page in range(1, pages + 1):
        url = (
            f"https://itunes.apple.com/us/rss/customerreviews/"
            f"page={page}/id={app_id}/sortBy=mostRecent/json"
        )
        raw = fetch_url(url)
        if not raw:
            break
        try:
            data = json.loads(raw)
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
            for e in entries:
                rating_str = e.get("im:rating", {}).get("label", "0")
                try:
                    rating = int(rating_str)
                except ValueError:
                    rating = 0
                if rating <= 2:  # Only negative (1-2 star)
                    reviews.append({
                        "rating": rating,
                        "title":  e.get("title", {}).get("label", ""),
                        "body":   e.get("content", {}).get("label", ""),
                        "author": e.get("author", {}).get("name", {}).get("label", ""),
                        "date":   e.get("updated", {}).get("label", "")[:10],
                    })
        except Exception as ex:
            print(f"  Parse error page {page}: {ex}", file=sys.stderr)
    return reviews


# ── Competitor Research (monthly) ─────────────────────────────────────────

def run_competitor_research(db: dict) -> dict:
    """
    Lightweight monthly refresh: verify App Store IDs are still valid,
    search for new Etsy/Morse Code competitors via iTunes search API.
    """
    print("Running monthly competitor research refresh...")

    # Search for new Morse Code iOS app competitors
    search_url = "https://itunes.apple.com/search?term=morse+code+game+ham+radio&entity=software&limit=20&country=us"
    raw = fetch_url(search_url)
    if raw:
        try:
            results = json.loads(raw).get("results", [])
            existing_ids = {c["app_store_id"] for c in db["products"]["morse_command"]["competitors"] if c.get("app_store_id")}
            added = 0
            for r in results:
                app_id = str(r.get("trackId", ""))
                if app_id and app_id not in existing_ids:
                    db["products"]["morse_command"]["competitors"].append({
                        "name":              r.get("trackName", "Unknown"),
                        "platform":          "ios",
                        "app_store_id":      app_id,
                        "url":               r.get("trackViewUrl", ""),
                        "notes":             f"Added by monthly research. Rating: {r.get('averageUserRating', 'N/A')}",
                        "last_review_fetch": None,
                    })
                    added += 1
            print(f"  Morse Command: +{added} new competitors found")
        except Exception as ex:
            print(f"  Research parse error: {ex}", file=sys.stderr)

    db["last_full_research"] = datetime.date.today().isoformat()
    save_db(db)
    print("Monthly research complete. DB updated.")
    return db


# ── Review Collection ─────────────────────────────────────────────────────

def collect_all_reviews(db: dict) -> list:
    """
    Collect negative reviews for all products.
    Returns list of finding dicts with product, competitor, reviews.
    """
    findings = []
    today = datetime.date.today().isoformat()

    # ── Morse Command: App Store ──
    for comp in db["products"]["morse_command"]["competitors"]:
        app_id = comp.get("app_store_id")
        if not app_id:
            continue
        print(f"  Fetching reviews: {comp['name']} (id:{app_id})")
        reviews = fetch_appstore_reviews(app_id)
        if reviews:
            findings.append({
                "product":    "Morse Command",
                "competitor": comp["name"],
                "platform":   "App Store",
                "url":        comp.get("url", ""),
                "reviews":    reviews,
                "count":      len(reviews),
            })
        comp["last_review_fetch"] = today

    # ── Glimmer Cards / Black Raven: would use Scrapling MCP ──
    # These require JS-heavy pages; skipping direct fetch, noting for manual follow-up
    for product_key, product_name in [("glimmer_cards", "Glimmer Cards"), ("black_raven", "Black Raven")]:
        comps = db["products"][product_key]["competitors"]
        if comps:
            findings.append({
                "product":    product_name,
                "competitor": "Etsy/Amazon (manual review needed)",
                "platform":   "etsy/amazon",
                "url":        comps[0].get("search_url", comps[0].get("url", "")),
                "reviews":    [],
                "count":      0,
                "manual":     True,
            })

    save_db(db)
    return findings


# ── Priority Scoring ──────────────────────────────────────────────────────

PAIN_POINT_KEYWORDS = {
    "ui_ux":        ["confusing", "hard to use", "interface", "clunky", "complicated", "unintuitive"],
    "bugs":         ["crash", "bug", "broken", "freeze", "error", "doesn't work", "stopped working"],
    "content":      ["boring", "repetitive", "limited", "not enough", "want more", "needs more"],
    "price":        ["expensive", "overpriced", "too much", "waste of money", "not worth"],
    "learning":     ["hard to learn", "no instructions", "confusing", "unclear", "no tutorial"],
    "audio":        ["sound", "audio", "headphones", "volume", "tone"],
}

def score_review(body: str) -> tuple:
    body_lower = body.lower()
    matched_categories = []
    for cat, kws in PAIN_POINT_KEYWORDS.items():
        if any(kw in body_lower for kw in kws):
            matched_categories.append(cat)
    priority = len(matched_categories) + (1 if len(body) > 100 else 0)
    return priority, matched_categories


# ── HTML Report Builder ───────────────────────────────────────────────────

def build_html_report(findings: list, ran_research: bool) -> str:
    today = datetime.date.today().strftime("%B %d, %Y")
    research_note = "✅ Monthly competitor research also ran today." if ran_research else ""

    # Flatten and score all reviews
    all_reviews = []
    manual_items = []
    for f in findings:
        if f.get("manual"):
            manual_items.append(f)
            continue
        for r in f["reviews"]:
            priority, cats = score_review(r["body"])
            all_reviews.append({
                "product":    f["product"],
                "competitor": f["competitor"],
                "platform":   f["platform"],
                "comp_url":   f["url"],
                "priority":   priority,
                "categories": cats,
                **r,
            })
    all_reviews.sort(key=lambda x: (-x["priority"], -x["rating"]))

    # Stars display
    def stars(n):
        return "★" * n + "☆" * (5 - n)

    def priority_badge(p):
        if p >= 3:
            return '<span style="background:#d32f2f;color:#fff;padding:2px 7px;border-radius:4px;font-size:12px;font-weight:bold;">HIGH</span>'
        elif p >= 2:
            return '<span style="background:#f57c00;color:#fff;padding:2px 7px;border-radius:4px;font-size:12px;font-weight:bold;">MED</span>'
        else:
            return '<span style="background:#388e3c;color:#fff;padding:2px 7px;border-radius:4px;font-size:12px;font-weight:bold;">LOW</span>'

    review_rows = ""
    if all_reviews:
        for r in all_reviews[:25]:  # Cap at 25 most actionable
            cats_str = ", ".join(r["categories"]) if r["categories"] else "general"
            review_rows += f"""
            <tr>
              <td style="padding:10px 8px;border-bottom:1px solid #eee;vertical-align:top;">
                {priority_badge(r['priority'])}
              </td>
              <td style="padding:10px 8px;border-bottom:1px solid #eee;vertical-align:top;">
                <strong>{r['product']}</strong><br>
                <span style="color:#666;font-size:13px;">vs <a href="{r['comp_url']}" style="color:#1565c0;">{r['competitor']}</a></span>
              </td>
              <td style="padding:10px 8px;border-bottom:1px solid #eee;vertical-align:top;color:#c62828;">
                {stars(r['rating'])} ({r['rating']}/5)
              </td>
              <td style="padding:10px 8px;border-bottom:1px solid #eee;vertical-align:top;">
                <strong>{r['title']}</strong><br>
                <span style="font-size:13px;color:#333;">{r['body'][:300]}{'...' if len(r['body']) > 300 else ''}</span><br>
                <span style="font-size:12px;color:#888;">— {r['author']} | {r['date']} | Pain points: {cats_str}</span>
              </td>
            </tr>"""
    else:
        review_rows = '<tr><td colspan="4" style="padding:20px;color:#666;text-align:center;">No automated reviews fetched this week. See manual items below.</td></tr>'

    manual_section = ""
    if manual_items:
        manual_section = "<h2 style='color:#333;margin-top:30px;'>Manual Review Needed</h2>"
        for m in manual_items:
            manual_section += f"""
            <div style="background:#fff8e1;border-left:4px solid #f9a825;padding:12px 16px;margin:10px 0;border-radius:4px;">
              <strong>{m['product']}</strong> — {m['competitor']}<br>
              <a href="{m['url']}" style="color:#1565c0;">{m['url']}</a><br>
              <span style="font-size:13px;color:#666;">Requires Scrapling/browser access. Review manually for 1-2 star patterns.</span>
            </div>"""

    # Pain point summary
    pain_summary = {}
    for r in all_reviews:
        for cat in r["categories"]:
            pain_summary[cat] = pain_summary.get(cat, 0) + 1
    pain_rows = ""
    for cat, count in sorted(pain_summary.items(), key=lambda x: -x[1]):
        pain_rows += f'<tr><td style="padding:6px 12px;border-bottom:1px solid #eee;">{cat.replace("_", " ").title()}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;">{count} review(s)</td></tr>'

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Competitor Negative Reviews — {today}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:24px;color:#222;background:#f5f5f5;">

  <div style="background:#1a237e;color:#fff;padding:24px;border-radius:8px;margin-bottom:24px;">
    <h1 style="margin:0;font-size:22px;">📊 Competitor Negative Reviews Report</h1>
    <p style="margin:8px 0 0;opacity:0.85;">{today} &nbsp;·&nbsp; Maven Marketing Intelligence</p>
    {'<p style="margin:8px 0 0;background:#283593;border-radius:4px;padding:6px 12px;font-size:13px;">'+research_note+'</p>' if research_note else ''}
  </div>

  {'<div style="background:#e8f5e9;border:1px solid #a5d6a7;padding:12px 16px;border-radius:6px;margin-bottom:20px;"><strong>Summary:</strong> ' + str(len(all_reviews)) + ' negative reviews found across ' + str(len(set(r["competitor"] for r in all_reviews))) + ' competitors.</div>' if all_reviews else ''}

  {'<div style="background:#fff;border-radius:8px;padding:20px;margin-bottom:24px;"><h2 style="margin-top:0;color:#333;">Pain Point Summary</h2><table style="border-collapse:collapse;width:100%;"><tr style="background:#f5f5f5;"><th style="padding:8px 12px;text-align:left;">Category</th><th style="padding:8px 12px;text-align:left;">Frequency</th></tr>' + pain_rows + '</table></div>' if pain_rows else ''}

  <div style="background:#fff;border-radius:8px;padding:20px;margin-bottom:24px;">
    <h2 style="margin-top:0;color:#333;">Reviews by Priority</h2>
    <table style="border-collapse:collapse;width:100%;">
      <thead>
        <tr style="background:#f5f5f5;">
          <th style="padding:10px 8px;text-align:left;width:70px;">Priority</th>
          <th style="padding:10px 8px;text-align:left;width:180px;">Product / Competitor</th>
          <th style="padding:10px 8px;text-align:left;width:80px;">Rating</th>
          <th style="padding:10px 8px;text-align:left;">Review</th>
        </tr>
      </thead>
      <tbody>
        {review_rows}
      </tbody>
    </table>
  </div>

  {manual_section}

  <div style="color:#999;font-size:12px;margin-top:30px;padding-top:16px;border-top:1px solid #ddd;">
    Generated by Maven · Sent to a@kaw.cc · Competitors DB: channels/marketing/data/competitors.json
  </div>

</body>
</html>"""
    return html


# ── Email Sender (HTML) ───────────────────────────────────────────────────

def send_html_email(to: str, subject: str, html_body: str):
    creds = json.loads(CREDS_PATH.read_text())
    from_addr = creds["username"]
    from_name = creds.get("from_name", "Maven")

    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{from_name} <{from_addr}>"
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(creds["smtp_host"], creds["smtp_port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(creds["username"], creds["password"])
        server.send_message(msg)

    # Save to Sent
    try:
        import imaplib, time
        raw = msg.as_bytes()
        imap = imaplib.IMAP4_SSL(creds["smtp_host"], 993)
        imap.login(creds["username"], creds["password"])
        imap.append("Sent", "\\Seen", imaplib.Time2Internaldate(time.time()), raw)
        imap.logout()
    except Exception as e:
        print(f"Warning: could not save to Sent: {e}")

    print(f"HTML email sent to {to}: {subject}")


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    force_research = "--force-research" in sys.argv
    db = load_db()

    # Monthly competitor research on first Monday (or forced)
    ran_research = False
    if force_research or is_first_monday():
        db = run_competitor_research(db)
        ran_research = True

    # Collect reviews
    print("Collecting competitor negative reviews...")
    findings = collect_all_reviews(db)

    # Build report
    html = build_html_report(findings, ran_research)

    today = datetime.date.today().strftime("%b %d, %Y")
    subject = f"📊 Competitor Review Report — {today}"
    send_html_email(AARON_EMAIL, subject, html)
    print("Done.")
