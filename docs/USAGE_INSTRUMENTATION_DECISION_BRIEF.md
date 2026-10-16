# USAGE_INSTRUMENTATION_DECISION_BRIEF.md
**§G decision brief — recommended defaults for the dev-only usage-instrumentation layer (owner-review).**
**Documentation only. No code written or run. No real data, no external services, no billing, no price change, no wallet, no staging/production change.** Pricing/usage amounts remain open hypotheses.

> Each item below gives: **Recommendation → exact value → why**, plus schema/event examples and any spec/§G change.

---

## 1. Retention
**Recommendation:** raw events **30 days**, then keep **de-identified daily aggregates** for **24 months**.
**Exact values:** `RAW_RETENTION_DAYS = 30` · `AGGREGATE_RETENTION_MONTHS = 24` (both configurable).
**Why:** 30 days is enough to debug the pipeline and build the first rollups while minimizing how long any account-scoped row exists (data minimization). Trend/ROI analysis only needs aggregates, so raw detail should not linger. 24 months of aggregates supports year-over-year comparison without retaining row-level data.

**How deletion works (hard delete, not soft):**
- A scheduled dev job runs daily (reuses the existing HMAC cron pattern). Each run:
  1. **Rolls up** raw events older than yesterday into `usage_aggregates` keyed by `(day, workflow_type, tenant_ref, product_ref, cohort)` — **dropping** `account_ref` and all per-run ids so aggregates are de-identified.
  2. **Deletes** raw rows where `occurred_at < now − RAW_RETENTION_DAYS` with a SQL `DELETE` (physical removal; the table is append-only otherwise — no updates).
  3. **Deletes** aggregates older than `AGGREGATE_RETENTION_MONTHS`.
- Deletion is idempotent and audited (`usage.retention_run` event with counts, no content).
- On an owner-requested purge, a parameterized `DELETE … WHERE tenant_ref = :ref` removes everything for that scope immediately.
**Spec change:** tighten `USAGE_INSTRUMENTATION_SPEC.md` §6 raw retention from "≤90 days" to **30 days** default.

---

## 2. Pseudonymization
**Recommendation:** use **generated surrogate IDs scoped to each (tenant, product)**; **never** link a person across products in this layer.
**Exact scheme:**
- `tenant_ref`, `product_ref` = opaque generated IDs (random UUIDv4) assigned per tenant / per product.
- `account_ref` = a **per-(person, tenant, product)** random surrogate (UUIDv4). The same real person active in two products receives **two unrelated** `account_ref`s. There is **no cross-product identity key** in the usage layer.
- Surrogates are **generated server-side**; the layer **never accepts a client-supplied identifier** and stores **no** name/email/phone. Any surrogate→identity mapping (if ever needed) lives **outside** this layer, behind separate access control, and is **not required** for Stage-1 aggregate analysis. For synthetic Stage-1 data, no mapping exists at all.
**Why:** scoped surrogates give per-product measurement while structurally preventing cross-product person-level correlation — the privacy property you asked for. Server-side generation stops PII from entering via the id field.

---

## 3. Attribution (baseline vs. assisted)
**Recommendation:** default to **observational cohort comparison**, clearly labeled **"observational — not causal,"** and only upgrade the label when the assignment method supports it.
**How we compare:**
- Tag each run with `cohort ∈ {baseline, caul_assisted}` and `attribution ∈ {assisted, baseline, unattributed}`.
- Compute the metric for each cohort and report the **difference** (e.g., `support_time_saved`, `onboarding_completion_rate`, `renewal_followup_effectiveness`, `conversion_lift`).
- **Labeling rule:**
  - *Observational* (default): cohorts formed by natural/convenience assignment → report as **association**, show confounders, never claim CAUL "caused" the lift.
  - *Quasi-experimental*: difference-in-differences with a pre/post period + comparison group → label **"quasi-experimental, causal-suggestive with assumptions."**
  - *Experimental*: randomized holdout (eligible runs randomly assigned) → label **"experimental,"** and only then may we state a causal effect (with confidence interval).
- Every reported comparison carries its method label and sample size.
**Why:** it prevents over-claiming. Most early internal data will be observational; the honest default protects pricing decisions from spurious "lift."

---

## 4. Model cost assumptions
**Recommendation:** source rates from the **AI provider's public pricing page**, store them **configurable with an effective date**, and separate **input / output / cached** token rates. **Never** use $CAUL's market price as a cost input.
**Exact approach:**
- **Provider:** AI access is via the Emergent LLM key (OpenAI / Anthropic / Google models). Record the specific `model_ref` used per `ai.step`.
- **Pricing source:** the respective provider's **official public pricing page**, captured as `source_url` + `effective_date` (the date the rate was published/observed). Rates are **estimates for internal cost modeling**, not invoices.
- **Configurable rate table** (not hardcoded), e.g.:
```json
{
  "model_ref": "example-model-v1",
  "provider": "example-provider",
  "currency": "USD",
  "rate_input_per_1k": 0.0000,
  "rate_output_per_1k": 0.0000,
  "rate_cached_input_per_1k": 0.0000,
  "source_url": "https://<provider>/pricing",
  "effective_date": "2026-06-15"
}
```
- **Cost formula:** `est_cost_usd = (tokens_in/1000 × rate_input) + (tokens_out/1000 × rate_output) + (tokens_cached/1000 × rate_cached_input)`. `cache_hit`/cached tokens are counted at the cached rate.
- **Explicit exclusion:** `est_cost_usd` is a **compute-cost** estimate only; the $CAUL token price is **never** an input to any AI cost figure.
**Why:** keeps cost math transparent, auditable, and decoupled from token markets; configurability means rate changes don't require code edits; splitting input/output/cached matches how providers actually bill.
**Spec/§G change:** replace the single "token$/model rate" note with this three-rate + effective-date model; add `tokens_cached` to the `ai.step` fields.

