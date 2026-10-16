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

## Phase 1A — FINAL ACCEPTANCE
- **Status: ACCEPTED** by user (written approval granted 2026-06). Phase 1A closed.
- Verification at acceptance: 44/44 pytest green; security remediations (CORS/CSRF/rate-limit/BOLA/cron HMAC) verified; audit chain verifying clean; all Command Center pages live (WCAG 2.1 AA).

## Post-acceptance work (2026-06)
- **100% backend test coverage achieved and enforced** (original-prompt requirement). 123 tests; `fail_under=100` in `/app/backend/.coveragerc`. New suites: `tests/test_endpoints.py` (full TestClient router + auth/deps/CSRF/cron coverage), `tests/test_units.py` (utility/domain modules), `tests/test_seed_full.py` (seed create+exists on a throwaway schema). Doc: `docs/TEST_COVERAGE.md`.
- **CI hardened** (`.github/workflows/ci.yml`): provisions least-privilege roles + separate `caul_staging` DB, runs dev+staging migrations/grants, default-deny route coverage, the 100% coverage gate, and a live hardening suite (boots stub server). Uploads `coverage.xml`.
- **requirements.txt cleanup**: removed unused `emergentintegrations==0.2.1` and the `litellm` wheel (no LLM usage in Phase 1A) — they caused a pip resolver conflict that would break CI and redeploys. `pip install -r requirements.txt` now resolves cleanly.
- Rewrote `README.md` (overview, stack, local dev, testing/coverage, CI, security + phase boundaries, coverage badge).
- Removed orphaned `frontend/src/views/ComingSoon.jsx`.
- Deployment readiness scan: PASS (no blockers; CORS auto-updated at deploy; Postgres self-hosted in-container — fresh prod DB seeds via idempotent guards).
- Executive acceptance certificate PDF generated: `docs/PHASE_1A_ACCEPTANCE_CERTIFICATE.pdf`.

## Audit filters + dashboard range/export (2026-06)
- **Saved Audit Filters**: `saved_audit_filters` table (migration `e1f2a3b4c5d6`) + `GET/POST/DELETE /api/audit/filters` (gated `audit:list`, owner-scoped delete, optional shared); Audit page "+ Save view" bar.
- **Dashboard Date Range**: `/api/dashboard/analytics?days=7|30|90`; frontend range selector.
- **Export Dashboard**: `GET /api/dashboard/export` (CSV) + client print-to-PDF button.
- 129 tests, **100% coverage maintained**. Verified via screenshots.

## Dashboard analytics (2026-06)
- Added `GET /api/dashboard/analytics` (gated by `dashboard:read`): recommendations/approvals/executions grouped by status/tier + audit events/day. Frontend `DashboardAnalytics.jsx` renders recharts line/bar charts on the dashboard. 127 tests, **100% coverage maintained**.
- Note: a transient pod/supervisor+Postgres outage occurred during this session and was recovered via `supervisord`; structured JSON logging + `X-Request-ID` confirmed working in backend logs.

## Phase 1B prep & production hardening (2026-06)
- **Production hardening (no external spend):** added `/api/health/ready` readiness probe (DB + seed state), structured **JSON logging** with per-request `X-Request-ID` correlation middleware. 126 tests, **100% coverage maintained**; `/api/health/ready` whitelisted in route-coverage.
- **Auth0 pre-connection dossier** (`docs/PHASE_1B_AUTH0_DOSSIER.md/.pdf`): exact resources/keys, SDK versions, codebase mapping (RBAC stays in Postgres; Auth0 = identity only, behind `AUTH_PROVIDER` flag with stub rollback), migration/cutover plan, test matrix, and the approval/values needed before any connection. ExecOwner identity = **sean.gaden@gmail.com**. NOTHING connected/wired — awaits written approval.
- Deal Flow OS integration paused by user; Phase 0 deliverables complete (bundle + auto-rebuild script `docs/build_dealflow_bundle.sh`).

## Filter Sharing UX + Scheduled Weekly Digest (2026-06-15)
- **Filter Sharing UX**: `saved_audit_filters.is_default` column (migration `f2b3c4d5e6f7`). `GET /api/audit/filters` now returns `owner_label` + `is_default`; save flow asks share-with-team (OK/Cancel). New `POST /api/audit/filters/{fid}/pin` (gated `setting:update`, admin-only) pins ONE team-wide default (auto-shares it, clears any prior default). Audit page shows "shared by {owner}", amber ★ default badge, and admin pin/unpin control; the pinned default view auto-applies once on load.
- **Scheduled Weekly Digest**: `POST /api/cron/weekly-digest` (HMAC cron auth, shared `_require_cron_auth` helper) builds a 7-day governance digest (approvals by status, audit growth, emergency pauses) and stores it as a broadcast `Notification` (kind=`digest`) + a `digest.generated` audit event. **No email sent — generated-and-stored only** to honor the $0-spend / no-external-connectivity guardrail. Scheduled in `.emergent/crons.yml` (Mondays 13:00 UTC).
- 131 tests, **100% coverage maintained**. Verified live on preview (shared label + pin/star render; digest cron returns 200 and stores notification).

