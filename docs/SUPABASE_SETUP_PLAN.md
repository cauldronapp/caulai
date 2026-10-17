# SUPABASE_SETUP_PLAN.md — read-only plan (CAUL AI)
**Owner is signing up for Supabase Pro but NOT connecting it yet. Production freeze in effect.**
**Planning only. No Supabase connection, no code/config/secret/DB/deploy change, no projects created, no migrations run.** No secret values requested or shown.

> Legend: **[FACT]** verified evidence · **[CANNOT VERIFY]** not determinable here · **[RECOMMEND]** proposal · **[DECISION]** owner input.

---

## 1. Production region (for choosing a nearby Supabase region)
- **[FACT — deployer-confirmed]** Production runs on **AWS, region `us-west-2` (Oregon)**, arm64/Graviton nodes. Evidence: the active run's ECR image host `287883095218.dkr.ecr.us-west-2.amazonaws.com/...` and pods scheduled on EC2 nodes in `deployment-cluster-06` (us-west-2).
- **[CANNOT VERIFY]** The exact Availability Zone (`us-west-2a/b/c`) is not determinable from available tooling — an Emergent support ticket is needed if you want the AZ.
- **[RECOMMEND]** Create your Supabase projects in **`West US (Oregon) / us-west-2`** to co-locate the DB with the app and minimize app↔DB latency. Supabase region is **fixed per project at creation** — choose deliberately.

## 2. Staging + production project arrangement & monthly cost (nothing created)
- **[FACT — Supabase billing, latest]** Billing is **organization-based**: the **Pro plan is $25/mo** per organization and **includes $10/mo of compute credit**. **Each project runs on its own dedicated compute instance**, billed hourly; the $10 credit applies to total compute.
- **[RECOMMEND] Two separate projects in one Pro org** — a **staging** project and a **production** project — for true data isolation (never share a DB across envs). This matches the app's dev/staging/prod separation model.
- **Estimated monthly cost [FACT-based estimate]:**
  - Both projects on **Micro** (~$10/mo each): **$25 (Pro) + $10 + $10 − $10 credit = ~$35/mo.**
  - Cost-saver: **pause the staging project** when idle (paused projects incur no compute) → effectively **~$25/mo** while only production runs.
  - Compute can scale later (Small ~$15, Medium ~$60, etc.); Micro is appropriate for a low-volume pilot.
  - **IPv4 note:** the free **Session pooler is IPv4** (see §3), so you should **not** need the dedicated **IPv4 add-on (~$4/mo/project)**. Only budget it if you must use a *direct* (non-pooler) connection over IPv4.
- **[DECISION]** One project vs two (isolation vs cost); compute size; whether to pause staging between tests.

## 3. Exact PostgreSQL connection method the deployed app requires
**App shape [FACT]:** FastAPI + **synchronous SQLAlchemy** `create_engine(... pool_pre_ping=True)` (`app/database.py`), psycopg3 driver (`postgresql+psycopg://`), long-lived uvicorn pod (not serverless). It uses SQLAlchemy's own connection pool and relies on session semantics (transactions, `SELECT current_database()` guard).

- **[RECOMMEND] Use the Supabase Supavisor *Session* pooler, port `5432`.** Rationale:
  - It is **reachable over IPv4 on all plans** (avoids the IPv4 add-on and any IPv6 uncertainty in the Emergent pod).
  - **Session mode** preserves session-level features and works cleanly with SQLAlchemy's persistent pool (unlike transaction mode on `6543`, which would require `NullPool` + disabling prepared statements).
  - A *direct* connection (`5432`, non-pooler) is **IPv6-only unless** the paid IPv4 add-on is enabled — not recommended here.
  - **Do NOT use the transaction pooler (`6543`)** for this app unless it is refactored to `NullPool` + `prepare_threshold=None`.
- **SSL [RECOMMEND/required]:** append **`sslmode=require`** to the URL (psycopg3 honors it). This also satisfies the Stage B production TLS guard (§3.5 of Stage B design).
- **Engine tuning [RECOMMEND]:** keep SQLAlchemy `pool_size` small (5–10), add `pool_recycle≈600–1800`s and keep `pool_pre_ping=True` to avoid stale pooled SSL connections. (Implementation detail for the future build, not changed now.)
- **Exact environment variable NAMES the app will need (values never shown; set later via the platform Secrets panel, not committed):**
  - `APP_ENV` = `production` (and `staging` for the staging project)
  - `PROD_DATABASE_URL` — **app / least-privilege** role, Session pooler host, `:5432`, `?sslmode=require`
  - `PROD_ADMIN_DATABASE_URL` — **migrations/admin** role only (never used by the running app)
  - `PROD_DB_EXPECTED_NAME` — the production dbname identity guard expects (**[DECISION]**, see note below)
  - `WEBHOOK_CRON_SECRET_PRODUCTION` — per-env cron secret
  - (staging mirrors these via the existing `STAGING_DATABASE_URL` / `STAGING_ADMIN_DATABASE_URL` names)
