# PRODUCTION_READINESS_PLAN.md
**CAUL AI — production-readiness plan (owner review draft).**
**Plan only. Nothing executed.** No code, configuration, cron, secret, database, staging, production, or deployment change. Dev and staging remain untouched.

> Legend: **[EXISTS]** in repo today · **[PROPOSED]** future work (not built) · **[DECISION]** owner choice · **[BLOCKER]** must be resolved before go-live · **[LEGAL/3P]** third-party/account action the owner must take.

---

## 0. Why this plan exists (confirmed incident context)
- The production frontend loads (static/Cloudflare), but **all DB-backed endpoints 500**: the backend resolves `DEV_DATABASE_URL = localhost:5432/caul_dev`, and the production pod has **no PostgreSQL at localhost** → `connection refused`.
- The app has **no production environment concept**: `get_app_env()` permits only `{dev, staging}` and defaults to `dev`; production currently runs as `APP_ENV=dev`.
- There is **no dedicated production database** and no production-reachable PostgreSQL. This plan fixes that safely, with gates.

---

## 1. Explicit production environment mode (no routing through DEV/STAGING URLs)
**Current [EXISTS]:** `config.get_app_env()` → `{dev, staging}` only; `get_runtime_database_url()` returns `DEV_DATABASE_URL`/`STAGING_DATABASE_URL`. Production piggybacks on `dev`. This is the core defect.

**Proposed [PROPOSED]:**
- Add `production` to an explicit allow-list and a **dedicated** `PROD_DATABASE_URL` / `PROD_ADMIN_DATABASE_URL`. `get_runtime_database_url("production")` returns **only** `PROD_DATABASE_URL` — it must **never** fall back to dev/staging.
- **Fail-fast startup checks** (run at import/boot): (a) `APP_ENV` is a known value; (b) the required `*_DATABASE_URL` for that env is set; (c) **in production, the resolved host is NOT `localhost`/`127.0.0.1`** and the `dbname` is **not** `caul_dev`/`caul_staging` (guard against accidental dev/staging reuse); (d) a connectivity probe (`SELECT 1`) succeeds; (e) schema is at the expected Alembic head. If any check fails, the app refuses to serve (clear error), rather than booting into a broken state.
- **Readiness probe** upgraded to assert env + DB identity + head, so a misconfigured prod can't report "ready."
- **[DECISION]** Confirm the production dbname convention (e.g., `caul_prod`) and that production must be a distinct env value (`production`) rather than reusing `dev`.

---

## 2. A production-reachable PostgreSQL, isolated from dev/staging — options & costs
**Requirement:** a PostgreSQL instance **reachable from the production pod** (not pod-local `localhost`), **physically isolated** from `caul_dev`/`caul_staging` (separate instance or at least separate DB+role on a managed, externally reachable server).

**Option comparison (NOTHING provisioned; no accounts created; no spend):**

