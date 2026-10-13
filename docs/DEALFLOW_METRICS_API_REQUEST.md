# Deal Flow OS — Build Request: Read-Only Metrics API + API Key for CAUL AI

**What this is:** The exact spec to submit to the **Deal Flow OS** Emergent project (paste the "Prompt" in §4 to its agent) so it exposes a **versioned, read-only, aggregate-only** metrics API and issues a **scoped API key** that CAUL AI uses to connect.

**Scope guardrails (must hold):** staging-only first · aggregate metrics only (NO customer/seller/buyer/transaction/PII rows) · least-privilege · rotatable/revocable · Deal Flow OS keeps zero runtime dependency on CAUL AI · no production rollout until separately approved.

---

## 1. What "submitting" actually means
Emergent has **no cross-project key-sharing form**. You (the owner of both projects) get the key by having the **Deal Flow OS agent build it**, then you copy the key value into **CAUL AI's secrets**. Three concrete steps:

1. **Submit the build prompt (§4)** to the Deal Flow OS project's chat.
2. Deal Flow OS builds the endpoint + generates a **random API key**, stored as a Deal Flow OS **secret** (e.g. `CAUL_METRICS_API_KEY`).
3. Deal Flow OS returns to you: the **staging base URL** + the **API key value** (share securely, not in plain chat). You paste both into CAUL AI as env secrets (§5).

> Deal Flow OS **generates** the key itself (a long random string). Emergent does not mint third-party keys for you; your app creates and validates its own key.

## 2. What to ask Deal Flow OS to create
- **One service account / API client** named `caul-ai-metrics-reader`.
- **One API key** for it, scope = `metrics:read` (aggregate only), environment = **staging/preview** only.
- Key format: opaque random ≥ 32 bytes (e.g. `dfos_sk_<random>`); store hashed at rest; **rotatable** + **revocable**.
- (Production key deferred until a separate approved rollout.)

## 3. API contract Deal Flow OS should expose (read-only, versioned)
- `GET /v1/metrics/summary` — all headline aggregates, `as_of`, `tenant`.
- `GET /v1/metrics/subscriptions?window=30d` — subscription aggregates for a window.
- **Auth:** `Authorization: Bearer <API_KEY>` (or `X-API-Key`). Reject with 401 if missing/invalid, 403 if out of scope.
- **Aggregate-only:** counts/sums/rates only — never row-level records.
- **Limits:** per-key rate limit (e.g. 60 req/min), stable JSON, `ETag`/`as_of` for caching, HTTPS only.
- **Metrics to include:** registered accounts, active accounts, paying subscribers, MRR, ARR, new subscriptions, cancellations/churn, trial→paid conversion, activation, feature adoption, CAC. (If a metric isn't computable yet, return `null` + note it.)

Example response (`/v1/metrics/summary`):
```json
{
  "schema_version": "1.0",
  "tenant": "dealflowos",
  "as_of": "2026-06-01T00:00:00Z",
  "metrics": {
    "registered_accounts": 1240,
    "active_accounts_30d": 410,
    "paying_subscribers": 180,
    "mrr_usd": 17820.00,
    "arr_usd": 213840.00,
    "new_subscriptions_30d": 22,
    "cancellations_30d": 6,
    "churn_rate_30d": 0.033,
    "trial_to_paid_rate": 0.28,
    "activation_rate": 0.54,
    "feature_adoption": { "deal_analyzer": 0.62, "buyer_marketplace": 0.41 },
    "cac_usd": 96.50
  }
}
```

## 4. PROMPT TO PASTE INTO THE DEAL FLOW OS PROJECT
> **Build (staging/preview only): a read-only aggregate metrics API for an external consumer (CAUL AI).**
> Do **not** change production, run destructive migrations, or expose any customer/seller/buyer/transaction/PII records — aggregate numbers only.
>
> 1. Add a versioned, read-only JSON API:
>    - `GET /v1/metrics/summary` and `GET /v1/metrics/subscriptions?window=30d`.
>    - Returns only aggregates: registered accounts, active accounts (30d), paying subscribers, MRR, ARR, new subscriptions (30d), cancellations/churn (30d), trial→paid conversion, activation rate, feature adoption, CAC. Include `schema_version`, `tenant`, `as_of`. Return `null` for any metric not yet computable and list it.
> 2. Add API-key auth for a new service client `caul-ai-metrics-reader`:
>    - Accept `Authorization: Bearer <key>` (also accept `X-API-Key`). 401 if missing/invalid, 403 if scope ≠ `metrics:read`.
>    - Generate ONE random staging key (≥32 bytes, prefix `dfos_sk_`), store it **hashed** as a secret `CAUL_METRICS_API_KEY`, make it **revocable** and **rotatable**. Do not print the raw key in logs.
> 3. Enforce: HTTPS only, per-key rate limit (~60/min), request timeout, and read-only DB access for this endpoint. No writes.
> 4. Tell me (a) the **staging base URL**, (b) the **raw API key value once** (so I can store it in the consumer app), and confirm the key is staging-scoped and revocable.
> 5. Keep Deal Flow OS fully functional and independent — this endpoint must not affect existing features.

## 5. What you then give CAUL AI
Store these as CAUL AI **secrets/env** (names CAUL AI's connector will read):
- `DEALFLOW_API_BASE_URL` = the Deal Flow OS **staging** base URL.
- `DEALFLOW_API_KEY` = the raw key value (delivered securely, once).

CAUL AI then connects **server-to-server** from its backend connector (`connector:dealflow`, `metrics:read`), with timeouts/retries/circuit-breaker + kill switch + audit on every fetch — per `DEALFLOW_INTEGRATION_READINESS.md`.

## 6. How to deliver the key safely
- Do **not** paste the raw key in open chat/email. Use a secret manager, 1Password/Bitwarden share link, or paste it **directly into CAUL AI's Secrets** field yourself.
- Rotate on a schedule; revoke immediately if exposed.

---
**Reminder:** building this in Deal Flow OS is **Phase 1 (staging)** and needs your written go-ahead. This document is the request; it does not authorize or perform any build.
