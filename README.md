# Interview Assistant

A personal CRM that helps candidates organize, automate, and optimize their job search — the operating system for job seekers.

Product vision, MVP scope, and roadmap: [docs/discovery_summary.md](docs/discovery_summary.md).

## Stack

Monorepo bootstrapped from [micro-saas-template](https://github.com/wlatanowicz/micro-saas-template):

- **Backend** — FastAPI on AWS Lambda (HTTP API + Mangum), SQLModel + Alembic, PostgreSQL
- **Frontend** — Vite + React SPA on S3 + CloudFront
- **CI/CD** — Serverless v3, GitHub Actions OIDC, S3 deploy, CloudFront invalidation, optional Cloudflare DNS

The demo `items` API and UI are **placeholder scaffolding** from the template. They will be replaced with job-search domain models (application tracker, kanban pipeline, interview notes, reminders).

## Layout

- `backend/` — Serverless stack (`service: interview-assistant`), FastAPI app, Alembic migrations
- `frontend/` — React SPA (`VITE_API_BASE_URL` injected at build time)
- `scripts/` — Deploy frontend to S3 + invalidate CloudFront; invoke migration Lambda; optional Cloudflare CNAME updates (frontend + API); **`collect-gha-env.sh`** builds **`.env.gha`** for GitHub Actions from AWS + prompts; **`push-gha-env.sh`** uploads **`.env.gha`** to repo Actions secrets/variables via **`gh`**
- `docs/` — Product discovery notes, [GitHub Actions AWS OIDC setup](docs/github-actions-aws-oidc.md), and [micro-saas-template origin](docs/micro-saas-template-origin.md) (tracked commit for future template updates)

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python toolchain and lockfile-driven installs)
- Node.js 22+ and npm (Serverless CLI + frontend build)
- Python 3.11 (matches `serverless.yml` runtime; uv will install/use it via `setup-uv` in CI)
- AWS account; optional **ACM certificate in us-east-1** only if you use a **custom frontend hostname** on CloudFront; optional **ACM certificate in the deploy region** (e.g. eu-central-1) for a **custom API hostname** on API Gateway
- PostgreSQL (or compatible) URL for `DATABASE_URL` if you use the API routes that touch the DB

## First-time deploy checklist

1. Optional: set **`FRONTEND_DOMAIN_NAME`** and **`FRONTEND_ACM_CERT_ARN`** (us-east-1) together when deploying. The certificate's SAN must include that hostname; otherwise CloudFront returns an invalid CNAME error. If you omit either, the stack uses the default **\*.cloudfront.net** URL only.
2. Optional: set **`API_DOMAIN_NAME`** and **`API_ACM_CERT_ARN`** (same region as **`AWS_REGION`**, e.g. eu-central-1) together for a custom API hostname (e.g. `api.example.com`). If **`API_DOMAIN_NAME`** is unset in GitHub Actions but **`FRONTEND_DOMAIN_NAME`** is set, deploy derives **`api.<frontend-host>`**. Omit both API vars to keep the default **execute-api** URL.
3. Set **`DATABASE_URL`** for deploy (GitHub secret and/or local env). The **migration** Lambda uses it to reach your database. Lambdas run **outside a VPC** and connect over the network URL in **`DATABASE_URL`** (ensure RDS or your Postgres host allows inbound connections from the internet or your Lambda egress IPs, as appropriate).
4. Copy `frontend/.env.example` to `frontend/.env` for local dev and set `VITE_API_BASE_URL` to your API URL (or local server).
5. Configure GitHub **Actions** secrets and variables (below). Grant the OIDC role **`lambda:InvokeFunction`** on the **`migrate`** function (see [docs/github-actions-aws-oidc.md](docs/github-actions-aws-oidc.md)).

## Local development

### Full stack (Docker Compose)

```bash
docker compose up --build   # backend :8000, frontend :5173, postgres :5432
```

### Backend only

Dependencies live in [`backend/pyproject.toml`](backend/pyproject.toml) and [`backend/uv.lock`](backend/uv.lock). Runtime deps include **Alembic** (used by the **`migrate`** Lambda). Test tooling stays in the **dev** dependency group.

**Integration tests** hit **real PostgreSQL** (same engine as production). When any integration test runs, pytest **clears** the `public` schema and applies **`alembic upgrade head`** once per run (disposable DB only). From the repo root:

```bash
make test-be            # Docker postgres:18 on TEST_DB_PORT (default 5433), then pytest
```

