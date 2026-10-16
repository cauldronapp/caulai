# CLIENT_OPERATIONS_AND_PRIVACY_SPEC.md
**CAUL AI client-operations layer across the product portfolio — identity, privacy, isolation (Milestone 0 design).**
**Design only. No production data accessed, no cross-product data movement, $0 spend.**

> Legend: **[EXISTS]** · **[PROPOSED]** · **[ASSUMPTION]** · **[DECISION]** · **[LEGAL]**.

---

## 1. Purpose
Let company staff (and bounded AI workflows) run portfolio-wide **client operations**: lead intake, onboarding checklists, support triage, renewal reminders, product-usage summaries, feedback analysis, suggested follow-ups — **without** merging customer populations or crossing tenant/product boundaries.

## 2. Two distinct populations — never merged
- **Business customers** of Cauldron Technologies (e.g., SaaS account owners / tenants).
- **End users** of individual products (e.g., Cauldron App members, Cauldron Wars players).

These are **separate record types** with separate consent, ownership, and communication preferences. A single person may appear in both with **linked-but-not-merged** references. Do **not** create one undifferentiated customer record.

## 3. Canonical identity model [PROPOSED]
```
Party (global, minimal)            # a real-world person/org, minimal attributes
  ├─ BusinessCustomer(tenant_id)   # SoR: billing/CRM system [DECISION]
  └─ ProductEndUser(product_id,    # SoR: each product's own user store
        product_user_id)
IdentityLink(party_id, ref, confidence, basis, consent_flag)  # safe matching
```
- **Source of truth [DECISION]:** each product owns its own end-user records; the business-customer SoR is the billing/CRM system (to be named). CAUL AI stores **references + aggregates**, not a copy of the master records, unless explicitly approved.
- **Duplicate matching:** probabilistic match with a confidence score and a recorded basis; **no auto-merge** of records above the boundary — links only, reversible, audited. High-confidence merges of *references* require review. [DECISION on match thresholds]
- **Data ownership, consent & comms preferences, retention/deletion:** tracked per population; honored on every workflow.

## 4. Least-privilege product adapters & server-side isolation [PROPOSED]
- Each product connects via a **least-privilege adapter** (see `PRODUCT_ADAPTER_CONTRACT.md`) with a scoped, read-only service identity.
- **Every request** enforces tenant **and** product boundaries **server-side** (default-deny; reuses existing `require_permission` + adds `tenant_id` / `product_id` scoping). A staff member or AI workflow may access **only** the records authorized for its role and purpose.
- **Never** expose one customer's info to another customer, tenant, or unrelated product.
- **No cross-product model training/improvement** using another product's customer data without notice, permission, contracts, and **[LEGAL]** review.

## 5. Roles & auditable access [EXISTS → extend]
- Reuse CAUL AI RBAC (default-deny). Add client-ops permissions, e.g. `client:read`, `client:list`, `client:note:create`, `client:comms:draft` (draft only), each scoped by tenant/product.
- Every access and action writes a tamper-evident audit event (who, what record, purpose, result).

## 6. Data protection [PROPOSED]
- **Data minimization:** collect only what a workflow needs; avoid unnecessary sensitive personal data.
- **Encryption:** TLS in transit; at-rest encryption for stored references/aggregates; field-level protection for any sensitive attributes. [DECISION on provider]
- **Secrets management:** adapter keys in the approved secret store (names only); never in source or chat.
- **Retention limits:** per-population retention windows with automated expiry.
- **Incident response:** documented runbook; breach notification path. **[LEGAL]**
- **Customer export/deletion workflows:** per-population export + deletion (DSAR-style), propagated to products that own the data, audited. **[LEGAL]** for jurisdiction-specific obligations.

## 7. What CAUL AI stores vs. references [DECISION]
Default: CAUL AI stores **aggregates + minimal references + workflow state (tasks, notes, approvals)**. It does **not** replicate full product datasets. Any proposal to cache fuller records requires owner approval + a retention/consent review.

## 8. Open privacy decisions
- Name the business-customer SoR (CRM/billing). [DECISION]
- Lawful basis + consent capture per population and per communication type. [LEGAL][DECISION]
- Cross-border data handling for each product's user base. [LEGAL]
- Match-confidence thresholds and human-review policy for identity links. [DECISION]
