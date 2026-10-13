# PHASED_IMPLEMENTATION_PLAN.md
**Phase 0 — Milestones, estimates, prerequisites, explicit STOP gates.** Estimates are rough engineering ranges, not commitments; each phase starts only after its specific approval.

| Phase | Outcome | Key prerequisites | Rough estimate | STOP gate (acceptance) |
|---|---|---|---|---|
| **0 (now)** | This discovery + 8 docs | CAUL AI access (have it) | — (done) | Exec reviews `PHASE0_EXECUTIVE_DECISION.md` |
| **1** CAUL AI hardening | Production-grade identity (Auth0), re-verified RBAC/audit/a11y/secrets/CI/backup-restore/rollback | Auth0 staging values + MFA policy; close Phase 1A gates | ~1–2 wks | tests + threat model + audit evidence + sign-off |
| **2** Deal Flow OS read-only | Connector in isolated staging; minimal approved DealFlow API; disabled-by-default | Authorized DealFlow audit + scoped staging token; both-owner sign-off | ~1–2 wks | reconciled metrics, zero leakage, zero uptime impact, tested kill switch |
| **3** Multi-product growth intel | Exec dashboards + draft-only agents on approved aggregates | Baseline KPIs agreed; agent permission registry | ~2–3 wks | perf vs baselines; human gates for spend/publish/outreach |
| **4** Utility Gateway prototype | Testnet/sandbox noncustodial wallet + quote/credit/reconciliation | **Legal review** + XRPL identity audit + budget | ~2–4 wks | security + abuse + reconciliation + regulatory sign-off |
| **5** Single-product token pilot | One low-risk opt-in credit/discount use case | Validated demand; support/refund policy; caps | ~2–3 wks | unit economics, fraud controls, independent approvals |
| **6** Customer AI + ecosystem | Per-product premium AI + optional gateway; evaluate Wars/SaaS | Per-product validation, consent, pricing | per product | separate per-product launch gates |

## Recommended lowest-risk sequence
1. **Phase 1 first** (unblocks everything; closes the stub-identity gap). 
2. **Phase 2** (read-only DealFlow) — highest value, lowest blast radius, reuses existing connector primitives. 
3. **Phase 3** growth dashboards once ≥1 real product feed exists. 
4. Token work (4→5) only after legal + XRPL verification; keep strictly isolated. 
5. Wars/future SaaS last.

## Cross-cutting prerequisites
Versioned OpenAPI per connector; short-lived/least-privilege service creds + rotation/revocation/replay protection; signed webhooks (if used); metric dictionary w/ source+refresh+reconciliation; observability (tracing/error budgets/latency/incident playbooks); a11y+security regression gates; documented cost+permission per vendor.
