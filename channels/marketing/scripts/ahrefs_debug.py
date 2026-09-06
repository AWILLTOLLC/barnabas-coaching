#!/usr/bin/env python3
"""Debug Ahrefs login page structure."""
import json
from pathlib import Path
from patchright.sync_api import sync_playwright

CREDENTIALS_PATH = Path("/root/.openclaw/credentials/ahrefs.json")

with open(CREDENTIALS_PATH) as f:
    creds = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()

    page.goto("https://app.ahrefs.com/user/login", wait_until="networkidle", timeout=30000)

    # Dump all input fields
    inputs = page.query_selector_all("input")
    print("=== INPUT FIELDS ===")
    for inp in inputs:
        print(f"  type={inp.get_attribute('type')} name={inp.get_attribute('name')} id={inp.get_attribute('id')} placeholder={inp.get_attribute('placeholder')}")

    # Dump all buttons
    buttons = page.query_selector_all("button, input[type=submit]")
    print("=== BUTTONS ===")
    for btn in buttons:
        print(f"  tag={btn.evaluate('el => el.tagName')} type={btn.get_attribute('type')} text={btn.inner_text()[:80] if btn.inner_text() else ''}")

    # Try filling and check for errors
    print("\n=== Attempting login ===")
    # Try different selectors
    for sel in ['input[type="email"]', 'input[name="email"]', '#email', 'input[name="login"]', 'input[placeholder*="email" i]', 'input[placeholder*="Email" i]']:
        el = page.query_selector(sel)
        if el:
            print(f"Found email field: {sel}")
            el.fill(creds["email"])
            break

    for sel in ['input[type="password"]', 'input[name="password"]', '#password', 'input[placeholder*="password" i]']:
        el = page.query_selector(sel)
        if el:
            print(f"Found password field: {sel}")
            el.fill(creds["password"])
            break

    # Screenshot before submit
    page.screenshot(path="/tmp/ahrefs_before_submit.png")
    print("Screenshot saved: /tmp/ahrefs_before_submit.png")

    # Submit
    for sel in ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log in")', 'button:has-text("Sign in")', 'button:has-text("Login")', 'button:has-text("Continue")']:
        el = page.query_selector(sel)
        if el:
            print(f"Clicking: {sel} — text: {el.inner_text()[:50] if el.inner_text() else ''}")
            el.click()
            break

    page.wait_for_timeout(5000)
    page.screenshot(path="/tmp/ahrefs_after_submit.png")
    print(f"Post-submit URL: {page.url}")
    print("After screenshot saved: /tmp/ahrefs_after_submit.png")

    # Check for error messages
    for sel in ['.error', '.alert', '[class*="error"]', '[class*="alert"]']:
        els = page.query_selector_all(sel)
        for el in els:
            txt = el.inner_text().strip()
            if txt:
                print(f"Error/alert ({sel}): {txt[:200]}")

    browser.close()
