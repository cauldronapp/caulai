# MONETIZATION_VALIDATION_PLAN.md
**CAUL AI — monetization validation plan (owner-review draft).**
**Validation design only. No billing, no payment collection, no live pricing change, no production changes.** Treats all prices as **hypotheses to validate before any build**.

> Legend: **[HYPOTHESIS]** · **[PROPOSED]** · **[LEGAL]** · **[DECISION]**.

---

## 1. Goal
Prove, with evidence, that CAUL AI (a) delivers measurable internal value and (b) has an external SaaS offer with healthy unit economics — **before** implementing any billing or changing pricing.

## 2. Stage 1 — Internal value proof (lowest risk, $0 external)
- **Instrumentation:** measured via the dev-only, $0 `USAGE_INSTRUMENTATION_SPEC.md` (event taxonomy, metric formulas, privacy/retention limits, synthetic-data test plan). Spec only until owner approves a dev-only implementation.
- **Hypotheses:** CAUL AI reduces support time, lifts onboarding completion, lifts renewals, and improves cross-product conversion at acceptable AI cost/account.
- **Method:** instrument internal usage; baseline vs. CAUL-assisted cohorts where feasible.
- **Metrics:** support minutes/ticket, onboarding completion %, renewal rate, conversion lift, AI cost/account (from cost model).
- **Acceptance:** clear positive ROI (value > AI + ops cost) on at least support + renewals.

## 3. Stage 2 — Willingness-to-pay & packaging research (no billing)
- **Method:** structured interviews + simple pricing surveys (e.g., Van Westendorp-style price sensitivity) with target segments; landing-page / "fake-door" interest tests with **no payment capture**.
- **Hypotheses tested:** tier shape, base-price ranges, included-usage levels, add-on appeal, overage tolerance.
- **Acceptance:** converging price ranges per segment + top-ranked add-ons.

## 4. Stage 3 — Non-production paid pilot (small external cohort)
- **Design:** a handful of external businesses on a **monthly base + clear usage limits**; pricing as a time-boxed pilot. **[DECISION]** on whether to collect payment at pilot (if yes, billing is a *separate, approved* integration with its own security review — not part of this work).
- **Metrics:** activation, usage vs. included limits, overage incidence, retention, support load, gross margin per account, qualitative value.
- **Acceptance:** target activation + retention + gross margin `[HYPOTHESIS]`; overage behavior matches the model.

## 5. Stage 4 — $CAUL utility validation (gated, last)
- Only after core pricing + value + **[LEGAL]** review are settled.
- Validate demand for optional token-based discount/benefit **with a fiat path always available**; test messaging with counsel review.
- **Acceptance:** counsel sign-off on design + marketing; demonstrated opt-in demand without pressuring token purchase.

## 6. Decision gates
1. Stage 1 ROI proven → proceed to pricing research.
2. Pricing ranges converge → design pilot.
3. Pilot hits unit-economics targets → propose (separately) a billing integration + external launch.
4. Core offer validated + legal cleared → consider $CAUL utility.

## 7. What this plan explicitly does NOT do
No billing implementation, no PSP wiring, no payment collection, no live pricing change, no production modification, $0 external spend. Any build that follows is proposed separately with its own approval + security review.

## 8. Open validation decisions (→ `DECISIONS_REQUIRED.md`)
Which internal workflows to instrument first; target segments + recruiting for research; whether the pilot collects real payment; unit-economics thresholds that authorize an external launch; and timing for the $CAUL utility review.
