# CAUL AI — Audit Integrity Runbook (Phase 1A)

The audit log is **tamper-evident, NOT tamper-proof, and never "immutable."**

## Design
- **Canonical serialization**: `app/canonical.py` — key-sorted, whitespace-free JSON.
- **Hash chain**: each event stores `prev_hash` and `hash = sha256(canonical(body))`,
  where `body` includes `seq`, `timestamp`, actor, action, resource, payload, `prev_hash`.
- **Genesis**: `seq = 0`, `prev_hash = "0"*64`.
- **Concurrency-safe sequencing**: `pg_advisory_xact_lock` per `(chain_env, chain_org)`
  serializes appenders; `UNIQUE(chain_env, chain_org, seq)` is the backstop.
- **Transactional insertion**: the audit row is written in the SAME transaction as the
  business change, so they commit or roll back atomically.
- **Per-environment/org scope**: dev and staging chains never mix (separate DBs + scope).
- **Checkpoints**: `audit_checkpoints` stores independent `(seq, hash)` snapshots.

## DB-level protection
Audit tables are owned by `postgres`. The application role
(`caul_dev_user` / `caul_staging_user`) has **only SELECT + INSERT**; UPDATE / DELETE /
TRUNCATE are **revoked** (`scripts/apply_grants.py`). The app therefore cannot edit or
delete audit history.

## Verification
- **On-write**: chain head read under lock guarantees correct linkage.
- **On-demand**: `GET /api/audit/verify` recomputes the whole chain.
- **Scheduled**: run `verify_chain` periodically (deferred wiring to next milestone).
Detects: `gap_or_reorder`, `duplicate`, `field_tamper`, `hash_mismatch`, `broken_link`.

## Residual risk (documented)
A **DB-owner compromise** (superuser/`postgres`) can rewrite rows and recompute hashes,
defeating detection unless an independent checkpoint was previously exported off-box.
This is why the log is *tamper-evident*, not tamper-proof.

## Integrity-failure response
1. Freeze writes (engage emergency global pause).
2. Compare current head against the last independent checkpoint.
3. Export the chain (`GET /api/audit/export`) and preserve it read-only.
4. Identify the earliest failing `seq` from the verification `issues`.
5. Rotate DB credentials; review DB access logs; file an incident record.
