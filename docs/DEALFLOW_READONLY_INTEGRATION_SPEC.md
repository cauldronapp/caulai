# DEALFLOW_READONLY_INTEGRATION_SPEC.md
**Phase 0 — Deal Flow OS read-only connector spec (supersedes/absorbs the earlier DEALFLOW_* readiness drafts).** SPEC ONLY; nothing built.

## 1. Scope
CAUL AI consumes **aggregate, read-only** growth metrics from Deal Flow OS. No PII/records, no writes, staging-first, disabled-by-default, behind kill switch. Deal Flow OS keeps zero runtime dependency on CAUL AI.

## 2. Minimal API (to be built *in Deal Flow OS staging*, Phase 2, separately approved)
- `GET /v1/metrics/summary` → `{schema_version, tenant, as_of, metrics{...aggregates...}}`
- `GET /v1/metrics/subscriptions?window=30d`
- Versioned, OpenAPI-documented, aggregate-only, tenant-scoped, idempotent, `ETag`/`as_of`.
- Auth: scoped read-only service token (Bearer / `X-API-Key`); 401 invalid, 403 out-of-scope; HTTPS; rate-limited.

## 3. Metric dictionary (authoritative source + formula to CONFIRM during audit ❓)
registered accounts, active accounts, trials, paying subscriptions, MRR, ARR, churn, activation, engagement, feature adoption, trial→paid conversion. Each must carry source, definition, last-refresh, reconciliation status. **Never fabricate**; return `null` + note when not computable.

## 4. CAUL AI side (Phase 2)
`metrics:read` permission + `DealFlow Metrics Reader` service identity + `DealFlowMetricsConnector` (timeout, bounded retries, circuit breaker, idempotent by `as_of`, aggregate-only schema validation that rejects PII) + `dealflow_metrics` table + scheduled pull + audit per fetch + kill switch `connector:dealflow`.

## 5. Test matrix (synthetic/anonymized data only)
contract, authN (valid/expired/invalid), authZ default-deny, **tenant isolation**, reconciliation (CAUL == source), load/rate-limit, failure (timeout/retry/circuit-breaker), secret handling, kill-switch + rollback. Acceptance: reconciled metrics, zero sensitive-data leakage, zero impact on Deal Flow OS uptime, tested kill switch, sign-off from BOTH project owners.

## 6. Rollback (independent)
Emergency pause `connector:dealflow`; revoke DealFlow token; feature-flag off; CAUL serves last-good `as_of`; no Deal Flow OS change required.

## 7. Access required (see access-request checklist already drafted)
Authorized DealFlow audit (stack/APIs/billing source/tenant model) + a scoped read-only **staging** token. Building the endpoint/token in Deal Flow OS = a separate approved change in *its* project.
