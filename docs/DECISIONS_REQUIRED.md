# DECISIONS_REQUIRED.md
**Owner decisions needed to proceed past Milestone 0.** Nothing below is started. No secret should be pasted in chat — identify by name; provide via the approved secret store.

> Legend: **[DECISION]** owner choice · **[LEGAL]** licensed-professional review · **[SECRET]** provide via secure mechanism, not chat.

---

## A. Unblock development (Milestone 1, dev-only, $0)
1. **[DECISION]** Approve the hub-and-spoke, pull-based, read-only architecture (Option A)?  **[Approve / Change]**
2. **[DECISION]** Adapter auth method: HMAC request signing (recommended, reuses existing pattern) vs. mTLS vs. OAuth2 client-credentials?  **[Pick one]**
3. **[DECISION]** May I build M1 **mocks + schemas + tests in the dev environment only** now (no product/token access, no spend)?  **[Yes / Hold]**

## B. Pilot selection (Milestone 2)
4. **[DECISION]** Which single product is the non-production pilot?  **[Deal Flow OS / Cauldron App / Other]**
5. **[DECISION]** Authorize a **read-only** audit of the pilot product and a **scoped read-only token issued by that product** (its own project change, staging)?  **[Approve / Hold]** · token is **[SECRET]**.

## C. Identity & privacy
6. **[DECISION]** Name the business-customer source of truth (CRM/billing system).
7. **[DECISION]** Identity-link match-confidence thresholds + human-review policy (no auto-merge across the boundary).
8. **[LEGAL]** Lawful basis + consent capture per population and per communication type; cross-border data handling.

## D. $CAUL / XRPL (Phases gated)
9. **[DECISION + LEGAL]** Authorize a **read-only** XRPL identity/ownership audit (no token ops, no keys either way)?  **[Approve / Hold]**
10. **[LEGAL]** Engage qualified counsel on $CAUL treatment (securities, money transmission, consumer protection, privacy, tax, accounting, gaming, platform rules). Provide the factual function list to counsel; do **not** claim regulatory exemption.
11. **[DECISION]** Per-feature: is a **fiat/non-token fallback** required so $CAUL is never mandatory for a core feature?  **[Default: yes]**

## E. CAUL AI production readiness (hard blockers)
12. **[DECISION]** Proceed to wire the real IdP (Auth0) per the existing dossier?  If yes, provide staging **[SECRET]** `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_AUDIENCE` + MFA policy (via secure mechanism, not chat).
13. **[DECISION]** Confirm Phase 1A acceptance gates are closed for the production track (prior certificate exists; reconfirm).

## F. Budget & authority
14. **[DECISION]** Budget envelope for any future paid services (production IdP tier, LLM usage for client-ops/agent features, production infra, legal counsel, future token/treasury ops) and **who may approve spend**.  **[Set / Hold]**
15. **[DECISION]** Baseline KPIs: who provides authoritative MRR/churn/activation numbers per product?

## G. Autonomy limits
16. **[DECISION]** Confirm the human-approval list for AI actions (sensitive comms, refunds, account suspension/deletion, pricing/entitlement changes, any token tx/reward above a limit) and the pre-approved reward limit value.

## G. Usage instrumentation (Stage 1 measurement)
17. **[DECISION]** Approve a **development-only, $0** implementation of `USAGE_INSTRUMENTATION_SPEC.md` (synthetic data only; no real customer data; no external services; staging/production untouched)?  **[Approve / Hold]**
18. **[DECISION]** Raw-event retention window (default ≤90 days in dev), pseudonymization method for account/tenant/product refs, baseline-vs-assisted attribution method, and token$/model rate assumptions for `est_cost_usd`.

---

### Cost summary for these decisions
- **$0 now:** M0 docs (done); M1 mocks/schemas/tests in dev (pending A3).
- **Potential paid (needs #14):** Auth0 tier, LLM usage, production infra, legal counsel, real token/treasury operations.

### Next safe action
Await owner responses to **Section A** (and ideally B). On approval of A1–A3 with no unresolved dependency, I can implement **Milestone 1 in dev only** (schemas + adapter interfaces + mocks + feature flags + tests, 100% coverage held). Everything else waits at its documented gate. Staging stays isolated; production untouched.
