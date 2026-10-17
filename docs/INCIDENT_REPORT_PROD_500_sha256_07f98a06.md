# INCIDENT REPORT — Production DB-backed endpoints return HTTP 500
**App:** CAUL AI Command Center (`caul-impl-gate` → caul.ai / www.caul.ai)
**Active image:** `customers-app@sha256:07f98a069a37575a386caa4ade9fd72a4df1586789d11b73cf8231e63b6161a9`
**Active run:** `1594a92f-65e9-4f5b-901e-1793dfe2ff1d` (COMPLETE/SUCCESS, promoted to production)
**Mode:** STRICTLY READ-ONLY. No code/DB/secret/env/deploy/traffic/permission change. Production freeze respected.
**Secrets:** never displayed — config names + redacted host/port only.

> Legend: **[FACT]** verified from source/logs/deployer · **[ASSUMPTION]** inferred, not directly observed on the prod runtime · **[DECISION]** owner input required.

---

## 1. Which DB-backed endpoints are failing
**[FACT]** The engine is created at import from the environment-selected PostgreSQL URL (`app/database.py`), with `pool_pre_ping=True`. Every route that depends on `get_db` executes SQL against that URL; in production that URL is unreachable (see §2), so the pre-ping/connect fails → **HTTP 500** on **all DB-backed endpoints**. The failing set is effectively every data route:

