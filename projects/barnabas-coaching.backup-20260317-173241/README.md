# Barnabas Coaching — Website

Static marketing site for [Barnabas Coaching](https://barnabascoaching.com), an AI strategy coaching practice led by Aaron Williams in Seattle.

Built with [Astro](https://astro.build) + [Tailwind CSS](https://tailwindcss.com).

---

## Quick Start

### Prerequisites

- Node.js 18 or later
- npm 9 or later

### Install dependencies

```bash
cd barnabas-coaching
npm install
```

### Run locally

```bash
npm run dev
```

Site will be available at [http://localhost:4321](http://localhost:4321).

### Build for production

```bash
npm run build
```

Output goes to `./dist/`. Preview the build locally:

```bash
npm run preview
```

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home — hero, services overview, about teaser, CTA |
| `/services` | AI Audit ($2,500) and Coaching Retainer ($1,500/mo) |
| `/about` | Aaron's story and career timeline |
| `/blog` | Blog index (no posts yet, ready for content) |
| `/contact` | Contact form + Calendly embed placeholder |
| `/thanks` | Post-form-submission confirmation page |

---

## Deploy to Netlify

### Option 1: Netlify CLI

```bash
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

### Option 2: Git-based deploy (recommended)

1. Push this repo to GitHub (or GitLab / Bitbucket)
2. Log into [app.netlify.com](https://app.netlify.com)
3. Click **"Add new site" → "Import an existing project"**
4. Connect your repo
5. Set build settings:
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
6. Deploy

Netlify will automatically redeploy on every push to `main`.

### netlify.toml (optional)

You can add a `netlify.toml` at the project root for explicit config:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/404"
  status = 404
```

---

## Netlify Forms

The contact form and blog notification form use [Netlify Forms](https://docs.netlify.com/forms/setup/) (`data-netlify="true"`).

Forms will **only work on Netlify** — they're no-ops locally. To test locally, use a service like [Netlify Dev](https://docs.netlify.com/cli/get-started/#run-a-local-development-environment).

Form submissions appear in the Netlify dashboard under **Site → Forms**.

To set up email notifications for new submissions:
- Netlify Dashboard → **Forms → Notifications → Add notification → Email**

---

## Calendly Integration

The contact page (`src/pages/contact.astro`) has a Calendly embed placeholder.

To activate:
1. Create a [Calendly](https://calendly.com) account and set up an event type (e.g., "30 min Discovery Call")
2. In `src/pages/contact.astro`, replace the placeholder `<div>` with Calendly's inline embed code:

```html
<!-- Calendly inline widget begin -->
<div
  class="calendly-inline-widget"
  data-url="https://calendly.com/YOUR_USERNAME/discovery-call"
  style="min-width:320px;height:700px;"
></div>
<script
  type="text/javascript"
  src="https://assets.calendly.com/assets/external/widget.js"
  async
></script>
<!-- Calendly inline widget end -->
```

---

## SEO

The site includes:

- **Meta tags** — title, description, canonical URL per page
- **Open Graph** — og:title, og:description, og:image, og:url
- **Twitter Card** — summary_large_image
- **Schema.org JSON-LD** — LocalBusiness, Person, Service, Blog schemas
- **XML Sitemap** — auto-generated at `/sitemap-index.xml` via `@astrojs/sitemap`
- **robots.txt** — at `/robots.txt`, references the sitemap

### Update the site URL

The production URL is set in `astro.config.mjs`:

```js
export default defineConfig({
  site: 'https://barnabascoaching.com',
  // ...
});
```

Change this to your actual domain before deploying.

### Open Graph image

Add a 1200×630px OG image at `public/og-default.png`. Reference it in `src/layouts/Layout.astro` if you need per-page images.

---

## Fonts

The site uses [Playfair Display](https://fonts.google.com/specimen/Playfair+Display) (headings) and [Inter](https://fonts.google.com/specimen/Inter) (body) loaded from Google Fonts with `font-display: swap` for Core Web Vitals compliance.

---

## Project Structure

```
barnabas-coaching/
├── public/
│   ├── favicon.svg
│   └── robots.txt
├── src/
│   ├── components/
│   │   ├── Header.astro
│   │   └── Footer.astro
│   ├── layouts/
│   │   └── Layout.astro          # Base layout with SEO, fonts, schema
│   └── pages/
│       ├── index.astro           # Home
│       ├── services.astro        # Services
│       ├── about.astro           # About Aaron
│       ├── contact.astro         # Contact + Calendly
│       ├── thanks.astro          # Post-form confirmation
│       └── blog/
│           └── index.astro       # Blog index
├── astro.config.mjs
├── tailwind.config.mjs
├── tsconfig.json
└── package.json
```

---

## Future: Adding Blog Posts

When ready to publish blog content:

1. Enable Astro's [Content Collections](https://docs.astro.build/en/guides/content-collections/):
   - Create `src/content/blog/` directory
   - Add a `config.ts` defining the collection schema
   - Write posts as `.md` or `.mdx` files

2. Update `src/pages/blog/index.astro` to query and list posts:
   ```js
   import { getCollection } from 'astro:content';
   const posts = await getCollection('blog');
   ```

3. Create `src/pages/blog/[slug].astro` for individual post pages.

---

## License

Proprietary. All rights reserved. © Barnabas Coaching.
