# RCA — CAUL AI (caul-impl-gate) — Read-only diagnosis under release freeze

**Scope:** Diagnosis only. No deploy/redeploy/rollback/secret/DB/routing changes were made. An isolated throwaway sandbox (eph pod) was used to read the active run's source; it does not touch production.

## 1. Most-recent deployment run — status
- Run `31bef5ce-7237-4cd9-ac33-183a46f1dbbf`: **COMPLETED — success**.
- Steps all green: wakeup_environment, build, mongodb_migrate, manage_secrets, deploy, health_check (`get_step_status`).
- It is the deployment's **active_run_id** (currently serving). No pending/in-progress/queued run is visible in metadata.
- **Caveat on the "new background deployment":** No run newer than `31bef5ce` exists in deployment metadata or logs. If a background deployment was "just initiated", it has NOT yet registered a run and has NOT reached production. Production currently serves `31bef5ce`.

## 2. Target
- **Production.** Deployment `caul-impl-gate`, live URL https://caul-impl-gate.emergent.host, custom domains `caul.ai` + `www.caul.ai` (both verified), target_cluster `deployment-cluster-05`, type=redeploy, tier_0, frontend_type=cloudflare.
- (Note: the app's own code declares "Phase 1A … NO production environment" — but it is in fact deployed to the production runtime.)

## 3. Source identity
- Pipeline excludes `.git`, so no branch/commit SHA is available in the pulled source.
- **Image digest (live):** `287883095218.dkr.ecr.us-west-2.amazonaws.com/customers-app@sha256:ef70a3cb77a7b94e573d4b5d27d5445ae64fa76036ec1fd20ce45d17243b521f`
- Run timestamps: created_at `2026-10-16T20:30:53Z`, completed_at `2026-10-16T20:36:10Z`. Trigger: agentic.

## 4. IDs
- deployment_id: `994120f4-929a-41c2-a895-093d4fd242e8`
- run_id (most recent = active): `31bef5ce-7237-4cd9-ac33-183a46f1dbbf`
- job_id: `cecc1265-925c-45b5-a43d-6a83ddc65df1`

## 5. Did a PRODUCTION PROMOTION occur?
**YES.** Run `31bef5ce` is the active_run_id; `deployment_updated_at` (2026-10-16T20:36:10Z) equals the run's completion; the live URL serves this run's pods (CAUL AI frontend 200; `GET /api/` returns the run's JSON). New source **did** reach the live production runtime. Production is **NOT** unchanged — it was advanced to run `31bef5ce`.

## 6. Are the usage migration / routes / cron in the live production image?
**Contrary to the prior "expect NOT" diagnosis — YES, they are present and (for the routes/cron) live.**

- **/api/usage/* routes — PRESENT and LIVE.** `backend/app/routers/usage.py` defines `APIRouter(prefix="/api/usage")` with `/metrics` and `/purge`. `server.py:135` mounts it unconditionally (`for r in (…, cron, usage): app.include_router(r.router)`). There is NO runtime env-gate — "DEV-ONLY" is only a docstring. Live probe: `GET /api/usage/metrics` → **401 "Not authenticated"** (reaches the auth dependency; a non-existent route would be 404). PROVEN live.
- **usage-retention cron — PRESENT and LIVE.** `backend/app/routers/cron.py` defines `POST /api/cron/usage-retention` (plus verify-audit, weekly-digest). Cron router mounted at `server.py:135`. Live evidence: `POST /api/cron/verify-audit` → **401** in logs (router is mounted & serving). No env-gate.
- **Alembic migration `a1b2c3d4e5f6` — FILE PRESENT in the image.** `backend/alembic/versions/a1b2c3d4e5f6_usage_instrumentation.py` ships in the built image. It is NOT auto-applied on boot (the FastAPI `lifespan` runs only `run_seed()`, no `alembic upgrade`). Whether it has been applied to any production database cannot be confirmed from here, and the app's `config.py` has a "production guard" that refuses any env other than dev/staging, so there is no sanctioned production DB.

## Additional finding (not asked, but material)
The live backend is partially erroring:
- `GET /api/health` → **500**; `POST /api/auth/login` → **500** (Traceback in logs).
- `config.py` `get_app_env()` only permits `dev`/`staging` and raises `ConfigError` otherwise; `/api/health` depends on `get_db`/env, which is the likely 500 source (APP_ENV not dev/staging in prod, or DB URL unset). 
- The k8s probe hits `GET /health` which 404s (app serves `/api/health`); 404 is non-5xx, so the pipeline health_check passed even though the real health route 500s. This is why the deploy went green despite a degraded backend.

## Evidence summary
- describe_deployment_state: active_run_id, image digest, run history, promotion state.
- get_step_status(31bef5ce): all steps success.
- eph pod (source of 31bef5ce): server.py router wiring, routers/usage.py, routers/cron.py, alembic/versions/a1b2c3d4e5f6, config.py production guard.
- Live probes: `/api/`→200, `/api/health`→500, `/api/usage/metrics`→401.
- fetch_app_logs(31bef5ce): `/api/cron/verify-audit`→401, `/api/auth/login`→500, `/health`→404 probe, Traceback.

## Nothing changed. Report-only, freeze respected.
