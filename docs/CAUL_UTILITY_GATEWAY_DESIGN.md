# CAUL_UTILITY_GATEWAY_DESIGN.md
**Phase 0 — $CAUL Utility Gateway design (assumptions + threats).** SEPARATE service. Design only; no token ops, no keys, no legal commitment. Phase 4+ and gated on legal review.

## 1. XRPL asset identity — ASSUMPTIONS TO VERIFY (not inferred from ticker)
issuer address, currency code (hex/3-char), total/circulating supply config, trust-line requirements/authorization, treasury wallet addresses, distribution, any exchange/liquidity claims, freeze/clawback flags, operational constraints. **All UNVERIFIED until an authorized on-chain + ownership audit is done.**

## 2. Core principles (from spec §4)
- Token is an **optional utility** for real services. **No** guaranteed price/$1 target/passive returns/dividends/buybacks messaging.
- Prefer **USD-denominated service catalog**; token quote is transparent, time-limited (expiry, slippage limit, failure handling). Redemption grants **nontransferable off-chain service credits** (NOT a new tradable token).
- **Noncustodial only:** wallet ownership proof + user-signed redemptions. **Never** request seed phrases. **No** hot-wallet keys or signing in any AI agent.
- Entitlements granted only on **confirmed settlement** — never on pending/unconfirmed tx.

## 3. Wallet + redemption flow (noncustodial)
```
User wallet --(ownership challenge: sign nonce)--> Gateway verifies signature
User initiates redemption --> Gateway issues time-limited USD-priced quote (expiry+slippage)
User signs XRPL payment to treasury --> Gateway waits for VALIDATED ledger settlement
On confirmed settlement + idempotency check --> issue off-chain service credits
Credits --> entitlement at product (via product connector, approved policy)
```

## 4. Off-chain ledger (double-entry, reconciled)
States: on-chain tokens, pending redemption, confirmed settlement, issued credits, redeemed credits, expired credits, refunds, liabilities. Enforce idempotency keys + double-entry reconciliation; anti-replay on every tx and quote.

## 5. Rewards / treasury
Eligibility rules, caps, anti-sybil/abuse, appeals, approved treasury budgets. All issuance/treasury movement/policy change = separately approved, tightly controlled procedures. CAUL AI **recommends**; a separate approved policy service enforces.

## 6. Threat model (top)
seed-phrase phishing (mitigate: never request; sign-nonce only) · replay of settlement (idempotency + ledger-validated tx hash) · quote manipulation/slippage (expiry + bounds) · entitlement on unconfirmed tx (require VALIDATED) · sybil reward farming (caps + anti-abuse) · key exposure (no keys in agents) · regulatory misclassification (legal review first) · treasury drain (multi-control + budgets).

## 7. Hard prerequisites
Legal/regulatory review (securities, money transmission, consumer protection, privacy, tax, accounting, gaming, platform rules) + XRPL identity audit + budget approval **before** any production utility. Testnet/sandbox prototype only until then.
