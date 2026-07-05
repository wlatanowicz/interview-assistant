# micro-saas-template origin

This project was bootstrapped from [micro-saas-template](https://github.com/wlatanowicz/micro-saas-template).

| Field | Value |
|-------|-------|
| Template repository | `git@github.com:wlatanowicz/micro-saas-template.git` |
| Commit (bootstrap) | `9faf3b8328a4310e8fd6b270562f7cdda455acf9` |
| Commit date | 2026-07-05 |
| Commit message | Update Cloudflare DNS scripts to support proxied CNAME records |
| Applied to this repo | 2026-07-05 |

## Applying future template updates

1. In a clone of `micro-saas-template`, inspect changes since the bootstrap commit:

   ```bash
   git log 9faf3b8328a4310e8fd6b270562f7cdda455acf9..HEAD --oneline
   git diff 9faf3b8328a4310e8fd6b270562f7cdda455acf9..HEAD
   ```

2. Cherry-pick or manually port relevant changes into this repo. Skip product-specific files (e.g. `docs/discovery_summary.md`, i18n product strings, `serverless.yml` `service:` name).

3. After merging template changes, update the **Commit (bootstrap)** row above to the new baseline commit and set **Applied to this repo** to today's date.

See also [downstream-template-tracking.md](downstream-template-tracking.md) for the convention used across MST-based products.
