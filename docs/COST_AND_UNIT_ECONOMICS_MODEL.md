# COST_AND_UNIT_ECONOMICS_MODEL.md
**CAUL AI — cost & unit-economics model (owner-review draft).**
**Model only. No spend authorized, no vendors engaged, no billing built.** **All figures = `[HYPOTHESIS]` to validate.**

> Legend: **[EXISTS]** · **[PROPOSED]** · **[HYPOTHESIS]** · **[LEGAL]**.

---

## 1. Costs we must track
**Direct / variable (scale with usage):**
- LLM / AI usage (tokens in+out per workflow) — the dominant variable cost.
- Any metered 3rd-party APIs (email, integrations) when enabled.
- Data egress / storage growth per tenant.

**Platform / semi-fixed:**
- Hosting/compute for the control plane + per-tenant overhead.
- PostgreSQL storage + backups.
- Identity provider (Auth0) tier when production auth lands [PROPOSED].
- Observability/logging, error tracking.
- Security/compliance tooling + periodic audits/reviews **[LEGAL]** for token/privacy.

**People / GTM (for external SaaS):**
- Support time per account, onboarding effort, sales/marketing CAC.

## 2. Usage unit definition ("work unit")
Define **1 work unit** = a normalized AI operation (e.g., one triage classification, one summary, one drafted message) mapped to an **estimated token cost** so overage pricing tracks real cost. Maintain a conversion table per workflow. `[HYPOTHESIS: token-per-unit averages]`

## 3. AI cost per account (method)
`AI cost/account = Σ(work units by type × avg token cost/type × model $/token)`.
Track **per-account** and **per-tier** monthly. Watch the ratio **AI cost ÷ plan price** (target well under the gross-margin ceiling, e.g. keep variable cost ≤ ~20–30% of plan price `[HYPOTHESIS]`).

## 4. Unit-economics metrics to compute (once real data exists)
- **Gross margin %** per tier = (price − variable cost) ÷ price. Target `[HYPOTHESIS: ≥70–80%]`.
- **Contribution margin** per account after support.
- **CAC** and **CAC payback** (months) for external SaaS.
- **LTV** and **LTV:CAC** `[HYPOTHESIS: ≥3:1]`.
- **Net revenue retention** (expansion − churn).
- **Usage distribution** — % of accounts exceeding included usage (sizing overage revenue + bill-shock risk).

## 5. Internal-value metrics (portfolio use, no external revenue)
- Support time saved (hours × loaded cost).
- Renewal-rate lift, onboarding completion lift, conversion lift in Cauldron App / Deal Flow OS.
- AI cost per internal account vs. value delivered — this proves ROI before any external pricing.

## 6. Cost-control levers [PROPOSED]
- Model tiering (cheaper models for routine classification; stronger models only where needed).
- Caching + retrieval to cut repeat token spend.
- Per-tenant usage caps + alerts (from pricing model).
- Budget envelope + kill switch on AI actions [EXISTS pattern].

## 7. Separation of $0 vs. paid
- **$0 now:** this model + internal measurement using existing infrastructure.
- **Paid later (needs budget approval):** production LLM usage, Auth0 tier, production infra beyond the current container, security/legal reviews, billing/PSP integration. Itemized in `DECISIONS_REQUIRED.md` §F.

## 8. Open cost decisions
Target gross-margin ceiling for variable cost, token-per-work-unit assumptions, which models map to which workflows, internal cost-allocation method for portfolio teams, and who owns the budget/approves spend.
