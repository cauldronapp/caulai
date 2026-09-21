# CAUL AI — Product Requirements Document (PRD)

## Original problem statement
CAUL AI — Phase 1A. Standalone private enterprise governance platform (Cauldron Growth OS
Command Center), owned by Cauldron Technologies, Inc. (Exec Owner: Sean Gaden). PostgreSQL
authoritative system of record, **no MongoDB**. Phase 1A only: provider-neutral OIDC auth
**interface** + labeled **stub**; sessions; server-side **RBAC default-deny**; complete
resource×action matrix; recommendation + approval state machines with hardened safeguards;
**tamper-evident** hash-chained audit; emergency pause/revocation (stub paths); connector
contract-test suite; Command Center pages with all states; **separate physical dev/staging
Postgres DBs** + seed guards; full automated + adversarial tests; docs + completion report.
No production, no IdP connection, no live connectors, $0 external spend.

## Architecture
- FastAPI + SQLAlchemy 2.0 + Alembic on PostgreSQL 15 (psycopg3); React 19 + Tailwind + shadcn/ui.
- Envs: `dev`→`caul_dev`, `staging`→`caul_staging` (separate DBs + creds on one local server).
- Migrations/DDL as owner `postgres`; runtime as least-privilege app user. Audit tables INSERT-only for app user.
- Supervisor manages postgres (persistent `/app/postgres_data`), backend, frontend, mongodb (unused).

## User personas
- **ExecOwner (Sean)** — only production Super Admin (production not in 1A); full grant.
- **Admin** — users/roles, approvals, emergency, settings.
- **Marketing Manager** — create/read recommendations.
- **Developer** — read recs/audit/connectors/policies.
- **Security/Compliance** — audit export/verify + emergency controls.
- **Analyst** — read-only dashboard/recs/audit.
- **Auditor** — read-only audit + approvals.
- **Agent Service Identity** — non-interactive; create/read recs only; never approves/grants/pauses.
- **No-Role** — default-deny probe.

## Core requirements (static)
1. PostgreSQL SoR, no MongoDB. 2. Labeled AUTH STUB, no prod/IdP claim. 3. Server-side RBAC
default-deny; every route explicit permission (CI-enforced). 4. Approval safeguards (digest
binding, no self-approval high-risk, quorum, no expired/revoked/paused/payload-changed reuse,
no service-identity approval, permanently_prohibited never approvable). 5. Tamper-evident
hash-chained audit (never "immutable"). 6. Separate physical dev/staging DBs + seed prod guards.
7. Emergency controls against stub paths. 8. All-states, AA, responsive Command Center. 9. $0 spend.

## Implemented (2026-06)
### Foundation milestone
- PostgreSQL foundation + separate dev/staging DBs + least-privilege + audit INSERT-only (DB-level).
- Schema + migrations on both DBs; idempotent seed with production guards; 9 synthetic `*.invalid` stub identities.
- Provider-neutral OIDC interface + StubIdentityProvider; JWT httpOnly sessions with server-side expiry/revocation.
- 34→37 permission RBAC matrix, default-deny, CI route-coverage test.
- Recommendation + approval state machines with all hardened safeguards.
- Tamper-evident hash-chained audit (canonical, advisory-lock sequencing, transactional insert, verify, checkpoints).
- Login, Dashboard, Approvals (list+detail), Audit pages.
### Continuation milestone (remaining Phase 1A)
- Full Emergency controls: global+granular pause/resume, queue cancel/drain, emergency revoke, rollback with irreversible-action warnings (stub paths only).
- Connector contract-test suite (8 checks) + StubConnector + endpoint + pytest.
- Execution queue model + synchronous stub execution + rollback eligibility.
- Remaining Command Center pages: Recommendations (list+create), Notifications, Policies, Emergency, Connectors, Admin Users, Admin Roles (permission matrix), Settings, MFA stub — all with states, RBAC-filtered nav.
- Admin management endpoints (create/disable users, assign roles, upsert roles) with service-identity guard.
- Fixed CRITICAL audit resource_id truncation (widened to 255); migrated to FastAPI lifespan.
- Tests: 31 pytest + connector contract + 2 green frontend iterations. Backup+restore proven.
- Full Phase 1A completion report: docs/PHASE_1A_COMPLETION_REPORT.md.

## Prioritized backlog
### Deferred (separate written approval)
- Auth0 pre-connection dossier + connection (Phase 1B). No tenant in 1A.
- True separate-server DB isolation provisioning.
- Scheduled audit-verification cron + off-box checkpoint export.
- Formal per-page axe accessibility report attachment (CI job exists).

## Next tasks
Await FINAL Phase 1A acceptance. Do not begin Phase 1B (Auth0, staging infra, live connectors, external integrations) without separate written approval.
