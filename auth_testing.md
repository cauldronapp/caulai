# CAUL AI — Auth Testing (AUTH STUB — NOT PRODUCTION), PostgreSQL edition

The testing agent should read this file. Auth is a **development/staging stub**; there is
no real IdP and no MFA. Authorization is resolved from PostgreSQL RBAC, not the token.

## Credentials
See `/app/memory/test_credentials.md`. Shared stub password: `StubPass!2026`.
All stub emails end in `.invalid` (non-deliverable, by governance requirement).

## API base
Use the external `REACT_APP_BACKEND_URL` from `/app/frontend/.env`, or `http://localhost:8001`.

## Core flows
1. Login sets an httpOnly `access_token` cookie:
```
curl -c c.txt -X POST $API/api/auth/login -H "Content-Type: application/json" \
  -d '{"email":"admin@example.invalid","password":"StubPass!2026"}'
curl -b c.txt $API/api/auth/me
```
`/me` returns `roles` and the resolved `permissions` array.

2. **Default-deny**: `norole@example.invalid` logs in but every permissioned route returns 403.
3. **Service identity**: `agent-service@example.invalid` login returns **403** (non-interactive).
4. **Session expiry/revocation**: sessions expire after `SESSION_TTL_MINUTES` (default 30);
   `POST /api/auth/logout` revokes the server-side session (subsequent `/me` → 401).

## Adversarial approval checks (backend, pytest)
`cd backend && APP_ENV=dev python -m pytest tests/ -q` runs:
- no self-approval of high-risk, no double-count reviewer, quorum for high-risk,
  no reuse after payload change, no expired reuse, service identity cannot approve,
  permanently_prohibited cannot approve, no execution after revocation, no execution under pause.

## Audit chain
- `GET /api/audit/verify` → `{verified, event_count, head_seq, issues[]}`.
- DB-level: the app user cannot UPDATE/DELETE `audit_events` (owner-enforced).
