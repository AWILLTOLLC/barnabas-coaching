#!/usr/bin/env python3
"""
Peter Brandt Factor Reports - Fetch and extract latest PDF
"""

import json
import os
import sys
import requests
from bs4 import BeautifulSoup
import pdfplumber

CREDS_FILE = "/root/.openclaw/credentials/peterlbrandt.json"
DOWNLOAD_DIR = "/root/.openclaw/workspace/reports/peterlbrandt"
SEEN_FILE = "/root/.openclaw/workspace/reports/peterlbrandt/.seen_reports.json"

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
    payload = {
        "log": creds["username"],
        "pwd": creds["password"],
        "wp-submit": "Log In",
        "redirect_to": creds["reports_url"],
        "testcookie": "1"
    }
    session.get(login_url)  # get login cookies
    r = session.post(login_url, data=payload, allow_redirects=True)
    return "wp-settings" in session.cookies or r.url != login_url

def get_pdf_links(session, url):
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            title = a.get_text(strip=True) or os.path.basename(href)
            links.append({"url": href, "title": title})
    return links

def download_pdf(session, url, dest_path):
    r = session.get(url, stream=True)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def extract_text(pdf_path):
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n\n".join(text)

def main(fetch_first_only=False):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    creds = load_creds()
    seen = load_seen()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; personal-use-bot)"})

    print("Logging in...")
    logged_in = wp_login(session, creds)
    if not logged_in:
        print("WARNING: Login may have failed, trying anyway...")

    print("Fetching reports page...")
    links = get_pdf_links(session, creds["reports_url"])

    if not links:
        print("No PDF links found on page.")
        return

    print(f"Found {len(links)} PDF(s) on page.")

    if fetch_first_only:
        # Only process the first (most recent) link regardless of seen status
        to_process = [links[0]]
        print(f"Fetching first report only: {links[0]['title']}")
    else:
        to_process = [l for l in links if l["url"] not in seen]
        print(f"{len(to_process)} new report(s) to process.")

    if not to_process:
        print("Nothing new to process.")
        return

    for report in to_process:
        filename = os.path.basename(report["url"].split("?")[0]) or "report.pdf"
        dest = os.path.join(DOWNLOAD_DIR, filename)
        print(f"\nDownloading: {report['title']} -> {filename}")
        download_pdf(session, report["url"], dest)
        print(f"Saved to {dest}")

        print("Extracting text...")
        text = extract_text(dest)
        text_path = dest.replace(".pdf", ".txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Text extracted ({len(text)} chars) -> {text_path}")
        print("\n--- EXTRACTED TEXT PREVIEW (first 500 chars) ---")
        print(text[:500])
        print("--- END PREVIEW ---")

        if not fetch_first_only:
            seen.append(report["url"])
            save_seen(seen)

if __name__ == "__main__":
    first_only = "--first" in sys.argv
    main(fetch_first_only=first_only)
