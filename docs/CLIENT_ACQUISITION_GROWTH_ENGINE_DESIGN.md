# CLIENT_ACQUISITION_GROWTH_ENGINE_DESIGN.md
**CAUL AI — Client Acquisition Growth Engine (internal dogfooding) — design brief (owner review).**
**Planning & documentation ONLY. Nothing built or changed.** No code, DB, migration, schema, infra, env var, credential, permission, project-setting, or production change. **$0 spend**, no accounts/social/analytics/ad/email/3P connections, no contact with `cauldrontech.com`/Deal Flow OS/Cauldron App or any production DB, **synthetic examples only**. No phase is marked accepted.

> Legend: **[EXISTS]** today · **[PROPOSED]** future, not built · **[DECISION]** needs Sean's written approval · **[OOS]** out of scope now.

---

## 1. Current phase & approval-gate status (incl. discrepancy)
**Discrepancy found — reported, not resolved by me:**
- **Prior project notes / artifacts** report **Phase 1A foundation as complete** and even include a `PHASE_1A_ACCEPTANCE_CERTIFICATE.pdf`, `PHASE_1A_COMPLETION_REPORT.md`, and `PHASE_1A_FOUNDATION_COMPLETION_REPORT.md` (and the app does pass 131 backend tests at 100% coverage in **dev**).
- **The latest master ecosystem specification** states the **currently authorized stage is Milestone 0 / Phase 0 — discovery & documentation only**, and the ecosystem `DECISIONS_REQUIRED.md` still lists open executive decisions with **no written authorization to implement** beyond documentation.
- **These conflict.** A completion report / certificate existing in `/app/docs` is **not** the same as a recorded, written owner acceptance that authorizes the *next* phase.

**What I will NOT infer:** I do **not** treat Phase 1A as formally accepted, and I do **not** treat any implementation as authorized. 

**Current written approval gate (as I read it):** the authorized activity is **Phase 0 / Milestone 0 — documentation only**. Everything beyond (Auth0 go-live, ecosystem integrations, the usage layer in any deployed env, and this Growth Engine) sits **behind an uncleared gate** pending Sean's explicit written approval. **Open blocker for Sean:** confirm in writing whether Phase 1A is formally accepted and which stage is authorized next. Until then, this Growth Engine remains **Phase 0 design only**.

> Related production caveat (unchanged): production currently serves frontend only; DB-backed features are UNAVAILABLE (dangling `localhost` Postgres), and a production release freeze is in place. None of that changes here.

## 2. Proposed scope & explicit out-of-scope (Growth Engine MVP)
**In-scope (future MVP, isolated dev only, after acceptance + written approval):**
- Two **separate** campaign tracks with their own briefs/audiences/offers/CTAs:
  1. **Founders** needing a SaaS product / web app / mobile app / product integration (Deal Flow OS usable **only** as a build example to the extent its *published, verified* details support the claim).
  2. **Small businesses** wanting to automate a specific workflow with AI/business software.
- Campaign planner, content calendar / creative studio (drafts only), approval queue, **synthetic** lead pipeline, executive dashboard + weekly summary.
- Draft generation: social posts, short-video scripts, static-ad concepts, personalized outreach **drafts** (never sent).
- Recommendation engine that suggests experiments from **approved, available** info only.

**Out of scope [OOS] (now and until separately approved):**
- Any real publishing, scheduling, outreach, advertising, or spend; any budget change; any autonomous action.
- Any connection to social/email/analytics/ad platforms or third-party APIs.
- Marketing for **Cauldron App, $CAUL, CAUL AI-as-external-product, or Cauldron Wars** — these are **separate products/audiences** and must not be blended into these client-services campaigns.
- Any real leads/PII/message content; any live measurement/analytics instrumentation.
- Any coupling to another product's production database.

## 3. User roles & permissions (Sean retains decision authority)
Reuses CAUL AI's **default-deny RBAC** [EXISTS]; new **proposed** permissions (not created):
- **ExecOwner (Sean)** — sole approval authority for public claims, publishing, outreach, partnerships, ads, and any budget/limit. Final say on every gate.
- **Growth Manager [PROPOSED role]** — create/edit campaign briefs + drafts; submit to approval; cannot approve own high-risk items.
- **Content Drafter [PROPOSED]** — create drafts only; no approval, no pipeline edits beyond notes.
- **Reviewer (Security/Compliance/Brand) [PROPOSED]** — runs factual/brand/privacy/rights/policy checks; can reject/annotate; cannot self-approve publication.
- **Analyst/Auditor [EXISTS]** — read-only dashboard/metrics/audit.
- **Agent Service Identity [EXISTS]** — may draft/classify/recommend only; **never** approves, publishes, sends, or changes budgets.
Proposed permission names (illustrative, not implemented): `campaign:read|create|update`, `content:draft`, `content:submit`, `growth:approve` (ExecOwner/Reviewer), `lead:read|update`, `growth:dashboard:read`. **`growth:approve` is high-risk** (human-only, no service identity).

## 4. Proposed screens / modules
1. **Campaign Planner** — two separate tracks; per-track brief, audience definition, offer, CTA, channel intent, status.
2. **Content Calendar / Creative Studio** — LinkedIn-first calendar for Sean with draft **formats**: product demonstrations, practical guidance, build stories; plus post/short-video/static-ad/outreach **drafts**. Notes how approved content could *later* be adapted to other channels (adaptation drafted, never auto-published).
3. **Approval Queue** — every public-facing claim/post/outreach/partnership/ad passes **factual, brand, privacy, rights, policy** checks → human approval; records approver, decision, timestamp, and a content digest (tamper-evident audit).
4. **Lead Pipeline (synthetic)** — leads by **stage** and **source**; suggested follow-ups drafted for Sean to review; no real contact.
5. **Executive Dashboard + Weekly Summary** — approvals, campaign work, leads needing attention, qualified calls, proposals, wins, **revenue by source**, time-to-close; all from synthetic/approved data; measurement documentation-only until approved.

