# CAUL_UTILITY_SERVICE_SPEC.md
**$CAUL as a reusable, optional utility across Cauldron products — service + versioned API spec (Milestone 0 design).**
**Design only. No token operations, no keys, no legal commitment, no real blockchain transactions.** Gated behind legal review + XRPL identity audit + budget approval.

> Legend: **[EXISTS]** · **[PROPOSED]** · **[ASSUMPTION]** · **[DECISION]** · **[LEGAL]**.

---

## 1. Purpose & guardrails
A central **CAUL Utility Service** (separate from products and from the CAUL AI control plane) exposes a **versioned API** that any product can use for *reviewed* $CAUL features. $CAUL is an **optional** utility for real services.

**Must not (without separate written review/approval):** promise a token price, appreciation, investment return, guaranteed liquidity or earnings; introduce staking, yield, buybacks, token custody, exchange activity, or sale of balances. **Must not** broadcast any real blockchain transaction as part of this work. **Must not** request seed phrases or private keys — ever. Calling $CAUL a "utility token" does **not** make it exempt from regulation. **[LEGAL]**

## 2. XRPL asset identity — assumptions to verify [ASSUMPTION]
Issuer address · currency code (3-char/hex) · total & circulating supply config · trust-line requirement/authorization · treasury wallet addresses · distribution · exchange/liquidity claims · freeze/clawback flags · operational constraints. **All unverified until an authorized on-chain + ownership audit.** No wallet/keys in scope.

## 3. API surface (versioned, `/v1`) [PROPOSED]
All endpoints: signed requests, scoped auth, idempotency, rate-limited, fully audited. **Read endpoints first; value-moving endpoints behind flags + human approval.**

| Group | Endpoint (illustrative) | Notes |
|---|---|---|
| Registry | `POST /v1/products` / `GET /v1/products/{id}` | Register a product + environment identity (dev/staging/prod separate). |
| Wallet | `POST /v1/wallets/link/challenge` → `POST /v1/wallets/link/verify` | Noncustodial ownership proof via **sign-a-nonce**. Never asks for seed/keys. |
| Balance | `GET /v1/wallets/{id}/balance` · `GET /v1/eligibility` | **Read-only** balance + eligibility where supported. |
| Catalog | `GET /v1/catalog` | **USD-denominated** service catalog; token quote is derived, transparent, time-limited. |
| Quote | `POST /v1/quotes` | Time-limited quote (expiry + slippage bound + failure handling). |
| Redemption | `POST /v1/redemptions` | User-signed, noncustodial. Entitlement granted **only on confirmed VALIDATED settlement**. [DECISION][LEGAL] |
| Status | `GET /v1/redemptions/{id}` | Transaction status, reconciliation state. |
| Reversal | `POST /v1/redemptions/{id}/refund` | Refund/reversal **only where technically & legally available**. [LEGAL] |
| Flags | `GET /v1/products/{id}/features` | Per-product feature flags; each product enables only its reviewed features. |
| Admin | `POST /v1/emergency/pause` | Emergency pause of utility features (reuses CAUL AI emergency pattern). |

**Versioning:** URL-versioned (`/v1`), additive changes only within a major; breaking changes = new major + deprecation window.

## 4. Product adapter & auth model
- Each product registers a **service identity** per environment (dev/staging/prod). See `PRODUCT_ADAPTER_CONTRACT.md`.
- **Authentication:** per-product API key id + HMAC **request signing** (body + timestamp + nonce) to prevent tampering/replay. (Carries forward the existing per-env HMAC cron pattern.) [DECISION: key vs. mTLS vs. OAuth client-credentials]
- **Authorization scopes:** narrow, e.g. `caul.balance:read`, `caul.eligibility:read`, `caul.redeem:create` (flagged), `caul.refund:create` (flagged). Default-deny.
- **Idempotency:** mandatory `Idempotency-Key` on all state-changing calls; stored + de-duplicated.
- **Rate limits:** per product + per environment; 429 with retry semantics.
- **Audit events:** every call emits a tamper-evident audit event (actor = product service identity).

## 5. Wallet-linking & redemption flow (noncustodial) [PROPOSED]
```
User wallet --(sign nonce challenge)--> Service verifies signature (ownership proof)
User initiates redemption --> Service issues USD-priced, time-limited quote (expiry + slippage)
User signs XRPL payment to treasury --> Service waits for VALIDATED ledger settlement
On confirmed settlement + idempotency --> issue nontransferable OFF-CHAIN service credits
Credits --> entitlement at product (via product adapter, approved policy)
```
Clear **user confirmation** is required before any transaction. No entitlement on pending/unconfirmed tx.

## 6. Off-chain credit ledger (double-entry, reconciled) [PROPOSED]
States: on-chain balance (read), pending redemption, confirmed settlement, issued credits, redeemed credits, expired credits, refunds, liabilities. Enforce idempotency keys, double-entry reconciliation, and anti-replay on every tx/quote. Credits are **nontransferable off-chain service credits**, not a new tradable token.

## 7. Fiat / non-token fallback [PROPOSED]
Wherever practical, a **fiat or non-token path** exists so holding $CAUL is **not required** to access a core product feature. Token is an optional convenience/benefit, not a gate. [DECISION per feature]

## 8. Rewards / treasury [PROPOSED, tightly controlled]
Eligibility rules, caps, anti-sybil/abuse, appeals, approved treasury budgets. All issuance / treasury movement / policy change = separately approved, controlled procedures. CAUL AI **recommends**; a separate approved policy service enforces. Any reward above a pre-approved limit requires human approval.

## 9. Ops: monitoring, incident response, key rotation, emergency pause [PROPOSED]
- Health + readiness endpoints; metrics on quote/redemption/settlement/refund rates and reconciliation drift.
- Incident response runbook; alerting on settlement-confirmation failures and ledger imbalance.
- Key rotation schedule for product API keys and signing secrets (names only, stored in the approved secret store — never in source/chat).
- **Emergency pause** that disables value-moving features while leaving read-only reporting intact.

## 10. Hard prerequisites before any production utility [LEGAL][DECISION]
Legal/regulatory review (securities, money transmission, consumer protection, privacy, tax, accounting, gaming, platform rules) + XRPL identity/ownership audit + budget approval. **Testnet/sandbox or mock flows only until then.**
