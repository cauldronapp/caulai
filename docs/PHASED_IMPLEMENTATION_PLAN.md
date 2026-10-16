# PHASED_IMPLEMENTATION_PLAN.md
**CAUL AI Ecosystem Integration — milestone plan & approval gates (Milestone 0 deliverable).**
Supersedes the earlier phased plan for the ecosystem-integration track. **Each milestone ends at a STOP gate requiring owner approval.**

> Legend: **[EXISTS]** · **[PROPOSED]** · **[DECISION]** · **[LEGAL]**. Constraints carried forward: **$0 spend**, **separate dev/staging**, **production untouched**, **no live wallet/keys**, **no secrets in chat/source** — unless the owner explicitly changes them in writing.

---

## Milestone 0 — Repo & environment audit + architecture/decision docs  ✅ (this deliverable)
**Scope:** inspect CAUL AI; produce `ECOSYSTEM_INTEGRATION_ARCHITECTURE.md`, `CAUL_UTILITY_SERVICE_SPEC.md`, `CLIENT_OPERATIONS_AND_PRIVACY_SPEC.md`, `PRODUCT_ADAPTER_CONTRACT.md`, this plan, `SECURITY_AND_TEST_PLAN.md`, `DECISIONS_REQUIRED.md`.
**No code changes.** 
**Acceptance:** owner reviews docs; answers decisions in `DECISIONS_REQUIRED.md`.
**Exit gate → M1:** owner approves the architecture + selects which decisions unblock M1.

## Milestone 1 — Schemas, adapter interfaces, mocks, flags, tests (DEV ONLY) [PROPOSED]
**Scope:** API schemas (`/v1` utility service + product adapter), interface stubs, **mock** implementations (no real product/token calls), feature flags, and automated tests — all in the **development** environment only. Reuse `BaseConnector`/`run_contract_suite`, default-deny RBAC, HMAC signing, tamper-evident audit. Maintain the **100% coverage gate**.
**Hard constraints:** no cross-boundary access; no unresolved owner decision required; no staging/prod; no external accounts/spend; mock token flows only.
**Acceptance:** contract-test suite green in dev; schemas reviewed; coverage 100%.
**Exit gate → M2:** owner selects the pilot product + approves a non-production pilot.
> **Current status:** NOT started. M1 may proceed in dev only **after** the owner approves M0 and confirms it needs no unresolved decision (e.g., auth method choice §DECISIONS 1–3). Until then: proposed changes only, wait at the gate.

## Milestone 2 — Non-production pilot with ONE product (sandbox/mock) [PROPOSED]
**Scope:** wire one owner-selected product's adapter in **staging** using sandbox/mock token flows and a product-issued read-only token. Aggregate-metrics pull + (optional) client-ops read, fully audited, kill-switch tested.
**Hard constraints:** staging isolated; production untouched; sandbox/mock tokens only; no live wallet.
**Acceptance:** end-to-end pull verified in staging; isolation + kill-switch + audit proven; privacy checks pass.
**Exit gate → M3:** security/privacy review scheduled.

## Milestone 3 — Security/privacy review + operational readiness + owner approval [PROPOSED]
**Scope:** independent security + privacy review; **[LEGAL]** token-treatment review; incident-response, key-rotation, monitoring runbooks; readiness checklist.
**Acceptance:** review sign-offs; runbooks complete; owner go/no-go.
**Exit gate → M4:** explicit written production approval.

## Milestone 4 — Production rollout, one product at a time [PROPOSED]
**Scope:** separately approved production enablement, per product, behind feature flags, with fiat/non-token fallback where practical. Real token utility only after **[LEGAL]** + XRPL identity audit + budget approval.
**Hard constraints:** no bulk enablement; one product at a time; emergency pause ready; CAUL AI never modifies a product's prod code/DB/DNS/billing.
**Acceptance:** per-product production verification + monitoring green.

---

## Cost separation (every milestone)
- **$0 / local / mock:** M0 fully; M1 fully (dev, mocks); M2 staging with sandbox/mock (no paid token ops).
- **Potential paid (requires budget approval):** production IdP (Auth0) tier; LLM usage for client-ops/agent features; any production infra beyond current container; legal counsel; any real token/treasury operations. All itemized in `DECISIONS_REQUIRED.md`.

## Boundaries that never change without written owner approval
No production deploys from CAUL AI; no live wallet/keys; no external accounts/spend; no modifying any product's prod code/DB/DNS/billing/live records/token config; no DB merges; no autonomous spend/publish/outreach; no token custody/signing.
