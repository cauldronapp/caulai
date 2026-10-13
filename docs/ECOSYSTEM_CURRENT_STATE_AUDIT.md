# ECOSYSTEM_CURRENT_STATE_AUDIT.md
**Phase 0 — Verified vs. Unknown inventory.** Cauldron Technologies, Inc. | read-only.

> Honesty rule honored: only CAUL AI (this Emergent project) was inspected from real sources. All other products were observed via public surfaces only or are entirely unknown pending authorized access. Nothing below is assumed from the spec.

## A. CAUL AI — VERIFIED from source (this project)
| Area | Verified finding |
|---|---|
| Phase status | Phase 1A **accepted/closed**; production hardening + dashboard analytics + saved audit filters added since. |
| Stack | FastAPI + SQLAlchemy 2.0 + Alembic; React 19 + Tailwind + shadcn/ui + recharts. |
| Datastore | PostgreSQL 15 (psycopg3); separate `caul_dev` / `caul_staging`; least-privilege roles (`caul_dev_user`/`caul_staging_user`); audit tables INSERT-only at DB level. |
| Identity | Provider-neutral `IdentityProvider` + **labeled STUB** (`StubIdentityProvider`). **NOT production identity.** JWT httpOnly sessions, server-side revocation. |
| RBAC | Server-side, default-deny, resolved from Postgres; CI-enforced route→permission coverage. |
| Audit | Tamper-**evident** hash-chained; per-env verify cron (HMAC). |
| Emergency | Global/granular pause, queue cancel/drain, revoke, rollback (stub paths). |
| Connectors | `BaseConnector` + contract-test gate; all connectors **Not Connected**. |
| Ops | `/api/health` + `/api/health/ready`; structured JSON logs + `X-Request-ID`; CI with 100% coverage gate; deployment readiness PASS. |
| Tests | 129 passing, **100% backend coverage** enforced. |
| Secrets | env-only (names): `JWT_SECRET`, `WEBHOOK_CRON_SECRET[_DEV|_STAGING]`, `*_DATABASE_URL`, `CORS_ORIGINS`. No external API keys. |

**Outstanding CAUL AI acceptance gates (must close before production integration):** real IdP (Auth0 dossier ready, not wired); no production environment yet; accessibility/security claims from Phase 1A should be re-verified independently; off-box audit export not active.

## B. Deal Flow OS — ACCESS GAP (public surface only)
Observed at https://dealflowos.app: real-estate **wholesaling** SaaS (seller finder, deal analyzer, cash-buyer marketplace, offer generator), marketed "Claude Sonnet 4.5 powered", register/login, free-trial→paid.
**UNKNOWN (needs authorized audit):** repo/stack, DB engine, hosting, APIs + versioning, subscription/billing provider, schema, tenant model, observability, backups, compliance posture, rate limits, webhook capability.

## C. Cauldron App (spiritual-practitioner marketplace) — UNKNOWN
No access provided. **UNKNOWN:** URL/repo, stack, features (profiles/booking/messaging/payments), payment provider, data model, tenant model, hosting. Not inspected.

## D. Cauldron Wars (planned game) — DOES NOT EXIST YET
No architecture, platform, or code. Nothing to audit. Integration is premature until a real game architecture exists.

## E. $CAUL token on XRPL — UNVERIFIED
**UNKNOWN (needs on-chain + authorization proof):** issuer address, currency code, supply config, trust-line behavior, treasury wallets, distribution, exchange/liquidity claims, operational constraints. **Nothing inferred from the ticker.** No wallet/keys in scope.

## F. Corporate governance layer — PARTIAL
CAUL AI already provides executive owner/admin, roles, approvals, audit, policy views. Budget management and multi-product governance are **not yet built**.

## G. What is accessible to me right now
- Full read/write within the **CAUL AI** Emergent project only.
- No access to Deal Flow OS, Cauldron App, token infra, or game code — each requires **separate authorized access in its own project** (see `PHASE0_EXECUTIVE_DECISION.md`).
