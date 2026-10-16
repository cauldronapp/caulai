# STAGE_B_PRODUCTION_ENV_DESIGN.md
**CAUL AI — Stage B design: explicit production environment mode, fail-fast checks, and default-off feature flags (owner review).**
**Planning document only. Nothing executed.** No code written/run, no accounts created, no secrets changed, no database provisioned, no dev/staging/production modification. The **$0 / no-paid-accounts** constraint is preserved; **no free-tier account is assumed approved.** Production database-backed functionality remains **UNAVAILABLE** until the DB and release controls are approved.

> Legend: **[EXISTS]** today · **[PROPOSED]** design, not built · **[DECISION]** owner choice · **[BLOCKER]** must resolve before go-live.

---

## 1. Goal of Stage B
Introduce a real, explicit **`production`** environment in the configuration layer so production (a) uses its **own** database, never dev/staging; (b) **refuses to boot** into a misconfigured/unsafe state; and (c) keeps **dev-only routes and the retention cron OFF by default** everywhere except explicitly enabled development. Stage B is **developed and tested in dev only** when later approved; this document just specifies it.

**Explicitly out of scope for Stage B:** provisioning a DB, creating accounts, editing secrets, deploying. Those are Stages C–E and remain frozen.

---

## 2. Proposed production environment configuration

### 2.1 Environment values
- Extend the allowed set from `{dev, staging}` to `{dev, staging, production}` **[PROPOSED]**. `production` is a first-class value — **not** an alias of `dev`.
### 2.2 Required variable names (names only — no values here; not created by this doc)
| Variable | Purpose | Notes |
|---|---|---|
| `APP_ENV` | Selects env (`dev`/`staging`/`production`) | **Required in every deployed environment**; missing/unknown ⇒ fail-closed (no default). Local dev sets `dev` explicitly. |
| `PROD_DATABASE_URL` | App (least-privilege) connection for production | **New.** Used ONLY when `APP_ENV=production`. |
| `PROD_ADMIN_DATABASE_URL` | Owner/admin connection for prod migrations + grants | **New.** Never used by the running app. |
| `PROD_DB_EXPECTED_NAME` | Expected production dbname for the identity guard | **New.** Suggested value `caul_prod` **[DECISION]**. |
| `WEBHOOK_CRON_SECRET_PRODUCTION` | Per-env cron secret for production | **New.** Mirrors existing per-env cron secret pattern. |
| `USAGE_LAYER_ENABLED` | Feature flag for the dev-only usage routes/cron | **New.** Default **false**; see §4. |

**Resolution rule [PROPOSED]:** `get_runtime_database_url("production")` returns **only** `PROD_DATABASE_URL`; `get_admin_database_url("production")` returns **only** `PROD_ADMIN_DATABASE_URL`. There is **no fallback** to `DEV_DATABASE_URL`/`STAGING_DATABASE_URL` under any circumstance. If the prod variable is missing, the app fails fast (see §3) — it must never borrow a dev/staging URL.

### 2.3 What stays unchanged
- `DEV_DATABASE_URL`, `STAGING_DATABASE_URL`, and their admin URLs keep their current meaning for dev/staging. Dev and staging behavior is unaffected by Stage B.

---

## 3. Fail-fast startup checks (production safety guards) [PROPOSED]
Executed at application startup (before serving traffic). If **any** check fails, the app **refuses to start / refuses readiness** with a clear, non-secret error — it never boots into a broken or unsafe state.

1. **Known env (fail-closed):** `APP_ENV` is **explicitly set** and ∈ `{dev, staging, production}`. A **missing** `APP_ENV` or an **unknown** value causes the app to **refuse to start / refuse readiness** — there is **no default to `dev`** in deployed environments. (Local development sets `APP_ENV=dev` explicitly via its launcher/`.env`.)
2. **Required URL present:** the `*_DATABASE_URL` for the active env is set; otherwise refuse (no fallback).
3. **Production host guard:** when `APP_ENV=production`, the resolved DB host must **not** be `localhost`/`127.0.0.1` (prevents the current dangling-localhost failure).
4. **Production isolation guard:** when `APP_ENV=production`, the resolved `dbname` must **equal `PROD_DB_EXPECTED_NAME`** and must **not** be `caul_dev`/`caul_staging` (prevents accidental reuse of dev/staging).
5. **TLS expectation (production):** require a TLS-enabled connection setting (e.g., `sslmode=require`) **[DECISION]** — a managed, externally reachable DB should use TLS.
6. **Connectivity probe:** a `SELECT 1` against the resolved DB succeeds.
7. **Schema head check:** the DB's Alembic head matches the expected head bundled with the release; a mismatch blocks readiness (surfaces "migrations not applied/incompatible").
8. **Seed/permissions presence:** `permissions` table is non-empty (existing readiness semantics), else `not_ready`.

