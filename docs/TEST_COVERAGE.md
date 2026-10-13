# CAUL AI — Backend Test Coverage (Phase 1A)

The original Phase 1A requirement includes **100% test coverage**. This is now
measured and enforced.

## Status

- **100.00% line coverage** across `app/` and `server.py` (123 tests).
- Coverage gate: `fail_under = 100` in `/app/backend/.coveragerc`.
- CI route-permission coverage (default-deny) is additionally enforced by
  `tests/test_route_coverage.py`.

## Run it

```bash
cd /app/backend
python -m pytest tests/ --cov=app --cov=server --cov-report=term-missing
# machine-readable artifacts:
python -m pytest tests/ --cov=app --cov=server --cov-report=xml --cov-report=html
```

The run fails if total coverage drops below 100%.

## Test suites

| File | Scope |
|------|-------|
| `test_units.py` | config, canonical, security, ratelimit, auth_provider, rbac helpers, connector contract (incl. negative paths), audit empty-chain, approval-engine edge branches, seed guard/happy path |
| `test_endpoints.py` | In-process `TestClient` over every `/api` router; auth flow; `get_current_user` token branches; default-deny (403); server root/health/CSRF; cron auth + rate-limit |
| `test_seed_full.py` | Seed create **and** idempotent-exists branches on a throwaway Postgres schema |
| `test_adversarial.py` | Approval safeguard rejection criteria |
| `test_rbac.py` / `test_route_coverage.py` | RBAC matrix integrity + default-deny route coverage |
| `test_audit.py` / `test_hardening.py` | Tamper-evidence, INSERT-only enforcement, per-env cron secret, rate limits (live HTTP) |
| `test_connector_contract.py` / `test_seed_guard.py` / `test_cron_verify.py` | Connector contract, seed production guard, cron verification |

## Notes on excluded lines

A small number of genuinely unreachable defensive lines are marked
`# pragma: no cover` with an inline justification (e.g. the duplicate-seq audit
branch guarded by the `uq_chain_seq` unique constraint, best-effort audit/seed
`except` handlers, and the logout cookie-decode fallback). `.coveragerc` also
excludes `raise NotImplementedError` abstract stubs and `__main__` guards.