- **⚠️ dbname-guard nuance [DECISION]:** Supabase's default database is named **`postgres`**, but the app's isolation guard (`seed.py` / Stage B guard #4) expects a dedicated name like `caul_prod`. Options: (a) set `PROD_DB_EXPECTED_NAME=postgres` and isolate via a **dedicated schema + least-privilege role**, or (b) create a dedicated database within the project and point the URL at it. This must be decided before wiring the guard.
- **⚠️ least-privilege [RECOMMEND]:** create a dedicated **app role** (limited grants) for `PROD_DATABASE_URL`; reserve the Supabase `postgres`/service role strictly for `PROD_ADMIN_DATABASE_URL` migrations.

## 4. Code & migration work for an explicit production env + reachable URL (and how to test in isolation)
All of this is **[PROPOSED]** per `STAGE_B_PRODUCTION_ENV_DESIGN.md`; **none is implemented here.**
- **Config:** extend `ALLOWED_ENVS` to `{dev, staging, production}`; add `PROD_*` resolution with **no fallback** to dev/staging (`config.py`).
- **Fail-fast startup/readiness guards:** reject when `APP_ENV` missing/unknown; require the active `*_DATABASE_URL`; in production reject `localhost`/`127.0.0.1`, reject dbname = `caul_dev`/`caul_staging` (must equal `PROD_DB_EXPECTED_NAME`), require TLS (`sslmode=require`), run `SELECT 1`, check Alembic head, require non-empty `permissions`.
- **Health semantics:** make the probe the pipeline actually hits (`/health`) **DB-aware** (today it's a 404 that falsely reads as "up") so a DB outage fails the gate instead of passing. (Note: the gate's probe path is platform-side; pair the code fix with a platform config/support request.)
- **Feature-flag dev-only surface OFF in prod:** register `/api/usage/*` and `usage-retention` cron **only** when `APP_ENV=dev` + `USAGE_LAYER_ENABLED=true`; forced off in staging/production (404). Keep `usage-retention` out of the production-bound `crons.yml`.
- **Migrations (deliberate, never on boot):** run `alembic upgrade head` **manually** against `PROD_ADMIN_DATABASE_URL` (the Supabase project) to create the schema. **The seed does NOT run in production** — `seed.py` already refuses any env other than dev/staging, so production gets **schema only, no synthetic/demo data** (correct). Production's first real users come from real auth (Phase 1B), not the seed.
- **Testing with synthetic data only — in isolation:**
  1. Build + unit-test Stage B **in dev** (the 100% coverage gate stays green; guards tested via simulated config inputs — no real prod DB).
  2. For a **reachable-URL** rehearsal, use the **Supabase *staging* project** (never production): set the staging env URL, run `alembic upgrade head`, then populate with the **existing synthetic generators** — `seed.py` (dev/staging-guarded, `*.invalid` stub users) and `usage_synth.generate_synthetic()` (PII-free golden dataset). Verify health/readiness, RBAC, audit chain, dashboards against synthetic data.
  3. Do this rehearsal from a **separate, isolated Emergent app** (the $0 isolated-project path confirmed earlier) so no step can promote WIP to `caul-impl-gate` production. **No real customer data at any point.**

## 5. Are agent-driven production promotions blocked / manual-approval only?
- **[FACT — deployer-confirmed] NO. There is no manual-approval gate, and agent-driven (`agentic`) redeploys currently promote to production WITHOUT any manual confirmation.** The promote step auto-flips the active run on passing health checks; there is **no deployment-panel control or agent tool** to inspect or create such a gate. Confirmed chain `504a6073 → 1594a92f → 83a39522` (all `agentic`, all promoted). So I **cannot** confirm promotions are blocked — the evidence proves they are **not**.
- **[FACT]** Adding an approval checkpoint before the promote step is a **platform-level capability with no user control today** — it requires an **Emergent support ticket** (quote deployment `caul-impl-gate` / `994120f4-929a-41c2-a895-093d4fd242e8`, job `cecc1265-925c-45b5-a43d-6a83ddc65df1`).
- **[RECOMMEND]** Until the platform confirms a gate: (a) I will **not** trigger any deploy; (b) file the support request (pairs with `STAGE_B_PRODUCTION_ENV_DESIGN.md §7a`) to require manual approval + a pre-deploy summary and to stop secret-change/agentic rebuilds of unapproved source. Treat "promotions require your approval" as **false today** until support enables a gate.

---

## Decisions you need to make (nothing proceeds until you decide)
1. **Supabase region** — create projects in **`us-west-2` (Oregon)** to match production (confirmed), or override for your pilot users. (Region is permanent per project.)
2. **Projects & compute** — two projects (staging+prod) vs one; Micro vs larger; pause staging when idle (~$35/mo both Micro vs ~$25/mo prod-only).
3. **Connection** — confirm **Session pooler :5432 + `sslmode=require`** (recommended) vs direct+IPv4 add-on.
4. **dbname guard** — `PROD_DB_EXPECTED_NAME=postgres` (schema-isolated) vs a dedicated database name; and create a least-privilege app role for the app URL.
5. **Approve the Stage B dev-only build** (code/guards/flags) with the 100% coverage gate, tested against the **staging Supabase project with synthetic data only** — still **no** production connect/deploy.
6. **Release gating** — authorize sending the §7a support request to get agent-driven/secret-change promotions behind a manual approval gate before any go-live.

**Status:** read-only plan delivered. No Supabase connection, no projects, no code/config/secret/DB/migration/deploy change. Production freeze intact.