| Option | Reachable from prod? | Isolation | Cost / recurring | Notes |
|---|---|---|---|---|
| **Pod-local `localhost` Postgres** (today's config) | **No** (no server in prod pod) | n/a | $0 | This is the current broken state. Not viable. |
| **Emergent platform-managed PostgreSQL** (if offered) | Likely yes | Yes (dedicated DB) | **Unknown — ask support** | Platform provisioned MongoDB for this template; whether a managed Postgres is available (and at what price) is **unconfirmed**. See support request §7. |
| **Managed Postgres free tier** — e.g., Neon / Supabase / Railway free plans | Yes (public host + TLS) | Yes (dedicated project/DB) | **$0** on free tier (with size/compute/idle limits); paid tiers ~$upwards/month if limits exceeded | **[LEGAL/3P]** requires the owner to create an account; I will not. Free tiers may sleep/limit connections — acceptable for low-traffic governance app, validate. |
| **Managed Postgres paid** — e.g., small RDS/Cloud SQL/managed instance | Yes | Yes (dedicated instance) | Recurring **paid** (small instance + storage + backups + egress; varies by provider/region) | Most robust; predictable. Requires account + spend. |

**$0 assessment / [BLOCKER] honesty:**
- A true $0 option that is **both production-reachable and requires no new account/spend** is **not confirmed to exist** in this environment. The pod-local Postgres is $0 but unreachable in prod; free-tier managed Postgres is $0 but **requires the owner to create a third-party account**.
- **Therefore: if (a) the Emergent platform does not offer a $0 production-reachable PostgreSQL, and (b) you do not wish to create any free-tier account, then there is NO suitable $0 option and this is a hard [BLOCKER] to production go-live.** Decisions in §8 resolve it.

---

## 3. Backups, restore testing, least-privilege, network security, gated migrations
**[PROPOSED] — applies to the chosen prod DB:**
- **Backups:** automated daily logical backups (`pg_dump`) + provider point-in-time recovery if available; retention policy **[DECISION]** (e.g., 7–30 days). Store off the app pod.
- **Restore testing:** scheduled **restore drills** into a throwaway DB to prove backups are usable; record RPO/RTO. A backup is not "done" until a restore has been verified.
- **Least-privilege credentials:** reuse the existing pattern — migrations/grants run as an **owner/admin** role (`PROD_ADMIN_DATABASE_URL`); the **app** connects as a restricted role (`PROD_DATABASE_URL`) with INSERT/SELECT/UPDATE/DELETE on app tables and **INSERT/SELECT-only on audit tables** (via `apply_grants.py` policy). No superuser for the app.
- **Network security:** TLS-required connections (`sslmode=require`); restrict DB network access to the prod pod's egress (IP allow-list / private networking where supported); no public 0.0.0.0 exposure; rotate credentials on a schedule.
- **Gated migration process:** migrations never auto-run on boot. A **manual, approved** step runs `alembic upgrade` against `PROD_ADMIN_DATABASE_URL`, preceded by a **schema-only backup** and a **pending-migration manifest** for sign-off, followed by verification (head + table presence). Mirrors the controlled process used during the staging incident remediation.

---

## 4. Keeping dev-only routes, migrations, and scheduled jobs out of production by default
**Problem:** today, `/api/usage/*`, the usage migration, and `usage-retention` cron would ship to any environment because they're unconditional in code / shared `crons.yml`.

**[PROPOSED] controls:**
- **Feature flags, default-off:** gate dev-only routers (e.g., the usage layer) behind an explicit flag (e.g., `USAGE_LAYER_ENABLED`, default **false**; and/or an env allow-list). In production the flag stays off unless you approve it. Handlers return 404/disabled when off.
- **Cron env-guarding:** `run_usage_retention()` (and any dev-only job) refuses unless its feature/env is enabled — so even if registered, it no-ops in prod.
- **`crons.yml` as release-controlled:** keep dev-only cron entries **out of the production-bound** manifest; a pre-deploy diff (see §5) surfaces any cron additions for approval. Consider separate cron manifests per environment if the platform supports it **[DECISION]**.
- **Migration gating:** the explicit per-env migration profile (§1) means a dev-only migration is only applied to prod by a deliberate, approved `upgrade` against the prod admin URL — never implicitly.

---

## 5. Release controls — identify exact source; stop secret-change silent promotion
**Confirmed gap:** the last prod deploy built from the **preview pod `/app` with no Git SHA** (image digest only), and was triggered by a **secret change** — so a secret edit can silently promote whatever is in the pod.

**[PROPOSED] controls (mostly platform/support — see §7):**
- **Identifiable source per release:** record a durable, human-labeled source identifier + content hash for every production build; be able to state "prod = release X" and diff/rollback to it.
- **Decouple secret rotation from code promotion:** `secret_change` redeploys must **reuse the last approved image**, not rebuild current pod source.
- **Explicit release gate:** production deploy/redeploy requires owner approval + a **pre-deploy manifest** (pending migrations, `crons.yml` diff, new `/api/*` routes, feature-flag states) for sign-off.
- **Promotion from staging:** prefer promoting a staging-verified artifact to prod rather than building fresh from preview.

---

## 6. Staged implementation & verification plan
Each stage is **gated**; nothing proceeds without your approval of that stage. Dev/staging stay unchanged throughout.

- **Stage A — Decisions & source of a prod DB (no build):** resolve §8 decisions, especially the DB option (and the $0 [BLOCKER]). *Verify:* chosen DB target identified (host/dbname only; no secrets in chat).
- **Stage B — Code: production env mode + startup guards + feature flags (DEV ONLY first):** implement `production` env + `PROD_*_DATABASE_URL` resolution + fail-fast checks + default-off flags + cron guards; **develop and test in dev**, maintain 100% coverage. *Verify:* dev tests prove prod-mode refuses localhost/dev/staging targets and that dev-only routes/crons are off by default. **No prod/staging touch.**
- **Stage C — Provision prod DB + least-privilege roles (owner/platform action):** owner provisions the managed Postgres, creates `caul_prod` + app/admin roles, sets TLS + network restrictions. *Verify:* connectivity from a controlled check; `apply_grants` policy applied; audit tables INSERT/SELECT-only.
- **Stage D — Secrets + gated migration (owner action, approved):** owner sets `PROD_DATABASE_URL`/`PROD_ADMIN_DATABASE_URL` + `APP_ENV=production` in the prod Secrets panel; run schema-only backup → approved `alembic upgrade` → seed. *Verify:* head correct, tables present, backup+restore drill passes.
- **Stage E — Release controls + deploy (approved):** apply source-pinning + secret-change decoupling (platform/support); deploy the approved artifact. *Verify:* `/api/health` 200 with `env=production`, `database=caul_prod`; `/api/health/ready` ready; dev-only routes 404; `usage-retention` not registered/inert; audit chain verifies.
- **Stage F — Post-go-live:** monitoring, backup schedule live, restore drill cadence, incident runbook. *Verify:* alerts fire on DB-unreachable and readiness failures.

---

## 7. Platform-support request (DRAFT TEXT — do not send)
> **To:** Emergent Platform Support — **Subject:** CAUL AI (`caul-impl-gate`) production hardening: managed PostgreSQL, source pinning, secret-change behavior
>
> 1. **Managed PostgreSQL:** Do you offer a production-reachable managed PostgreSQL for this app (the template provisioned MongoDB, which we don't use)? If yes, what are the plan tiers and **recurring costs**, and is there a **$0** tier reachable from the production pod? We need a DB **isolated** from our dev/staging (`caul_dev`/`caul_staging`, currently pod-local `localhost`).
> 2. **Identifiable source per release:** Our last prod deploy built from the preview pod with **no Git SHA** (image digest only). How can each production release record a durable, human-identifiable source revision for diff/rollback?
> 3. **Secret-change behavior:** A `secret_change` triggered a rebuild from current preview source. Please make secret rotations **reuse the last approved image** instead of promoting unreviewed code, or advise how to configure that.
> 4. **Release gate:** Can we require manual approval + a pre-deploy manifest (pending migrations, cron entries, new routes) before any production deploy?
>
> **Constraints:** We have a production release freeze. Please do **not** deploy, redeploy, rotate secrets, or change databases while answering. We will not share secret values; sanitized host/dbname confirmations are sufficient.

---

## 8. Decisions you need to make
1. **Prod DB option** (§2): Emergent managed Postgres (pending support) **vs** a free-tier managed Postgres (you create the account) **vs** paid managed instance — and acceptance that **if neither a platform $0 option nor a free-tier account is acceptable, go-live is blocked**.
2. **Isolation level:** dedicated instance vs. dedicated DB+role on a shared managed server.
3. **Env model:** approve a real `production` `APP_ENV` + `PROD_*_DATABASE_URL` (never dev/staging fallback) and the `caul_prod` naming.
4. **Backup/retention + restore-drill cadence** (RPO/RTO targets).
5. **Feature-flag defaults** for dev-only layers (usage endpoints/cron) — confirm default-off in prod.
6. **Release controls:** approve the source-pinning + secret-change decoupling + pre-deploy manifest gate.
7. **Who performs** the owner/platform actions (provisioning, secret edits, approved migration) and the approval checkpoints.

**Until you review this plan and approve a specific stage, nothing will be implemented. The release freeze stays in place.**
