# PRICING_MODEL_DRAFT.md
**CAUL AI — draft pricing model (owner-review hypotheses).**
**Draft only. No billing built, no payments collected, no live pricing changed.** **Every price, limit, and ratio below is a `[HYPOTHESIS]` to validate — not a committed price.**

> Default billing currency: **fiat (USD)**. $CAUL appears only as an optional, counsel-reviewed discount/benefit path, never required. **[LEGAL]** review of any token pricing + marketing.

---

## 1. Packaging shape
Hybrid **subscription + included usage + metered overage + paid add-ons**. "Usage" = AI work units (defined in `COST_AND_UNIT_ECONOMICS_MODEL.md` §2) so overages map to real cost.

## 2. Draft tiers (ALL VALUES = HYPOTHESES)
| Tier | Target segment | Monthly base `[HYPOTHESIS]` | Seats incl. | Included AI usage/mo `[HYPOTHESIS]` | Key capabilities |
|---|---|---|---|---|---|
| **Starter** | Solo / micro | $49 | 1 | 1,000 work units | Client list, support triage, basic reporting, email drafts (human-approved) |
| **Growth** | SMB | $199 | 5 | 6,000 work units | + onboarding checklists, renewal reminders, feedback analysis, 3 integrations |
| **Scale** | Mid-market | $699 | 20 | 25,000 work units | + branded portal, advanced analytics, higher automation limits, priority support |
| **Enterprise** | Custom | Custom | Custom | Custom | + SSO, security review, custom retention, dedicated environment, SLA |
| **Portfolio-internal** | Cauldron teams | Cost-allocated (not external revenue) | n/a | Pooled | Full internal use; charged as internal cost, not billed |

## 3. Metered overage (ALL VALUES = HYPOTHESES)
- Overage beyond included usage: **$X per 1,000 additional work units** `[HYPOTHESIS]`, tiered down with volume.
- Soft cap + alert at 80% / 100% of included usage; hard cap optional per tenant to prevent bill shock.
- Extra seats: **$Y/seat/mo** `[HYPOTHESIS]` above included seats.

## 4. Paid add-ons (à la carte) [HYPOTHESIS]
- Advanced analytics pack · Branded/white-label portal · Premium integrations (per connector) · Higher automation limits · Extended data retention · Additional environments.
- Priced as monthly uplift or one-time + monthly, validated separately.

## 5. Optional $CAUL utility pricing [PROPOSED, LEGAL-gated]
- Catalog priced in **USD**; $CAUL may be accepted for **selected** digital features/rewards/discounts at a transparent, time-limited quote.
- A **fiat/non-token path is always available** for the same feature.
- No token price promise, no appreciation/return messaging. Design + marketing reviewed by counsel before any launch.

## 6. Discounts & commercial levers [HYPOTHESIS]
Annual prepay discount (e.g., ~2 months free) · nonprofit/early-adopter pilot pricing · usage-commit discounts · partner/referral credits. All validated, not committed.

## 7. Guardrails on pricing claims
- Prices are hypotheses until validated against willingness-to-pay + unit economics (gross margin target in cost model).
- No implementation of billing, no Stripe/PSP wiring, no live price change as part of this work.
- When validated, propose a billing integration **separately** with its own approval + security review.

## 8. Open pricing decisions (→ `DECISIONS_REQUIRED.md`)
Base prices, included-usage amounts, overage rate, seat price, add-on prices, annual-discount %, pilot pricing, and whether $CAUL discount is in scope for the first external release.
