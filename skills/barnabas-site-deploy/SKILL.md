---
name: "barnabas-site-deploy"
description: "Deploy barnabas.coach static site (build, rsync, verify). Use when pushing changes live in projects/barnabas-coaching."
---

# Barnabas Site Deploy

Deploy `/Users/apollo/.openclaw/workspace/projects/barnabas-coaching` (Astro static site) to barnabas.coach.

## Deploy

1. `cd /Users/apollo/.openclaw/workspace/projects/barnabas-coaching && npm run build`
2. Deploy with exactly this command — the user `barnabas@` and the explicit key are required, and `/opt/homebrew/bin/rsync` must be used because macOS `openrsync` does not support `--chmod`:

```
/opt/homebrew/bin/rsync -avz --delete --chmod=D755,F644 -e "ssh -i ~/.ssh/id_ed25519" dist/ barnabas@barnabas.coach:/home/barnabas/html/
```

Using `apollo@barnabas.coach` or bare `rsync` fails with `Permission denied (publickey,password)`.

3. Verify live: `curl -s https://barnabas.coach/<changed-path> | diff - <local dist or public copy>` and confirm the changed content is in the served HTML. Report the live URL only after verification.

## Page lifecycle

- Pages in `public/` deploy with the site. A page uploaded directly to the server but absent from `public/` gets wiped by the next `--delete` rsync (this happened to the workshop page). If a live page is missing from `public/`, pull it down and add it to `public/` before deploying.
- `--delete` is intentional; never deploy without it and never deploy a stale `dist/`.

## Page removal

Removing a page takes three touches in one pass, then deploy:
1. Delete `src/pages/<page>.astro` (`git rm`).
2. Remove its entry from `src/components/Footer.astro` link list — the footer is the only nav source, so deleting the page alone leaves a dead link on every page.
3. `npm run build`, deploy, then verify the removal: removed path must return 404 live and `grep -ci <name>` on the live homepage must be 0. Commit with the attribution trailers and push.

## Commits

Every commit appends the standing attribution trailers:

```
Worked on by: - @erasei
Co-authored-by: erasei <110475288+erasei@users.noreply.github.com>
```

Normal push to `origin master` only; never force push or rewrite history. Verify remote head matches local after push.
