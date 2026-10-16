# LAUNCH_READINESS.md
**CAUL AI — launch-readiness for a smallest-credible paid pilot (owner review).**
**Documentation only. Nothing built, provisioned, priced, connected, or deployed.** All prices/features marked **[HYPOTHESIS]**. Production backend remains **frozen** and **frontend-only**.

> Legend: **[NOW]** verified today · **[PLANNED]** not built · **[HYPOTHESIS]** unvalidated assumption · **[BLOCKER]** must clear before paid launch · **[DECISION]** owner input.

---

## 1. Smallest credible paid pilot (proposed)
- **Target customer [HYPOTHESIS]:** a **single small business** (an existing Cauldron Technologies relationship) that wants **one specific workflow** governed — e.g., an **approval + audit trail for a sensitive operational action** (the capability that is genuinely **[NOW]** in dev).
- **Core pilot workflow [NOW-based]:** capture a proposed action as a *recommendation* → run checks → **human approval** → record immutably in the **tamper-evident audit log** → show it on a simple dashboard. This uses only verified capabilities.
- **Explicitly NOT in the pilot:** external product integrations, client-acquisition automation, AI content generation, $CAUL, voice — all **[PLANNED]**.

## 2. Required product integrations for the pilot
- **Minimum:** none external — the pilot runs entirely inside CAUL AI's own governed workflow (no third-party connection). This keeps it $0-dependency and honest.
- **If the customer needs their data in it [PLANNED, separately approved]:** a **read-only, aggregate-only, authenticated, least-privilege** import — never direct production-DB access, never real PII until a privacy decision is approved.

## 3. Fiat billing assumptions (hypotheses only — no billing enabled)
- Billing currency: **fiat (USD)** only. **No token/$CAUL checkout.**
- Pilot shape **[HYPOTHESIS]:** a short fixed-fee pilot (e.g., a small one-time or monthly pilot fee) — **exact price is an open hypothesis, not set.**
- **No payment processor is connected and none will be** until conditions in §4 are met. No form collects payment details in this phase.

## 4. Conditions that MUST be met before taking any payment
1. **Production is actually functional** — currently it is **frontend-only with DB endpoints 500** → **[BLOCKER]**.
2. **Real authentication** (replace the labeled stub) + MFA → **[BLOCKER]**.
3. **A reachable, isolated production PostgreSQL** (see §5) → **[BLOCKER]**.
4. **Approved release path** (no secret-triggered promotion of unapproved source; identifiable source artifact) → **[BLOCKER]**.
5. A **signed pilot agreement** + validated price (price is a **[HYPOTHESIS]** until agreed).
6. **Legal/privacy review** for handling any customer data; consent + export/deletion in place.
7. A **payment method** (fiat processor) set up under its own approval + limits — **not** in scope now.

## 5. Database & release-readiness (owner blockers)
**Production environment**
- **[BLOCKER]** No dedicated production PostgreSQL exists; production resolves an unreachable `localhost` DB (→ 500s). The app has **no explicit `production` env** (allows only dev/staging; Stage B design proposes `production` + dedicated `PROD_DATABASE_URL`/`PROD_ADMIN_DATABASE_URL` with **no** dev/staging fallback).
- **External PostgreSQL account & cost = OWNER BLOCKER [DECISION].** Per human support findings: Emergent provides **MongoDB by default**; PostgreSQL in production means **Supabase or bring-your-own (external account)**; **no documented $0 / no-new-account production PostgreSQL** exists, and deployment itself carries recurring credit cost. **No vendor selected, no account created, no DB provisioned, no price set.** Owner must choose: **remain frontend-only / evaluate a free external account / consider paid** (see PRODUCTION_READINESS_PLAN §0a).

**Authentication**
- **[BLOCKER]** Current auth is a **labeled stub** ("AUTH STUB — NOT PRODUCTION"); needs a real IdP (Auth0 dossier exists) + MFA before any customer login.

**Backups / restore**
- **[PLANNED]** Automated backups + **verified restore drills** (RPO/RTO) on the chosen prod DB; none exist yet.

**Migrations**
- **[PLANNED]** Gated, manual, approved `alembic upgrade` against a prod admin URL, preceded by schema-only backup + pending-migration manifest; never auto-run on boot. (Note: the usage migration **file** currently ships in the image but is not auto-applied.)

**Health checks**
- **[BLOCKER]** Real `/api/health` + `/api/health/ready` currently **500** in production (DB unreachable + production-guard). The k8s probe hits `/health` (404, non-5xx) so the pipeline passed despite the app being degraded — readiness semantics must be fixed so a broken prod cannot report healthy.

**Release-source controls**
- **[BLOCKER]** Deploys build from the preview pod with **no Git SHA** (image digest only), and a **secret change triggers a rebuild from current preview source** — which currently contains the usage code + shared `usage-retention` cron (both are **live in the current production image**, mounted unconditionally; only a docstring says "DEV-ONLY"). Need: identifiable source artifact per release, manual approval gate, and secret-change decoupled from rebuilds (support requests pending).

## 6. $CAUL
- Treated **only** as a **possible future, optional utility subject to legal review**. **No** token checkout, wallet connection, token discounts, investment language, or value/return claims anywhere.

## 7. Exact owner/platform decisions blocking a paid launch
1. **Production DB path [DECISION/BLOCKER]:** remain frontend-only (current) vs. free external account vs. paid DB — and accept the associated account/cost.
2. **Approve the `production` env + `PROD_*` vars** (Stage B) and the release-path fixes (source pinning + secret-change decoupling) — requires lifting the freeze for a scoped, approved release.
3. **Authentication:** approve replacing the stub with a real IdP + MFA.
4. **Pilot customer + workflow + price [DECISION]:** confirm the single pilot customer, the one workflow, and validate the (currently hypothetical) price.
5. **Contact destination [DECISION]:** confirm a verified pilot-contact address (for the landing CTA) — no PII-storing form.
6. **Legal/privacy review** for any customer data and for $CAUL framing.
7. **Billing:** when conditions met, approve a fiat processor + limits (separate step).

---

**Status:** documentation only; production frozen + frontend-only; no code/DB/secret/cron/deploy/integration/billing change; no real customer data. Nothing proceeds until the owner clears the blockers above and approves a specific, isolated step.
