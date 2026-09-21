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

## Implemented (2026-06 — Foundation milestone)
- PostgreSQL foundation + separate dev/staging DBs + least-privilege + audit INSERT-only (DB-level).
- Initial schema + Alembic migration on both DBs; idempotent seed with production guards; 9 synthetic `*.invalid` stub identities.
- Provider-neutral OIDC interface + StubIdentityProvider; JWT httpOnly sessions with server-side expiry/revocation.
- Complete 34-permission RBAC matrix, default-deny, CI route-coverage test.
- Recommendation + approval state machines with all hardened safeguards.
- Tamper-evident hash-chained audit (canonical serialization, advisory-lock sequencing, transactional insert, verify, checkpoints).
- Emergency pause/resume model + enforcement in execution gate.
- Command Center: Login, Dashboard, Approvals (list+detail), Audit (search/verify/export); RBAC-filtered nav; gated placeholders for the rest.
- Tests: 29 pytest + 9 live API + frontend flows all pass. Backup+restore proven. Docs (preflight, branching, audit runbook, backup/restore, completion report, auth_testing).

## Prioritized backlog
### P0 (next milestone, needs Gate 2 approval)
- Remaining Command Center pages with all states: Recommendations UI, Emergency controls UI (global/granular pause, queue cancel/drain, rollback + irreversible-action labeling), Connectors (Not Connected, no credential fields), Policies, Admin Users/Roles editors, Settings (versioned $24.99/mo + 2.30%), Notifications, MFA stub page.
- Connector contract-test suite (pause, revocation, timeout, failure, audit, idempotent safe-retry).
- Scheduled audit-chain verification + independent exported checkpoints.
### P1
- Accessibility automation (axe) in CI; formal AA report per page.
- Emergency queue drain/rollback flag semantics against stub paths.
### P2
- Auth0 pre-connection dossier (Phase 1B, separate approval). No tenant in 1A.
- True separate-server DB isolation proposal (deferred provisioning).

## Next tasks
Await written Gate 2 approval, then build remaining Command Center pages + emergency controls + connector contract tests (per user's stated milestone-gating).
