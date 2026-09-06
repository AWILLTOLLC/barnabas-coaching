#!/usr/bin/env python3
"""
Login to Ahrefs and save session cookies for reuse.
Usage: python3 ahrefs_login.py [--test]
"""
import json
import sys
import os
from pathlib import Path
from patchright.sync_api import sync_playwright

CREDENTIALS_PATH = Path("/root/.openclaw/credentials/ahrefs.json")
COOKIES_PATH = Path("/root/.openclaw/credentials/ahrefs_cookies.json")

def load_credentials():
    with open(CREDENTIALS_PATH) as f:
        return json.load(f)

def login_and_save_cookies():
    creds = load_credentials()
    print(f"Logging in as {creds['email']}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Loading login page...")
        page.goto("https://app.ahrefs.com/user/login", wait_until="networkidle", timeout=30000)

        print("Filling credentials...")
        page.fill('input[type="email"], input[name="email"], #email', creds["email"])
        page.fill('input[type="password"], input[name="password"], #password', creds["password"])

        print("Submitting...")
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=20000)

        current_url = page.url
        print(f"Post-login URL: {current_url}")

        if "login" in current_url or "signin" in current_url:
            print("ERROR: Still on login page — check credentials or captcha")
            sys.exit(1)

        # Save cookies
        cookies = context.cookies()
        with open(COOKIES_PATH, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"Saved {len(cookies)} cookies to {COOKIES_PATH}")

        # Quick test — fetch dashboard title
        title = page.title()
        print(f"Page title: {title}")

        browser.close()
        return cookies

def test_cookies():
    """Test if saved cookies still work."""
    if not COOKIES_PATH.exists():
        print("No saved cookies — run login first")
        sys.exit(1)

    with open(COOKIES_PATH) as f:
        cookies = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto("https://app.ahrefs.com/dashboard", wait_until="networkidle", timeout=20000)
        url = page.url
        title = page.title()
        print(f"URL: {url}")
        print(f"Title: {title}")
        logged_in = "login" not in url and "signin" not in url
        print(f"Logged in: {logged_in}")
        browser.close()
        return logged_in

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_cookies()
    else:
        login_and_save_cookies()
