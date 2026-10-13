# CAUL_AI_ECOSYSTEM_ARCHITECTURE.md
**Phase 0 — Target architecture, boundaries, dependencies, alternatives.**

## 1. Boundaries (non-negotiable)
Independently deployable services; **no merged DBs/repos/deployments**. Products keep their own auth, DB, billing, uptime, pipelines, and must keep working if CAUL AI or the Gateway is down (token features may degrade). CAUL AI is an orchestration/insight/approval layer — **never** an unrestricted production admin, no self-deploy, no unsupervised financial/token/billing changes.

## 2. Logical layers
```
+---------------------------------------------------------------+
| Corporate Governance (exec owner/admin, budgets, roles,        |
|   policy, audit)  -- lives in CAUL AI                          |
+---------------------------------------------------------------+
| CAUL AI Control Plane: agent orchestration, policy engine,     |
|   human approval queues, scheduled jobs, analytics,            |
|   growth dashboards, observability          [PostgreSQL SoR]   |
+---------------------------------------------------------------+
| Product Connectors (per product): versioned HTTPS REST,        |
|   scoped service identity, contract tests, retries+backoff,    |
|   circuit breaker, rate limit, idempotency, health, KILL SWITCH|
|   -- READ-ONLY + AGGREGATE-ONLY initially                      |
+------------------+------------------+-------------------------+
         |                   |                      |
   Deal Flow OS        Cauldron App         Future SaaS / Wars
   (live, isolated)    (isolated)           (isolated)
+---------------------------------------------------------------+
| CAUL Utility Gateway (SEPARATE service): XRPL identity verify, |
|   noncustodial wallet proof, user-signed redemptions,          |
|   off-chain credit ledger, entitlements, reconciliation.       |
|   NO private keys in AI agents. CAUL AI only *recommends*.     |
+---------------------------------------------------------------+
```

## 3. Integration pattern (reuse of existing CAUL AI primitives)
- Each product connector implements the existing `BaseConnector` contract + passes `run_contract_suite()`.
- A new `metrics:read` permission + least-privilege **service identity** per product.
- Scheduled pull via platform cron (per-env HMAC, same pattern as audit-verify).
- Every fetch written to the tamper-evident audit chain; disable via emergency pause scope `connector:<product>`.
- Storage: per-product aggregate metrics table; aggregate-only, no PII/records.

## 4. Dependencies
- **Hard blocker for production:** CAUL AI production IdP (Auth0 dossier ready) + closed Phase 1A acceptance gates.
- Authorized read access to each product (repo/API/staging) + a scoped read-only token issued *by that product*.
- Utility Gateway depends on verified XRPL identity + legal review (Phase 4).
- LLM agents depend on model-data boundary + prompt-injection defenses + budget approval.

## 5. Architecture options
- **A (recommended): Hub-and-spoke, pull-based, read-only.** CAUL AI pulls aggregates from each product's versioned API. Lowest blast radius, product autonomy preserved. 
- **B: Event-driven (signed webhooks/queue).** Products push signed aggregate events. Lower latency, more moving parts (dead-letter, replay). Defer to later phase.
- **C: Shared data warehouse.** Rejected for now — risks tenant/data-isolation and merges data stores (violates boundary #1).

## 6. Non-goals (this epoch)
No DB merges, no write-back to products, no autonomous spend/publish/outreach, no token custody/signing, no Cauldron Wars integration until a real game exists.
