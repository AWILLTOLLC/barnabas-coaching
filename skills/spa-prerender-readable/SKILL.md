---
name: "spa-prerender-readable"
description: "Make a Vite/React SPA readable to AI agents: detect empty-shell serving, add dependency-free prerendering with correct hydration, robots.txt, llms.txt."
---

# Making a Vite/React SPA agent-readable via build-time prerendering

Use when a website serves an empty `<div id="root">` shell (content only after JS runs), so AI agents and non-JS crawlers see nothing. Procedure produces static HTML per route at build time with zero new dependencies, plus robots.txt and llms.txt.

## 1. Confirm the problem
- `curl -s <site> | wc -c` and inspect: an SPA shell is a few hundred bytes, empty root div, one JS bundle link.
- Confirm content exists in the bundle: `curl -s <bundle-url> -o /tmp/b.js` then grep for a known phrase. If content is in lazy chunks, render with Playwright first (`page.content()` after `networkidle`) to find chunk URLs.
- Check `/robots.txt` (often 404s into the SPA shell).

## 2. Refactor for SSR-safe rendering
- In the app entry, split the page component into its own file (e.g. `src/App.tsx`) with `export default App`. It must not touch `window`/`document` at module scope; route-specific `window.location` reads become a prop (`{ pathname }`).
- Entry bootstrap hydrates when the root already has children:
  ```tsx
  const rootEl = document.getElementById('root')!
  if (rootEl.hasChildNodes()) hydrateRoot(rootEl, <App />)
  else createRoot(rootEl).render(<App />)
  ```

## 3. Prerender script (no new deps, no headless browser)
`scripts/prerender.mjs`, run after `vite build`:
- `createServer({ server: { middlewareMode: true }, appType: 'custom', logLevel: 'error' })` from vite.
- `const { default: App } = await server.ssrLoadModule('/src/App.tsx')`.
- **Use `renderToString`, never `renderToStaticMarkup`.** Static markup omits React's `<!-- -->` text-node separators; hydration then throws React #418 (text mismatch) on any component with adjacent text nodes (e.g. `© {year} Brand`). This is the classic failure mode.
- Inject markup into each built `dist/<template>` inside `<div id="root">...</div>` (replace the empty contents).
- Wire into package.json: `"build": "tsc -b && vite build && node scripts/prerender.mjs"`.

## 4. Add robots.txt and llms.txt
- Create `public/robots.txt` (`User-agent: *` / `Allow: /`) — vite copies `public/` into dist.
- Add `public/llms.txt`: markdown brief with company one-liner, services, page map, contact. This is what AI agents read first.

## 5. Verify before shipping
- `npm run build` — expect `prerendered / -> index.html (...)` lines and page sizes in the KB range, not bytes.
- `curl` the built page: real `<h1>` content must appear without JS.
- Playwright hydration check: open `npx vite preview`, assert `console` errors is empty, interactive elements still work (menu toggle), and text content is intact after hydration.
- If a hydration error appears: rerun with `{ onRecoverableError: (err, info) => console.error('HYDRATION:', err, info?.componentStack) }` on `hydrateRoot` to get the component; the fix is almost always renderToString (step 3).

## 6. Ship safely
- Commit locally; do not push without explicit user approval — static-host integrations often auto-deploy on push.
- After deploy, re-curl the live URL to confirm the host serves prerendered HTML and not a cached shell.
