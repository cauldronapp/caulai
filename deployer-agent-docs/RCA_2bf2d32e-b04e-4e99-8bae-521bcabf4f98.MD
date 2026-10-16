# Read-Only Incident Report — CAUL AI (caul-impl-gate)

**Mode:** Diagnosis only. No deploy, redeploy, pause, cancel, or production change was performed.

## 1. Deployment / Job ID of today's deployment
- **Deployment ID:** `994120f4-929a-41c2-a895-093d4fd242e8` (name: `caul-impl-gate`)
- **Today's run (2026-10-16):** `run_id = 2bf2d32e-b04e-4e99-8bae-521bcabf4f98`
- **Job ID:** `cecc1265-925c-45b5-a43d-6a83ddc65df1` (shared across all runs of this deployment)
- **Type / trigger:** `redeploy`, triggered by `secret_change` (not a code change)

## 2. Target environment
- **PRODUCTION.** Live URL `https://caul-impl-gate.emergent.host`; custom domains `caul.ai` and `www.caul.ai` (both verified). Deployment status `active`, frontend served via Cloudflare. This is not preview/staging.

## 3. Current status
- **COMPLETED — SUCCESS.** Run created `2026-10-16T04:08:51Z`, completed `2026-10-16T04:14:10Z`.
- There is **no queued or in-progress run**. Nothing is currently running.
- **It cannot be paused/cancelled** — it already reached a terminal success state and is the active, serving run.

## 4. Source git revision
- **No git commit SHA is recoverable.** The pipeline pulls source from the preview pod filesystem (`/app`) and excludes `.git` — no git ref is recorded for the build (confirmed: no `.git` in the pulled source).
- Build identity available instead:
  - Image digest: `sha256:0721b61546cfa269a3b9b226491046774de56b56a292b05bbc7bf9cf25c6b5d4`
  - Base image: `fastapi_react_mongo_shadcn_base_image_cloud_arm:release-20092026-1`

## 5. Are the two specific changes live?

### (a) Alembic migration `a1b2c3d4e5f6` ("usage instrumentation") — NOT LIVE, NOT PRESENT
- The migration `a1b2c3d4e5f6` **does not exist** in the deployed source. The complete Alembic version chain present is:
  `04fa0e699dc6` (initial) → `0abdc53a92e5` → `d88e3be3f8b8` → `e1f2a3b4c5d6` → **`f2b3c4d5e6f7` (HEAD)**.
- Tables `usage_events`, `usage_aggregates`, `model_cost_rates` are **not defined** anywhere in `backend/app/models.py` (18 tables defined; none usage-related).
- `/api/usage/summary` live probe → **404 Not Found**. No `/api/usage/*` routes or usage router exist in the source.
- **Additional critical finding:** The source is a **PostgreSQL / SQLAlchemy / Alembic** app (models.py: "PostgreSQL system-of-record... No MongoDB"). However, the platform-provisioned production database is **MongoDB** (`caul-impl-gate-base`, **0 collections**). The platform does not provision PostgreSQL for this template (`fastapi_react_mongo_shadcn_base_image`). Regardless of where Postgres runs, the usage migration is simply not in the deployed code, so it is not live.

### (b) `usage-retention` cron (`POST /api/cron/usage-retention`) — NOT REGISTERED, NOT PRESENT
- `.emergent/crons.yml` contains exactly **two** crons, neither is usage-retention:
  - `audit-verify` → `/api/cron/verify-audit` (`*/30 * * * *`)
  - `weekly-governance-digest` → `/api/cron/weekly-digest` (`0 13 * * 1`, Mondays 13:00 UTC)
- The cron router (`backend/app/routers/cron.py`) exposes only `/verify-audit` and `/weekly-digest`. There is **no** `usage-retention` route.
- `/api/cron/usage-retention` live probe → **404 Not Found**. Since the endpoint does not exist, it **cannot have run** in production.

### Requested extra confirmation of what IS live
- **Alembic head in source:** `f2b3c4d5e6f7` (saved_filter_is_default).
- **`/api/usage/*` routes:** absent (404 in prod).
- **Cron registrations in prod `crons.yml`:** `audit-verify` and `weekly-governance-digest` only. The **weekly-digest** cron IS registered (as `weekly-governance-digest` → `/api/cron/weekly-digest`). The **usage-retention** cron is NOT registered.

## Conclusion
Today's production redeploy (`2bf2d32e…`, trigger `secret_change`) completed successfully ~04:14 UTC and is the active serving run; there is nothing in progress to pause or cancel. **Neither** the `a1b2c3d4e5f6` usage-instrumentation migration **nor** the `usage-retention` cron is present in the source that built the live image, and both corresponding live endpoints return 404 — so neither change is live in production. They were never part of the deployed revision (likely never committed/merged into the deployed source, or they live on an un-deployed branch).