## Ecosystem Integration — Milestone 0 (Discovery) (2026-06-15)
- Produced 7 ecosystem-integration documents in `/app/docs/` per the Master Prompt: `ECOSYSTEM_INTEGRATION_ARCHITECTURE.md`, `CAUL_UTILITY_SERVICE_SPEC.md`, `CLIENT_OPERATIONS_AND_PRIVACY_SPEC.md`, `PRODUCT_ADAPTER_CONTRACT.md`, `PHASED_IMPLEMENTATION_PLAN.md` (superseded w/ M0–M4 gates), `SECURITY_AND_TEST_PLAN.md`, `DECISIONS_REQUIRED.md`.
- **No code changed, no deploy, no spend, no secrets, no token ops.** Stopped at the M0→M1 approval gate. M1 (dev-only mocks/schemas/tests) is pre-specified and awaits owner answers to Section A of `DECISIONS_REQUIRED.md`.

## Monetization & unit-economics plan — Milestone 0 (2026-06-15)
- Produced 4 owner-review strategy docs in `/app/docs/`: `MONETIZATION_STRATEGY.md`, `PRICING_MODEL_DRAFT.md`, `COST_AND_UNIT_ECONOMICS_MODEL.md`, `MONETIZATION_VALIDATION_PLAN.md`.
- Internal-first → validated external SaaS; fiat billing default; $CAUL optional/counsel-reviewed only; no return/appreciation claims. **All prices are hypotheses.** No billing/payments/live-pricing/production changes. Validation precedes any build.

## Usage-instrumentation spec — Milestone 0 (2026-06-15)
- Produced `/app/docs/USAGE_INSTRUMENTATION_SPEC.md`: dev-only, $0 measurement layer to prove internal value before pricing. Covers first 5 workflows, event taxonomy + fields, metric formulas (AI cost/account, support time saved, onboarding completion, renewal follow-up, workflow success), privacy/retention limits (pseudonymous refs, no PII/content, ≤90-day raw retention), synthetic-data test plan, and acceptance criteria.
- **Spec only — no code, no real data, no external services, no billing/pricing/production changes.** Awaiting owner review before any dev-only implementation. Cross-linked from `MONETIZATION_VALIDATION_PLAN.md` and `DECISIONS_REQUIRED.md` (§G).

## §G usage-instrumentation decision brief — (2026-06-15)
- Produced `/app/docs/USAGE_INSTRUMENTATION_DECISION_BRIEF.md`: recommended defaults for retention (30d raw / 24mo aggregates + hard-delete flow), per-(tenant,product) scoped pseudonymization with no cross-product linkage, observational attribution with labeling rule, configurable 3-rate model-cost table (input/output/cached) with source_url + effective_date ($CAUL price never a cost input), and PII safeguards (no free-text; what validation can/cannot detect; small-cell suppression n<5). Includes schema/event JSON examples.
- Updated `DECISIONS_REQUIRED.md` §G with concrete defaults. **Documentation-only — no code until owner explicitly approves implementation.**

## Usage measurement layer (dev-only) — implemented (2026-06-15)
- Approved dev-only Stage-1 value-instrumentation layer built with **synthetic data only** (no real customer data, no external services, no billing, no staging/prod changes).
- **Backend:** `usage_events` (append-only, PII-free), `usage_aggregates` (de-identified), `model_cost_rates` (configurable input/output/cached rates + source_url + effective_date; $CAUL price never a cost input). Migration `a1b2c3d4e5f6` (dev+staging) + grants applied.
- `app/usage.py`: scoped server-side pseudonymous refs (per tenant+product, no cross-product linkage), `record_event` (controlled-vocab validation, no free-text), `compute_metrics` (AI cost/account, workflow success, support-time-saved, onboarding completion, renewal follow-up, conversion lift; observational labeling; small-cell suppression n<5), `rollup_aggregates`, `run_retention` (30d raw / 24mo aggregates, hard delete), `purge_tenant`, `purge_account_raw`.
- `app/usage_synth.py`: deterministic synthetic generator with planted baseline-vs-assisted deltas.
- Endpoints: `GET /api/usage/metrics` (`usage:read`), `POST /api/usage/purge` (`usage:purge`, admin-only/high-risk). Cron `POST /api/cron/usage-retention` (HMAC) + `.emergent/crons.yml` entry (daily 02:30).
- **Tests:** 141 passing, **100% backend coverage maintained**. Spec updated with the "aggregation is irreversible at the individual level" caveat + tenant purge + pre-aggregation deletion.

## Next tasks
Phase 1A CLOSED/ACCEPTED (100% coverage). Production hardening done. Auth0 identity (Phase 1B) is dossier-ready but **NOT started** — needs explicit written approval + staging Auth0 values (see dossier §7). Deal Flow OS integration resumes after CAUL AI is further along. Do NOT begin any external connection (Auth0, live connectors, off-box export, Deal Flow OS) without separate written approval.
