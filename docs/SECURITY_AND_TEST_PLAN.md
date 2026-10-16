# SECURITY_AND_TEST_PLAN.md
**Security, privacy, token, and operational risk + test/acceptance plan (Milestone 0 deliverable).**

> Legend: **[EXISTS]** · **[PROPOSED]** · **[LEGAL]** · **[DECISION]**.

---

## 1. Security model (reuse + extend)
- **Default-deny RBAC**, server-side, from PostgreSQL [EXISTS] → add tenant/product scoping + new client-ops and utility scopes [PROPOSED].
- **Identity:** labeled stub today [EXISTS]; **real IdP (Auth0) is a hard production blocker** [PROPOSED, dossier ready].
- **Request signing (HMAC)** for product adapters + utility API [PROPOSED]; constant-time compare, timestamp + nonce anti-replay (extends the existing cron-auth pattern).
- **Tamper-evident audit** on every integration action [EXISTS pattern]; secrets never recorded.
- **Emergency pause / kill switch** per connector + for utility value-moving features [EXISTS pattern → extend].
- **Secrets**: env/secret-store only, names only, rotated. Never in chat or source.

## 2. Isolation guarantees (tested)
- No cross-product / cross-tenant / cross-customer data exposure.
- Aggregate-only metrics (schema-validated to contain no PII) until records access is separately approved.
- No cross-product model training without notice/permission/contract/**[LEGAL]** review.

## 3. Risk register (top)
| # | Risk | Class | Mitigation |
|---|---|---|---|
| 1 | Seed-phrase/private-key phishing | Token/Security | Never request; sign-nonce ownership only; no keys in agents. |
| 2 | Entitlement on unconfirmed tx | Token | Require VALIDATED settlement + idempotency before credits. |
| 3 | Replay of settlement/requests | Security | Idempotency keys + nonce + ledger tx-hash de-dup. |
| 4 | Quote manipulation/slippage | Token | Expiry + slippage bounds + failure handling. |
| 5 | Cross-tenant/product data leak | Privacy | Server-side scoping on every request; isolation tests. |
| 6 | Over-broad AI autonomy | Operational | Bounded autonomy + human approval gates + kill switch (§5). |
| 7 | Regulatory misclassification of $CAUL | Legal | **[LEGAL]** review before any production utility; no exemption claims. |
| 8 | Treasury drain / unauthorized issuance | Token/Ops | Multi-control, budgets, approvals; AI only recommends. |
| 9 | Secret exposure | Security | Secret store, rotation, no secrets in chat/source. |
| 10 | Product outage coupling | Operational | Circuit breaker; products independent of CAUL AI/Gateway. |
| 11 | PII in "aggregate" metrics | Privacy | Schema validation + contract test #3. |
| 12 | Coverage/regression drift | Quality | 100% coverage gate in CI [EXISTS]. |

## 4. Bounded AI autonomy (policy to enforce) [PROPOSED]
AI may draft, summarize, classify, recommend, and perform **pre-approved low-risk** steps only. **Human approval required** for: sensitive/legally significant comms; refunds/credits/compensation; suspending/deleting accounts; pricing/contract/entitlement changes; any blockchain tx / wallet change / token transfer or reward above a pre-approved limit; legal/financial/identity/safety/account-security decisions. Every action = authenticated actor/service identity + policy check + audit record + rollback/escalation path. **Kill switch** disables AI actions while leaving read-only reporting on.

## 5. Test plan & acceptance criteria per milestone
**M0:** docs complete + decisions enumerated. *Accept:* owner review.
**M1 (dev, mocks):**
- Unit + contract tests for `/v1` schemas and adapter interface (mock product/token).
- Auth/signing tests: valid accepted; bad/absent/stale/replayed rejected.
- Default-deny scope tests; aggregate-only PII-absence schema test.
- Idempotency, rate-limit, kill-switch, audit-event-emitted tests.
- **100% backend coverage maintained** (`fail_under=100`). *Accept:* all green in dev.
**M2 (staging pilot, sandbox):** end-to-end aggregate pull from the pilot product; isolation proven (negative tests for cross-tenant/product); kill-switch halts fetches; audit chain verifies; privacy checks (retention/export/delete dry-run). *Accept:* staging verification report.
**M3:** independent security + privacy review sign-off; **[LEGAL]** token review; runbooks (incident response, key rotation, monitoring). *Accept:* sign-offs + owner go/no-go.
**M4:** per-product production verification + monitoring; fiat fallback verified where applicable. *Accept:* per-product prod check.

## 6. Verification discipline
No integration is "complete" unless implemented, tested in the correct environment, and independently verified. Claims distinguish mock vs. sandbox vs. production explicitly.
