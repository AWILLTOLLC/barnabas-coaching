---
name: "live-site-csp-debug"
description: "Debug a static page broken live but fine locally: CSP headers, self-hosted vendor JS, headless verification. Use when a live site silently fails after deploy."
---

# Debug a Live Static Page That Works Locally but Breaks Deployed

## 1. Reproduce in a headless browser before reading code
Load the live URL with Python Playwright (`python3.14`, installed at `/opt/homebrew/lib/python3.14/site-packages/playwright`; import path differs from npm — use the Python sync API). Capture `console` errors and `pageerror` events first; they usually name the cause (blocked script, 403, ReferenceError). Write the test script to `/tmp`, not the workspace.

## 2. If CDN scripts are blocked, check the CSP response header
`curl -sI <url> | grep -i content-security` — a server-level `Content-Security-Policy` header silently blocks third-party CDN `<script src>` while the page otherwise renders. Symptom: the dependent feature does nothing on click (e.g. `JSZip is not defined` on a Download button) with no visible error for the user. Fix by self-hosting, not by editing the server header:
- Download the vendor file into `<project>/public/vendor/` and change the script tag to a relative `src="vendor/<file>.js"` (same-origin passes `script-src 'self'`).
- Delete script tags for libraries the inline code never references (grep the inline script for the global name first).
- rsync the vendor **directory** separately; then `chmod 755` the remote vendor dir and `chmod 644` the file — rsync can leave the dir 700 and the server returns 403. Verify with `curl -s -o /dev/null -w "%{http_code} %{content_type}"`.

## 3. Deploy single files with permission flags baked in
`rsync -avz --chmod=F644 -e "ssh -i ~/.ssh/id_ed25519" <file> user@host:/path/` — avoids post-hoc chmod. ssh exec to this host may get SIGTERM'd mid-command; retry or route the chmod through `--rsync-path`. Confirm deploy by md5-comparing `curl` output against the local file.

## 4. Verify interactions in the real page, not just markup
Drive the full user flow (select → toggle → download) and assert computed `display`/`className` transitions, not just element presence. Known Playwright pitfalls on this site class, none of which indicate a real bug:
- `html { scroll-behavior: smooth }` + a sticky header makes Playwright report "element is not stable" then "header intercepts pointer events" on real clicks. Assert state via `page.evaluate` calling the page's own functions (e.g. `selectHarness('hermes')`), and do at most one real click after an `behavior:'instant'` scrollIntoView to viewport center.
- The page may scroll on `body` rather than `window`; check both `window.scrollY` and body overflow when testing scroll behavior.

## 5. Verify every intermediate step after changing gating logic
Multi-step pages often reveal sections with a `.visible` class that flips opacity/pointer-events, not `display` — computed `display` stays `block` even when the section is invisible, so assert `className`, not display. When a gate added to one section's update function early-returns, it can also skip the call that reveals an earlier sibling section sharing the same code path (e.g. gating Step 4 on harness selection silently suppressed Step 3's reveal). After any gating change, drive the full flow and assert each step's visibility at each point (before and after the new gate), not just the end state.

## 6. Finish only when the live page passes end-to-end
Zero console errors, the previously broken action produces its output (file download event fires), and both deploy-source copies of the file stay in sync (they may differ by exactly one logo href — diff with that substitution applied before declaring sync).
