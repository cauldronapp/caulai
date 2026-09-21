# CAUL AI — Phase 1A Foundation Milestone: Completion Report

**Owner:** Cauldron Technologies, Inc. · Executive Owner: Sean Gaden
**Scope delivered:** Foundation-first milestone (items 1–10 of the approved order).
**System of record:** PostgreSQL. **No MongoDB.** **No production environment.**
**Actual external cost incurred: $0.** No IdP connected, no live connectors, no egress.

---

## 1. Repository & branch info
- Standalone private codebase under `/app`, isolated from the Cauldron App.
- Branching model + protected-`main` rules documented in `docs/BRANCHING.md`.
- CI workflow at `.github/workflows/ci.yml` (route-coverage, tests, SAST, dep-scan, migration check, build). Connect the Cauldron-owned private repo via Emergent "Save to GitHub" (org OAuth). **Flag any CI charge before enabling** (currently assumes $0 GitHub-hosted runners).

## 2. Implemented architecture
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic on PostgreSQL 15 (psycopg3). Supervisor-managed cluster with persistent data dir at `/app/postgres_data`.
- **Frontend:** React 19 + Tailwind + shadcn/ui, dark tactical command center.
- **Environments:** `dev` → `caul_dev` (user `caul_dev_user`); `staging` → `caul_staging` (user `caul_staging_user`). Physically separate databases, separate credentials. Migrations/DDL run as owner (`postgres`); app runs as least-privilege user.

## 3. Schema & migrations
- Models in `app/models.py`; initial Alembic migration `04fa0e699dc6_initial_schema` applied to **both** dev and staging.
- Tables: users, roles, permissions, role_permissions, user_roles, sessions, recommendations, approvals, approval_decisions, audit_events, audit_checkpoints, pause_states, settings, connectors, notifications, policies.

## 4. Complete RBAC matrix (default-deny, CI-enforced)
- 34 explicit `resource:action` permissions in `app/rbac_matrix.py`.
- Roles: ExecOwner (full), Admin, Marketing Manager, Developer, Security/Compliance, Analyst, Auditor, Agent Service Identity (create/read recs only; **never** approve/grant/pause), No-Role (empty — default-deny probe).
- Every protected route declares `require_permission(...)`; `tests/test_route_coverage.py` fails CI if any `/api` route lacks an explicit permission.
- Authorization resolved from PostgreSQL, **never** from the token/IdP.

## 5. Authentication stub + limitations
- Provider-neutral `IdentityProvider` interface + `StubIdentityProvider` (`app/auth_provider.py`), labeled **"AUTH STUB — NOT PRODUCTION"** in UI, logs, `/api/auth/provider`, and docs.
- JWT httpOnly-cookie sessions with server-side session table (expiry + revocation). No MFA claimed. No external IdP created/connected.
- Service identity login blocked (403). Seeded identities are synthetic `*.invalid`, dev/staging only.

## 6. Approval safeguards implemented
Action-payload **digest binding**; no self-approval of high-risk; no single reviewer counted twice (app check + DB unique constraint); quorum (2 distinct reviewers for high-risk); no expired-approval reuse; no reuse after payload change; no execution after revocation; no execution under active global/granular pause; `permanently_prohibited` can never be approved; **no agent/service identity may approve/reject/revoke**.

## 7. Audit chain design & test results
Deterministic canonical serialization; `pg_advisory_xact_lock` monotonic sequencing + `UNIQUE(chain_env,chain_org,seq)`; transactional insertion; per-env/org scope; genesis + checkpoints; on-write/on-demand verification detecting gap/reorder/duplicate/field-tamper/hash-mismatch/broken-link. **DB-level INSERT-only**: app user's UPDATE/DELETE/TRUNCATE on `audit_events`/`audit_checkpoints` revoked (owner-enforced) — verified denied. Documented as **tamper-evident, never immutable** (`docs/AUDIT_RUNBOOK.md`).

## 8. Command Center pages (this milestone)
Login (stub) · Governance Dashboard · Approvals (list + detail with Approve/Reject/Revoke + payload-binding state) · Tamper-evident Audit log (searchable, GENESIS row, CHAIN VERIFIED banner, CSV export). RBAC-filtered sidebar; remaining pages present as gated placeholders. Dark WCAG-oriented theme with focus rings and data-testids throughout.

## 9. Test inventory & results
- Backend pytest: **29/29 pass** — route coverage, RBAC, audit (incl. owner-tamper detection), adversarial approvals, seed guards.
- Live API: **9/9 pass** (`tests/live_api_test.py`) — provider label, login/cookie/me for 7 stubs, service-identity 403, no-role default-deny, per-role RBAC, logout revocation, audit verify/search/export.
- Frontend: all listed flows pass (login→dashboard→approvals detail→audit). Zero critical/minor issues in testing report `iteration_1.json`.

## 10. Adversarial-test results
100% pass (see §6 items in `tests/test_adversarial.py`).

## 11. Backup/restore evidence
`pg_dump` (custom format, 52K) of `caul_dev` restored into a scratch DB and verified (users/audit/permissions row counts intact), then dropped. Procedure in `docs/BACKUP_RESTORE.md`.

## 12. Accessibility (completed pages)
Dark theme meeting AA-oriented contrast, visible focus rings (`focus:ring-indigo-500`), semantic labels, keyboard-activatable controls, responsive layout. Formal automated axe audit deferred to CI accessibility job (wired in `ci.yml`).

## 13. Security-scan results
CI includes bandit (SAST) + pip-audit (dependency scan). DB least-privilege enforced. Secrets in `.env` only. No hardcoded external credentials.

## 14. Known defects & limitations
- **Deferred (approval required):** true separate-**server** DB isolation (currently separate DBs on one local server); scheduled audit-verification cron; remaining Command Center pages (Recommendations UI, Emergency, Connectors, Policies, Users, Roles, Settings editors, Notifications, MFA stub page); connector contract-test suite; formal axe accessibility report.
- Backend uses FastAPI `@app.on_event` (deprecation warning only; functional).
- Stub is explicitly **not** production auth and makes no MFA/IdP claim.

## 15. Actual costs incurred
**$0.** Local open-source PostgreSQL. No accounts, subscriptions, credits, or external services provisioned.

## 16. Confirmation — no prohibited actions
No production environment, no IdP connection/purchase, no live connectors, no external egress, no AI services, no Cauldron App/production-DB access, no publishing/advertising/crypto, no autonomous agents, no paid services. No MongoDB. Option 3 not used.

## 17. Demonstration guide
1. Open the app → `/login`. Note the sticky **AUTH STUB — NOT PRODUCTION** banner.
2. Quick-sign-in as **Demo Admin** (`admin@example.invalid` / `StubPass!2026`).
3. Dashboard shows pending approvals, prohibited count, and **CHAIN VERIFIED**.
4. Approvals → open the high-risk `$12k ad budget` item → observe digest binding; try approving as the submitter to see the self-approval block (sign in as a second reviewer to reach quorum).
5. Audit → search, view the GENESIS row and hash links, click **Export CSV**.
6. Sign in as `norole@example.invalid` to see default-deny (empty nav / 403s); `agent-service@example.invalid` login is refused (403).

## 18. Proposed scope for next milestone (Gate 2 request)
Remaining Command Center pages + states, emergency controls UI + queue drain/rollback flags, connector contract-test suite, scheduled audit verification, settings versioning UI ($24.99/mo, 2.30%), accessibility automation, and the Auth0 pre-connection dossier (Phase 1B, separate approval). **Awaiting written approval before proceeding.**
