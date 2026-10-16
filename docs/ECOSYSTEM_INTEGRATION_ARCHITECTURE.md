# ECOSYSTEM_INTEGRATION_ARCHITECTURE.md
**Cauldron Technologies, Inc. — CAUL AI Ecosystem Integration (Milestone 0 / Discovery).**
Read-only audit + target architecture. **Documentation only. No production changes, no deploys, no spend, no token operations, no secrets requested.**

> Legend used throughout: **[EXISTS]** verified in this repo · **[PROPOSED]** future work, not built · **[ASSUMPTION]** must be verified · **[DECISION]** owner decision required · **[LEGAL]** requires a licensed professional's review.

---

## 1. Scope & non-negotiable boundaries
CAUL AI (this project, "Cauldron Growth Operating System Command Center") is the intended **company-wide control plane**. Deal Flow OS, Cauldron App, Cauldron Wars, and future products are **separate applications**. This architecture assumes they do **NOT** share a database, auth system, codebase, or customer-permission model.

Boundaries (carried forward from prior Phase 0, reaffirmed):
- Independently deployable products; **no merged DBs / repos / deployments**. Each product keeps its own auth, DB, billing, uptime, and pipelines, and must keep working if CAUL AI or the Gateway is down (token features may degrade gracefully).
- CAUL AI is an **orchestration / insight / approval** layer — never an unrestricted production admin, no self-deploy, no unsupervised financial/token/billing changes.
- **$0 spend**, **separate dev/staging**, **production untouched** unless the owner explicitly changes these constraints in writing.
- No live blockchain transaction, no wallet connection, no signing keys as part of this work.

## 2. Verified current state (what already EXISTS in CAUL AI)
Source: direct inspection of `/app/backend`, `/app/frontend`, tests, CI, `/app/docs`.

| Area | Verified finding [EXISTS] |
|---|---|
| Phase | Phase 1A accepted/closed; production hardening, dashboard analytics, saved audit filters, filter-sharing + weekly-digest cron added since. |
| Stack | FastAPI + SQLAlchemy 2.0 + Alembic (PostgreSQL 15 / psycopg3); React 19 + Tailwind + shadcn/ui + recharts. |
| Datastore | PostgreSQL system-of-record. Separate `caul_dev` / `caul_staging` DBs + least-privilege roles; audit tables INSERT-only at the DB level. **No MongoDB.** |
| Identity | Provider-neutral `IdentityProvider` interface + **labeled `StubIdentityProvider` ("AUTH STUB — NOT PRODUCTION")**. JWT httpOnly sessions, server-side expiry + revocation. Auth0 go-live dossier ready, **not wired**. |
| AuthZ | Server-side **RBAC default-deny** resolved from Postgres (`require_permission(...)`); CI route→permission coverage test; complete resource×action catalog. |
| Audit | Tamper-**evident** hash-chained events (canonical serialization, advisory-lock sequencing, `verify_chain`, checkpoints); per-env HMAC cron `/api/cron/verify-audit`. |
| Emergency | Global/granular pause, queue cancel/drain, emergency revoke, rollback — all against **stub paths**. |
| Connectors | `BaseConnector` + `run_contract_suite()` gate; all connectors **Not Connected**. |
| Scheduling | Platform cron via `.emergent/crons.yml` (HMAC-authenticated endpoints): audit-verify (30 min) + weekly governance digest (Mon 13:00 UTC, stored, not emailed). |
| Ops | `/api/health`, `/api/health/ready`; structured JSON logs + `X-Request-ID`; CI with 100% coverage gate (`fail_under=100`). |
| Tests | 131 passing, **100% backend coverage** enforced. |
| Secrets (names only) | `JWT_SECRET`, `WEBHOOK_CRON_SECRET[_DEV|_STAGING]`, `DEV/STAGING_DATABASE_URL`, `DEV/STAGING_ADMIN_DATABASE_URL`, `CORS_ORIGINS`. No external API keys present. |

**Reusable primitives for integration:** `BaseConnector` contract-test gate · default-deny `require_permission` · tamper-evident `audit.append_event` · emergency pause scopes · per-env HMAC cron pattern · idempotent seed with production guards.

## 3. Access gaps (what is NOT verified)
- **Deal Flow OS** — public surface only (real-estate wholesaling SaaS, "Claude Sonnet 4.5 powered"). Repo/stack/DB/billing/tenant model/APIs all **[ASSUMPTION]**; need an authorized read-only audit + a scoped token issued *by that product*.
- **Cauldron App** — no access. Everything **[ASSUMPTION]**.
- **Cauldron Wars** — does not exist yet; integration premature.
- **$CAUL / XRPL** — issuer address, currency code, supply, trust-line, treasury all **[ASSUMPTION]**; require on-chain + ownership audit and **[LEGAL]** review. Nothing inferred from the ticker.

