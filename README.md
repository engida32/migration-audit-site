# Preflight Audit

Static site for a fixed-fee migration risk audit.

Published with GitHub Pages from the `main` branch, repository root. `.nojekyll` disables Jekyll. The canonical base is `https://engida32.github.io/migration-audit-site/`.

This repository contains the published build only. The Astro source lives in the private project workspace. There is no build step here, no runtime JavaScript beyond the copy button, and no third-party requests.

## Local check

```bash
python3 -m http.server 8000 --directory .
```

Open `http://localhost:8000/`.
