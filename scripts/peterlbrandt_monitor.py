#!/usr/bin/env python3
"""
Peter Brandt Factor Reports - Monitor, download, summarize, and email new reports.
Run via cron daily. Emails Aaron when a new report is published.
"""

import json, os, re, sys, subprocess, requests
from bs4 import BeautifulSoup
import pdfplumber

CREDS_FILE   = "/root/.openclaw/credentials/peterlbrandt.json"
DOWNLOAD_DIR = "/root/.openclaw/workspace/reports/peterlbrandt"
SEEN_FILE    = os.path.join(DOWNLOAD_DIR, ".seen_reports.json")
EMAIL_TO     = "a@kaw.cc"
EMAIL_SCRIPT = "/root/.openclaw/workspace/scripts/send_email.py"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)

def wp_login(session, creds):
    login_url = creds["site"] + "/wp-login.php"
    session.get(login_url)
    session.post(login_url, data={
        "log": creds["username"],
        "pwd": creds["password"],
        "wp-submit": "Log In",
        "redirect_to": creds["reports_url"],
        "testcookie": "1"
    }, allow_redirects=True)

def get_report_posts(session, creds):
    """Return list of {title, url} for report posts, most recent first."""
    r = session.get(creds["reports_url"])
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"factor-updates?-\w", href):
            title = a.get_text(strip=True)
            if title and href not in [p["url"] for p in posts]:
                posts.append({"title": title, "url": href})
    return posts

def get_pdf_url(session, post_url):
    """Scrape a report post and return the direct PDF URL."""
    r = session.get(post_url)
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf") and "wp-content" in href:
            # prefer the clean filename (not the double-url-encoded one)
            if "httpswww" not in href:
                return href
    # fallback: any pdf
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".pdf"):
            return a["href"]
    return None

def download_pdf(session, url, dest):
    r = session.get(url, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

def extract_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n\n".join(pages)


# ── parser ───────────────────────────────────────────────────────────────────

def parse_report(text):
    """
    Pull out the structured sections from a Factor Update.
    Returns a dict with keys: positions, exits, nips, markets, notes
    """
    lines = text.split("\n")

    # Current positions bullet list (after "Current Factor Prop Account positions")
    positions = []
    nips = []
    exits = []
    in_positions = in_nips = in_exits = False

    for line in lines:
        l = line.strip()
        if "Current Factor Prop Account positions" in l:
            in_positions = True; in_nips = False; in_exits = False; continue
        if "Markets under consideration" in l or "New Initial Positions" in l:
            in_nips = True; in_positions = False; in_exits = False; continue
        if "Trades exited" in l:
            in_exits = True; in_nips = False; in_positions = False; continue
        if in_positions and l.startswith("•"):
            positions.append(l[1:].strip())
        if in_nips and l.startswith("•"):
            nips.append(l[1:].strip())
        if in_exits and l.startswith("•"):
            exits.append(l[1:].strip())
        # stop capture at section breaks
        if in_positions and l and not l.startswith("•") and len(l) > 4 and "Markets under" not in l:
            if not any(x in l for x in ["Note:", "2026"]):
                in_positions = False
        if in_exits and l and not l.startswith("•") and len(l) > 4:
            if "For the video" in l or "Just a reminder" in l:
                in_exits = False

    # Per-market sections: find headers followed by bullet points
    market_sections = []
    current_market = None
    current_bullets = []

    for line in lines:
        l = line.strip()
        # A market header is a short non-bullet line followed by bullets
        if l and not l.startswith("•") and not l.startswith("[") and len(l) < 60:
            # flush previous
            if current_market and current_bullets:
                market_sections.append((current_market, current_bullets))
            current_market = l
            current_bullets = []
        elif l.startswith("•") and current_market:
            current_bullets.append(l[1:].strip())

    if current_market and current_bullets:
        market_sections.append((current_market, current_bullets))

    # NAV performance
    nav_match = re.search(r"NAV performance[^=]+=\s*([\d.]+)", text)
    nav = nav_match.group(1) if nav_match else None

    return {
        "positions": positions,
        "nips": nips,
        "exits": exits,
        "market_sections": market_sections,
        "nav_2026": nav
    }


def format_email(title, parsed):
    lines = []
    lines.append(f"Factor Update Summary: {title}")
    lines.append("=" * 60)

    if parsed["nav_2026"]:
        lines.append(f"\n📊 2026 YTD Closed-Trade NAV: {parsed['nav_2026']}")

    if parsed["positions"]:
        lines.append("\n📌 CURRENT POSITIONS")
        for p in parsed["positions"]:
            lines.append(f"  • {p}")

    if parsed["exits"]:
        lines.append("\n📤 EXITED THIS WEEK")
        for e in parsed["exits"]:
            lines.append(f"  • {e}")

    if parsed["nips"]:
        lines.append("\n👀 WATCHING FOR NEW ENTRIES (NIPs)")
        for n in parsed["nips"]:
            lines.append(f"  • {n}")

    if parsed["market_sections"]:
        lines.append("\n📈 MARKET-BY-MARKET NOTES")
        # Filter to sections that look like real market analysis
        skip = {"factor update", "factor", "share this", "for the video", "just a reminder",
                "trading commentary", "why my focus", "factor's trading"}
        for market, bullets in parsed["market_sections"]:
            if any(s in market.lower() for s in skip):
                continue
            if not bullets:
                continue
            lines.append(f"\n  {market}")
            for b in bullets[:5]:  # cap at 5 bullets per market
                lines.append(f"    • {b}")

    lines.append("\n" + "=" * 60)
    lines.append("Source: peterlbrandt.com/factor-reports/")
    return "\n".join(lines)


def send_email(subject, body):
    result = subprocess.run(
        ["python3", EMAIL_SCRIPT, EMAIL_TO, subject, body],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Email error: {result.stderr}")
    else:
        print(f"Email sent to {EMAIL_TO}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    creds = load_creds()
    seen = load_seen()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    print("Logging in...")
    wp_login(session, creds)

    print("Fetching reports list...")
    posts = get_report_posts(session, creds)
    if not posts:
        print("No report posts found.")
        return

    new_posts = [p for p in posts if p["url"] not in seen]
    print(f"Found {len(posts)} total, {len(new_posts)} new.")

    for post in new_posts:
        print(f"\nProcessing: {post['title']}")
        pdf_url = get_pdf_url(session, post["url"])
        if not pdf_url:
            print("  No PDF found, skipping.")
            continue

        filename = os.path.basename(pdf_url.split("?")[0])
        dest = os.path.join(DOWNLOAD_DIR, filename)
        print(f"  Downloading {filename}...")
        download_pdf(session, pdf_url, dest)

        print("  Extracting text...")
        text = extract_text(dest)

        txt_path = dest.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            f.write(text)

        print("  Parsing report...")
        parsed = parse_report(text)

        body = format_email(post["title"], parsed)
        subject = f"Uncle Pete's Report: {post['title']}"

        print(f"  Sending email: {subject}")
        send_email(subject, body)

        seen.append(post["url"])
        save_seen(seen)
        print(f"  Done. Marked as seen.")

    if not new_posts:
        print("Nothing new. All done.")


if __name__ == "__main__":
    main()