## 4. Target topology (hub-and-spoke, pull-based, read-only first)
```
           +-------------------------------------------------------+
           |  Corporate Governance (exec owner/admin, budgets,     |
           |  roles, policy, audit) — lives in CAUL AI [EXISTS]    |
           +-------------------------------------------------------+
           |  CAUL AI Control Plane [EXISTS core]                  |
           |   agent orchestration* · policy engine · human        |
           |   approval queues · scheduled jobs · analytics        |
           |   · observability        [PostgreSQL SoR]             |
           +--------+--------------------+----------------+--------+
                    | least-privilege    | per-product    |
                    | service identity   | adapter (R/O)  |
          +---------v------+   +---------v------+   +------v---------+
          | Deal Flow OS   |   | Cauldron App   |   | Future / Wars  |
          | (live, own DB) |   | (own DB)       |   | (own DB)       |
          +----------------+   +----------------+   +----------------+

           +-------------------------------------------------------+
           |  CAUL Utility Service / Gateway (SEPARATE) [PROPOSED] |
           |   product+env registry · wallet-ownership proof ·     |
           |   USD-priced catalog · off-chain credit ledger ·      |
           |   entitlements · reconciliation · feature flags ·     |
           |   emergency pause.  NO keys in AI agents.             |
           +-------------------------------------------------------+
*agent orchestration is bounded — see §6 and AGENT autonomy spec.
```

## 5. Data-flow summary
1. **Metrics pull [PROPOSED]:** CAUL AI scheduled job → per-product adapter (signed, scoped, read-only) → aggregate metrics stored in a per-product table (aggregate-only, no PII) → every fetch written to the audit chain. Disable via emergency pause scope `connector:<product>`.
2. **Client-operations [PROPOSED]:** staff/AI workflow → policy check (default-deny, tenant+product scoped) → adapter read of only the authorized records → draft/summary/recommendation → human approval gate for any sensitive/irreversible action → audit record.
3. **$CAUL utility [PROPOSED, gated]:** product → CAUL Utility Service API (feature-flagged) → USD-priced quote → user-signed, noncustodial redemption → off-chain credits on **confirmed settlement only** → entitlement at product. CAUL AI only *recommends*; a separate approved policy service enforces.

## 6. Integration principles
- **Least privilege per product:** a dedicated service identity with a narrow scope set (initially `metrics:read` only). Enforced server-side on **every** request.
- **Tenant & product isolation:** no cross-product/cross-tenant/cross-customer data exposure; no using one product's data to train/improve another's models without notice, permission, contracts, and **[LEGAL]** review.
- **Keep private data off-chain:** customer records, messages, credentials, business data never go on-chain.
- **Reuse, don't rebuild:** each adapter implements the existing `BaseConnector` + passes `run_contract_suite()`; metrics pulls reuse the HMAC cron pattern; all actions audited.

## 7. Architecture options & recommendation
- **A (recommended):** hub-and-spoke, pull-based, read-only — lowest blast radius, preserves product autonomy.
- **B:** event-driven signed webhooks/queue — lower latency, more moving parts (dead-letter/replay); defer.
- **C:** shared data warehouse — **rejected** (violates data-isolation boundary).

## 8. Dependencies & non-goals
**Hard production blockers:** real IdP (Auth0) wired in CAUL AI; closed Phase 1A acceptance gates; per-product authorized read access + scoped token; Gateway depends on verified XRPL identity + **[LEGAL]** review + budget approval.
**Non-goals this epoch:** DB merges; write-back to products; autonomous spend/publish/outreach; token custody/signing; Cauldron Wars integration.

## 9. Related prior documents (preserved)
`ECOSYSTEM_CURRENT_STATE_AUDIT.md`, `CAUL_AI_ECOSYSTEM_ARCHITECTURE.md`, `CAUL_UTILITY_GATEWAY_DESIGN.md`, `DEALFLOW_READONLY_INTEGRATION_SPEC.md`, `AGENT_PERMISSIONS_AND_APPROVALS.md`, `SECURITY_PRIVACY_LEGAL_RISK_REGISTER.md`, `PHASE_1B_AUTH0_DOSSIER.md`, `PHASE0_EXECUTIVE_DECISION.md`. This document set supersedes and extends them for the ecosystem-integration track.
