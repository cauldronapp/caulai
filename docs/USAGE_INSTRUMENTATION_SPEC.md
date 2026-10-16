# USAGE_INSTRUMENTATION_SPEC.md
**CAUL AI — lightweight, $0, DEVELOPMENT-ONLY usage-instrumentation specification (owner-review draft).**
**Specification only. No instrumentation code written or run, no real customer data, no external services, no billing, no price change, no live wallet, no staging/production change.** Pricing/usage amounts remain **open hypotheses**.

> Legend: **[EXISTS]** in repo · **[PROPOSED]** future dev-only work · **[HYPOTHESIS]** value to validate · **[PRIVACY]** data-protection control · **[DECISION]** owner choice.

---

## 1. Purpose & scope
Define *what* to measure (and how) so we can prove **internal value** and **AI cost per account** before setting any prices. This spec describes a **development-environment-only** measurement layer that reuses existing primitives (PostgreSQL system-of-record, default-deny RBAC, tamper-evident audit, 100% coverage gate). It intentionally does **not** specify billing, external telemetry vendors, or production rollout.

**In scope:** event taxonomy, fields, metric formulas, privacy/retention limits, synthetic-data test plan, acceptance criteria.
**Out of scope (explicitly):** writing/running code, real customer data, external analytics SaaS, billing/PSP, pricing changes, token/wallet ops, staging/production.

## 2. First workflows to measure (Stage 1 internal value)
Prioritized for clear ROI signal and low measurement complexity:
1. **Support triage** — classify/route/draft a reply to an inbound support item (human approves send).
2. **Onboarding checklist** — guide a new account through required setup steps to completion.
3. **Renewal follow-up** — detect upcoming renewals and draft/sequence reminders (human approves send).
4. **Cross-product usage reporting** — generate an account/product usage summary.
5. **Feedback analysis** — summarize + classify sentiment/themes from feedback (aggregate).

Each is modeled as a **workflow run** with a lifecycle: `started → (ai_step*) → (awaiting_approval?) → completed | failed | abandoned`.

## 3. Event taxonomy (what to record) [PROPOSED]
Append-only events written through the existing tamper-evident audit pattern into a dedicated **dev-only** `usage_events` table (separate from governance audit; same INSERT-only discipline).

| Event | When | Key purpose |
|---|---|---|
| `workflow.started` | a workflow run begins | denominator for success/throughput |
| `ai.step` | each AI operation inside a run | AI cost + work-unit counting |
| `workflow.approval_requested` | run hits a human-approval gate | measure human-in-the-loop load |
| `workflow.approval_decided` | approver approves/rejects | approval latency + override rate |
| `workflow.completed` | run reaches its goal | success numerator |
| `workflow.failed` | run errors out | failure analysis |
| `workflow.abandoned` | run dropped/expired | funnel leakage |
| `outcome.recorded` | a business outcome is attributed (e.g., renewal confirmed, onboarding step done, ticket resolved) | operational-result metrics |
| `human.time_logged` | staff logs handling time (or system-derived) | support-time-saved baseline vs. assisted |

## 4. Fields to record (schema) [PROPOSED]
**Common envelope (every event):**
- `event_id` (uuid), `event_type`, `occurred_at` (UTC ISO-8601)
- `env` (always `dev` for this spec), `schema_version`
- `workflow_type` (enum: support_triage | onboarding | renewal_followup | usage_reporting | feedback_analysis)
- `workflow_run_id` (groups events of one run)
- `actor_type` (human | ai | system) + `actor_id` (internal id / service identity — **never** an end-customer PII identifier)
- `account_ref` (pseudonymous account key — see §6; **not** a name/email)
- `product_ref` (which product the work relates to), `tenant_ref`
- `result` (success | failure | pending | n/a), `error_class` (nullable, non-sensitive)

**`ai.step` extra fields (for cost):**
- `model_ref` (model identifier/label), `tokens_in`, `tokens_out`
- `work_unit_type` + `work_units` (normalized unit per cost model §2)
- `est_cost_usd` (computed = tokens × model $/token `[HYPOTHESIS]`), `latency_ms`, `cache_hit` (bool)

