# MONETIZATION_STRATEGY.md
**CAUL AI — monetization strategy: internal portfolio use vs. future external SaaS (owner-review draft).**
**Strategy document only. No billing implemented, no payments collected, no live pricing changed, no production systems modified.** All figures are **hypotheses to validate**.

> Legend: **[EXISTS]** · **[PROPOSED]** · **[HYPOTHESIS]** value to validate · **[LEGAL]** counsel review required.

---

## 1. Thesis
Make CAUL AI **useful inside Cauldron first**, prove the results and unit economics, then sell a **standalone external SaaS** version once validated. SaaS revenue is billed in **fiat by default**; $CAUL is only an **optional, counsel-reviewed utility** for specific product functions — never required for ordinary access, and never marketed as an investment.

## 2. Two postures compared
| Dimension | Internal portfolio use (now) | Future external SaaS (after validation) |
|---|---|---|
| Buyer | Cauldron Technologies itself | Outside businesses (SMB → mid-market) |
| Value captured | Lower support cost, better onboarding/retention, more conversions in Cauldron App / Deal Flow OS / future products | Direct subscription + usage + add-on revenue |
| Revenue recognition | Indirect (shows up in each product's subscriptions/transactions) | Direct CAUL AI ARR |
| Risk | Low — no external commitments | Medium — support, SLAs, multi-tenant isolation, billing ops |
| Prerequisite | Current control-plane [EXISTS] | Real IdP, multi-tenant isolation, billing integration, pricing validated [PROPOSED] |

## 3. Revenue streams (portfolio of options)
1. **CAUL AI SaaS plans** — monthly subscription for client management, support triage, reporting, and approved workflow automation.
2. **Paid add-ons** — advanced analytics, branded portals, extra integrations, higher automation limits.
3. **Usage-based billing** — a set amount of AI usage included per plan; metered overage beyond it (hybrid subscription + metered).
4. **Portfolio product revenue** — CAUL AI improves onboarding/retention/sales inside Cauldron App, Deal Flow OS, and future products; revenue accrues through those products.
5. **Optional $CAUL utility** — allow $CAUL for selected digital features, rewards, or discounts, with a fiat/non-token path always available. **[LEGAL]** review of design *and marketing* required; SEC crypto-asset FAQs are staff guidance, not binding law.

## 4. Firewall between SaaS revenue and the token
Keep CAUL AI subscription revenue **separate** from $CAUL's price or trading activity. **Do not** promise token appreciation, returns, or guaranteed income. Token utility, if any, is a convenience/benefit for specific functions — priced transparently against a USD catalog.

## 5. Customer segments (external SaaS) [HYPOTHESIS]
- **Solo / micro-business** — single operator, light automation, self-serve.
- **SMB (growth)** — a small team doing support + onboarding + renewals; wants analytics + integrations.
- **Mid-market** — multiple seats/teams, branded portal, higher automation + usage, security review.
- **Portfolio-internal** — Cauldron product teams (treated as an internal "tenant", cost-allocated, not billed externally).

## 6. Data-use commitments (carried from privacy spec)
Clearly explain how client data is used. **Do not** reuse one product's customer data to train AI or market another product without proper notice and permission. Tenant/product isolation enforced server-side. **[LEGAL]** for consent language.

## 7. Recommended order
1. Use CAUL AI internally — support, onboarding, renewal follow-up, cross-product reporting.
2. Measure results + operating costs — support time saved, renewal rates, conversions, AI cost per account (see `COST_AND_UNIT_ECONOMICS_MODEL.md`).
3. Pilot a paid external plan with a small group — monthly base + clear usage limits (see `PRICING_MODEL_DRAFT.md`).
4. Add $CAUL utility only after core pricing, user value, and legal review are settled.

## 8. Boundaries (unchanged)
No billing implementation, no payment collection, no live pricing change, no production changes, $0 spend, separate dev/staging — unless the owner explicitly approves otherwise in writing. Validation precedes any build (see `MONETIZATION_VALIDATION_PLAN.md`).
