# SECURITY_PRIVACY_LEGAL_RISK_REGISTER.md
**Phase 0 — Risks, mitigations, external-counsel decisions.**

## Legend: L=Likelihood, I=Impact (H/M/L)

| # | Risk | L | I | Mitigation | Owner / gate |
|---|---|---|---|---|---|
| R1 | Stub auth mistaken for production identity | M | H | Keep "STUB" labels; wire Auth0 (dossier) + close Phase 1A gates before any production integration | Eng + exec |
| R2 | Cross-product / cross-tenant data leakage | M | H | Aggregate-only, tenant-scoped tokens, schema validation rejecting PII, default-deny RBAC | Eng |
| R3 | Customer PII / financial docs reaching corporate growth agents | M | H | Event taxonomy with approved fields only; no raw seller/property/customer docs; purpose limitation | Legal + Eng |
| R4 | $CAUL treated/marketed as investment (securities/MSB exposure) | M | H | USD service catalog; optional-utility only; NO price/return claims; **counsel review before production** | **External counsel** |
| R5 | Wallet key compromise / seed phishing | L | H | Noncustodial, sign-nonce only, never request seed, no keys in agents | Eng + Security |
| R6 | Entitlement on unconfirmed/duplicated tx | M | H | Require VALIDATED ledger settlement + idempotency + double-entry reconciliation | Eng |
| R7 | Prompt injection via external content | M | M | Model-data boundary, allowlisted tools, output review, no secrets in prompts | Eng |
| R8 | Connector outage harming a product | L | H | Connector failure must never block product login/booking/payments; disabled-by-default; circuit breaker | Eng + product owners |
| R9 | Unauthorized spend / publish / outreach | M | M | Human-in-the-loop gates; outreach-law + platform-ToS compliance | Exec + Legal |
| R10 | Regulatory: money transmission / consumer protection / tax / gaming | M | H | Jurisdictional review before token utility; gaming review before Cauldron Wars token use | **External counsel** |
| R11 | Audit tamper (DB-owner) | L | M | Tamper-evident chain (documented residual); off-box export (proposed) | Eng |
| R12 | Accessibility/security regressions on user-facing changes | M | M | Mandatory a11y + security regression tests pre-release | Eng |
| R13 | Vendor/cost sprawl (LLM, hosting, token infra) | M | M | Document cost + permission before use; budget approval | Exec |

## External-counsel decisions required BEFORE Phase 4/5 (token)
Securities classification · money-transmission/MSB licensing · consumer-protection/refunds · privacy (GDPR/CCPA) · tax & accounting treatment of credits/liabilities · gaming/sweepstakes (for Wars) · platform ToS (Apple/Google/ad networks). **Utility labeling does not determine legal status.**

## Privacy by design
Encryption in transit/at rest, least privilege, data minimization, retention + owner per metric, lawful purpose for any cross-product data, backups + tested restore, monitoring + incident response + rollback playbooks.
