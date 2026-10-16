# LANDING_PAGE_PREVIEW_SPEC.md
**CAUL AI — private landing-page design + content specification for caul.ai (owner review).**
**Specification ONLY. No application files edited, no page built, no preview published, no private preview URL created.** Reason: this environment is the **shared preview source** that a secret-change redeploy rebuilds into production; isolation could **not** be confirmed, so per the owner's instruction I deliver a design/content spec only.

> Legend: **[NOW]** implemented & verified today · **[PLANNED]** not implemented / not verified · **[DECISION]** owner input needed. Nothing on the page may claim a capability that is not **[NOW]**.

---

## 0. Isolation statement
- **Not isolated.** `/app` here = the preview pod feeding `caul-impl-gate` production; `REACT_APP_BACKEND_URL` is the preview URL; a `secret_change` redeploy rebuilds this source. No separate project/copy/isolated preview is available.
- **Consequence:** no landing-page code was written and no preview was published. This document is the deliverable. Building the page later must happen in an **isolated** project/branch (see §7) so it can never be promoted to production by a secret-triggered rebuild.

## 1. Verified reality (grounding — do not overclaim)
- **[NOW, dev only]** A **governance Command Center** exists and is tested (141 backend tests, 100% coverage in dev): default-deny RBAC, recommendation→approval workflow with safeguards, **tamper-evident hash-chained audit**, emergency pause/revoke/rollback (stub paths), dashboards/analytics, saved audit filters, usage measurement (dev-only).
- **[PLANNED / NOT VERIFIED]** Real authentication (current is a **labeled stub**, "AUTH STUB — NOT PRODUCTION"); any external product integrations (Deal Flow OS / Cauldron App); client-management / Growth Engine (design only); customer results/metrics; production security posture; $CAUL utility; voice assistant.
- **Production status:** frontend-only; backend DB-backed endpoints currently **500** (no reachable prod DB). So nothing production-functional can be promised.

## 2. Positioning & honest message
- **Who:** CAUL AI, a **business AI product from Cauldron Technologies, Inc.**
- **One-liner (truthful):** "A private, governed control plane for business operations — approvals, recommendations, and a tamper-evident audit trail." (Avoid "secure/compliant/enterprise-grade" as bare claims; describe the *mechanism* — e.g., "default-deny role-based access and a tamper-evident audit log" — only because those are **[NOW]** in dev.)
- **Available-now vs planned must be explicit on the page** (see §4 "Status" treatment).

## 3. Page structure (content spec — copy is drafted, not published)
1. **Hero:** product name + the one-liner above; a single honest primary CTA (see §5). A small badge: "In development — private preview."
2. **What it does today [NOW]:** 3–4 cards describing only verified dev capabilities — *Role-based access (default-deny)*, *Approval workflow with safeguards*, *Tamper-evident audit trail*, *Operational dashboard*. Each phrased as a mechanism, not a guarantee.
3. **On the roadmap [PLANNED]:** clearly separated section — *Production sign-in & MFA*, *Client-acquisition assistant (design stage)*, *Product integrations (read-only, aggregate, when approved)*, *$CAUL optional utility (subject to legal review)*. Labeled "Planned — not yet available."
4. **How it works:** the governed flow — *recommendation → checks → human approval → action → audit*. (Matches the real model.)
5. **About Cauldron Technologies:** factual company blurb; link to cauldrontech.com (external link only; no data coupling).
6. **Footer:** copyright; "Private preview — not a public release"; no tracking/analytics.

## 4. "Now vs planned" treatment
- Every roadmap item carries a visible **"Planned"** tag; every live item a **"Available in preview"** tag.
- No customer logos, testimonials, result numbers, uptime/security certifications, or integration claims (none are verified).

## 5. Primary CTA — "Request a pilot" (conditional)
- **Constraint:** include a working CTA only if there is an **existing, verified contact destination**. **None exists** in this app (no contact/pilot/lead endpoint; no verified public inbox confirmed).
- **Spec decision:** render "Request a pilot" as a **`mailto:` link to an owner-confirmed Cauldron Technologies address** — **[DECISION: provide/confirm the address]**. A `mailto:` stores nothing and receives nothing on our side; it simply opens the visitor's email client.
- **Do NOT** build a form that stores personal information, and do **not** imply submissions are received/tracked. Until the owner confirms an address, show the CTA as **"Request a pilot — coming soon"** (disabled), with a note: *blocked on a confirmed contact destination.*

## 6. Customer-login link (conditional)
- **Constraint:** include a login link only if it connects to an **existing, verified** auth flow.
- **Reality:** the auth flow is a **labeled stub** ("AUTH STUB — NOT PRODUCTION"), and **production login currently returns 500**. It is **not** a verified production auth flow.
- **Spec decision:** show login as a **clearly labeled "Customer sign-in — coming soon"** item (not a live link).
- **What must be completed before a real login link can ship:** (a) replace the stub with a real IdP (e.g., the Auth0 dossier) + MFA; (b) a reachable **production database** (current prod DB is unreachable → 500s); (c) the explicit `production` env + guards (Stage B); (d) a non-secret-triggered, approved release carrying that code; (e) verification that `/api/auth/login` returns 200 in production.

## 7. If/when the owner approves building the page (future, isolated only)
- Build in an **isolated project/branch** that is **not** the production-bound preview source, so a secret-change redeploy cannot promote it.
- Keep it a **static, unauthenticated** marketing page: no tracking, no forms storing PII, no token/wallet/checkout, no investment language, no claims beyond §1 **[NOW]** items.
- Publishing is a **separate owner approval** after a factual/brand/privacy/rights review.

## 8. Prohibited on this page (explicit)
No token checkout, wallet connection, token discounts, investment language, or claims about $CAUL value/returns ($CAUL is only a *possible future, optional utility subject to legal review*). No unverified capability, integration, client-management, customer-results, or security claims. No real customer data.