**Health/readiness reporting [PROPOSED]:** `/api/health` and `/api/health/ready` report `env`, the resolved `database` **name** (non-secret), and head status. In production, if guards 3–8 fail, readiness returns a non-200 with a sanitized reason — making a misconfigured prod *observably* not-ready instead of a raw 500.

> Note: the guards are **validation logic only**; they expose **no secret values** (host/dbname are non-secret identifiers used for comparison messages).

---

## 4. Default-off feature flags — blocking dev-only routes & the retention cron outside dev

### 4.1 Principle
Dev-only capabilities (the usage measurement layer: `/api/usage/*` and the `usage-retention` cron) must be **inert by default** and only active where **explicitly enabled development** turns them on. Production (and staging) keep them **off** unless the owner explicitly approves enabling them.

### 4.2 Flag definition [PROPOSED]
- `USAGE_LAYER_ENABLED` (boolean), resolved from env, **default `false`**.
- **Allowed-to-enable rule:** the flag may only take effect when `APP_ENV` is in an explicit dev allow-list (e.g., `{dev}`) **and** the flag is truthy. In `staging`/`production`, the layer is **forced off** regardless of the flag value (defense in depth — a stray `true` in prod still yields "off").
  - Effective predicate (design intent): `usage_enabled = (APP_ENV == "dev") and (USAGE_LAYER_ENABLED is true)`.
  - **[DECISION]** whether `staging` may ever enable it; default proposal: **no** (dev only).

### 4.3 How routes are blocked
- The `/api/usage/*` router is **registered only when `usage_enabled` is true**; when false, the paths **do not exist** → return 404. (No reliance on description text or RBAC alone.)
- Result in production: `/api/usage/metrics` and `/api/usage/purge` return **404**, matching today's live-prod behavior, by design rather than by accident.

### 4.4 How the retention cron is blocked
- The `usage-retention` cron endpoint is **registered only when `usage_enabled` is true**; otherwise `/api/cron/usage-retention` returns **404**.
- Additionally, `run_usage_retention()` **no-ops with a logged notice** if `usage_enabled` is false (second layer: even a manual/stray invocation does nothing).
- `.emergent/crons.yml` is **release-controlled**: the `usage-retention` entry is kept **out of the production-bound manifest**; a pre-deploy diff surfaces any cron change for approval. **[DECISION]** whether to maintain per-environment cron manifests.

### 4.5 Migrations
- The usage migration (`a1b2c3d4e5f6`) is applied to an environment **only** by a deliberate, approved `alembic upgrade` against that env's admin URL (Stage D process). It is never auto-applied on boot and never implicitly reaches production.

---

## 5. Test / verification checklist (for the future dev-only implementation)
All tests run **in dev only** when Stage B is approved; **100% backend coverage gate** must stay green. No staging/prod execution.

**Environment resolution (fail-closed; no implicit default)**
- [ ] **Missing `APP_ENV`** (unset/empty) → fail-closed: `get_app_env()` raises and the app refuses to start/ready. (Asserts the old default-to-`dev` is gone.)
- [ ] **Invalid `APP_ENV`** (e.g., `prod`, `production2`, `PROD`, random) → fail-closed: raises; no fallback to any env.
- [ ] **`APP_ENV=dev`** (explicit) → resolves `DEV_DATABASE_URL`; usage layer may be enabled (see flags).
- [ ] **`APP_ENV=staging`** (explicit) → resolves `STAGING_DATABASE_URL`; usage layer forced off.
- [ ] **`APP_ENV=production`** (explicit) → resolves `PROD_DATABASE_URL`; **never** dev/staging (assert no fallback); usage layer forced off.
- [ ] Missing `PROD_DATABASE_URL` with `APP_ENV=production` → fail-fast error (no silent fallback to dev/staging).
- [ ] Missing `DEV_DATABASE_URL`/`STAGING_DATABASE_URL` with their explicit env → fail-fast (regression; no cross-fallback).