**`workflow.approval_*` extra:** `approval_gate`, `decision` (approve|reject), `decided_by_ref`, `decision_latency_ms`.

**`outcome.recorded` extra:** `outcome_type` (ticket_resolved | onboarding_step_completed | onboarding_completed | renewal_confirmed | renewal_lapsed | conversion), `outcome_value` (optional numeric, non-PII), `attribution` (assisted | baseline | unattributed).

**`human.time_logged` extra:** `handling_seconds`, `cohort` (baseline | caul_assisted), `source` (manual | derived).

> **No message bodies, no customer content, no PII** are stored in any field. Only counts, refs, enums, timings, and token/cost numerics. [PRIVACY]

## 5. Metric formulas
Computed over a chosen window per `workflow_type`, per `account_ref`, per `tenant_ref`/`product_ref`, and per `cohort` where applicable.

**AI cost:**
- `ai_cost_per_run = Σ(ai.step.est_cost_usd within run)`
- `ai_cost_per_account = Σ(ai.step.est_cost_usd for account_ref in window)`
- `work_units_per_account = Σ(ai.step.work_units for account_ref)`
- `ai_cost_ratio = ai_cost_per_account ÷ plan_price` *(plan_price is a `[HYPOTHESIS]`; ratio reported, not used to bill)*

**Workflow success & throughput:**
- `workflow_success_rate = completed ÷ (completed + failed + abandoned)`
- `automation_rate = runs_completed_without_reject ÷ completed` *(proxy for low-touch automation)*
- `avg_run_latency = mean(workflow.completed.occurred_at − workflow.started.occurred_at)`

**Human-in-the-loop:**
- `approval_rate = approval_requested ÷ started`
- `approval_latency = mean(decision_latency_ms)`
- `override_rate = rejects ÷ approval_decided`

**Operational results:**
- `support_time_saved = mean(handling_seconds | cohort=baseline) − mean(handling_seconds | cohort=caul_assisted)` (× ticket volume × loaded cost for $ value)
- `onboarding_completion_rate = accounts_with(onboarding_completed) ÷ accounts_started_onboarding` (compare cohorts)
- `renewal_followup_effectiveness = renewal_confirmed ÷ (renewal_confirmed + renewal_lapsed)` for accounts with assisted follow-up vs. baseline
- `conversion_lift = conversion_rate(caul_assisted) − conversion_rate(baseline)`

**Unit-economics inputs (reported once real data exists):** feeds `COST_AND_UNIT_ECONOMICS_MODEL.md` (gross margin, usage distribution, % exceeding included usage).

## 6. Privacy & data-retention limits [PRIVACY]
- **Pseudonymous refs only.** `account_ref`/`tenant_ref`/`product_ref`/`*_by_ref` are opaque keys (e.g., salted hashes) with the mapping held outside this table and **not required** for Stage-1 aggregate analysis. No names, emails, phone numbers, message content, or free text.
- **Data minimization.** Store only counts, enums, timings, token/cost numerics, and refs. Reject any field not enumerated in §4 (schema-validated).
- **No special-category/sensitive data** collected.
- **Access:** reads gated by a new default-deny permission (e.g., `usage:read`); every read audited. Append-only; no updates/deletes of events except retention expiry.
- **Retention:** raw events retained **≤ 90 days `[DECISION]`** in dev; roll up to anonymous daily/weekly aggregates for longer-term trend analysis; aggregates contain no account-level identifiers beyond pseudonymous refs (or are fully de-identified). Automated expiry job.
- **Dev-only isolation:** this layer exists **only** in the development environment for this spec; staging/production are untouched. No external telemetry vendor.
- **Consent/lawful-basis:** because Stage 1 uses internal/synthetic data only, no customer consent flow is exercised here; any future real-data use is gated by `CLIENT_OPERATIONS_AND_PRIVACY_SPEC.md` + counsel review.

