# PHASE0_EXECUTIVE_DECISION.md
**Phase 0 — Decisions needed + recommendation.** For the Cauldron Technologies executive owner.

## What Phase 0 confirmed
- **CAUL AI is real and solid** (verified): PostgreSQL SoR, default-deny RBAC, tamper-evident audit, emergency controls, connector contract, 100% test coverage, CI, health/readiness, dashboards. 
- **Everything else is unverified / access-gapped:** Deal Flow OS (public site only), Cauldron App (no access), Cauldron Wars (doesn't exist), $CAUL/XRPL (unverified identity). 
- **Production blocker:** CAUL AI still uses a labeled auth **stub** — real identity (Auth0) must land before any production integration.

## Decisions requested (pick per item)
1. **Proceed to Phase 1 (CAUL AI hardening)?** → If yes, provide staging **Auth0** `DOMAIN` / `CLIENT_ID` / `AUDIENCE` + MFA policy (dossier ready). [Approve / Hold]
2. **Authorize read-only Deal Flow OS audit + staging token** (its own project change)? [Approve / Hold]
3. **Grant access to Cauldron App** for a future audit, or defer? [Grant / Defer]
4. **$CAUL / XRPL:** authorize a *read-only* identity audit + engage legal counsel? (No token ops either way.) [Approve legal+audit / Hold]
5. **Budget envelope** for external vendors (LLM usage, etc.) and who may approve spend? [Set / Hold]
6. **Baseline KPIs:** who provides authoritative numbers for MRR/churn/activation per product? [Owner names]

## Recommendation (lowest-risk path)
- **Approve Phase 1 now** (hardening is self-contained, no live-product risk, unblocks all later phases). Provide Auth0 staging values.
- **Approve Phase 2 discovery** (DealFlow read-only) in parallel — highest value, smallest blast radius.
- **Hold token work (Phases 4–5)** until legal review + XRPL identity audit; start only the *legal engagement* + *read-only identity audit* now if desired.
- **Defer Cauldron App / Wars / future SaaS** until the above are in motion.

## Guardrails reaffirmed
No live-product changes, no deploys, no spend, no credentials, no token ops, no DB changes without your explicit, per-phase approval. Each phase has a mandatory STOP gate.

---
**Awaiting your authorization to proceed. No further execution until you approve a specific next phase.**