## 5. Conceptual data fields & written data-flow (NO schemas/migrations)
**Conceptual entities (fields illustrative, not a schema):**
- *CampaignBrief*: id, track(founders|small_biz), audience_def, offer, cta, channels_intended, status, owner, timestamps.
- *ContentDraft*: id, campaign_id, format(post|short_video|static_ad|outreach), body_draft (synthetic), claims[], status(draft|in_review|approved|rejected), reviewer_notes.
- *ApprovalRecord*: id, item_ref, checks{factual,brand,privacy,rights,policy}, decision, approver, digest, timestamp.
- *Lead (synthetic)*: id, pseudonymous_ref, stage, source, next_action_draft, owner. **No real PII/message content.**
- *MetricRollup (doc-only)*: period, track, source, counts (calls/proposals/wins), revenue_by_source, time_to_close — **de-identified, approved data only**.

**Written end-to-end flow (future):**
`campaign brief → draft → factual/brand/privacy/rights/policy checks → human approval (Sean/Reviewer) → separately-approved scheduling or outreach → measurement → recommendation`.
Every step writes a tamper-evident audit event; nothing advances past "human approval" without an explicit, separately-approved action; disabled campaigns cannot be bypassed; the engine never raises budgets or acts autonomously.

## 6. Using the website inquiry & discovery-call paths later (without coupling to another product's prod DB)
- **[PROPOSED, separately approved only]** a **read-only, aggregate-only, authenticated, least-privilege, versioned** interface to the Cauldron Technologies **inquiry/booking** flow — surfacing **counts/trends**, not records.
- **Never** direct production-database access; **never** real customer data until data/privacy decisions are approved. Begins read-only + aggregate-only; isolation enforced server-side; consent-aware.
- Until then, the pipeline/dashboard run on **synthetic** data only.

## 7. Security, privacy, consent, audit, retention, product isolation
- **Isolation:** CAUL AI remains a **standalone, private** system — own datastore, auth, RBAC, approval records, audit history. No blending of audiences/products. Any cross-product access is **separately approved, consent-aware, authenticated, least-privilege, versioned, read-only + aggregate-only** at start.
- **Privacy/consent:** synthetic data only now; no PII/message content; future real-data use gated by `CLIENT_OPERATIONS_AND_PRIVACY_SPEC.md` + counsel review; honor consent/comms preferences and export/deletion.
- **Audit:** every draft, check, approval, and status change recorded in the tamper-evident chain (no secrets/PII in payloads).
- **Retention:** short raw retention + de-identified aggregates (consistent with the usage-instrumentation decision brief); documented deletion/purge paths.
- **Autonomy limits + emergency pause:** all publishing/outreach/ads/spend/public claims require human approval; a kill switch disables engine actions while leaving read-only reporting on.

## 8. Phased sequence & testable acceptance criteria
- **Phase 0 (current authorized):** this brief + risks/dependencies/gates/decisions. *Accept:* Sean reviews; status discrepancy acknowledged; approval gate confirmed. **No implementation.**
- **Growth Engine MVP** *(only after explicit foundation acceptance + written implementation approval; isolated dev only)*: campaign planner, draft generation, approval queue, **synthetic** lead pipeline, dashboard. *Accept:* default-deny enforced; no-self-approval on high-risk; approval required before any "publish/send" state; synthetic-only data; 100% coverage; dev-only.
- **Test & review:** permissions, audit history, approval enforcement, synthetic-data handling, emergency pause; privacy/security review. *Accept:* negative tests pass (unauthorized blocked), audit verifies, pause halts actions.
- **Website measurement pilot** *(separate approval)*: authenticated, read-only, aggregate interface to inquiry/booking; no direct DB, no real customer data until approved. *Accept:* aggregate-only proven; isolation + consent checks pass.
- **External channels** *(each separately approved)*: one approved social/email channel at a time via official least-privilege access; human approval for every publication/message; ads/spend need their own budget approval + hard limits. *Accept:* per-channel least-privilege verified; every send gated; spend caps enforced.

## 9. Open decisions requiring Sean's written approval
1. **Resolve the status discrepancy:** is Phase 1A formally accepted, and which stage is authorized next? (Blocks everything below.)
2. Approve the Growth Engine **as a Phase 0 roadmap item** (design only) vs. defer.
3. Confirm the **two-audience separation** and that no other product/audience is blended in.
4. Approve proposed **roles/permissions** (Growth Manager, Content Drafter, Reviewer) and that `growth:approve` is human-only.
5. Confirm **LinkedIn-first** content strategy for Sean and the three draft formats.
6. Approve the **synthetic-only** MVP boundary and that measurement stays documentation-only until a separate decision.
7. Pre-authorize nothing external: confirm that channels/ads/spend each require their own later approval + hard limits.

---
**Authorized now:** this planning document only. **Not authorized:** building the module, any external connection, any production/staging/DB/secret/deploy change, marking any phase accepted. **Next gate:** Sean's written decisions in §9 (starting with the status/acceptance reconciliation).