**Fail-fast guards** (simulated via config inputs; no real prod DB)
- [ ] Unknown `APP_ENV` → refuses.
- [ ] Production host `localhost`/`127.0.0.1` → refuses (guard #3).
- [ ] Production `dbname` = `caul_dev`/`caul_staging` or ≠ `PROD_DB_EXPECTED_NAME` → refuses (guard #4).
- [ ] TLS setting absent in production → refuses or flagged per [DECISION] (guard #5).
- [ ] Connectivity probe failure → readiness non-200 with sanitized reason (guard #6).
- [ ] Alembic head mismatch → readiness non-200 (guard #7).
- [ ] Empty `permissions` → `not_ready` (guard #8).
- [ ] No secret values appear in any error/health output.

**Feature flags / blocking**
- [ ] `APP_ENV=dev` + `USAGE_LAYER_ENABLED=true` → `/api/usage/*` and `/api/cron/usage-retention` exist and work.
- [ ] `APP_ENV=dev` + flag false → those paths 404; `run_usage_retention()` no-ops.
- [ ] `APP_ENV=staging` or `production` (flag true **or** false) → those paths 404; `run_usage_retention()` no-ops (forced off).
- [ ] `crons.yml` production-bound manifest contains **no** `usage-retention` entry; pre-deploy diff flags any addition.

**Health/readiness**
- [ ] `/api/health` returns `env` + resolved `database` name (non-secret) when DB reachable.
- [ ] Misconfigured production (guards fail) → readiness clearly **not_ready** (no raw 500), sanitized reason.

**Production functionality status**
- [ ] Until Stage C/D/E are approved and complete, production DB-backed functionality is reported **UNAVAILABLE** (readiness not-ready) rather than appearing to work.

---

## 6. Constraints preserved
- **$0 / no paid accounts:** Stage B introduces **no** database and **no** account; it only adds configuration/validation/flag logic (to be built in dev later). The production DB (Stage C) remains an **open [BLOCKER]** pending the owner's decision; **no free-tier account is assumed approved.**
- **Freeze intact:** no code, config, cron, secret, DB, staging, or production change from this document.
- **Production stays down-by-design for data:** DB-backed endpoints remain unavailable (readiness not-ready) until the DB + release controls are approved.

---

## 7. Platform-support question (TEXT ONLY — do not send)
> **To:** Emergent Platform Support — **Subject:** CAUL AI (`caul-impl-gate`) — is a production-reachable PostgreSQL available, and at what cost?
>
> Our app is PostgreSQL-only. The template provisioned a MongoDB (`caul-impl-gate-base`, unused). Production currently resolves to a pod-local `localhost:5432` Postgres that does not exist in the production pod, so DB-backed endpoints fail.
> 1. Do you offer a **production-reachable managed PostgreSQL** for this app, isolated from our dev/staging databases?
> 2. What are the **plan tiers and recurring costs**, and is there a **$0** tier reachable from the production pod (we are preserving a $0/no-paid-accounts constraint and have **not** approved any free-tier third-party account)?
> 3. If there is **no $0 option**, please state that plainly so we can treat production go-live as blocked pending a budget decision.
>
> **Constraints:** production release freeze in place. Do **not** deploy, redeploy, change secrets, or provision/modify any database while answering. We will not share secret values; sanitized host/dbname confirmations suffice.

---

## 7a. Platform-support request — release path & source integrity (DRAFT TEXT — do not send)
> **To:** Emergent Platform Support — **Subject:** CAUL AI (`caul-impl-gate`) — prevent secret-change rebuilds of unapproved preview source; pin releases to an identifiable artifact
>
> **Incident reference (no secret values):** production deployment **`994120f4-929a-41c2-a895-093d4fd242e8`** was a **redeploy triggered by a secret change** and built from the preview pod `/app` with **no Git SHA** (the pipeline excludes `.git`). Its only build identity was the image digest **`sha256:0721b61546cfa269a3b9b226491046774de56b56a292b05bbc7bf9cf25c6b5d4`**. This means a secret edit can silently promote whatever happens to be in the preview pod, and we cannot name the exact source a release contains.
>
> **Questions / requests:**
> 1. **Stop secret-change from rebuilding source:** How can we prevent a `secret_change` event from triggering a rebuild/redeploy of the current preview-pod source? Can that trigger be **disabled**, or configured to **reuse the last approved/released image** (apply the new secret to the existing image without rebuilding)?
> 2. **Pin each release to an identifiable source artifact:** Since `.git` is excluded, what is the supported way to tie each production release to a **durable, human-identifiable source identifier** (e.g., a tagged/versioned build artifact with a recorded content hash and release label), so we can state exactly what is live, diff two releases, and roll back to a known artifact — using the image digest as the anchor if that is the canonical identifier?
> 3. **Release gate:** Can production deploy/redeploy require **manual approval** plus a pre-deploy summary (pending DB migrations, `.emergent/crons.yml` changes, new API routes), so nothing is promoted without sign-off?
>
> **Constraints:** We have a production release freeze in place. Please do **not** deploy, redeploy, rotate secrets, or change any database while answering. We will not share secret values; sanitized confirmations are sufficient.

## 8. Decisions needed to proceed to a dev-only Stage B build
1. Approve adding a first-class `production` env + `PROD_DATABASE_URL`/`PROD_ADMIN_DATABASE_URL` with **no** dev/staging fallback.
2. Confirm `PROD_DB_EXPECTED_NAME` (proposed `caul_prod`) and the TLS requirement.
3. Confirm `USAGE_LAYER_ENABLED` default-off and **dev-only** enablement (staging/prod forced off).
4. Approve building + testing Stage B **in dev only** (100% coverage held), with **no** staging/prod/secret/DB/deploy changes.

**Nothing is implemented until you approve. The release freeze and the "production DB-backed functionality UNAVAILABLE" status remain in place.**
