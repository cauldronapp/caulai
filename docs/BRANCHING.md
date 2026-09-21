# CAUL AI — Repository & Branching (Phase 1A)

Owner: **Cauldron Technologies, Inc.** · Executive Owner: Sean Gaden
This is a **standalone private repository**, isolated from the Cauldron App
(separate repo, DB, auth, secrets, logs). Never accesses the Cauldron production DB.

## Branching model
- `main` — protected. Requires: PR review, passing CI, security scan, migration check.
  No direct pushes.
- `develop` — integration branch for Phase 1A work.
- `feature/*` — one branch per unit of work; merged into `develop` via PR.
- `feature/cauldron-saas-platform` — **untouched** (belongs to the Cauldron App).

## Required status checks on `main`
1. Route-permission coverage (default-deny, CI-enforced)
2. Unit + integration + audit + adversarial tests
3. Migration validation (`alembic upgrade head`) + DB grants
4. SAST (bandit) + dependency scan (pip-audit)
5. Frontend build

## Least privilege
Single-repo authorization. No org-wide access. Connect the private repo via
Emergent "Save to GitHub" (org OAuth). CI charges (if any) must be flagged before enabling.

## Ownership & export
All code, schemas, migrations and data exports remain owned/controllable by
Cauldron Technologies, Inc. Database export via `pg_dump`; import via `pg_restore`.
See `docs/BACKUP_RESTORE.md`.
