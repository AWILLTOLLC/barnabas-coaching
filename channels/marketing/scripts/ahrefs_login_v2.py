#!/usr/bin/env python3
"""
Login to Ahrefs using patchright with stealth settings to bypass Cloudflare Turnstile.
Saves session cookies for reuse by other scripts.
"""
import json
import sys
import time
from pathlib import Path
from patchright.sync_api import sync_playwright

CREDENTIALS_PATH = Path("/root/.openclaw/credentials/ahrefs.json")
COOKIES_PATH = Path("/root/.openclaw/credentials/ahrefs_cookies.json")

def login_and_save_cookies(debug=False):
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)
    print(f"Logging in as {creds['email']}...")

    with sync_playwright() as p:
        # Use patchright's stealth launch options
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Los_Angeles",
            color_scheme="light",
            # Stealth: make navigator.webdriver undefined
            java_script_enabled=True,
        )

        # Override navigator.webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        print("Navigating to login page...")
        page.goto("https://app.ahrefs.com/user/login", wait_until="domcontentloaded", timeout=60000)

        # Wait up to 30s for Cloudflare to resolve
        print("Waiting for Cloudflare to resolve...")
        for i in range(30):
            time.sleep(1)
            url = page.url
            # Check if we're past the CF challenge
            inputs = page.query_selector_all('input[type="email"], input[type="password"], input[name="email"], input[name="login"]')
            if inputs:
                print(f"  Login form found after {i+1}s")
                break
            if debug:
                print(f"  [{i+1}s] Still waiting... URL: {url}")
        else:
            print("Timed out waiting for login form")
            if debug:
                page.screenshot(path="/root/.openclaw/workspace/channels/marketing/ahrefs_cf_timeout.png")
            browser.close()
            sys.exit(1)

        if debug:
            page.screenshot(path="/root/.openclaw/workspace/channels/marketing/ahrefs_login_form.png")

        # Fill email
        email_sel = None
        for sel in ['input[type="email"]', 'input[name="email"]', 'input[name="login"]', '#email']:
            el = page.query_selector(sel)
            if el:
                email_sel = sel
                break
        if not email_sel:
            print("ERROR: Could not find email field")
            inputs = page.query_selector_all("input")
            for inp in inputs:
                print(f"  input: type={inp.get_attribute('type')} name={inp.get_attribute('name')} id={inp.get_attribute('id')}")
            browser.close()
            sys.exit(1)

        print(f"Filling email ({email_sel})...")
        page.click(email_sel)
        page.fill(email_sel, creds["email"])
        time.sleep(0.5)

        # Fill password
        pw_sel = None
        for sel in ['input[type="password"]', 'input[name="password"]', '#password']:
            el = page.query_selector(sel)
            if el:
                pw_sel = sel
                break
        if not pw_sel:
            print("ERROR: Could not find password field")
            browser.close()
            sys.exit(1)

        print(f"Filling password ({pw_sel})...")
        page.click(pw_sel)
        page.fill(pw_sel, creds["password"])
        time.sleep(0.5)

        # Submit
        submit_sel = None
        for sel in ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log in")', 'button:has-text("Sign in")', 'button:has-text("Login")']:
            el = page.query_selector(sel)
            if el:
                submit_sel = sel
                print(f"Clicking submit ({sel}): {el.inner_text()[:50] if el.inner_text() else ''}")
                el.click()
                break

        if not submit_sel:
            print("ERROR: Could not find submit button")
            browser.close()
            sys.exit(1)

        print("Waiting for post-login navigation...")
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        current_url = page.url
        print(f"Post-login URL: {current_url}")
        print(f"Page title: {page.title()}")

        if "login" in current_url or "signin" in current_url:
            # Check for error messages
            for sel in ['.error', '[class*="error"]', '[class*="alert"]', '[class*="Error"]']:
                els = page.query_selector_all(sel)
                for el in els:
                    txt = el.inner_text().strip()
                    if txt:
                        print(f"  Error: {txt[:200]}")
            if debug:
                page.screenshot(path="/root/.openclaw/workspace/channels/marketing/ahrefs_login_failed.png")
            print("Login failed — still on login page")
            browser.close()
            sys.exit(1)

        # Save cookies
        cookies = context.cookies()
        with open(COOKIES_PATH, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"✅ Login successful! Saved {len(cookies)} cookies to {COOKIES_PATH}")

        if debug:
            page.screenshot(path="/root/.openclaw/workspace/channels/marketing/ahrefs_logged_in.png")

        browser.close()
        return cookies

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    login_and_save_cookies(debug=debug)
