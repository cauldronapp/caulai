# PRODUCT_ADAPTER_CONTRACT.md
**Contract every product must satisfy to connect to CAUL AI / the CAUL Utility Service (Milestone 0 design).**
**Design only. Read-only + aggregate-only initially. No product production code/DB/DNS/billing is modified by CAUL AI.**

> Legend: **[EXISTS]** · **[PROPOSED]** · **[ASSUMPTION]** · **[DECISION]** · **[LEGAL]**.

---

## 1. Principles
- Products are **separate apps**: own auth, DB, billing, deploys. The adapter is a thin, **outbound-from-CAUL-AI, read-only** integration surface the product exposes (or that CAUL AI polls).
- Reuses the existing `BaseConnector` contract + `run_contract_suite()` gate [EXISTS]. A product is "connectable" only after it passes the contract suite in dev/staging.
- **Least privilege:** a scoped service identity per product per environment; default-deny.

## 2. Transport & versioning
- HTTPS REST, **URL-versioned** (`/v1`). Additive within a major; breaking = new major + deprecation window.
- JSON payloads; UTC ISO-8601 timestamps; stable resource ids.

## 3. Authentication & request signing [PROPOSED]
- **Identity:** `X-CAUL-Key-Id` identifies the product+env service identity.
- **Signing:** `X-CAUL-Signature = HMAC_SHA256(secret, timestamp + nonce + method + path + sha256(body))`; `X-CAUL-Timestamp`, `X-CAUL-Nonce`. Constant-time compare (as in existing cron auth). Reject stale timestamps + replayed nonces.
- **Secrets:** per-env secret, rotated on schedule; stored only in the approved secret store (names only). [DECISION: HMAC key vs. mTLS vs. OAuth2 client-credentials]

## 4. Authorization scopes
- Narrow scope set, default-deny. Initial scopes: `metrics:read` (aggregate product metrics only). Later, by approval: `client:read` (tenant/product-scoped), `caul.balance:read`, `caul.eligibility:read`, value-moving scopes (flagged).
- Enforced server-side on **every** request; tenant_id/product_id scoping mandatory where applicable.

## 5. Required endpoints a product adapter must expose [PROPOSED]
| Endpoint | Purpose | Data class |
|---|---|---|
| `GET /adapter/health` | Liveness/readiness of the adapter. | none |
| `GET /adapter/version` | Adapter + contract version. | none |
| `GET /adapter/metrics?since=&env=` | **Aggregate** metrics only (counts, rollups). **No PII, no records.** | aggregate |
| `GET /adapter/schema` | Declares fields + data classes it can return. | metadata |
| (later, approved) `GET /adapter/clients?...` | Tenant/product-scoped client records for client-ops. | restricted |

## 6. Reliability & safety semantics [PROPOSED]
- **Idempotency:** `Idempotency-Key` honored on any future state-changing call.
- **Retries + backoff**, **circuit breaker**, **rate limits** per product/env.
- **Pagination** + `since` cursors for incremental pulls.
- **Kill switch:** CAUL AI can disable a product's integration via emergency pause scope `connector:<product>` [EXISTS pattern]; the product keeps running independently.

## 7. Audit events
Every CAUL-AI→product fetch and every product→Utility-Service call emits a tamper-evident audit event (actor = service identity, action, resource, env, result, idempotency key). No secrets recorded.

## 8. Contract-test suite (gate) [EXISTS pattern → extend]
A product is connectable only after passing, in dev/staging:
1. Auth: valid signature accepted; bad/absent/stale/replayed rejected.
2. Scope: out-of-scope request denied (default-deny).
3. Aggregate-only: `/adapter/metrics` returns **no PII** (schema-validated).
4. Idempotency honored.
5. Rate-limit + backoff behavior.
6. Health/version present.
7. Kill-switch halts fetches.
8. Audit event emitted per call.

## 9. Per-product status matrix
| Product | Access | Adapter status | First scope |
|---|---|---|---|
| Deal Flow OS | [ASSUMPTION] needs authorized audit + scoped token issued by the product | Not built | `metrics:read` |
| Cauldron App | [ASSUMPTION] no access | Not built | `metrics:read` |
| Cauldron Wars | Does not exist | N/A | N/A |
| Future SaaS | N/A | N/A | `metrics:read` |

## 10. What products must provide (owner/product-team actions) [DECISION]
Authorized read access (repo/API/staging), a **scoped read-only token issued by that product**, the adapter endpoints above (or an approved shim), and sign-off on data classes returned.