For CI or your own Postgres, point **`DATABASE_URL`** at a **throwaway** database and run pytest (**do not** use a shared dev DB with data you care about):

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
export JWT_SECRET='your-test-secret-at-least-32-chars-long!'
uv run pytest
# Or from repo root: make test-be-ci
```

Lint and quick pytest **without Docker** (auth integration tests skip if `DATABASE_URL` is unset):

```bash
cd backend
uv run pytest
uv run ruff check src tests conftest.py
```

Run the API locally (set `DATABASE_URL` if you need routes that persist data):

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
PYTHONPATH=. uv run uvicorn src.main:app --reload --port 8000
```

### Frontend only

```bash
cd frontend
npm install
cp .env.example .env
# set VITE_API_BASE_URL=http://127.0.0.1:8000 in .env
npm run dev
```

## Database migrations

**Deploy workflow:** after `serverless deploy`, GitHub Actions runs **`scripts/invoke-migrate-lambda.sh`**, which invokes the **`migrate`** Lambda. That function runs **`alembic upgrade head`** programmatically (`command.upgrade`). The stack output **`MigrateLambdaName`** is the function to call.

**Local / manual:**

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://...'
uv run alembic upgrade head
```

After a successful deploy (CLI), from repo root:

```bash
bash scripts/invoke-migrate-lambda.sh prod eu-central-1
```

For a new migration after changing models:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

## Email notifications (registration & password recovery)

Verification codes are sent through the **`notifications`** app. Configure via `backend/.env.example`:

| Variable | Local dev | Production |
|----------|-----------|------------|
| `NOTIFICATIONS_TRANSPORT` | `local` (default in Docker Compose) | `ses` |
| `NOTIFICATIONS_FROM_EMAIL` | any placeholder | verified SES sender address |
| `NOTIFICATIONS_EML_DIR` | optional; default `backend/var/emails/` | n/a |

With **`NOTIFICATIONS_TRANSPORT=local`**, outgoing messages are written as **`.eml`** files under **`backend/var/emails/`** (gitignored) for manual review.

With **`NOTIFICATIONS_TRANSPORT=ses`**, the API calls **`ses:SendEmail`** (Lambda IAM includes SES permissions). Verify the sender domain or address in **Amazon SES in the deploy AWS account and region** (e.g. `eu-central-1`) before deploy. In GitHub Actions, **`NOTIFICATIONS_FROM_EMAIL`** defaults to **`noreply@<FRONTEND_DOMAIN_NAME>`** when **`FRONTEND_DOMAIN_NAME`** is set (override with the **`NOTIFICATIONS_FROM_EMAIL`** repository variable). SES identities are per-account and per-region; verifying a domain in one account does not apply to another.

## Deploy (CLI)

From `backend/` (requires AWS credentials and env vars as in CI):

```bash
npm ci
export DATABASE_URL='postgresql://...'
# Optional custom SPA hostname (set BOTH, cert must cover the hostname in us-east-1):
# export FRONTEND_ACM_CERT_ARN='arn:aws:acm:us-east-1:...:certificate/...'
# export FRONTEND_DOMAIN_NAME='app.yourdomain.com'
# Optional custom API hostname (set BOTH, cert must cover the hostname in the deploy region):
# export API_ACM_CERT_ARN='arn:aws:acm:eu-central-1:...:certificate/...'
# export API_DOMAIN_NAME='api.yourdomain.com'
npm run deploy -- --stage prod --region eu-central-1
```

**`npm run deploy`** runs **`predeploy`** (exports **`requirements-lambda.txt`**) then **`serverless deploy`**. Use **`npm run print`** from **`backend/`** to validate **`serverless.yml`**.

Then from repo root:

```bash
bash scripts/deploy-frontend.sh prod eu-central-1
bash scripts/update-cloudflare-api-cname.sh prod eu-central-1      # if Cloudflare token + zone are set
bash scripts/update-cloudflare-frontend-cname.sh prod eu-central-1   # if Cloudflare token + zone are set
```

Scripts accept an optional third argument: **CloudFormation stack name** (default `interview-assistant-{stage}` from `backend/serverless.yml`).

## GitHub Actions

### `CI` (`.github/workflows/ci.yml`)

Runs on every push and pull request: **uv** (`uv sync`, tests, Ruff), exports `requirements-lambda.txt`, Serverless `print` on **`serverless.yml`**, frontend build.

### `Deploy` (`.github/workflows/deploy.yml`)

Runs on pushes to `main` and on `workflow_dispatch`: deploy backend → **run migrations Lambda** → optional Cloudflare API DNS → deploy frontend → optional Cloudflare frontend DNS.

| Type | Name | Purpose |
|------|------|---------|
| Secret | `AWS_ROLE_TO_ASSUME` | IAM role ARN for OIDC (`sts:AssumeRoleWithWebIdentity` from GitHub) |
| Secret | `DATABASE_URL` | Passed to Lambdas (`api`, **`migrate`**). Required for migration step if the database should be updated on deploy. |
| Secret | `FRONTEND_ACM_CERT_ARN` | Optional; ACM cert ARN (us-east-1). Required with `FRONTEND_DOMAIN_NAME` if you use a custom SPA domain. |
| Secret | `API_ACM_CERT_ARN` | Optional; ACM cert ARN (deploy region, e.g. eu-central-1). Required with `API_DOMAIN_NAME` (or derived `api.<frontend-host>`) for a custom API domain. |
| Variable | `AWS_REGION` | Optional; default `eu-central-1` |
| Variable | `FRONTEND_DOMAIN_NAME` | Optional; custom SPA hostname. Use with `FRONTEND_ACM_CERT_ARN`; leave unset for default CloudFront URL only. |
| Variable | `API_DOMAIN_NAME` | Optional; custom API hostname (e.g. `api.example.com`). When unset but `FRONTEND_DOMAIN_NAME` is set, deploy uses `api.<frontend-host>`. |
| Variable | `NOTIFICATIONS_FROM_EMAIL` | Optional; verified SES sender (e.g. `noreply@example.com`). When unset but `FRONTEND_DOMAIN_NAME` is set, deploy uses `noreply@<frontend-host>`. |
| Secret | `CLOUDFLARE_API_TOKEN` | Optional; DNS:Edit for zone |
| Secret | `CLOUDFLARE_ZONE_ID` | Optional; or use `CLOUDFLARE_ZONE_NAME` |
| Secret | `CLOUDFLARE_ZONE_NAME` | Optional; e.g. `example.com` |

OIDC trust and IAM permissions for deploy are documented in **[docs/github-actions-aws-oidc.md](docs/github-actions-aws-oidc.md)**.

### Bootstrap GitHub secrets from AWS

With credentials available (e.g. **`AWS_PROFILE`**), run:

```bash
AWS_PROFILE=your-profile ./scripts/collect-gha-env.sh
```

The script prints **`sts get-caller-identity`**, lists **RDS** instances in the configured region (endpoint, identifier) and **ISSUED ACM** certs in **us-east-1** (CloudFront) and the **deploy region** (API Gateway), and prompts for **database name**, **password**, **OIDC role ARN**, optional **frontend** / **API** domains / **Cloudflare** values. When you build **`DATABASE_URL`** from an RDS instance, it uses the instance endpoint and your password. It writes **`.env.gha`** at the repo root (gitignored) with **`shlex`-safe** quoting. If **`.env.gha` already exists**, its values are loaded first and used as defaults (press **Enter** to keep each field, **`k`** to keep **DATABASE_URL** / ACM). Use **`./scripts/collect-gha-env.sh -n`** to print the file to stdout only.

Requires **AWS CLI**, **jq**, and **Python 3**. The generated **`.env.gha`** uses **`# --- Secrets ---`** and **`# --- Variables ---`** section headers; **`push-gha-env.sh`** uploads every non-empty line under each block to GitHub **secrets** or **variables**. Run **`./scripts/push-gha-env.sh`** (needs **`gh`** and **Python 3**; **`gh`** with **repo** scope). Use **`./scripts/push-gha-env.sh -n`** first to preview. The **master password** and **OIDC role ARN** are always prompted (not returned by AWS APIs).

## Lambda packaging notes

- **uv** produces `backend/requirements-lambda.txt` for **`serverless-python-requirements`** (`uv export --frozen --no-dev --no-emit-project --no-hashes`). That file is gitignored; CI and `npm run predeploy` create it before deploy. **`package.individually: true`**: the **`api`** function excludes `alembic/` and **`migrate_handler.py`**; the **`migrate`** function ships `alembic/` + `alembic.ini` plus app models. Both bundles still include shared runtime wheels (including Alembic) from the same export.
- `serverless-python-requirements` bundles those dependencies; `slim: true` keeps the zip smaller. On macOS, `dockerizePip: non-linux` uses Docker for Linux-compatible wheels when needed.
- Lambda runtime already includes `boto3`; it is listed under `noDeploy` to avoid duplication.

After changing Python dependencies, run **`uv lock`** in `backend/` and commit the updated **`uv.lock`**.

GitHub Actions installs **Python via `actions/setup-python`** before **`setup-uv`**, because **`serverless-python-requirements`** shells out to **`python3.11 -m pip`**, and uv's standalone interpreters may not ship with the `pip` module.
