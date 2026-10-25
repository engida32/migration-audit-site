# Migration Readiness Audit

Static site for a fixed-fee codebase migration audit. Four main pages plus a 404, no build step, no runtime JavaScript, no third-party requests.

## Run locally

```bash
python3.12 -m http.server 8000 --directory .
```

Open `http://localhost:8000/`.

## Test

```bash
python3.12 -m pytest
```

The tests check page structure, accessibility scaffolding, internal links, pricing, SEO metadata, JSON-LD, the sitemap, and the self-hosted fonts.

## Deploy

Published with GitHub Pages from the `main` branch, repository root. `.nojekyll` disables Jekyll. The canonical base is `https://engida32.github.io/migration-audit-site/`.

## Contact

engida32lishan@gmail.com
