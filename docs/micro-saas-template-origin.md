# micro-saas-template origin

This project was bootstrapped from [micro-saas-template](https://github.com/wlatanowicz/micro-saas-template).

| Field | Value |
|-------|-------|
| Template repository | `git@github.com:wlatanowicz/micro-saas-template.git` |
| Commit (bootstrap) | `931ab05f0501088523a2b0158c7a1598e58a3cb1` |
| Commit date | 2026-09-20 |
| Commit message | `feat: mobile app` |
| Applied to this repo | 2026-09-28 |

## Applying future template updates

1. In a clone of `micro-saas-template`, inspect changes since the bootstrap commit:

   ```bash
   git log 931ab05f0501088523a2b0158c7a1598e58a3cb1..HEAD --oneline
   git diff 931ab05f0501088523a2b0158c7a1598e58a3cb1..HEAD
   ```

2. Cherry-pick or manually port relevant changes into this repo. Skip product-specific files (e.g. `docs/discovery_summary.md`, i18n product strings, `serverless.yml` `service:` name).

3. After merging template changes, update the **Commit (bootstrap)** row above to the new baseline commit and set **Applied to this repo** to today's date.

See also [downstream-template-tracking.md](downstream-template-tracking.md) for the convention used across MST-based products.