- `GET /api/health` (runs `SELECT 1`) and `GET /api/health/ready` (`SELECT COUNT(*) FROM permissions`)
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` (all query `users`/`sessions`)
- All routers mounted in `server.py`: `dashboard`, `recommendations`, `approvals`, `audit`, `emergency`, `admin`, `admin_manage`, `system`, `notifications`, `cron`, `usage` — every endpoint that opens a DB session.

**[FACT] NOT DB-backed → still return 2xx in production** (no DB session): `GET /api/` (static JSON), `GET /api/auth/provider` (stub metadata), `POST /api/connectors/contract-test` (in-memory stub suite).

**[ASSUMPTION]** Specific per-endpoint 500 counts on the live image are not visible from this (preview) pod; preview logs show these routes returning 200/401 because preview HAS a reachable local Postgres. The production 500 behavior is inferred from the identical code path + the unreachable prod DB, and matches the previously-confirmed deployer diagnosis. A read-only query to the deployer for production runtime logs has been dispatched (async) to corroborate exact 500s.

**Note on auth 401s (not 500s):** `GET /api/auth/me` and the cron endpoints can short-circuit to **401** *before* touching the DB when no valid token/cron-secret is presented (auth dependency rejects first). With a valid token they would reach the DB and 500. So unauthenticated probes to those paths look like 401, not 500 — this is expected and not evidence the DB works.

## 2. Is the runtime using APP_ENV=dev → localhost:5432?
**[FACT — config, redacted]** `app/config.py` allows only `{dev, staging}` (`ALLOWED_ENVS`); `get_app_env()` defaults to `dev` when `APP_ENV` is unset and **refuses** any other value (production guard raises `ConfigError`). The repo `.env` defines `APP_ENV` set to one of the allowed `dev`/`staging` values (value withheld). Because the app boots and serves non-DB routes (200), `APP_ENV` is resolving to a valid dev/staging value — i.e., the running image has **no production environment**; it runs in the Phase-1A dev/staging mode by design.

**[FACT — redacted hosts]** The DB URLs the app selects all point at **`localhost:5432`**:
- `DEV_DATABASE_URL` → host:port `localhost:5432`, db `caul_dev` (user/password REDACTED)
- `STAGING_DATABASE_URL` → host:port `localhost:5432`, db `caul_staging` (REDACTED)
- `DEV_ADMIN_DATABASE_URL` / `STAGING_ADMIN_DATABASE_URL` → `localhost:5432` (migration/admin only; app never uses them)

**[FACT]** In the production pod there is **no PostgreSQL** on `localhost:5432` (the platform template is MongoDB-based; no Postgres is provisioned by the pipeline). Result: connection refused → 500 on every DB route. Config env var NAMES present in prod image: `APP_ENV, DEV_DATABASE_URL, STAGING_DATABASE_URL, DEV_ADMIN_DATABASE_URL, STAGING_ADMIN_DATABASE_URL, JWT_SECRET, WEBHOOK_CRON_SECRET(+_DEV/_STAGING), CORS_ORIGINS, SESSION_TTL_MINUTES, CHAIN_ORG, MONGO_URL, DB_NAME` (values withheld).

## 3. Current vs previous deployment: trigger, queue, auto-trigger
**[FACT]** Active run `1594a92f` created `2026-10-17T01:03:44Z`, completed `01:09:12Z`, **trigger = `agentic`**, image `sha256:07f98a06…`. It superseded prior run `504a6073` (`2026-10-16T23:48:56Z`, image `sha256:7f6d685b…`) under the **same** `job_id cecc1265…`. Both targeted and promoted production.
**[ASSUMPTION/PENDING]** Whether a *further* deployment is queued right now (a new "deployment initiated" notification was just received) and whether any **automatic** deploy trigger remains configured is being confirmed via a dispatched read-only deployer query (async). Nothing was disabled or changed.
**[FACT]** Earlier finding stands: the platform rebuilds from the **current preview pod source** on redeploy, so the `/app` WIP (incl. dev-only `usage` routes and `usage-retention` cron) is what reached production. Prior assumption that a *secret change* auto-promotes was corrected by support (secret save ≠ auto-redeploy; a manual Redeploy promotes).

## 4. Why did the deployment health check pass?
**[FACT]** The pipeline health check probes `GET /` and `GET /health` for **non-5xx** only. In this app:
- `GET /` is served by the **React frontend** (ingress routes non-`/api` paths to port 3000) → returns index.html → **200**.
- `GET /health` has **no backend route** and no SPA route → non-5xx (404/200 from the static server), still **non-5xx**.
- The backend DB health route is `GET /api/health` (would **500**), but the probe **never hits it**.
→ The gate sees only frontend 2xx/4xx and passes, so a backend with a dead DB is reported "healthy." This is a **readiness-semantics gap**, already flagged as a blocker in `LAUNCH_READINESS.md §5`.

## 5. Remediation options (preserve PostgreSQL + the freeze; no Mongo fallback, no cost, no changes made)
All options below are **proposals only** — none executed; each needs owner approval and a scoped freeze lift.
1. **[DECISION] Provision a reachable production PostgreSQL** that the app can target (own-account/managed Postgres reachable from the prod pod), then set `PROD_*` DB vars. Keeps the PostgreSQL system-of-record requirement. (Cost/account are an explicit owner decision — not chosen here.)
2. **[DECISION] Implement the explicit `production` env (Stage B)**: add `production` to allowed envs with dedicated `PROD_DATABASE_URL`/`PROD_ADMIN_DATABASE_URL` and **no dev/staging fallback**, fail-closed if unset. Pairs with option 1.
3. **[DECISION] Fix readiness semantics** so the gate hits `GET /api/health`/`/api/health/ready` (or an app-level readiness path) — a dead DB must fail the health check instead of passing.
4. **[DECISION] Env-gate dev-only routes/crons** (`/api/usage/*`, `usage-retention`) so they are off in production (default-deny), removing unapproved surface from the prod image.
5. **[DECISION] Keep production frontend-only (status quo)** until 1–4 are approved — accept that backend/API is intentionally non-functional in prod for now (no customer sign-in).
6. **Explicitly excluded:** MongoDB fallback (violates PostgreSQL requirement), creating any external DB account, incurring cost, running migrations, changing secrets/env, or deploying — **none** performed or recommended as an action to take now.

## 6. Owner decisions/approvals required before ANY remediation
1. **[DECISION]** Choose the production PostgreSQL path + accept its account/cost (or confirm staying frontend-only).
2. **[DECISION]** Approve the Stage B `production` env + `PROD_*` vars and fail-closed guards.
3. **[DECISION]** Approve the readiness-check fix so a broken DB cannot report healthy.
4. **[DECISION]** Approve env-gating/removal of dev-only `usage` routes + `usage-retention` cron from production.
5. **[DECISION]** Lift the production freeze for a single, scoped, reviewed release carrying the above (with an identifiable source artifact / Git SHA and a manual approval gate).
6. **[DECISION]** Confirm whether an automatic deploy trigger should be disabled (pending the deployer's read-only confirmation of its existence).

---
**Status:** read-only incident report delivered. No application code, DB, secret, environment, deployment, traffic, or permission change was made. Production freeze intact.