---

## 5. PII safeguards
**Confirmation:** the event schema has **no free-text fields**. Every field is a UUID/ref, enum, timestamp, boolean, or numeric. No message bodies, subjects, names, emails, notes, or error *messages* (only an `error_class` enum).

**What the schema CAN reliably reject (validation-enforced):**
- **Unknown/extra fields** (strict schema → reject, not ignore).
- **Wrong types** (e.g., a string where a number/enum is required).
- **Out-of-enum values** for `workflow_type`, `event_type`, `result`, `outcome_type`, `cohort`, `attribution`, `error_class`.
- **Client-supplied identifiers** — refs are generated server-side; inbound identifier fields are refused.
- **Oversized/malformed** values (length/format bounds on refs and numerics).

**What validation CANNOT reliably detect (honest limits + mitigations):**
- **PII deliberately encoded inside an allowed field** — e.g., if upstream code mislabeled a ref by hashing an email into it. *Mitigation:* server-side-only ref generation + code review; validation sees a well-formed UUID, not its origin.
- **Semantic misuse of a numeric/enum** (e.g., packing a birth year into `outcome_value`). *Mitigation:* `outcome_value` bounded + documented as non-identifying; reviewed in tests.
- **Re-identification by combination** — enough low-cardinality dims + small cohorts could narrow to an individual. *Mitigation:* aggregates suppress small cells (k-anonymity threshold, e.g. drop groups with `n < 5` `[DECISION]`), and raw rows expire in 30 days.
- Validation checks **structure, not meaning** — it guarantees shape and vocabulary, not that an upstream caller behaved. Defense is structural (no free-text, server-side refs) + review + tests, not content scanning.

**Example conformant `ai.step` event:**
```json
{
  "event_id": "f1b2…uuid",
  "event_type": "ai.step",
  "occurred_at": "2026-06-15T13:04:22Z",
  "env": "dev",
  "schema_version": 1,
  "workflow_type": "support_triage",
  "workflow_run_id": "9c7a…uuid",
  "actor_type": "ai",
  "actor_id": "svc:triage-worker",
  "account_ref": "a1e4…uuid",
  "tenant_ref": "t77…uuid",
  "product_ref": "p12…uuid",
  "model_ref": "example-model-v1",
  "tokens_in": 820,
  "tokens_out": 240,
  "tokens_cached": 400,
  "work_unit_type": "classification",
  "work_units": 1,
  "est_cost_usd": 0.0031,
  "latency_ms": 640,
  "cache_hit": true,
  "result": "success"
}
```
**Example conformant `outcome.recorded` event:**
```json
{
  "event_id": "7d90…uuid",
  "event_type": "outcome.recorded",
  "occurred_at": "2026-06-15T13:10:00Z",
  "env": "dev",
  "schema_version": 1,
  "workflow_type": "renewal_followup",
  "workflow_run_id": "9c7a…uuid",
  "account_ref": "a1e4…uuid",
  "tenant_ref": "t77…uuid",
  "product_ref": "p12…uuid",
  "outcome_type": "renewal_confirmed",
  "outcome_value": 1,
  "attribution": "assisted",
  "cohort": "caul_assisted",
  "result": "success"
}
```

---

## 6. Recommended changes to the spec / §G (summary)
1. Raw retention **90 → 30 days**; add explicit roll-up-then-hard-delete deletion flow + `usage.retention_run` audit event.
2. Pseudonymization: state **per-(tenant, product) scoped surrogates, no cross-product linkage, server-side generation only**.
3. Attribution: add the **observational default + labeling rule** (observational / quasi-experimental / experimental).
4. Model cost: adopt the **configurable three-rate table (input/output/cached) + `source_url` + `effective_date`**; add `tokens_cached` to `ai.step`; codify the "$CAUL price is never a cost input" exclusion.
5. PII: add **small-cell suppression** (`n < 5` default `[DECISION]`) for aggregates and the explicit "validation checks structure, not meaning" caveat.

## 7. Decisions still needed from you
- Confirm `RAW_RETENTION_DAYS = 30` and `AGGREGATE_RETENTION_MONTHS = 24`.
- Confirm small-cell suppression threshold (`n < 5`?).
- Confirm the attribution default (observational) and whether to plan a randomized holdout later.
- Confirm that provider public pricing pages (with effective dates) are an acceptable cost source.
- Then: **approve / hold** a development-only implementation of the (amended) `USAGE_INSTRUMENTATION_SPEC.md`.

**This remains documentation-only. No code will be written or run until you review this brief and explicitly approve implementation.**
