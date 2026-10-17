# INCIDENT REPORT — Production DB-backed endpoints return HTTP 500
**App:** CAUL AI Command Center (`caul-impl-gate` → caul.ai / www.caul.ai)
**Active image (UPDATED):** `customers-app@sha256:00dc352c…` via run `83a39522-dc0b-4bcc-9664-ef35966faf03` — promoted `2026-10-17T01:23:12Z`, now **live**. It **superseded** the earlier `sha256:07f98a06…` / run `1594a92f`. **Both images share the identical defect.**
**Mode:** STRICTLY READ-ONLY. No code/DB/secret/env/deploy/traffic/permission change. Production freeze respected.
**Secrets:** never displayed — config names + redacted host/port only.

> ⚠️ **FREEZE RISK [FACT]:** Both production promotions carry trigger `agentic` (agent-driven redeploy), NOT manual and NOT secret-change. Agent-driven redeploys remain the active promotion mechanism and have pushed the preview `/app` source (incl. dev-only `usage` routes + `usage-retention` cron) to production. No deploy is queued right now, but this mechanism is how the freeze keeps getting breached.

> Legend: **[FACT]** verified from source/logs/deployer · **[ASSUMPTION]** inferred, not directly observed on the prod runtime · **[DECISION]** owner input required.

---

## 1. Which DB-backed endpoints are failing
**[FACT]** The engine is created at import from the environment-selected PostgreSQL URL (`app/database.py`), with `pool_pre_ping=True`. Every route that depends on `get_db` executes SQL against that URL; in production that URL is unreachable (see §2), so the pre-ping/connect fails → **HTTP 500** on **all DB-backed endpoints**. The failing set is effectively every data route:

- `GET /api/health` (runs `SELECT 1`) and `GET /api/health/ready` (`SELECT COUNT(*) FROM permissions`)
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` (all query `users`/`sessions`)
- All routers mounted in `server.py`: `dashboard`, `recommendations`, `approvals`, `audit`, `emergency`, `admin`, `admin_manage`, `system`, `notifications`, `cron`, `usage` — every endpoint that opens a DB session.

**[FACT] NOT DB-backed → still return 2xx in production** (no DB session): `GET /api/` (static JSON), `GET /api/auth/provider` (stub metadata), `POST /api/connectors/contract-test` (in-memory stub suite).

**[FACT — deployer-confirmed]** Production runtime logs show `psycopg.OperationalError … connection to server at 127.0.0.1 port 5432 failed: Connection refused` (the Postgres seed on startup). This confirms the unreachable Postgres is the proven cause any DB-backed endpoint 500s on. The deployer did not capture a request-time 500 in the retained log window (observed live traffic was `GET /api/auth/me` → 401, which rejects before the DB), but the root cause is confirmed. Exact per-endpoint 500 counts remain unenumerated.

**Note on auth 401s (not 500s):** `GET /api/auth/me` and the cron endpoints can short-circuit to **401** *before* touching the DB when no valid token/cron-secret is presented (auth dependency rejects first). With a valid token they would reach the DB and 500. So unauthenticated probes to those paths look like 401, not 500 — this is expected and not evidence the DB works.

## 2. Is the runtime using APP_ENV=dev → localhost:5432?
**[FACT — deployer-confirmed]** The running production image logs `CAUL AI starting in env=dev (AUTH STUB — NOT PRODUCTION)` — **APP_ENV=dev is confirmed in production**. `app/config.py` allows only `{dev, staging}` and **refuses** a `production` value (guard raises `ConfigError`); there is **no production relational DB URL** in the env — only `DEV_/STAGING_DATABASE_URL` names exist. So production runs the Phase-1A dev/stub mode by design, with no production Postgres configured.

**[FACT — redacted hosts]** The DB URLs the app selects all point at **`localhost:5432`**:
- `DEV_DATABASE_URL` → host:port `localhost:5432`, db `caul_dev` (user/password REDACTED)
- `STAGING_DATABASE_URL` → host:port `localhost:5432`, db `caul_staging` (REDACTED)
- `DEV_ADMIN_DATABASE_URL` / `STAGING_ADMIN_DATABASE_URL` → `localhost:5432` (migration/admin only; app never uses them)

**[FACT]** In the production pod there is **no PostgreSQL** on `localhost:5432` (the platform template is MongoDB-based; no Postgres is provisioned by the pipeline). Result: connection refused → 500 on every DB route. Config env var NAMES present in prod image: `APP_ENV, DEV_DATABASE_URL, STAGING_DATABASE_URL, DEV_ADMIN_DATABASE_URL, STAGING_ADMIN_DATABASE_URL, JWT_SECRET, WEBHOOK_CRON_SECRET(+_DEV/_STAGING), CORS_ORIGINS, SESSION_TTL_MINUTES, CHAIN_ORG, MONGO_URL, DB_NAME` (values withheld).

## 3. Current vs previous deployment: trigger, queue, auto-trigger
**[FACT — deployer-confirmed]** Promotion sequence under the same job: `504a6073` (`2026-10-16T23:48:56Z`, `sha256:7f6d685b…`) → `1594a92f` (`2026-10-17T01:03:44Z`, `sha256:07f98a06…`) → **current `83a39522` (`2026-10-17T01:23:12Z`, `sha256:00dc352c…`, live)**. **Every promotion trigger = `agentic`** (agent-driven), NOT manual and NOT secret_change. **No deploy is queued or in-progress now** (`run_status=success`, no pending run). **Agent-driven (`agentic`) redeploys remain the active trigger mechanism** — this is what keeps rebuilding the preview `/app` source (incl. dev-only `usage` routes + `usage-retention` cron) into production.

## 4. Why did the deployment health check pass?
**[FACT — deployer-confirmed]** The pipeline health check probes **only `GET /health`** and treats non-5xx as "up"; it **SKIPS `GET /`** (Cloudflare frontend). In this app `GET /health` has **no backend route**, so FastAPI returns **404 = non-5xx = treated as up**. The probe **never exercises any DB-backed `/api` endpoint**, so an unreachable Postgres **cannot** fail the gate. This is a **readiness-semantics gap** (flagged in `LAUNCH_READINESS.md §5`): `/health` must become DB-aware so a DB outage fails the check.

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
