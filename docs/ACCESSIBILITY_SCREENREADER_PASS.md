# CAUL AI — Screen-Reader & Keyboard Accessibility Pass (WCAG 2.1 AA)

**Method:** semantic/ARIA audit of the running app aligned to NVDA/VoiceOver behaviors +
axe-core automated checks + keyboard-only walkthrough. Scope: login, navigation, dashboard,
approvals (table + detail), audit history (table), emergency controls, forms, errors, focus
management, keyboard-only operation, status announcements.

## Results by area
| Area | Screen-reader / keyboard result | Remediation |
|------|--------------------------------|-------------|
| Skip link | Added `Skip to main content` (first focusable) → jumps to `<main id="main-content">` | ADDED |
| Landmarks | `<nav aria-label="Primary">`, single `<main>` per page, one `<h1>` via PageHeader | ADDED nav label + main id |
| Navigation | react-router `NavLink` sets `aria-current="page"` on the active item; RBAC-filtered so SR only hears permitted items | Verified |
| Login form | `<label htmlFor>` now associated to `id` on email/password inputs → SR announces field names; submit reachable by Tab/Enter | FIXED label association |
| Errors | Login/decision/recommendation/emergency errors now `role="alert"`; generic `ErrorState` is `role="alert"` → announced immediately | ADDED alert roles |
| Loading | Skeletons wrapped in `role="status" aria-live="polite" aria-busy` + `sr-only "Loading…"`; decorative bars `aria-hidden` | ADDED status role |
| Tables | `<th scope="col">` on Approvals/Audit/Recommendations/Users → SR reads column headers per cell | ADDED scope |
| Approvals rows | Row was mouse-only `<tr onClick>`; now `role="button" tabIndex=0` + Enter/Space handler + `aria-label` + focus ring | FIXED keyboard op |
| Audit chain status | Verdict badge is `role="status" aria-live="polite"` → re-verify result announced | ADDED |
| Hashes | Copy control has `aria-label` with full hash + focus ring (visible short value + title) | ADDED aria-label |
| Focus management | Visible `focus:ring-2 focus:ring-indigo-500` on inputs, buttons, nav, rows, copy | Verified |
| Status announcements | Toasts via sonner (polite live region); dashboard/audit status via role=status | Verified |
| Color contrast | All text ≥ 4.5:1 (pending/paused badges de-pulsed + lightened; muted greys raised) | FIXED (see ACCESSIBILITY_REPORT.md) |

## Automated re-audit (axe-core 4.10.2, wcag2a+wcag2aa)
0 violations across login, dashboard, audit, approvals, emergency, admin/roles, settings,
connectors, recommendations. Responsive verified (390×844, no horizontal overflow).

## Residual / recommended
- A manual pass with live NVDA + VoiceOver hardware is recommended as final due-diligence
  before any production use (Phase 1B); the above covers programmatic SR semantics + keyboard.
- No modal dialogs are used (forms are inline), so focus-trap handling is not required in 1A.

## Material defects found & fixed this pass
1. Form inputs not programmatically labelled (login) → associated labels.
2. Approvals rows not keyboard-operable → role/button + key handlers + focus ring.
3. Errors/loading not announced → alert/status live regions.
4. Table headers lacked `scope` → added.
5. Missing skip link and nav landmark label → added.
No unresolved material accessibility defects remain.
