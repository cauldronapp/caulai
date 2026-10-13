# Deal Flow OS — Access & Approval Request (for CAUL AI Phase 1 readiness)

**From:** Cauldron Technologies, Inc. / CAUL AI engineering
**To:** Deal Flow OS owner / administrator
**Purpose:** Enable a limited, **staging-only, read-only** metrics connector from CAUL AI. This request is for **authorized discovery + a scoped staging credential only.** No production changes, no customer-record access, no spend.

> Deal Flow OS will **not** take any runtime dependency on CAUL AI. Everything requested is read-only and aggregate-only.

---

## A. Executive approval (required to start Phase 1)
- [ ] Written approval to begin a **staging-only** Phase 1 connector.
- [ ] Confirmation that production remains **out of scope** until a separate, tested, approved rollout.

## B. Read-only discovery access (for the authorized audit)
- [ ] Tech stack & repository (framework, language, DB engine).
- [ ] Hosting, monitoring, and deployment workflow (names only; no secrets).
- [ ] Authentication method (how services/users authenticate).
- [ ] Existing public/internal **APIs** + versioning + rate limits.
- [ ] **Billing/analytics source of truth** (e.g., Stripe? internal tables?).
- [ ] Webhook capability (yes/no) and tenant model (single vs. multi-tenant).

## C. Scoped staging credential (least-privilege)
- [ ] A **read-only service token** issued in **Deal Flow OS staging** (not production).
- [ ] Scoped to **aggregate metrics only** — no row-level/PII access.
- [ ] Rotatable + revocable; short TTL acceptable.
- [ ] Delivered via a secure channel (never in chat/email plain text).

## D. Metrics source-of-truth confirmation (fill-in)
For each metric: confirm **source**, **formula**, and **refresh cadence**.

| Metric | Source of truth | Formula | Cadence |
|---|---|---|---|
| Registered accounts | | | |
| Active accounts | | | |
| Paying subscribers | | | |
| MRR / ARR | | | |
| New subscriptions | | | |
| Cancellations / churn | | | |
| Trial → paid conversion | | | |
| Activation | | | |
| Feature adoption | | | |
| Acquisition cost (CAC) | | | |

## E. CAUL AI trust-model decision (pick one)
- [ ] **Option 1:** Stand up CAUL AI production IdP first (Phase 1B), then integrate.
- [ ] **Option 2:** Interim **signed service-token** for **staging-only** Phase 1, IdP decided later.

---

### What CAUL AI will build once A–E are granted (staging only)
A versioned **read-only** `/v1/metrics/*` consumer: scheduled pull, timeouts + bounded retries + circuit breaker, aggregate-only validation, audit on every fetch, and a kill switch (emergency pause scope `connector:dealflow`). Deal Flow OS exposes a new **read-only** aggregate metrics endpoint in **staging**; no other Deal Flow OS changes.

### What CAUL AI will NOT do
Modify/deploy Deal Flow OS production · run migrations · merge databases · read customer/seller/buyer/transaction records · create paid services · generate production credentials · trigger outreach or spend.

**Return this completed checklist + the staging credential to proceed to a scoped, staging-only Phase 1.**
