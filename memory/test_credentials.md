# CAUL AI — Test Credentials (AUTH STUB — NOT PRODUCTION)

These are **synthetic** development/staging stub identities. All use **non-deliverable
`*.invalid`** addresses and are seeded ONLY into the dev/staging PostgreSQL databases.
They can never reach a production path (no production environment exists in Phase 1A).

**Shared stub password for all interactive users:** `StubPass!2026`

| Role | Email (login) | Notes |
|------|---------------|-------|
| ExecOwner | `execowner@example.invalid` | "Sean Gaden — Demo ExecOwner", full grant |
| Admin | `admin@example.invalid` | Admin console + approvals + emergency |
| Marketing Manager | `marketing@example.invalid` | Create recommendations |
| Developer | `developer@example.invalid` | Read recs/audit/connectors |
| Security/Compliance | `security@example.invalid` | Audit export/verify + emergency |
| Analyst | `analyst@example.invalid` | Read-only dashboard/recs/audit |
| Auditor | `auditor@example.invalid` | Read-only audit + approvals |
| Agent Service Identity | `agent-service@example.invalid` | **Non-interactive** — login is BLOCKED (403); never approves |
| No-Role / Default-Deny | `norole@example.invalid` | Empty grant; used to verify default-deny (403 everywhere) |

## API base
- Local: `http://localhost:8001`
- External: value of `REACT_APP_BACKEND_URL` in `/app/frontend/.env`

## Auth endpoints
- `POST /api/auth/login` — body `{"email","password"}`, sets httpOnly `access_token` cookie
- `GET  /api/auth/me` — current user (roles + permissions)
- `POST /api/auth/logout` — revokes the server-side session
- `GET  /api/auth/provider` — returns the labeled stub provider metadata

## Notes for testing agent
- Sessions expire after `SESSION_TTL_MINUTES` (default 30) and are revocable server-side.
- Default-deny: any route requires an explicit permission; `norole@example.invalid` should get 403.
- Service identity (`agent-service@example.invalid`) cannot log in interactively (403 by design).
- PostgreSQL is the system of record. No MongoDB.