## 6a. Aggregation is irreversible at the individual level + deletion handling [PRIVACY]
**Caveat (must be understood before approving):** once `account_ref` is dropped during roll-up, an **individual's contribution cannot be removed from that aggregate** — the aggregate is de-identified and no longer linkable to a person. Deletion therefore has two distinct paths depending on timing:

- **Before aggregation (raw still present):** a deletion request for a person/account is honored by **hard-deleting that account's raw events** (`purge_account_raw(account_ref)`) *before* they are rolled up. This fully removes the individual's row-level contribution. Because raw events expire at 30 days and roll-ups run daily, the window to delete an individual contribution is bounded (≈ up to 1 day until the next roll-up, up to 30 days until raw expiry).
- **After aggregation (raw expired/rolled up):** the contribution exists only inside de-identified counts and **cannot be individually subtracted**. The only remaining lever is **tenant-wide purge** (below). This is an inherent, documented property of de-identified aggregation, not a defect.

**Tenant-wide purge path:** `purge_tenant(tenant_ref)` hard-deletes **all raw events and all aggregates** for that tenant (both pre- and post-aggregation data), audited as `usage.tenant_purged`. This is the authoritative "remove everything for this tenant" control.

**Deletion-request flow:** on a verified request, (1) immediately `purge_account_raw` to drop any still-raw contribution; (2) if tenant-level erasure is required, `purge_tenant`; (3) record the action in the governance audit chain. Requests that arrive after aggregation are answered honestly: row-level deletion is no longer possible, only tenant-wide purge.

## 7. Synthetic-data test plan (no real customer data)
Validate the measurement layer end-to-end using **generated** data only:
1. **Generator:** a dev fixture produces synthetic workflow runs across all 5 workflow types with controllable distributions (success/fail/abandon rates, token volumes, approval/override rates, baseline vs. assisted cohorts).
2. **Schema conformance:** every emitted event validates against the §4 schema; unknown/PII-looking fields are rejected. Negative tests assert PII fields cannot be written.
3. **Formula correctness:** feed known synthetic inputs → assert each §5 metric returns the mathematically expected value (golden-number tests).
4. **Cohort comparison:** synthesize a baseline vs. assisted gap → assert `support_time_saved`, `onboarding_completion_rate`, `conversion_lift` compute the planted deltas.
5. **Cost math:** assert `est_cost_usd` = tokens × rate and account/run aggregations sum correctly; `cache_hit` reduces counted cost as designed.
6. **Retention:** simulate aged events → assert expiry removes raw rows past the window and roll-ups survive.
7. **Isolation/RBAC:** assert `usage:read` default-deny (unauthorized role blocked) and all reads emit audit events.
8. **Coverage:** when implemented (separate approval), maintain the **100% backend coverage gate**.

## 8. Acceptance criteria (for the spec, and later for a dev build)
**Spec acceptance (now):** owner confirms workflows, event/field taxonomy, formulas, privacy/retention limits, and synthetic test plan are correct and sufficient.
**Dev-build acceptance (only if later approved):**
- All §5 metrics computable from recorded events on synthetic data, matching golden numbers.
- Schema rejects any non-enumerated/PII field (negative tests pass).
- `usage:read` enforced default-deny; reads audited; events append-only; retention expiry works.
- AI cost per account + per run computed; operational-result metrics (support time saved, onboarding completion, renewal follow-up effectiveness, workflow success) all derivable.
- 100% coverage maintained; dev-only; staging/production untouched; $0 external spend.

## 9. What a later dev implementation would touch (preview, NOT approved yet)
`[PROPOSED]` a `usage_events` table + Alembic migration (dev), an append helper reusing the audit pattern, a `usage:read` permission + metrics read endpoint, a synthetic-data fixture, and tests. **None of this is built until the owner approves a development-only implementation.**

## 10. Open decisions (→ `DECISIONS_REQUIRED.md`)
Raw-event retention window (default ≤90 days), pseudonymization method for refs, which cohort/attribution method to use for baseline-vs-assisted, token$/model rate assumptions for `est_cost_usd`, and whether to proceed to a dev-only implementation after review.
