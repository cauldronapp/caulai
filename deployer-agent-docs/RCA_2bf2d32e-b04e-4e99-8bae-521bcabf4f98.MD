# RCA — caul-impl-gate (CAUL AI Command Center)

Read-only diagnosis. No changes made. No secret values exposed (credentials masked throughout).

Active run inspected: `2bf2d32e-b04e-4e99-8bae-521bcabf4f98` (redeploy, status success, serving traffic). Frontend: cloudflare. Template: fastapi_react_mongo_shadcn_base_image.

## 1. APP_ENV in production runtime
**APP_ENV = `dev`** (not a secret). Confirmed two ways:
- `list_secrets equals {APP_ENV:"dev"}` → `matches_expected: true`.
- `app/config.py:get_app_env()` defaults to `dev` when unset; only `dev`/`staging` are permitted (production guard raises otherwise).

## 2. Which PostgreSQL connection the running app uses
Resolution logic (`app/config.py:get_runtime_database_url` → `app/database.py:engine`):
`DEV_DATABASE_URL` when `APP_ENV=="dev"`, else `STAGING_DATABASE_URL`.

With APP_ENV=`dev`, the app resolves to **`DEV_DATABASE_URL`**.

Both are set in production (neither empty). Production values match the source `.env` exactly (`matches_expected: true` for both via `list_secrets equals`). Sanitized identifiers (credentials masked):
- **DEV_DATABASE_URL (RESOLVED/ACTIVE): host=`localhost` (127.0.0.1), port=`5432`, dbname=`caul_dev`**
- STAGING_DATABASE_URL: host=`localhost` (127.0.0.1), port=`5432`, dbname=`caul_staging`
- (Admin URLs DEV_ADMIN/STAGING_ADMIN likewise point at localhost:5432, dbname caul_dev / caul_staging — used only for migrations, not by the running app.)

## 3. Production DB name + shared vs separate
- Production dbname = **`caul_dev`** (the dev database name). It is **NOT** a distinct, dedicated production database. `caul_staging` is the staging name.
- Host/instance: **dev and staging point at the SAME host/instance** — both `localhost:5432` — differing only by dbname. There is **no separate production PostgreSQL instance**. The code explicitly states "There is NO production environment" (config.py docstring / production guard).
- Important nuance: `localhost:5432` was the preview pod's local PostgreSQL (the repo even carries a `postgres_data/` dir from that local instance). In the production pod there is no PostgreSQL process, so this URL does not actually reach any live dev/staging database — it reaches nothing (see #4).
- The platform-provisioned MongoDB (`caul-impl-gate-base`, 0 collections) is **unused** by this app, as expected — the app is PostgreSQL-only.

## 4. Root cause of 500 on /api/health and /api/health/ready
**The backend cannot connect to its PostgreSQL database because the resolved DB URL points at `localhost:5432`, and no PostgreSQL server runs inside the production pod.**

Verified error from production backend logs (run 2bf2d32e), on both endpoints:
```
sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed:
connection to server at "127.0.0.1", port 5432 failed: Connection refused
  File "/app/backend/server.py", line 116, in health
```
- `/api/health` executes `SELECT 1` / `SELECT current_database()`; `/api/health/ready` executes `SELECT COUNT(*) FROM permissions`. Both open a DB connection via the engine bound to `DEV_DATABASE_URL` (localhost:5432) → connection refused → unhandled → HTTP 500.
- `GET /` returns 200 because it is the static frontend (served via Cloudflare/R2), which touches no database.
- This is NOT a missing env var (all DB URLs are present and non-empty) and NOT a MongoDB issue. It is a DB URL that targets a local PostgreSQL that does not exist in production.
- `preview_health_check`: `/api/health` → 500, `/api/health/ready` → 500, `/` → 200 (matches report).
- Note: `/health` (no `/api` prefix) returns 404 by design — the app only defines `/api/health*`; the pod's probe hitting `/health` is harmless noise.

## Suggested fixes (NOT applied — release freeze respected)
1. USER (Secrets): In Deployment Panel → Secrets, set `DEV_DATABASE_URL` (and `STAGING_DATABASE_URL`/admin URLs if used in prod) to a PostgreSQL instance that is reachable from the production pod — i.e. an external/managed Postgres host, not `localhost`. Then redeploy. The current values are the preview pod's local Postgres, which has no server in production.
2. USER/third-party: Provision (or point to) a real managed PostgreSQL for this deployment and create the `caul_dev` (and/or `caul_staging`) database + run migrations/seed there. The provisioned MongoDB is unused and can be ignored.
3. Architectural note (for E1/owner, not required to clear the 500): the app has no "production" env concept — in prod it runs as `APP_ENV=dev` against `caul_dev`. If dev/staging are meant to stay isolated from production, a dedicated prod database/instance and a corresponding APP_ENV policy would be needed. This is a design decision, not the cause of the current 500.

Nothing was changed. No deploy, no secret edits, no migrations.
