# AGENT_PERMISSIONS_AND_APPROVALS.md
**Phase 0 — Agent catalog → tools, scopes, approval matrix, audit rules.** Design only; no agents built yet.

## 1. Principles
Central permissions registry (extends existing Postgres RBAC), scope-limited credentials, approved tool allowlists, immutable audit trail per action, human-in-the-loop gates, emergency disable per agent. Agents are **read-only + draft-only** initially. Model-data boundary + prompt-injection defenses required before connecting any external content.

## 2. Catalog → default scope + approval gate
| Agent | Allowed (initial) | Must NOT | Approval gate |
|---|---|---|---|
| Corporate Growth | read aggregates; draft positioning/budgets | commit spend | exec approve budgets |
| Marketing Content | draft ads/SEO/copy/scripts | auto-publish | per-channel publish approval |
| Acquisition | permitted prospect research, outreach drafts | scraping, unsolicited bulk msg | human approve each send |
| Revenue Intelligence | reconciled MRR/ARR/churn/CAC/LTV w/ provenance+confidence | fabricate numbers | source + reconciliation required |
| Customer Success | onboarding/retention insights, approved workflows | act on customer accounts | human approve account actions |
| Product Intelligence | feedback clustering, PRD + staged/tested code proposals | unilateral prod release | PR review + CI gates |
| Utility Intelligence | redemption/credit economics analysis | autonomous policy change | policy service + approval |
| Security/Risk | read approved logs, anomaly alerts | bypass access controls | n/a (read-only) |
| Treasury Reporting | read-only wallet + reconciliation reports | custody/sign tx | n/a (read-only) |

## 3. Approval matrix (who authorizes)
- Spend / publish / outreach / customer-account actions → **human (role-appropriate) approval**, logged.
- Token issuance / treasury movement / tokenomics / fees / billing / access-rights → **executive owner**, separate controlled procedure, never agent-initiated.
- Code to production → PR + CI (100% coverage gate) + reviewer; agents only propose.

## 4. Mapping to existing CAUL AI
Each agent = a service identity with explicit Postgres permissions (default-deny). New permissions e.g. `agent:growth:draft`, `metrics:read`, `agent:security:read`. Every agent action appends an `audit_events` row (actor = agent identity). Emergency pause scope `agent:<name>` disables an agent instantly.

## 5. Audit rules
Immutable (INSERT-only) chain already enforced. Log: actor, tool, inputs hash, output hash, approval ref, timestamp. No raw customer financial documents or PII in logs or model prompts for corporate growth analytics.
