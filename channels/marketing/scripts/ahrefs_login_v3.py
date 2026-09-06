#!/usr/bin/env python3
"""
Login to Ahrefs - waits for Cloudflare Turnstile to auto-verify before submitting.
"""
import json
import sys
import time
from pathlib import Path
from patchright.sync_api import sync_playwright

CREDENTIALS_PATH = Path("/root/.openclaw/credentials/ahrefs.json")
COOKIES_PATH = Path("/root/.openclaw/credentials/ahrefs_cookies.json")
SCREENSHOT_DIR = Path("/root/.openclaw/workspace/channels/marketing")

def login_and_save_cookies():
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)
    print(f"Logging in as {creds['email']}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--no-first-run",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Los_Angeles",
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [
                {name: 'Chrome PDF Plugin'}, {name: 'Chrome PDF Viewer'}, {name: 'Native Client'}
            ]});
        """)

        page = context.new_page()
        print("Loading login page...")
        page.goto("https://app.ahrefs.com/user/login", wait_until="networkidle", timeout=60000)

        # Fill credentials first
        print("Filling credentials...")
        page.fill('input[type="email"]', creds["email"])
        time.sleep(0.3)
        page.fill('input[type="password"]', creds["password"])
        time.sleep(0.3)

        # Check Turnstile status
        print("Checking Turnstile widget...")
        for i in range(20):
            turnstile_val = page.evaluate("""
                () => {
                    const el = document.querySelector('input[name="cf-turnstile-response"]');
                    return el ? el.value : null;
                }
            """)
            print(f"  [{i+1}s] Turnstile response: {repr(turnstile_val[:20]) if turnstile_val else 'empty'}")
            if turnstile_val and len(turnstile_val) > 10:
                print("  Turnstile solved!")
                break
            time.sleep(1)
        else:
            print("  Turnstile never populated — submitting anyway (may fail)")

        page.screenshot(path=str(SCREENSHOT_DIR / "ahrefs_v3_pre_submit.png"))

        # Submit via Enter key in password field
        print("Submitting form...")
        page.press('input[type="password"]', "Enter")
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)

        current_url = page.url
        print(f"Post-submit URL: {current_url}")
        print(f"Title: {page.title()}")

        page.screenshot(path=str(SCREENSHOT_DIR / "ahrefs_v3_post_submit.png"))

        if "login" in current_url:
            # Dump any visible errors
            body_text = page.inner_text("body")
            error_lines = [l.strip() for l in body_text.split("\n") if "error" in l.lower() or "invalid" in l.lower() or "incorrect" in l.lower() or "wrong" in l.lower()]
            for e in error_lines[:5]:
                print(f"  Error hint: {e}")
            print("Login failed.")
            browser.close()
            sys.exit(1)

        cookies = context.cookies()
        with open(COOKIES_PATH, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"✅ Login successful! Saved {len(cookies)} cookies.")
        browser.close()

if __name__ == "__main__":
    login_and_save_cookies()
