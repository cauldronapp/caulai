# CAUL AI — Cauldron Growth OS Command Center (Phase 1A)

![backend coverage](https://img.shields.io/badge/backend%20coverage-100%25-brightgreen)
![tests](https://img.shields.io/badge/tests-123%20passing-brightgreen)
![phase](https://img.shields.io/badge/phase-1A%20(stub%2C%20non--prod)-informational)

> **AUTH STUB — NOT PRODUCTION.** Phase 1A is a standalone, private, dev/staging-only
> governance platform. No external identity provider, no live connectors, no external
> service spend. PostgreSQL is the authoritative system of record (no MongoDB).

A governance Command Center: recommendations → hardened approval state machine →
tamper-evident hash-chained audit, with server-side RBAC (default-deny) and emergency
controls (pause / revoke / rollback) operating against stub paths only.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Tailwind, shadcn/ui, React Query |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| Datastore | PostgreSQL 15 (psycopg3) — separate `caul_dev` / `caul_staging` DBs |
| Auth | Provider-neutral OIDC/OAuth2 interface + labeled **stub**, JWT httpOnly sessions |

## Local development

Services are supervisor-managed (`backend`, `frontend`, `postgresql`). Backend serves on
`:8001` (all routes prefixed `/api`); frontend on `:3000`. Config comes from
`backend/.env` and `frontend/.env` — never hardcoded.

```bash
# backend
cd backend && python -m alembic upgrade head && python -m scripts.apply_grants
# seed runs automatically on app startup (idempotent, production-guarded)
```

Stub credentials (dev/staging only, non-deliverable `*.invalid`) are in
`memory/test_credentials.md`. Shared password: `StubPass!2026`.

## Testing & coverage

**100% backend line coverage, enforced.** See [`docs/TEST_COVERAGE.md`](docs/TEST_COVERAGE.md).

```bash
cd backend
python -m pytest tests/ --cov=app --cov=server --cov-report=term-missing   # gate: fail_under=100
```

- `.coveragerc` enforces `fail_under = 100`.
- `tests/test_route_coverage.py` enforces that **every** `/api` route declares an explicit
  permission (default-deny), checked in CI.

## CI

`.github/workflows/ci.yml` runs on PR/push to `main`/`develop`:

1. Provisions least-privilege DB roles + a separate `caul_staging` database.
2. Runs migrations + `apply_grants` (audit tables locked to INSERT-only).
3. Default-deny route-permission coverage.
4. Full suite with the **100% coverage gate**.
5. Live hardening suite (per-env cron secret, rate-limits, audit INSERT-only at the DB level).

Recommended branch protection: require the `backend` and `frontend` checks on `main`.

## Security & phase boundaries

- Tamper-**evident** (not "immutable") hash-chained audit; residual DB-owner risk documented
  in [`docs/AUDIT_RUNBOOK.md`](docs/AUDIT_RUNBOOK.md).
- Default-deny RBAC resolved from PostgreSQL, never from the IdP.
- **Deferred to Phase 1B (separate written approval required):** Auth0 / live IdP, real
  connectors, true separate-server isolation, off-box checkpoint export.

See [`docs/PHASE_1A_COMPLETION_REPORT.md`](docs/PHASE_1A_COMPLETION_REPORT.md) and
[`docs/PHASE_1A_ACCEPTANCE_CERTIFICATE.pdf`](docs/PHASE_1A_ACCEPTANCE_CERTIFICATE.pdf).
